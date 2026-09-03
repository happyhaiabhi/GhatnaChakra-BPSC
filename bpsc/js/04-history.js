/* attempt history, study-notes screen
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function recordAttempt(meta){
  const attempts=getAttempts();
  attempts.unshift(Object.assign({id:'att_'+Date.now()+'_'+Math.random().toString(36).slice(2,7),date:new Date().toISOString()},meta));
  if(attempts.length>50)attempts.pop();
  saveAttempts(attempts);
}

function showNotesScreen(){
  showScreen('notes-screen');
}

function backFromNotes(){
  clearInterval(timerInterval);
  if(currentBook){ showScreen('setup-screen'); buildDashboard(); }
  else { showScreen('books-screen'); renderBooksScreen(); }
}

function showHistoryScreen(){
  const attempts=getAttempts();
  const list=document.getElementById('history-list');
  document.getElementById('history-count-lbl').textContent=attempts.length+' attempt'+(attempts.length!==1?'s':'');
  if(!attempts.length){list.innerHTML='<div class="search-empty">No attempts yet. Finish a quiz and it will be recorded here. 🌱</div>';showScreen('history-screen');return;}
  list.innerHTML=attempts.map(a=>{
    const total=a.total||0,c=a.correct||0,w=a.wrong||0,s=a.skip||0,barW=total||1;
    const pct=total?Math.round(c/total*100):0;
    const date=new Date(a.date);
    return `<div class="history-item">
      <div class="history-item-top">
        <span class="history-subj">${escapeHtml(a.subject||'Quiz')}</span>
        ${a.chapter?`<span class="sr-chapter">${escapeHtml(a.chapter)}</span>`:''}
        <span class="history-date">${escapeHtml(date.toLocaleString())}</span>
      </div>
      <div class="history-stats">
        <span class="history-stat" style="color:var(--gold);">Score: <b>${pct}%</b></span>
        <span class="history-stat" style="color:var(--green);">&#x2713; ${c}</span>
        <span class="history-stat" style="color:var(--red);">&#x2717; ${w}</span>
        <span class="history-stat" style="color:var(--text3);">— ${s}</span>
        <span class="history-stat" style="color:var(--blue);">&#x23F1; ${escapeHtml(formatDuration(a.durationMs||0))}</span>
      </div>
      <div class="history-bar"><div class="hb-c" style="flex:0 0 ${(c/barW*100)}%"></div><div class="hb-w" style="flex:0 0 ${(w/barW*100)}%"></div><div class="hb-s" style="flex:0 0 ${(s/barW*100)}%"></div></div>
      <div class="history-actions">
        <button class="modal-btn modal-btn-secondary" onclick="viewAttemptDetails('${escapeHtml(a.id)}')">&#x1F4CB; Details</button>
        <button class="modal-btn modal-btn-secondary" onclick="openExportModal('history','${escapeHtml(a.id)}')">&#x1F4C4; PDF</button>
        ${w>0?`<button class="modal-btn modal-btn-secondary" style="color:var(--red);border-color:var(--red);" onclick="retryAttemptSubset('${escapeHtml(a.id)}','wrong')">&#x2717; Retry Wrong (${w})</button>`:''}
        ${s>0?`<button class="modal-btn modal-btn-secondary" style="color:var(--text2);" onclick="retryAttemptSubset('${escapeHtml(a.id)}','skips')">&#8212; Retry Skipped (${s})</button>`:''}
        <button class="modal-btn modal-btn-primary" onclick="redoAttempt('${escapeHtml(a.id)}')">&#x1F504; Re-practice</button>
      </div>
    </div>`;
  }).join('');
  showScreen('history-screen');
}
function clearAllAttempts(){if(confirm('Delete the entire attempt history? This cannot be undone.')){saveAttempts([]);showHistoryScreen();}}
function redoAttempt(id){
  const a=getAttempts().find(x=>x.id===id);if(!a)return;
  const uids=(a.questions||[]).filter(Boolean);
  if(!uids.length){alert('This attempt has no stored questions to re-practice.');return;}
  ensureSyncQuestionCatalog().then(catalog=>{
    const pool=uids.map(uid=>catalog[uid]).filter(Boolean);
    if(!pool.length){alert('Those questions are not available in the current book.');return;}
    selectedChapters=new Set(pool.map(q=>q.chapter));
    currentSubjectId=pool[0]._subjectId||null;
    processData({chapters:[]},currentSubjectId||'redo');
    allQuestions=pool;pool.forEach(q=>{if(!chapterMap[q.chapter])chapterMap[q.chapter]=[];chapterMap[q.chapter].push(q);});
    startQuiz('history',pool);
  }).catch(()=>{alert('Could not load the questions for this attempt.');});
}

// Rebuild a lastResults array for a stored attempt. New attempts store each
// question's outcome ({uid, userKey}); attempts recorded before that (legacy)
// are reconstructed from the Mistakes / Skips banks that submission updates.
async function buildAttemptResults(a){
  const uids=(a.questions||[]).filter(Boolean);
  const catalog=await ensureSyncQuestionCatalog();
  const stored=Array.isArray(a.results)?new Map(a.results.filter(r=>r&&r.uid).map(r=>[r.uid,r])):null;
  const mistakes=getMistakes(),skips=getSkips();
  let recovered=false;
  const out=[];
  uids.forEach(uid=>{
    const q=catalog[uid];if(!q)return;
    if(stored&&stored.has(uid)){
      const userKey=(stored.get(uid)||{}).userKey??null;
      const isSkipped=isSkippedAnswer(userKey);
      out.push({q,userKey,isCorrect:!isSkipped&&isQuestionCorrect(q,userKey),isSkipped});
    }else{
      recovered=true;
      const m=mistakes[uid];
      if(m&&m.q)out.push({q,userKey:m.userKey??null,isCorrect:false,isSkipped:false});
      else if(skips[uid]&&skips[uid].q)out.push({q,userKey:null,isCorrect:false,isSkipped:true});
      else out.push({q,userKey:null,isCorrect:true,isSkipped:false});
    }
  });
  out.recovered=recovered;
  return out;
}

// Open the same result screen shown right after submission — score, counts,
// time, question review with correct answers + explanations, and the
// Retry Wrong / Retry Skipped buttons — for a past attempt.
async function viewAttemptDetails(id){
  const a=getAttempts().find(x=>x.id===id);if(!a)return;
  let results;
  try{results=await buildAttemptResults(a);}
  catch(e){alert('Could not load the questions for this attempt.');return;}
  if(!results.length){alert('This attempt has no stored questions to review.');return;}
  lastResults=results;
  shuffledOptionOrders=[];
  const correct=a.correct??results.filter(r=>r.isCorrect).length;
  const wrong=a.wrong??results.filter(r=>!r.isCorrect&&!r.isSkipped).length;
  const skip=a.skip??results.filter(r=>r.isSkipped).length;
  const pct=a.pct??(results.length?Math.round(correct/results.length*100):0);
  const date=new Date(a.date).toLocaleString();
  document.getElementById('res-eyebrow').innerHTML=`${escapeHtml(a.subject||'Quiz')} &#183; ${escapeHtml(String(a.chapter||'').substring(0,50))} &#183; attempt of ${escapeHtml(date)}${results.recovered?' &#183; reconstructed':''}`;
  document.getElementById('res-score').textContent=pct+'%';
  document.getElementById('res-score').style.color=pct>=70?'var(--green)':pct>=50?'var(--gold)':'var(--red)';
  document.getElementById('res-grade').textContent=pct>=80?'\uD83C\uDFC6 Excellent!':pct>=60?'\u2705 Good Performance':pct>=40?'\u26A1 Keep Practicing':'\uD83D\uDCD6 Needs More Practice';
  document.getElementById('rs-correct').textContent=correct;
  document.getElementById('rs-wrong').textContent=wrong;
  document.getElementById('rs-skip').textContent=skip;
  document.getElementById('rs-time').textContent=formatDuration(a.durationMs||0);
  document.getElementById('btn-retry-wrong').style.display=wrong>0?'':'none';
  document.getElementById('btn-retry-skip').style.display=skip>0?'':'none';
  const expBtn=document.getElementById('btn-export-pdf-result');if(expBtn)expBtn.onclick=()=>openExportModal('history',id);
  resetReviewFilter();
  buildReview('all');
  buildTopicBreakdown();
  resultBackTo='history';
  document.getElementById('btn-back-home').innerHTML='&#x2190; Back to History';
  showScreen('result-screen');
}

// Re-attempt only the wrong (kind='wrong') or only the skipped (kind='skips')
// questions of a past attempt. Runs like a normal quiz: timer, submission,
// its own result screen and its own history entry.
function retryAttemptSubset(id,kind){
  const a=getAttempts().find(x=>x.id===id);if(!a)return;
  buildAttemptResults(a).then(results=>{
    const pool=results.filter(r=>kind==='skips'?r.isSkipped:(!r.isCorrect&&!r.isSkipped)).map(r=>r.q);
    if(!pool.length){alert(kind==='skips'?'No skipped questions could be recovered for this attempt.':'No wrong questions could be recovered for this attempt.');return;}
    selectedChapters=new Set(pool.map(q=>q.chapter));
    currentSubjectId=pool[0]._subjectId||a.subjectId||null;
    processData({chapters:[]},currentSubjectId||kind);
    allQuestions=pool;pool.forEach(q=>{if(!chapterMap[q.chapter])chapterMap[q.chapter]=[];chapterMap[q.chapter].push(q);});
    startQuiz(kind,pool);
  }).catch(()=>{alert('Could not load the questions for this attempt.');});
}

// ════════════════════════════════════════════════════════════════
// SUPER SEARCH — instant search across every question in the book
// ════════════════════════════════════════════════════════════════
let bookSearchIndex=null,bookSearchIndexPromise=null;
