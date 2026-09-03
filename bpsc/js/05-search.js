/* cross-book super search
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
async function ensureBookSearchIndex(){
  if(bookSearchIndex)return bookSearchIndex;
  if(bookSearchIndexPromise)return bookSearchIndexPromise;
  bookSearchIndexPromise=Promise.all(SUBJECTS_CONFIG.map(async subj=>{
    let data=subjectDataCache[subj.id];
    if(!data){
      try{data=await fetchBookData(subj);subjectDataCache[subj.id]=data;}
      catch(e){console.warn('Super search: skipping '+subj.id,e&&e.message);return[];}
    }
    let idx=0;const out=[];
    (data.chapters||[]).forEach(ch=>{const chName=ch.chapter_name||ch.name||'General';(ch.questions||[]).forEach(q=>{const internal=toInternalQuestion(q,subj.id,idx++,chName);out.push(internal);});});
    return out.map(q=>({q,subject:subj.name,subjectId:subj.id,chapter:q.chapter,sub_topic:q.sub_topic,type:getQuestionType(q)}));
  })).then(arrays=>{const flat=arrays.flat();bookSearchIndex=flat;return flat;}).catch(e=>{bookSearchIndexPromise=null;throw e;});
  return bookSearchIndexPromise;
}
let superSearchState={lastResults:[]};
function openSuperSearch(){
  document.getElementById('supersearch-modal').classList.remove('hidden');
  const sel=document.getElementById('supersearch-subject');
  if(SUBJECTS_CONFIG.length&&sel.options.length<=1){
    sel.innerHTML='<option value="">All subjects</option>'+SUBJECTS_CONFIG.map(s=>`<option value="${escapeHtml(s.id)}">${escapeHtml(s.name)}</option>`).join('');
  }
  ensureBookSearchIndex().then(idx=>{
    const types=[...new Set(idx.map(r=>r.type))].sort();
    const tsel=document.getElementById('supersearch-type');
    if(tsel.options.length<=1){
      tsel.innerHTML='<option value="">All types</option>'+types.map(t=>`<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    }
    const subtopics=[...new Set(idx.map(r=>r.sub_topic).filter(Boolean))].sort();
    const stsel=document.getElementById('supersearch-subtopic');
    const stlbl=document.getElementById('supersearch-subtopic-lbl');
    if(stsel){
      if(subtopics.length>0){
        stsel.style.display='';if(stlbl)stlbl.style.display='';
        stsel.innerHTML='<option value="">All sub-topics</option>'+subtopics.map(st=>`<option value="${escapeHtml(st)}">${escapeHtml(st)}</option>`).join('');
      }else{
        stsel.style.display='none';if(stlbl)stlbl.style.display='none';
      }
    }
  }).catch(()=>{});
  setTimeout(()=>{const i=document.getElementById('supersearch-input');if(i)i.focus();},50);
}
function closeSuperSearch(){document.getElementById('supersearch-modal').classList.add('hidden');}
function superSearchInput(){runSuperSearch();}
function highlightMatch(text,query){
  const esc=escapeHtml(text);
  if(!query)return esc;
  const q=query.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  try{return esc.replace(new RegExp('('+q+')','ig'),'<mark>$1</mark>');}catch(e){return esc;}
}
function runSuperSearch(){
  const input=document.getElementById('supersearch-input');
  const q=(input?input.value:'').trim().toLowerCase();
  const subject=document.getElementById('supersearch-subject').value;
  const type=document.getElementById('supersearch-type').value;
  const subtopic=document.getElementById('supersearch-subtopic')?.value||'';
  const resEl=document.getElementById('supersearch-results');
  const countEl=document.getElementById('supersearch-count');
  const practiceBtn=document.getElementById('supersearch-practice');
  const exportBtn=document.getElementById('supersearch-export-pdf');
  if(!q&&!subject&&!type&&!subtopic){resEl.innerHTML='<div class="search-empty">Type to search across the entire book. Results appear instantly.</div>';countEl.textContent='';if(practiceBtn)practiceBtn.style.display='none';if(exportBtn)exportBtn.style.display='none';return;}
  ensureBookSearchIndex().then(idx=>{
    const results=idx.filter(r=>{
      if(subject&&r.subjectId!==subject)return false;
      if(type&&r.type!==type)return false;
      if(subtopic&&r.sub_topic!==subtopic)return false;
      if(q){
        const hay=[r.q.question,r.q.stem,r.chapter,r.sub_topic,r.q.explanation,r.q.note,r.subject,JSON.stringify(r.q.options||{})].join(' ').toLowerCase();
        if(!hay.includes(q))return false;
      }
      return true;
    });
    superSearchState.lastResults=results;
    if(practiceBtn)practiceBtn.style.display=results.length?'':'none';
    if(exportBtn)exportBtn.style.display=results.length?'':'none';
    countEl.textContent=results.length+' result'+(results.length!==1?'s':'');
    if(!results.length){resEl.innerHTML='<div class="search-empty">No matching questions. Try another keyword.</div>';return;}
    resEl.innerHTML=results.slice(0,200).map((r,i)=>{
      const text=bookText(r.q.question||'');
      const snippet=text.length>220?text.slice(0,220)+'…':text;
      return `<div class="search-result" onclick="superSearchOpen('${i}')">
        <div class="sr-top">
          <span class="sr-subj">${escapeHtml(r.subject)}</span>
          <span class="sr-chapter">${escapeHtml(r.chapter||'')}</span>
          ${topicPillHtml(r.q)}
          <span class="question-type-pill">${escapeHtml(r.type)}</span>
        </div>
        <div class="sr-q">${highlightMatch(snippet,q)}</div>
      </div>`;
    }).join('')+(results.length>200?`<div class="search-empty">Showing first 200 of ${results.length}. Narrow your search to see more.</div>`:'');
  }).catch(()=>{resEl.innerHTML='<div class="search-empty">Search could not load the question bank. Try again.</div>';});
}
function superSearchOpen(i){
  const r=(superSearchState.lastResults||[])[i];if(!r)return;
  closeSuperSearch();
  selectedChapters=new Set([r.chapter]);
  currentSubjectId=r.subjectId;
  processData({chapters:[]},currentSubjectId||'search');
  allQuestions=[r.q];if(!chapterMap[r.chapter])chapterMap[r.chapter]=[];chapterMap[r.chapter].push(r.q);
  startQuiz('supersearch',[r.q]);
}
function practiceSuperSearch(){
  const results=superSearchState.lastResults||[];
  if(!results.length){alert('No results to practice yet.');return;}
  closeSuperSearch();
  const pool=results.map(r=>r.q);
  selectedChapters=new Set(pool.map(q=>q.chapter));
  currentSubjectId=pool[0].subjectId||null;
  processData({chapters:[]},currentSubjectId||'search');
  allQuestions=pool;pool.forEach(q=>{if(!chapterMap[q.chapter])chapterMap[q.chapter]=[];chapterMap[q.chapter].push(q);});
  startQuiz('supersearch',pool);
}

// ════════════════════════════════════════════════════════════════
// FOCUS / POMODORO TIMER
// ════════════════════════════════════════════════════════════════
let focusTimerInterval=null,focusRunning=false,focusMode='25',focusTotal=25*60,focusRemaining=25*60;
