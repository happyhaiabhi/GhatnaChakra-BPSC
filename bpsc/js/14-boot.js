/* opening a book, nav layout, global listeners and bootstrap
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function showBooksScreen(){
  clearInterval(timerInterval);
  showScreen('books-screen');
  renderBooksScreen();
}

async function openBook(bookId){
  const book=BOOKS.find(b=>b.id===bookId);if(!book)return;
  // Tear down any realtime listeners attached to the previous book.
  if(typeof syncListeners!=='undefined'&&syncListeners.length){try{syncListeners.forEach(u=>u&&u());}catch(e){}syncListeners=[];}
  applyBook(book);
  buildSubjectsGrid();buildDashboard();updateAllBadges();
  try{await loadBankOverview();}catch(e){console.error(e);}
  showScreen('setup-screen');
  // Re-initialise sync for the newly selected book using the same Google account.
  if(getSyncConfig()&&getSyncConfig().userId){initSyncOnLoad();}
  else{showSignedOutUI();setSyncStatus('offline');updateSyncNavBtn(false);}
  try{localStorage.setItem('gc_last_book',book.id);}catch(e){}
}

async function loadBooksManifest(){
  try{
    const r=await fetch('books/books.json');
    if(!r.ok)throw new Error('books.json http '+r.status);
    BOOKS=await r.json();
  }catch(error){
    console.error('Failed to load books manifest:',error);
    BOOKS=[];
  }
}

// Keep the sync indicator honest and re-sync when connectivity returns.
window.addEventListener('online',()=>{
  const cfg=getSyncConfig();
  if(cfg&&cfg.userId&&fbUserId){synchronizeAll(false).catch(()=>{});}
  else if(cfg&&cfg.userId){initSyncOnLoad();}
});
window.addEventListener('offline',()=>{if(syncStatus!=='error')setSyncStatus('offline');});

/* On phones the top navbar keeps only Switch Book + Search + Sync; the
   secondary tools move into the compact chip row beneath it. On desktop
   and iPad the single scrollable navbar is restored. */
const SETUP_NAV_TOOLS=['nav-portal-home','nav-review','nav-history'];
function layoutSetupNav(){
  const chips=document.getElementById('nav-chips-row');
  const bar=document.querySelector('#setup-screen .top-navbar');
  const anchor=document.getElementById('nav-search');
  if(!chips||!bar||!anchor)return;
  const mobile=window.innerWidth<=599;
  SETUP_NAV_TOOLS.forEach(id=>{
    const el=document.getElementById(id);
    if(!el)return;
    if(mobile)chips.appendChild(el);
    else bar.insertBefore(el,anchor);
  });
}
let navLayoutTimer=null;
window.addEventListener('resize',()=>{clearTimeout(navLayoutTimer);navLayoutTimer=setTimeout(layoutSetupNav,120);});

function init(){
  applyTheme('light');
  // Lightweight placeholder until a book is chosen.
  buildSubjectsGrid();buildDashboard();updateAllBadges();layoutSetupNav();setupGlobalBookSearch();
  document.body.dataset.activeScreen='books-screen';
  resetGlobalBookSearchResults();
  // Always land on the book-selection screen; never auto-reopen the last book.
  loadBooksManifest().then(()=>{
    renderBooksScreen();
    showScreen('books-screen');
    warmGlobalBookSearch();
  });
}
init();
