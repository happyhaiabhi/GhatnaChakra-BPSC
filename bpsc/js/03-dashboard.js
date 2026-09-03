/* dashboard, weekly chart, bloom bank and the four review banks
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function normalizeAnswerKeys(value,options){
  const values=Array.isArray(value)?value:[value];
  const keys=values.map(v=>String(v??'').trim().toUpperCase()).filter(Boolean);
  const unique=[...new Set(keys)];
  const valid=unique.filter(key=>Object.prototype.hasOwnProperty.call(options||{},key));
  return valid.length?valid:unique;
}

function toInternalQuestion(q,subjId,idx,chName){
  // Preserve the complete source object (asset/images/type/question_type/note
  // and future fields) before overlaying only the normalized engine fields.
  // The sync catalog calls this same mapper, so hydrated bank entries retain
  // exactly the same rich question data as a freshly loaded quiz.
  const options=q.options||{};
  const rawAnswer=q.answer??q.correct_option??q.correctKey??'A';
  const correctKeys=normalizeAnswerKeys(rawAnswer,options);
  const correctKey=correctKeys.length===1?correctKeys[0]:correctKeys;
  const mappedAnswer=correctKeys.map(key=>options[key]).filter(Boolean).join(' • ');
  const sub_topic=String(q.sub_topic||q.subtopic||q.topic||q.subTopic||'').trim();
  return Object.assign({},q,{
    uid:q.uid||`${subjId}_${idx}`,
    _subjectId:subjId,
    chapter:chName,
    sub_topic,
    topic:sub_topic,
    exam:q.exam||'',
    year:q.year||'',
    question:q.q||q.question||'',
    options,
    correctKey,
    correctKeys,
    correctAnswer:q.correct_answer||q.correctAnswer||mappedAnswer,
    explanation:q.explanation||'',
    note:q.note||''
  });
}

function processData(data,subjId){
  allQuestions=[];chapterMap={};chapterSubtopicsMap={};subjectSubtopics=new Set();selectedSubtopics=new Set();let idx=0;
  (data.chapters||[]).forEach(ch=>{
    const chName=ch.chapter_name||ch.name||'General';chapterMap[chName]=[];chapterSubtopicsMap[chName]=new Set();
    (ch.questions||[]).forEach(q=>{
      const internal=toInternalQuestion(q,subjId,idx++,chName);
      allQuestions.push(internal);chapterMap[chName].push(internal);
      if(internal.sub_topic){
        chapterSubtopicsMap[chName].add(internal.sub_topic);
        subjectSubtopics.add(internal.sub_topic);
      }
    });
  });
}

function updateHeroCounts(){
  let totalCh=0,totalQ=0;
  Object.values(subjectDataCache).forEach(data=>{const chs=data.chapters||[];totalCh+=chs.length;chs.forEach(ch=>{totalQ+=(ch.questions||[]).length;});});
  document.getElementById('sh-chapters').textContent=totalCh>0?totalCh.toLocaleString():'--';
  document.getElementById('sh-questions').textContent=totalQ>0?totalQ.toLocaleString():'--';
}

function buildDashboard(){
  const h=getHistory()||[],mistakes=Object.keys(getMistakes()).length;
  const ta=h.reduce((s,e)=>s+(e.correct||0)+(e.wrong||0),0),tc=h.reduce((s,e)=>s+(e.correct||0),0);
  const acc=ta>0?Math.round(tc/ta*100):0;
  document.getElementById('dash-accuracy').textContent=ta>0?acc+'%':'--';
  document.getElementById('dash-attempted').textContent=ta;document.getElementById('dash-sessions').textContent=h.length;document.getElementById('dash-mistakes').textContent=mistakes;
  document.getElementById('dash-meta').textContent=h.length?'Last: '+new Date(h[0].date).toLocaleDateString():'No sessions yet';
  const pctEl=document.getElementById('dash-ring-pct'),ring=document.getElementById('dash-ring-fill'),C=2*Math.PI*42;
  if(pctEl)pctEl.textContent=ta>0?acc+'%':'--';
  if(ring){ring.style.strokeDasharray=C;ring.style.strokeDashoffset=C*(1-Math.min(100,acc)/100);}
  buildWeeklyChart(h);
}
function buildWeeklyChart(h){
  h=h||[];
  const days=[];
  const now=new Date();
  const localKey=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  for(let i=6;i>=0;i--){const d=new Date(now);d.setDate(now.getDate()-i);days.push({key:localKey(d),label:d.toLocaleDateString(undefined,{weekday:'narrow'}),correct:0,wrong:0});}
  const map=new Map(days.map(d=>[d.key,d]));
  h.forEach(e=>{const key=localKey(new Date(e.date));const day=map.get(key);if(day){day.correct+=Number(e.correct)||0;day.wrong+=Number(e.wrong)||0;}});
  const total=days.reduce((s,d)=>s+d.correct+d.wrong,0);
  const dwTotal=document.getElementById('dw-total');if(dwTotal)dwTotal.textContent=total.toLocaleString()+' Qs';
  const chart=document.getElementById('weekly-chart');if(!chart)return;
  const max=Math.max(1,...days.map(d=>d.correct+d.wrong));
  if(total===0){chart.innerHTML='<div class="dw-empty">Complete a quiz to grow this garden 🌱</div>';return;}
  chart.innerHTML=days.map(d=>{
    const n=d.correct+d.wrong,height=Math.max(n?10:2,Math.round(n/max*100));
    return `<div class="dw-day"><div class="dw-bar-wrap"><div class="dw-bar" title="${d.correct} correct · ${d.wrong} wrong" style="height:${height}%"></div></div><div class="dw-day-label">${d.label}</div></div>`;
  }).join('');
}

function practiceFromBank(bank,mode){
  const pool=Object.values(bank).map(e=>e.q).filter(Boolean);if(!pool.length){alert('No questions in this filter!');return;}
  currentSubjectId=pool[0]._subjectId||null;processData({chapters:[]},currentSubjectId||'bank');allQuestions=pool;
  pool.forEach(q=>{if(!chapterMap[q.chapter])chapterMap[q.chapter]=[];chapterMap[q.chapter].push(q);});
  selectedChapters=new Set(pool.map(q=>q.chapter));startQuiz(mode,pool);
}

// ════════════════════════════════════════════════════════════════
// BLOOM REVIEW — spaced repetition for mistakes and skips
// ════════════════════════════════════════════════════════════════
function bloomFilteredDue(){
  const active=bankTypeFilters.bloom||'all';
  const due=getBloomDue().filter(e=>active==='all'||e.source===active);
  const q=(bankSearch.bloom||'').trim().toLowerCase();
  return q?due.filter(e=>bankSearchText(e).includes(q)):due;
}
function renderBloomTypeFilters(items){
  const counts={all:items.length,mistake:0,skip:0};
  items.forEach(e=>{counts[e.source]=(counts[e.source]||0)+1;});
  const active=bankTypeFilters.bloom;
  const chips=[['all','All',counts.all],['mistake','&#x1F534; Mistakes',counts.mistake],['skip','&#x23ED; Skipped',counts.skip]];
  const el=document.getElementById('bloom-type-filters');if(!el)return;
  el.innerHTML=chips.map(([value,label,count])=>`<button class="bank-filter-chip ${active===value?'active':''}" data-type="${value}" onclick="setBankTypeFilter('bloom','${value}')">${label} <span class="bank-filter-count">${count}</span></button>`).join('');
}
function bloomDueLabel(e){
  const t=Date.parse(e.nextReviewAt||e.addedAt||0);
  if(!Number.isFinite(t))return 'Due today';
  const diff=t-Date.now();
  if(diff<=0)return 'Due today';
  const days=Math.ceil(diff/DAY_MS);
  return days<=1?'Today':'In '+days+' days';
}
function bloomItemHtml(e){
  const q=e.q||{},questionType=getQuestionType(q),streak=Number(e.correctCount)||0;
  const dots=Array.from({length:MASTERY},(_,i)=>`<div class="cc-dot ${i<streak?'filled':''}"></div>`).join('');
  return `<div class="bank-item bloom-item ${bloomEntryDue(e)?'due-today':''}"><div class="bank-item-top"><span class="bloom-src ${e.source}">${e.source==='mistake'?'Mistake':'Skip'}</span><span class="question-type-pill">${escapeHtml(questionType)}</span>${topicPillHtml(q)}<span class="bloom-interval">Next: ${escapeHtml(bloomDueLabel(e))}</span><span class="bank-times" style="margin-left:auto;">${escapeHtml(q.chapter||'')}</span></div>${renderQuestionStem(q,'bank').html}<div class="bank-ans">&#x2713; ${bookText(questionCorrectAnswerLabel(q))}</div><div class="cc-dots">${dots}<span class="cc-label">bloom mastery</span></div></div>`;
}
function showBloomScreen(){
  const all=getBloomDue(),visible=bloomFilteredDue();
  renderBloomTypeFilters(all);
  const countLbl=document.getElementById('bloom-count-lbl');if(countLbl)countLbl.textContent=`${visible.length} of ${all.length} due`;
  const list=document.getElementById('bloom-list');
  if(!list)return;
  list.innerHTML=visible.length?visible.map(bloomItemHtml).join(''):`<div style="padding:30px;text-align:center;color:var(--text3);font-size:0.82rem;">${BANK_EMPTY_HTML.bloom}</div>`;
  showScreen('bloom-screen');
}
function practiceFromBloom(){
  const entries=bloomFilteredDue();
  const pool=entries.map(e=>e.q).filter(Boolean);
  if(!pool.length){alert('No bloom questions due yet. Your flowers are resting 🌷');return;}
  selectedChapters=new Set(pool.map(q=>q.chapter));
  startQuiz('bloom',pool);
}

const bankTypeFilters={mistake:'all',bookmark:'all',skip:'all',archive:'all',bloom:'all'};
const chapterFilters={mistake:'',bookmark:'',skip:'',archive:''};
const bankSearch={mistake:'',bookmark:'',skip:'',archive:''};
const BANK_EMPTY_HTML={
  mistake:'No mistakes yet! \uD83C\uDF89',
  bookmark:'No bookmarks yet! Tap \uD83D\uDD16 during a quiz.',
  skip:'No skipped questions. &#x2705;',
  archive:'Archive is empty. \uD83C\uDFC6',
  bloom:'Nothing is due today. 🌸 Check back tomorrow — your flowers are resting.'
};

function bankQuestionType(entry){return getQuestionType(entry&&entry.q||{});}
const subtopicFilters={mistake:'',bookmark:'',skip:'',archive:'',bloom:''};
function bankSearchText(entry){
  const q=entry&&entry.q||{};
  return [q.question,q.stem,q.chapter,q.sub_topic,q.topic,q.explanation,q.note,entry.note,JSON.stringify(q),...Object.values(q.options||{})].join(' ').toLowerCase();
}
function filteredBank(bank,bankType){
  const active=bankTypeFilters[bankType]||'all';
  const chapter=chapterFilters[bankType]||'';
  const subtopic=subtopicFilters[bankType]||'';
  const q=(bankSearch[bankType]||'').trim().toLowerCase();
  return Object.fromEntries(Object.entries(bank).filter(([,entry])=>{
    if(active!=='all'&&bankQuestionType(entry)!==active)return false;
    if(chapter&&(entry.q&&entry.q.chapter)!==chapter)return false;
    if(subtopic&&(entry.q&&entry.q.sub_topic)!==subtopic)return false;
    if(q&&!bankSearchText(entry).includes(q))return false;
    return true;
  }));
}
function populateChapterFilter(bankType,bank){
  const sel=document.getElementById('chapter-filter-'+bankType);if(!sel)return;
  const chapters=[...new Set(Object.values(bank).map(e=>e.q&&e.q.chapter).filter(Boolean))].sort((a,b)=>a.localeCompare(b));
  const current=sel.value;
  sel.innerHTML='<option value="">All chapters</option>'+chapters.map(c=>`<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');
  if(chapters.includes(current))sel.value=current;
}
function populateSubtopicFilter(bankType,bank){
  const sel=document.getElementById('subtopic-filter-'+bankType);
  const lbl=document.getElementById('subtopic-filter-lbl-'+bankType);
  if(!sel)return;
  const currentChapter=chapterFilters[bankType]||'';
  const subtopics=[...new Set(Object.values(bank).map(e=>{
    const q=e.q||{};
    if(currentChapter&&q.chapter!==currentChapter)return null;
    return q.sub_topic;
  }).filter(Boolean))].sort((a,b)=>a.localeCompare(b));

  if(subtopics.length===0){
    sel.style.display='none';
    if(lbl)lbl.style.display='none';
    subtopicFilters[bankType]='';
    return;
  }
  sel.style.display='';
  if(lbl)lbl.style.display='';
  const current=sel.value;
  sel.innerHTML='<option value="">All sub-topics</option>'+subtopics.map(st=>`<option value="${escapeHtml(st)}">${escapeHtml(st)}</option>`).join('');
  if(subtopics.includes(current))sel.value=current;
  else subtopicFilters[bankType]='';
}
function setChapterFilter(bankType,value){
  chapterFilters[bankType]=value||'';
  subtopicFilters[bankType]='';
  ({mistake:showMistakeScreen,bookmark:showBookmarkScreen,skip:showSkipScreen,archive:showArchiveScreen})[bankType]?.();
}
function setSubtopicFilter(bankType,value){
  subtopicFilters[bankType]=value||'';
  ({mistake:showMistakeScreen,bookmark:showBookmarkScreen,skip:showSkipScreen,archive:showArchiveScreen})[bankType]?.();
}
function setBankSearch(bankType,value){
  bankSearch[bankType]=value||'';
  ({mistake:showMistakeScreen,bookmark:showBookmarkScreen,skip:showSkipScreen,archive:showArchiveScreen})[bankType]?.();
}
function renderBankTypeFilters(bankType,items){
  const counts=new Map();items.forEach(entry=>{const type=bankQuestionType(entry);counts.set(type,(counts.get(type)||0)+1);});
  if(bankTypeFilters[bankType]!=='all'&&!counts.has(bankTypeFilters[bankType]))bankTypeFilters[bankType]='all';
  const active=bankTypeFilters[bankType];
  const chips=[['all','All',items.length],...[...counts.entries()].sort((a,b)=>a[0].localeCompare(b[0])).map(([type,count])=>[type,type,count])];
  const el=document.getElementById(`${bankType}-type-filters`);if(!el)return;
  el.innerHTML=chips.map(([value,label,count])=>`<button class="bank-filter-chip ${active===value?'active':''}" data-type="${escapeHtml(value)}" onclick="setBankTypeFilter('${bankType}',this.dataset.type)">${escapeHtml(label)} <span class="bank-filter-count">${count}</span></button>`).join('');
}
function setBankTypeFilter(bankType,type){
  bankTypeFilters[bankType]=type||'all';
  ({mistake:showMistakeScreen,bookmark:showBookmarkScreen,skip:showSkipScreen,archive:showArchiveScreen,bloom:showBloomScreen})[bankType]?.();
}
function editBookmarkNote(uid){
  const b=getBookmarks();
  if(!b[uid])return;
  const current=b[uid].note||'';
  const val=window.prompt('Add or edit your note for this bookmark:',current);
  if(val===null)return;
  b[uid].note=String(val).trim();
  saveBookmarks(b);showBookmarkScreen();
}
function bankItemHtml(e,bankType){
  const q=e.q||{},questionType=getQuestionType(q);
  const dots=Array.from({length:MASTERY},(_,i)=>`<div class="cc-dot ${i<(e.correctCount||0)?'filled':''}"></div>`).join('');
  const date=e.addedAt?new Date(e.addedAt).toLocaleDateString():'';
  const noteHtml=bankType==='bookmark'?`<div class="bank-note">${e.note?`<b>Your note</b>${bookText(e.note)}`:'<b>Personal note</b>Jot down why this matters to you.'}<button class="bank-note-btn" data-uid="${escapeHtml(q.uid)}" onclick="editBookmarkNote(this.dataset.uid)">${e.note?'Edit note':'Add note'}</button></div>`:'';
  return `<div class="bank-item" data-question-type="${escapeHtml(questionType)}"><div class="bank-item-top"><span class="bank-tag ${bankType}">${bankType.toUpperCase()}</span><span class="question-type-pill">${escapeHtml(questionType)}</span><span style="font-size:0.6rem;background:var(--gold-dim);color:var(--gold);border:1px solid rgba(201,137,123,0.3);padding:2px 6px;border-radius:3px;font-weight:700;">${escapeHtml(q.chapter||'')}</span>${topicPillHtml(q)}${e.times?`<span class="bank-times">x${Number(e.times)||0}</span>`:''}<span class="bank-times" style="margin-left:auto;">${escapeHtml(date)}</span></div>${renderQuestionStem(q,'bank').html}<div class="bank-ans">&#x2713; ${bookText(questionCorrectAnswerLabel(q))}</div><div class="cc-dots">${dots}<span class="cc-label">to mastery</span></div>${noteHtml}</div>`;
}
function archiveItemHtml(e){
  const q=e.q||{},questionType=getQuestionType(q),from=String(e.fromBank||'archive').toLowerCase();
  const date=e.archivedAt?new Date(e.archivedAt).toLocaleDateString():'';
  return `<div class="bank-item" data-question-type="${escapeHtml(questionType)}"><div class="bank-item-top"><span class="bank-tag archive">ARCHIVED</span><span class="question-type-pill">${escapeHtml(questionType)}</span><span class="from-badge ${escapeHtml(from)}">${escapeHtml(from.toUpperCase())}</span><span style="font-size:0.6rem;background:var(--gold-dim);color:var(--gold);border:1px solid rgba(201,137,123,0.3);padding:2px 6px;border-radius:3px;font-weight:700;">${escapeHtml(q.chapter||'')}</span>${topicPillHtml(q)}<span class="bank-times" style="margin-left:auto;">${escapeHtml(date)}</span></div>${renderQuestionStem(q,'bank').html}<div class="bank-ans">&#x2713; ${bookText(questionCorrectAnswerLabel(q))}</div></div>`;
}
function renderBankScreen(bankType,bank,screenId,itemRenderer){
  const allItems=Object.values(bank),visible=Object.values(filteredBank(bank,bankType));
  populateChapterFilter(bankType,bank);populateSubtopicFilter(bankType,bank);
  renderBankTypeFilters(bankType,allItems);
  const count=document.getElementById(`${bankType}-count-lbl`);
  count.textContent=visible.length===allItems.length?`${allItems.length} question${allItems.length!==1?'s':''}`:`${visible.length} of ${allItems.length} questions`;
  document.getElementById(`${bankType}-list`).innerHTML=visible.length?visible.map(itemRenderer).join(''):`<div style="padding:30px;text-align:center;color:var(--text3);font-size:0.82rem;">${BANK_EMPTY_HTML[bankType]}</div>`;
  showScreen(screenId);
}

function showMistakeScreen(){renderBankScreen('mistake',getMistakes(),'mistake-screen',e=>bankItemHtml(e,'mistake'));}
function clearAllMistakes(){if(!confirm('Archive all mistakes?'))return;const b=getMistakes();Object.values(b).forEach(e=>archiveQuestion(e.q,'mistake'));saveMistakes({});updateAllBadges();showMistakeScreen();}
function practiceFromMistakes(){practiceFromBank(filteredBank(getMistakes(),'mistake'),'mistakes');}

// ─── PDF EXPORT (A4, black & white) ─────────────────────────────────────────
// Builds a print-ready A4 document in a hidden iframe and opens the browser
// print dialog — choose "Save as PDF" to get the file. Respects the active filter.
function exportBankPdf(bankType){
  const bank=bankType==='skip'?getSkips():getMistakes();
  const items=Object.values(filteredBank(bank,bankType));
  if(!items.length){alert('No questions to export.');return;}
  const html=buildBankExportHtml(bankType,items);
  const frame=document.createElement('iframe');
  frame.setAttribute('aria-hidden','true');
  frame.style.cssText='position:fixed;right:0;bottom:0;width:1px;height:1px;border:0;opacity:0;';
  document.body.appendChild(frame);
  const doc=frame.contentDocument||frame.contentWindow.document;
  doc.open();doc.write(html);doc.close();
  setTimeout(()=>{
    try{frame.contentWindow.focus();frame.contentWindow.print();}
    catch(e){alert('Could not open the print dialog. Please try again.');frame.remove();return;}
    setTimeout(()=>frame.remove(),90000);
  },300);
}
function buildBankExportHtml(bankType,items){
  const title=bankType==='skip'?'Skipped Questions — Practice Sheet':'Mistakes — Practice Sheet';
  const bookName=(typeof currentBook!=='undefined'&&currentBook&&currentBook.title)?currentBook.title:'';
  const dateStr=new Date().toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'});
  const blocks=items.map((e,idx)=>{
    const q=e.q||{};
    const correctKeys=questionCorrectKeys(q);
    const userKey=e.userKey;
    const meta=[q.topic||q.sub_topic||q.chapter||'',[q.exam,q.year&&q.year!=='Unknown'?q.year:''].filter(Boolean).join(' · ')].filter(Boolean).join(' | ');
    const opts=Object.keys(q.options||{}).filter(k=>q.options[k]!=null&&q.options[k]!=='').map(k=>{
      const isCorrect=correctKeys.includes(k);
      const isUser=answerHasKey(userKey,k)&&!isCorrect;
      return `<div class="opt${isCorrect?' correct':''}${isUser?' userwrong':''}"><span class="key">(${escapeHtml(k)})</span> ${bookText(optionDisplayText(q.options[k],k))}${isCorrect?'<span class="mark">&#10003;</span>':''}${isUser?'<span class="mark x">&#10007; your answer</span>':''}</div>`;
    }).join('');
    return `<div class="q">
      <div class="qhead"><span class="qno">Q${idx+1}</span>${meta?`<span class="meta">${escapeHtml(meta)}</span>`:''}${e.times?`<span class="meta">attempted wrong &times;${Number(e.times)||1}</span>`:''}</div>
      <div class="qtext">${bookText(q.question||q.q||'')}</div>
      ${opts?`<div class="opts">${opts}</div>`:''}
      <div class="ans">&#10003; Correct Answer: <b>${escapeHtml(correctKeys.map(k=>`(${k})`).join(' + '))}</b> ${bookText(questionCorrectAnswerLabel(q))}</div>
      ${q.explanation?`<div class="exp"><span class="explbl">Explanation:</span> ${bookText(q.explanation)}</div>`:''}
      ${q.note?`<div class="note"><b>Note:</b> ${bookText(q.note)}</div>`:''}
    </div>`;
  }).join('');
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title>
<style>
  @page{size:A4;margin:15mm 13mm;}
  *{box-sizing:border-box;}
  body{font-family:Georgia,'Times New Roman',serif;color:#000;background:#fff;font-size:10.2pt;line-height:1.42;margin:0;}
  .sheet-head{border-bottom:2.5px solid #000;padding-bottom:7px;margin-bottom:12px;}
  .sheet-head h1{font-size:14.5pt;margin:0 0 3px;letter-spacing:.4px;text-transform:uppercase;}
  .sheet-head .sub{font-family:Arial,Helvetica,sans-serif;font-size:8.4pt;color:#000;}
  .q{border:1px solid #000;border-radius:3px;padding:8px 10px;margin-bottom:9px;break-inside:avoid;page-break-inside:avoid;}
  .qhead{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin-bottom:4px;font-family:Arial,Helvetica,sans-serif;font-size:8pt;}
  .qno{font-weight:700;font-size:9.5pt;}
  .meta{border:1px solid #000;border-radius:2px;padding:0 4px;font-size:7.2pt;text-transform:uppercase;letter-spacing:.3px;}
  .qtext{font-size:10.2pt;margin-bottom:5px;white-space:pre-line;}
  .opts{margin:0 0 5px 2px;}
  .opt{padding:1.5px 0 1.5px 4px;margin:0 0 1px;border-left:2px solid transparent;}
  .opt .key{font-weight:700;font-family:Arial,Helvetica,sans-serif;font-size:9pt;}
  .opt.correct{border-left:2.5px solid #000;background:#f0f0f0;font-weight:700;}
  .opt .mark{font-family:Arial,Helvetica,sans-serif;font-size:7.6pt;font-weight:700;margin-left:6px;border:1px solid #000;padding:0 3px;}
  .ans{font-family:Arial,Helvetica,sans-serif;font-size:9pt;border:1.5px solid #000;display:inline-block;padding:2.5px 7px;margin:2px 0 4px;border-radius:2px;}
  .exp{border-top:1px dashed #000;margin-top:4px;padding-top:4px;font-size:9.3pt;white-space:pre-line;}
  .explbl{font-family:Arial,Helvetica,sans-serif;font-weight:700;font-size:8pt;text-transform:uppercase;letter-spacing:.4px;}
  .note{font-size:9pt;margin-top:3px;border:1px dashed #000;padding:3px 6px;}
  .foot{font-family:Arial,Helvetica,sans-serif;font-size:7.6pt;color:#000;border-top:1px solid #000;margin-top:10px;padding-top:4px;display:flex;justify-content:space-between;}
</style></head><body>
<div class="sheet-head"><h1>${escapeHtml(title)}</h1><div class="sub">${bookName?escapeHtml(bookName)+' &middot; ':''}${items.length} questions &middot; generated ${escapeHtml(dateStr)} &middot; A4</div></div>
${blocks}
<div class="foot"><span>${escapeHtml(title)} &middot; ${escapeHtml(bookName||'MCQ Practise')}</span><span>Print &rarr; Save as PDF &middot; A4</span></div>
</body></html>`;
}

function showBookmarkScreen(){renderBankScreen('bookmark',getBookmarks(),'bookmark-screen',e=>bankItemHtml(e,'bookmark'));}
function clearAllBookmarks(){if(!confirm('Archive all bookmarks?'))return;const b=getBookmarks();Object.values(b).forEach(e=>archiveQuestion(e.q,'bookmark'));saveBookmarks({});updateAllBadges();showBookmarkScreen();}
function practiceFromBookmarks(){practiceFromBank(filteredBank(getBookmarks(),'bookmark'),'bookmarks');}

function showSkipScreen(){renderBankScreen('skip',getSkips(),'skip-screen',e=>bankItemHtml(e,'skip'));}
function clearAllSkips(){if(!confirm('Archive all skips?'))return;const b=getSkips();Object.values(b).forEach(e=>archiveQuestion(e.q,'skip'));saveSkips({});updateAllBadges();showSkipScreen();}
function practiceFromSkips(){practiceFromBank(filteredBank(getSkips(),'skip'),'skips');}

function showArchiveScreen(){
  const arc=getArchive();
  const sorted=Object.fromEntries(Object.entries(arc).sort(([,a],[,b])=>new Date(b.archivedAt)-new Date(a.archivedAt)));
  renderBankScreen('archive',sorted,'archive-screen',archiveItemHtml);
}
function practiceFromArchive(){practiceFromBank(filteredBank(getArchive(),'archive'),'archive');}
function clearAllArchive(){if(confirm('Permanently delete all archived questions?')){saveArchive({});updateAllBadges();showArchiveScreen();}}

// ════════════════════════════════════════════════════════════════
// ATTEMPT HISTORY — a per-quiz record of every finished attempt
// ════════════════════════════════════════════════════════════════
const getAttempts=()=>LS.get(sk('gc_attempts'),[]);let saveAttempts=a=>LS.set(sk('gc_attempts'),a);

