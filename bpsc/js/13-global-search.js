/* cross-book global search (PYQ Lab)
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
const GLOBAL_BOOK_SEARCH_BOOK_LIMIT=8;
const GLOBAL_BOOK_SEARCH_QUESTION_LIMIT=24;
let globalBookSearchIndex=null,globalBookSearchPromise=null,globalBookSearchTimer=null,globalBookSearchToken=0;
let globalBookSearchState={query:'',bookHits:[],questionHits:[]};

function normalizeGlobalSearchText(value){
  const raw=typeof normalizeBookText==='function'?normalizeBookText(value):String(value??'');
  return String(raw).replace(/\s+/g,' ').trim();
}
function resolveBookFilePathFor(book,file){
  if(/^(https?:)?\/\//.test(file))return file;
  let clean=String(file||'').replace(/^(\.\/)+/,'').replace(/^\/+/,'');
  const dir=String(book&&book.dataDir||'').replace(/\/+$/,'');
  if(!dir||dir==='.')return clean;
  if(clean===dir||clean.indexOf(dir+'/')===0)return clean;
  return dir+'/'+clean.replace(/^data\//,'');
}
function subjectsFromChapterIndexForBook(book,index){
  return (index||[]).map(s=>({id:s.key,name:s.label||s.key,icon:s.emoji||'📘',file:resolveBookFilePathFor(book,s.file),rawFile:s.file}));
}
function bookDataCandidatesForBook(book,subj){
  const raw=String((subj&&(subj.rawFile||subj.file))||'').replace(/^(\.\/)+/,'');
  const dir=String(book&&book.dataDir||'').replace(/\/+$/,'');
  const base=raw.split('/').pop();
  const key=subj&&subj.id?String(subj.id):'';
  const list=[];
  const add=p=>{if(p&&list.indexOf(p)===-1)list.push(p);};
  add(resolveBookFilePathFor(book,raw));
  add(raw);
  if(dir&&dir!=='.'){
    if(base)add(dir+'/'+base);
    if(key)add(dir+'/'+key+'.json');
  }
  if(subj)add(subj.file);
  return list;
}
async function fetchBookDataForBook(book,subj){
  const candidates=bookDataCandidatesForBook(book,subj);
  for(let i=0;i<candidates.length;i++){
    const url=candidates[i];
    let resp;
    try{resp=await fetch(url);}catch(err){continue;}
    if(!resp.ok)continue;
    try{
      const data=await resp.json();
      if(data&&typeof data==='object')return data;
    }catch(err){}
  }
  throw new Error('Could not load search data for '+((book&&book.title)||'book')+' / '+((subj&&subj.name)||'subject'));
}
function globalBookSearchPreview(text,maxLen){
  const clean=normalizeGlobalSearchText(text);
  return clean.length>maxLen?clean.slice(0,maxLen-1).trim()+'…':clean;
}
function globalBookSearchScore(entry,query,tokens){
  let score=0;
  const addScore=(text,startsWeight,containsWeight,tokenWeight)=>{
    if(!text)return;
    if(query&&text.startsWith(query))score+=startsWeight;
    else if(query&&text.includes(query))score+=containsWeight;
    tokens.forEach(token=>{if(text.includes(token))score+=tokenWeight;});
  };
  addScore(entry.primary||'',120,80,14);
  addScore(entry.meta||'',56,38,8);
  addScore(entry.details||'',20,12,3);
  return score;
}
async function loadGlobalBookSearchEntries(book){
  let chapterIndex=[];
  try{
    const res=await fetch(resolveBookChaptersUrl(book));
    if(!res.ok)throw new Error('chapters '+res.status);
    chapterIndex=await res.json();
  }catch(error){
    console.warn('Global search skipped book index',book&&book.id,error&&error.message);
    return [];
  }
  const subjects=subjectsFromChapterIndexForBook(book,chapterIndex);
  const entries=await Promise.all(subjects.map(async subj=>{
    try{
      const data=await fetchBookDataForBook(book,subj);
      let idx=0;
      const out=[];
      (data.chapters||[]).forEach(ch=>{
        const chName=ch.chapter_name||ch.name||'General';
        (ch.questions||[]).forEach(q=>{
          const internal=toInternalQuestion(q,subj.id,idx++,chName);
          const type=getQuestionType(internal);
          const primary=normalizeGlobalSearchText(internal.question||q.q||q.question||'').toLowerCase();
          const meta=normalizeGlobalSearchText([book.title,book.tag,book.subtitle,subj.name,chName,internal.sub_topic,type,internal.exam,internal.year].filter(Boolean).join(' ')).toLowerCase();
          const details=normalizeGlobalSearchText([Object.values(internal.options||{}).join(' '),internal.explanation||'',internal.note||''].join(' ')).toLowerCase();
          out.push({
            key:'gs_'+book.id+'_'+subj.id+'_'+idx,
            bookId:book.id,
            bookTitle:book.title||book.id,
            bookTag:book.tag||'',
            bookColor:book.color||'#C9897B',
            subjectId:subj.id,
            subjectName:subj.name||subj.id,
            chapter:chName,
            type,
            question:internal,
            preview:globalBookSearchPreview(internal.question||q.q||q.question||'',220),
            primary,meta,details,
            search:[primary,meta,details].join(' ')
          });
        });
      });
      return out;
    }catch(error){
      console.warn('Global search skipped subject',book&&book.id,subj&&subj.id,error&&error.message);
      return [];
    }
  }));
  return entries.flat();
}
async function ensureGlobalBookSearchIndex(){
  if(globalBookSearchIndex)return globalBookSearchIndex;
  if(globalBookSearchPromise)return globalBookSearchPromise;
  globalBookSearchPromise=Promise.all((BOOKS||[]).map(loadGlobalBookSearchEntries)).then(list=>{
    globalBookSearchIndex=list.flat();
    return globalBookSearchIndex;
  }).catch(error=>{globalBookSearchPromise=null;throw error;});
  return globalBookSearchPromise;
}
function renderGlobalBookSearchMessage(title,copy,cls){
  const host=document.getElementById('books-global-results');
  if(!host)return;
  host.hidden=false;
  host.innerHTML=`<div class="${cls||'books-global-loading'}"><strong>${title}</strong><div>${copy}</div></div>`;
}
function resetGlobalBookSearchResults(){
  const host=document.getElementById('books-global-results');
  const status=document.getElementById('books-global-search-status');
  const clearBtn=document.getElementById('books-global-search-clear');
  if(host){host.hidden=true;host.innerHTML='';}
  if(status)status.textContent='Integrated search across all books, subjects, chapters, questions, options and explanations.';
  if(clearBtn)clearBtn.hidden=true;
  globalBookSearchState={query:'',bookHits:[],questionHits:[]};
}
function renderGlobalBookSearchResults(){
  const host=document.getElementById('books-global-results');
  const status=document.getElementById('books-global-search-status');
  const clearBtn=document.getElementById('books-global-search-clear');
  if(!host||!status||!clearBtn)return;
  const {query,bookHits,questionHits}=globalBookSearchState;
  if(!query){resetGlobalBookSearchResults();return;}
  clearBtn.hidden=false;
  status.textContent=`${(bookHits.length+questionHits.length).toLocaleString()} search results for “${query}” across all data.`;
  host.hidden=false;
  if(!bookHits.length&&!questionHits.length){
    host.innerHTML='<div class="books-global-empty"><strong>No match found.</strong><div>Try a subject, chapter, keyword, exam name or concept from any book.</div></div>';
    return;
  }
  host.innerHTML=`
    ${bookHits.length?`<section class="books-global-section"><div class="books-global-sectionhead"><h3>Matching books</h3><span>${bookHits.length} shown</span></div><div class="books-global-bookhits">${bookHits.map(book=>`<button type="button" class="books-global-chip" data-global-book-id="${escapeHtml(book.id)}"><span>${escapeHtml(book.title)}</span><b>${escapeHtml(book.tag||'Open')}</b></button>`).join('')}</div></section>`:''}
    ${questionHits.length?`<section class="books-global-section"><div class="books-global-sectionhead"><h3>Question hits</h3><span>Top ${questionHits.length} matches from all books</span></div><div class="books-global-list">${questionHits.map((hit,index)=>`<article class="books-global-card"><div class="books-global-cardtop"><span class="books-global-badge book">${escapeHtml(hit.bookTitle)}</span><span class="books-global-badge subject">${escapeHtml(hit.subjectName)}</span><span class="books-global-badge chapter">${escapeHtml(hit.chapter)}</span><span class="books-global-badge type">${escapeHtml(hit.type)}</span></div><h4>${escapeHtml(hit.preview||'Question')}</h4><p class="books-global-snippet">${escapeHtml(hit.question.explanation?globalBookSearchPreview(hit.question.explanation,180):'Open this question directly, or jump into its book for wider practice.')}</p><div class="books-global-actions"><button type="button" class="books-global-action ghost" data-global-book-id="${escapeHtml(hit.bookId)}">Open book</button><button type="button" class="books-global-action primary" data-global-practice-index="${index}">Practice this question</button></div></article>`).join('')}</div></section>`:''}`;
}
function runGlobalBookSearch(){
  const input=document.getElementById('books-global-search-input');
  const query=normalizeGlobalSearchText(input&&input.value||'').toLowerCase();
  const token=++globalBookSearchToken;
  if(!query){resetGlobalBookSearchResults();return;}
  const tokens=query.split(/\s+/).filter(Boolean);
  const bookHits=(BOOKS||[]).map(book=>{
    const entry={id:book.id,title:book.title||book.id,search:normalizeGlobalSearchText([book.title,book.tag,book.subtitle,book.description].filter(Boolean).join(' ')).toLowerCase(),primary:normalizeGlobalSearchText(book.title||book.id).toLowerCase(),meta:normalizeGlobalSearchText([book.tag,book.subtitle].filter(Boolean).join(' ')).toLowerCase(),details:normalizeGlobalSearchText(book.description||'').toLowerCase()};
    if(tokens.some(token=>!entry.search.includes(token)))return null;
    return Object.assign(book,{score:globalBookSearchScore(entry,query,tokens)});
  }).filter(Boolean).sort((a,b)=>b.score-a.score).slice(0,GLOBAL_BOOK_SEARCH_BOOK_LIMIT);
  globalBookSearchState={query,bookHits,questionHits:[]};
  renderGlobalBookSearchMessage('Searching all data…',`Scanning every book, subject, chapter, question, option and explanation for “${escapeHtml(query)}”.`,'books-global-loading');
  const status=document.getElementById('books-global-search-status');
  const clearBtn=document.getElementById('books-global-search-clear');
  if(status)status.textContent=`Searching across ${BOOKS.length} books…`;
  if(clearBtn)clearBtn.hidden=false;
  ensureGlobalBookSearchIndex().then(index=>{
    if(token!==globalBookSearchToken)return;
    const questionHits=index.map(hit=>({hit,score:globalBookSearchScore(hit,query,tokens)}))
      .filter(item=>item.score>0&&tokens.every(token=>item.hit.search.includes(token)))
      .sort((a,b)=>b.score-a.score||(a.hit.preview||'').length-(b.hit.preview||'').length)
      .slice(0,GLOBAL_BOOK_SEARCH_QUESTION_LIMIT)
      .map(item=>item.hit);
    globalBookSearchState={query,bookHits,questionHits};
    renderGlobalBookSearchResults();
  }).catch(error=>{
    if(token!==globalBookSearchToken)return;
    console.error('Global search failed:',error);
    renderGlobalBookSearchMessage('Search is not ready yet.','The integrated search index could not be built right now. Please try again in a moment.','books-global-empty');
    if(status)status.textContent='Integrated search could not load every data file right now.';
  });
}
function queueGlobalBookSearch(){clearTimeout(globalBookSearchTimer);globalBookSearchTimer=setTimeout(runGlobalBookSearch,150);}
async function openGlobalBookSearchQuestion(index){
  const hit=(globalBookSearchState.questionHits||[])[Number(index)];
  if(!hit)return;
  await openBook(hit.bookId);
  currentSubjectId=hit.subjectId;
  selectedChapters=new Set([hit.chapter]);
  allQuestions=[hit.question];
  chapterMap={[hit.chapter]:[hit.question]};
  startQuiz('supersearch',[hit.question]);
}
function setupGlobalBookSearch(){
  const input=document.getElementById('books-global-search-input');
  const btn=document.getElementById('books-global-search-btn');
  const clearBtn=document.getElementById('books-global-search-clear');
  const results=document.getElementById('books-global-results');
  if(input&&!input.dataset.bound){
    input.dataset.bound='1';
    input.addEventListener('input',queueGlobalBookSearch);
    input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();runGlobalBookSearch();}});
  }
  if(btn&&!btn.dataset.bound){btn.dataset.bound='1';btn.addEventListener('click',runGlobalBookSearch);}
  if(clearBtn&&!clearBtn.dataset.bound){clearBtn.dataset.bound='1';clearBtn.addEventListener('click',()=>{if(input)input.value='';resetGlobalBookSearchResults();input&&input.focus();});}
  if(results&&!results.dataset.bound){
    results.dataset.bound='1';
    results.addEventListener('click',event=>{
      const bookButton=event.target.closest('[data-global-book-id]');
      if(bookButton){openBook(bookButton.dataset.globalBookId);return;}
      const practiceButton=event.target.closest('[data-global-practice-index]');
      if(practiceButton){openGlobalBookSearchQuestion(practiceButton.dataset.globalPracticeIndex);}
    });
  }
}
function warmGlobalBookSearch(){
  if(globalBookSearchIndex||globalBookSearchPromise||!BOOKS.length)return;
  const start=()=>ensureGlobalBookSearchIndex().catch(()=>{});
  if(window.requestIdleCallback)window.requestIdleCallback(start,{timeout:1800});
  else setTimeout(start,900);
}

