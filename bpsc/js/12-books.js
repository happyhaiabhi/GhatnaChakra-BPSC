/* book library: per-book stats and the book grid
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function applyBook(book){
  currentBook=book;
  bookDataDir=book.dataDir||'data';
  currentChaptersIndex=[];
  chapterIconMap={};
  SUBJECTS_CONFIG=[];
  subjectDataCache={};
  syncQuestionCatalog=null;syncQuestionCatalogPromise=null;
  currentSubjectId=null;selectedChapters=new Set();
  allQuestions=[];chapterMap={};
  quiz=[];state={};quizMeta={};
  Object.keys(bankTypeFilters).forEach(type=>{bankTypeFilters[type]='all';});
  clearInterval(timerInterval);timerInterval=null;
  // Brand the app with this book
  const tag=document.getElementById('nav-book-tag'),name=document.getElementById('nav-book-name');
  if(tag)tag.textContent=book.tag||book.title||'Quiz';
  if(name)name.textContent=book.title||'Ghatna Chakra';
  document.documentElement.style.setProperty('--book-accent',book.color||'#c9a84c');
  // Update browser tab title for Crown book
  if(book.id==='crown'){
    document.title='Crown Bihar General Studies — Quiz';
  }
}

// Build SUBJECTS_CONFIG from the active book's chapters index.
function subjectsFromChapterIndex(index){
  return (index||[]).map(s=>({id:s.key,name:s.label||s.key,icon:s.emoji||'\uD83D\uDCD8',file:bookFilePath(s.file),rawFile:s.file}));
}

async function loadBankOverview(){
  if(!currentBook)return;
  try{
    const response=await fetch(resolveBookChaptersUrl(currentBook));
    if(!response.ok)throw new Error('chapters.json could not be loaded');
    const index=await response.json();
    currentChaptersIndex=index;
    // Build chapter-name -> icon map so chapter rows can show a related icon.
    chapterIconMap={};
    (index||[]).forEach(subject=>(subject.chapters||[]).forEach(ch=>{
      if(ch.icon)chapterIconMap[ch.name]=ch.icon;
    }));
    SUBJECTS_CONFIG=subjectsFromChapterIndex(index);
    buildSubjectsGrid();
    const totalChapters=index.reduce((sum,subject)=>sum+(subject.chapters||[]).length,0);
    const totalQuestions=index.reduce((sum,subject)=>sum+(subject.chapters||[]).reduce((s,ch)=>s+(Number(ch.count)||0),0),0);
    document.getElementById('sh-subjects').textContent=index.length.toLocaleString();
    document.getElementById('sh-chapters').textContent=totalChapters.toLocaleString();
    document.getElementById('sh-questions').textContent=totalQuestions.toLocaleString();
    index.forEach(subject=>{
      const chapterPill=document.getElementById('sc-pill-ch-'+subject.key);
      const questionPill=document.getElementById('sc-pill-q-'+subject.key);
      const count=(subject.chapters||[]).reduce((sum,ch)=>sum+(Number(ch.count)||0),0);
      if(chapterPill)chapterPill.textContent=(subject.chapters||[]).length+' chapters';
      if(questionPill)questionPill.textContent=count.toLocaleString()+' Qs';
    });
  }catch(error){console.error('Failed to load bank overview:',error);}
}

// ----- Book selection screen -----
function bookStats(book){
  // Quick counts from the book's chapters index for the landing card.
  return fetch(resolveBookChaptersUrl(book)).then(r=>r.ok?r.json():[]).then(index=>{
    const subjects=(index||[]).length;
    const chapters=(index||[]).reduce((sum,s)=>sum+(s.chapters||[]).length,0);
    const questions=(index||[]).reduce((sum,s)=>sum+(s.chapters||[]).reduce((a,ch)=>a+(Number(ch.count)||0),0),0);
    return {subjects,chapters,questions};
  }).catch(()=>({subjects:0,chapters:0,questions:0}));
}

async function renderBooksScreen(){
  const grid=document.getElementById('books-grid');
  if(!grid)return;
  if(!BOOKS.length){grid.innerHTML='<div style="grid-column:1/-1;text-align:center;color:var(--red);font-size:.85rem;padding:40px;">No books found. Check books/books.json.</div>';return;}
  // The cover frame always renders. It shows the cover image when one is
  // registered and loads; otherwise the book emoji stands in for it. The tag
  // pill sits in normal flow above the title (not pinned to the corner), so
  // no element can overlap another at any zoom level or viewport width.
  grid.innerHTML=BOOKS.map(b=>`
    <div class="book-card ${b.cover?'has-cover':'no-cover'}" data-book="${b.id}" style="--book-accent:${b.color||'#C9897B'};" onclick="openBook('${b.id}')" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();openBook('${b.id}');}" role="button" tabindex="0" aria-label="Open ${escapeHtml(b.title||b.id)}">
      <div class="book-top">
        <div class="book-cover-frame">
          ${b.cover?`<img class="book-cover" src="${escapeHtml(b.cover)}" alt="${escapeHtml(b.title||b.id)} book cover" loading="lazy" onerror="this.closest('.book-card').classList.replace('has-cover','no-cover');this.remove();">`:''}
          <div class="book-emoji book-emoji-fallback" aria-hidden="true">${b.emoji||'\uD83D\uDCD8'}</div>
        </div>
        <div class="book-top-info">
          ${b.tag?`<span class="book-pill">${escapeHtml(b.tag)}</span>`:''}
          <div class="book-title">${escapeHtml(b.title||b.id)}</div>
          <div class="book-subtitle">${escapeHtml(b.subtitle||'')}</div>
        </div>
      </div>
      <div class="book-desc">${b.description||''}</div>
      <div class="book-stats" id="book-stats-${b.id}"></div>
      <div class="book-open">Open book &#x2192;</div>
    </div>`).join('');
  // Fill counts asynchronously without blocking the grid.
  BOOKS.forEach(async b=>{
    const el=document.getElementById('book-stats-'+b.id);if(!el)return;
    const st=await bookStats(b);
    el.innerHTML=`<span class="book-stat"><b>${st.subjects}</b> subjects</span><span class="book-stat"><b>${st.chapters}</b> chapters</span><span class="book-stat"><b>${st.questions.toLocaleString()}</b> questions</span>`;
  });
}

