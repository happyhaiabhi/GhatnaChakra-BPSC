/* quiz engine: options, palette, timer, submit, results review
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function renderQuestion(){
  const i=state.current,q=quiz[i],options=q.options||{};const optionKeys=shuffledOptionOrders[i]||Object.keys(options);const answered=state.answers[i],isMarked=state.marked[i];
  const pct=((i+1)/quiz.length)*100;document.getElementById('progress-bar').style.width=pct+'%';
  const examLabel=[q.exam,q.year&&q.year!=='Unknown'&&q.year!==q.exam?q.year:''].filter(Boolean).join(' · ');
  const presentation=renderQuestionStem(q,'quiz'),matchData=presentation.matchData;
  let optHtml='';
  if(matchData)optHtml=renderMatchOptions(matchData,optionKeys,answered);
  else optHtml=optionKeys.map(key=>{const value=options[key];if(value==null||value==='')return '';let cls='opt-btn';if(answerHasKey(answered,key))cls+=' selected';const text=optionDisplayText(value,key);return `<button class="${cls}" onclick="selectOption('${escapeHtml(key)}')" aria-label="Option ${escapeHtml(key)}: ${escapeHtml(text)}"><span class="opt-text">${escapeHtml(text)}</span></button>`;}).join('');
  const isMulti=questionCorrectKeys(q).length>1;
  document.getElementById('question-area').innerHTML=`<div class="q-header"><span class="q-num">Q ${i+1} / ${quiz.length}</span><span class="question-type-pill">${escapeHtml(presentation.type)}</span>${topicPillHtml(q)}${examLabel?`<span class="q-exam-tag">${escapeHtml(examLabel)}</span>`:''} ${isMarked?`<span style="font-size:0.65rem;background:var(--purple-dim);color:var(--purple);border:1px solid var(--purple);padding:3px 8px;border-radius:4px;">&#x2691; Marked</span>`:''}</div><div class="q-card ${matchData?'q-card-match':''}">${presentation.html}</div>${matchData?'<div class="match-code-caption">Answer codes</div>':''}${isMulti?'<div class="multi-answer-hint">Multiple answers are correct — select every correct option.</div>':''}<div class="options-grid ${matchData?'match-options-grid':''}">${optHtml}</div>`;
  if(i===quiz.length-1){document.getElementById('btn-next').style.display='none';document.getElementById('btn-submit').style.display='';}
  else{document.getElementById('btn-next').style.display='';document.getElementById('btn-submit').style.display='none';}
  const bookmarks=getBookmarks(),bBtn=document.getElementById('btn-bookmark');
  if(bBtn){const isB=!!bookmarks[quiz[i]?.uid];const bIc=bBtn.querySelector('.na-ic');if(bIc)bIc.textContent=isB?'\uD83D\uDD16 \u2713':'\uD83D\uDD16';bBtn.classList.toggle('is-bookmarked',isB);bBtn.style.borderColor=isB?'var(--cyan)':'var(--border)';bBtn.style.background=isB?'var(--cyan-dim)':'var(--surface2)';}
}

function selectOption(key){
  const q=quiz[state.current],multi=questionCorrectKeys(q).length>1;
  if(multi){const selected=selectedAnswerKeys(state.answers[state.current]);const next=selected.includes(key)?selected.filter(item=>item!==key):[...selected,key];state.answers[state.current]=next.length?next:null;}
  else state.answers[state.current]=key;
  renderQuestion();renderPalette();updateStats();
}
function toggleBookmark(){const q=quiz[state.current];if(!q)return;const b=getBookmarks();if(b[q.uid])removeFromBookmarks(q.uid,false);else addToBookmarks(q);renderQuestion();}
function saveAndNext(){if(state.current<quiz.length-1){state.current++;state.visited[state.current]=true;renderQuestion();renderPalette();updateStats();}}
function goToPrev(){if(state.current>0){state.current--;renderQuestion();renderPalette();updateStats();}}
function markForReview(){state.marked[state.current]=!state.marked[state.current];renderQuestion();renderPalette();updateStats();}
function clearResponse(){state.answers[state.current]=null;renderQuestion();renderPalette();updateStats();}

function setPaletteOpen(isOpen){
  const body=document.getElementById('quiz-body'),button=document.getElementById('palette-toggle'),icon=document.getElementById('palette-toggle-icon');
  if(!body)return;
  body.classList.toggle('palette-collapsed',!isOpen);
  if(button){
    button.setAttribute('aria-expanded',String(isOpen));
    button.setAttribute('aria-label',isOpen?'Hide question palette':'Show question palette');
    button.title=isOpen?'Hide question palette':'Show question palette';
  }
  if(icon)icon.textContent=isOpen?'\u203A':'\u2039';
}
function togglePalette(){
  const body=document.getElementById('quiz-body');
  if(body)setPaletteOpen(body.classList.contains('palette-collapsed'));
}
function renderPalette(){
  document.getElementById('palette-grid').innerHTML=quiz.map((q,i)=>{let cls='pal-btn',answered=!isSkippedAnswer(state.answers[i]);if(i===state.current)cls+=' current';else if(answered&&state.marked[i])cls+=' answered-marked';else if(answered)cls+=' answered';else if(state.marked[i])cls+=' marked';else if(state.visited[i])cls+=' visited';return `<button class="${cls}" onclick="jumpTo(${i})">${i+1}</button>`;}).join('');
}
function jumpTo(i){state.current=i;state.visited[i]=true;renderQuestion();renderPalette();updateStats();}
function updateStats(){const ans=state.answers.filter(a=>!isSkippedAnswer(a)).length,mark=state.marked.filter(Boolean).length,skip=quiz.length-ans;const put=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v;};put('stat-ans',ans);put('stat-skip',skip);put('stat-mark',mark);put('pal-count-ans',ans);put('pal-count-skip',skip);put('pal-count-mark',mark);}

function startTimer(){let remaining=totalSecs;document.getElementById('timer-display').textContent=formatTime(remaining);timerInterval=setInterval(()=>{if(paused)return;remaining--;document.getElementById('timer-display').textContent=formatTime(remaining);if(remaining<=60)document.getElementById('timer-display').classList.add('urgent');if(remaining<=0){clearInterval(timerInterval);submitQuiz();}},1000);}
function togglePause(){paused=!paused;document.getElementById('pause-btn').textContent=paused?'Resume':'Pause';}
function formatTime(s){const m=Math.floor(s/60),sec=s%60;return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;}
function formatDuration(ms){const s=Math.floor(ms/1000),m=Math.floor(s/60),sec=s%60;return m>0?`${m}m ${sec}s`:`${sec}s`;}

// SUBMIT - skipped questions do NOT block submission (iPad/mobile fix)
function submitQuiz(){
  const skippedCount=state.answers.filter(isSkippedAnswer).length;
  if(skippedCount>0){const go=confirm(`${skippedCount} question${skippedCount!==1?'s are':' is'} unanswered (skipped). Submit anyway?`);if(!go)return;}
  clearInterval(timerInterval);
  const elapsed=new Date()-quizMeta.startTime;let correct=0,wrong=0;
  lastResults=quiz.map((q,i)=>{const userKey=state.answers[i],isCorrect=isQuestionCorrect(q,userKey),isSkipped=isSkippedAnswer(userKey);if(isCorrect)correct++;else if(!isSkipped)wrong++;return{q,userKey,isCorrect,isSkipped};});
  const h=getHistory();h.unshift({date:new Date().toISOString(),correct,wrong,total:quiz.length,subject:currentSubjectId,chapter:Array.from(selectedChapters).join(',')});if(h.length>50)h.pop();saveHistory(h);
  const wr=lastResults.filter(r=>!r.isCorrect&&!r.isSkipped);const cr=lastResults.filter(r=>r.isCorrect);const sr=lastResults.filter(r=>r.isSkipped);
  if(wr.length)addToMistakes(wr);if(sr.length)addToSkips(sr.map(r=>r.q));if(cr.length)processCorrectAnswers(cr);
  const pct=Math.round(correct/quiz.length*100),skip=quiz.length-correct-wrong;
  const subj=SUBJECTS_CONFIG.find(s=>s.id===currentSubjectId);const chLabel=quizMeta.chapter||'';
  recordAttempt({subjectId:currentSubjectId,subject:subj?.name||'',chapter:chLabel,mode:quizMeta.mode,correct,wrong,skip,total:quiz.length,pct,durationMs:elapsed,questions:quiz.map(q=>q.uid),results:quiz.map((q,i)=>({uid:q.uid,userKey:state.answers[i]??null}))});
  resultBackTo=null;
  document.getElementById('btn-back-home').innerHTML='&#x2190; Back to Home';
  const expBtn=document.getElementById('btn-export-pdf-result');if(expBtn)expBtn.onclick=()=>openExportModal('result');
  document.getElementById('res-eyebrow').innerHTML=`${escapeHtml(subj?.name||'')} &#183; ${escapeHtml(chLabel.substring(0,50))}`;
  document.getElementById('res-score').textContent=pct+'%';document.getElementById('res-score').style.color=pct>=70?'var(--green)':pct>=50?'var(--gold)':'var(--red)';
  document.getElementById('res-grade').textContent=pct>=80?'\uD83C\uDFC6 Excellent!':pct>=60?'\u2705 Good Performance':pct>=40?'\u26A1 Keep Practicing':'\uD83D\uDCD6 Needs More Practice';
  document.getElementById('rs-correct').textContent=correct;document.getElementById('rs-wrong').textContent=wrong;document.getElementById('rs-skip').textContent=skip;document.getElementById('rs-time').textContent=formatDuration(elapsed);
  document.getElementById('btn-retry-wrong').style.display=wrong>0?'':'none';
  document.getElementById('btn-retry-skip').style.display=skip>0?'':'none';
  resetReviewFilter();
  buildTopicBreakdown();
  buildReview('all');showScreen('result-screen');buildDashboard();
}

function retryWrong(){const wrong=lastResults.filter(r=>!r.isCorrect&&!r.isSkipped).map(r=>r.q);if(!wrong.length)return;if(wrong[0]._subjectId)currentSubjectId=wrong[0]._subjectId;selectedChapters=new Set(wrong.map(q=>q.chapter));startQuiz('wrong',wrong);}
function retrySkipped(){const skipped=lastResults.filter(r=>r.isSkipped).map(r=>r.q);if(!skipped.length)return;if(skipped[0]._subjectId)currentSubjectId=skipped[0]._subjectId;selectedChapters=new Set(skipped.map(q=>q.chapter));startQuiz('skips',skipped);}
function resultBack(){if(resultBackTo==='history'){resultBackTo=null;showHistoryScreen();}else backToSetup();}
function resetReviewFilter(){const btns=document.querySelectorAll('.rflt-btn');btns.forEach((b,i)=>b.classList.toggle('active',i===0));}

// Topic-wise ✓/✗/— breakdown for test-series attempts (2+ distinct topics)
function buildTopicBreakdown(){
  const wrap=document.getElementById('res-topic-wrap');if(!wrap)return;
  const withTopics=lastResults.filter(r=>r.q&&(r.q.topic||r.q.sub_topic));
  const distinct=[...new Set(withTopics.map(r=>r.q.topic||r.q.sub_topic))];
  if(distinct.length<2){wrap.style.display='none';wrap.innerHTML='';return;}
  const rows=distinct.map(topic=>{
    const rs=withTopics.filter(r=>(r.q.topic||r.q.sub_topic)===topic);
    const c=rs.filter(r=>r.isCorrect).length,w=rs.filter(r=>!r.isCorrect&&!r.isSkipped).length,s=rs.filter(r=>r.isSkipped).length;
    return{topic,n:rs.length,c,w,s,acc:Math.round(c/rs.length*100)};
  }).sort((a,b)=>b.n-a.n);
  wrap.style.display='';
  wrap.innerHTML=`<div class="review-header"><h3>&#127991;&#65039; Topic-wise Performance</h3><span style="font-size:.62rem;color:var(--text3);">${rows.length} topics</span></div>
  <div style="padding:4px 10px 10px;overflow-x:auto;"><table class="topic-table">
  <thead><tr><th style="text-align:left;padding-left:8px;">Topic</th><th>Q</th><th style="color:var(--green);">&#10003;</th><th style="color:var(--red);">&#10007;</th><th>&#8212;</th><th>Score</th></tr></thead>
  <tbody>${rows.map(r=>`<tr><td style="text-align:left;padding:8px;color:var(--text);font-weight:700;">${TOPIC_EMOJI[r.topic]||''} ${escapeHtml(r.topic)}</td><td>${r.n}</td><td style="color:var(--green);font-weight:700;">${r.c}</td><td style="color:var(--red);font-weight:700;">${r.w}</td><td style="color:var(--text3);">${r.s}</td><td style="font-weight:800;color:${r.acc>=70?'var(--green)':r.acc>=40?'var(--gold)':'var(--red)'};">${r.acc}%</td></tr>`).join('')}</tbody></table></div>`;
}

function buildReview(filter){
  document.getElementById('review-body').innerHTML=lastResults.map((r,idx)=>{
    const{q,userKey,isCorrect,isSkipped}=r;const status=isSkipped?'skipped':isCorrect?'correct':'wrong';const show=filter==='all'||filter===status;
    const examLabel=[q.exam,q.year&&q.year!=='Unknown'&&q.year!==q.exam?q.year:''].filter(Boolean).join(' · ');
    const optKeys=shuffledOptionOrders[idx]||Object.keys(q.options||{}),correctKeys=questionCorrectKeys(q);
    const presentation=renderQuestionStem(q,'review'),matchData=presentation.matchData;
    const optHtml=matchData?renderMatchReviewOptions(matchData,optKeys,correctKeys,userKey,isCorrect):optKeys.map(k=>{const value=q.options[k];if(value==null||value==='')return '';let cls='rev-opt';if(correctKeys.includes(k))cls+=' correct-ans';else if(answerHasKey(userKey,k)&&!isCorrect)cls+=' user-wrong';return `<div class="${cls}">${escapeHtml(optionDisplayText(value,k))}</div>`;}).join('');
    return `<div class="review-item ${show?'show':''}" data-status="${status}"><div class="rev-meta"><span class="rev-num">Q${idx+1}</span><span class="question-type-pill">${escapeHtml(presentation.type)}</span>${topicPillHtml(q)}${examLabel?`<span class="rev-exam">${escapeHtml(examLabel)}</span>`:''}<span class="rev-correct-badge ${status}">${isSkipped?'SKIPPED':isCorrect?'CORRECT':'WRONG'}</span></div>${presentation.html}<div class="rev-options ${matchData?'match-review-options':''}">${optHtml}</div>${q.explanation?`<div class="rev-exp">${bookText(q.explanation)}</div>`:''}${q.note?`<div class="exp-note"><b>&#9888; Note:</b> ${bookText(q.note)}</div>`:''}</div>`;
  }).join('');
}

function filterReview(filter,btn){document.querySelectorAll('.rflt-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');document.querySelectorAll('.review-item').forEach(el=>{el.classList.toggle('show',filter==='all'||el.dataset.status===filter);});}

