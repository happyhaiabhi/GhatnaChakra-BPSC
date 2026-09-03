/* quiz state, localStorage, mistake/bookmark/skip/archive stores, bloom scheduling
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
let currentSubjectId=null,selectedChapters=new Set(),selectedSubtopics=new Set(),allQuestions=[],chapterMap={},chapterSubtopicsMap={},subjectSubtopics=new Set(),subjectDataCache={};
let quiz=[],state={},quizMeta={},timerInterval=null,paused=false,totalSecs=0,lastResults=[],shuffledOptionOrders=[],resultBackTo=null,topicQuizName='';

const LS={get:(k,d={})=>{try{return JSON.parse(localStorage.getItem(k)||JSON.stringify(d));}catch(e){return d;}},set:(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}};
const getHistory=()=>LS.get(sk('gc_history'),[]);let saveHistory=h=>LS.set(sk('gc_history'),h);
const getMistakes=()=>LS.get(sk('gc_mistakes'),{});let saveMistakes=m=>LS.set(sk('gc_mistakes'),m);
const getBookmarks=()=>LS.get(sk('gc_bookmarks'),{});let saveBookmarks=b=>LS.set(sk('gc_bookmarks'),b);
const getSkips=()=>LS.get(sk('gc_skips'),{});let saveSkips=s=>LS.set(sk('gc_skips'),s);
const getArchive=()=>LS.get(sk('gc_archive'),{});let saveArchive=a=>LS.set(sk('gc_archive'),a);
const MASTERY=5;
const BLOOM_INTERVALS=[0,1,3,7,21];
const DAY_MS=86400000;
const nowISO=()=>new Date().toISOString();
function scheduleBloom(entry,correctCount){
  entry.correctCount=correctCount;
  entry.lastReviewedAt=nowISO();
  if(correctCount>=MASTERY)return 'archive';
  const days=BLOOM_INTERVALS[Math.min(correctCount,BLOOM_INTERVALS.length-1)]||1;
  entry.nextReviewAt=new Date(Date.now()+days*DAY_MS).toISOString();
  return 'keep';
}
function archiveQuestion(q,fromBank){const arc=getArchive();arc[q.uid]={q,fromBank,archivedAt:nowISO()};saveArchive(arc);updateAllBadges();}
function addToMistakes(wr){const b=getMistakes(),sk=getSkips();let sc=false;wr.forEach(r=>{const p=b[r.q.uid]||{},base={q:r.q,userKey:r.userKey,source:'mistake',addedAt:p.addedAt||nowISO(),times:(p.times||0)+1};if(p.nextReviewAt){base.correctCount=0;base.lastReviewedAt=nowISO();base.nextReviewAt=new Date(Date.now()+DAY_MS).toISOString();}else{base.correctCount=p.correctCount||0;base.nextReviewAt=nowISO();}b[r.q.uid]=base;if(sk[r.q.uid]){delete sk[r.q.uid];sc=true;}});saveMistakes(b);if(sc)saveSkips(sk);updateAllBadges();}
function addToBookmarks(q){const b=getBookmarks();if(b[q.uid])return;b[q.uid]={q,addedAt:nowISO(),note:''};saveBookmarks(b);updateAllBadges();}
function removeFromBookmarks(uid,arc=true){const b=getBookmarks();if(arc&&b[uid])archiveQuestion(b[uid].q,'bookmark');delete b[uid];saveBookmarks(b);updateAllBadges();}
function addToSkips(qs){const b=getSkips();qs.forEach(q=>{const p=b[q.uid]||{},base={q,source:'skip',addedAt:p.addedAt||nowISO(),times:(p.times||0)+1};if(p.nextReviewAt){base.correctCount=0;base.lastReviewedAt=nowISO();base.nextReviewAt=new Date(Date.now()+DAY_MS).toISOString();}else{base.correctCount=p.correctCount||0;base.nextReviewAt=nowISO();}b[q.uid]=base;});saveSkips(b);updateAllBadges();}
function processCorrectAnswers(cr){const m=getMistakes(),s=getSkips();let mc=false,sc=false;cr.forEach(r=>{const uid=r.q.uid;if(m[uid]){m[uid].userKey=r.userKey;const next=(m[uid].correctCount||0)+1;if(scheduleBloom(m[uid],next)==='archive'){archiveQuestion(r.q,'mistake');delete m[uid];}mc=true;}if(s[uid]){const next=(s[uid].correctCount||0)+1;if(scheduleBloom(s[uid],next)==='archive'){archiveQuestion(r.q,'skip');delete s[uid];}sc=true;}});if(mc)saveMistakes(m);if(sc)saveSkips(s);}
function updateAllBadges(){
  let total=getBloomDue().length;
  ['mistake','bookmark','skip','archive'].forEach(k=>{const n=Object.keys({mistake:getMistakes,bookmark:getBookmarks,skip:getSkips,archive:getArchive}[k]()).length;total+=n;const el=document.getElementById(k+'-badge');if(el)el.textContent=n;});
  const bloom=document.getElementById('bloom-badge');if(bloom)bloom.textContent=getBloomDue().length;
  const review=document.getElementById('review-badge');if(review)review.textContent=total;
}

// ----- Consolidated Review dropdown (mistakes / bookmarks / skips / archive / bloom) -----
function toggleReviewMenu(e){
  if(e)e.stopPropagation();
  const menu=document.getElementById('nav-review-menu');
  const btn=document.getElementById('nav-review-btn');
  if(!menu||!btn)return;
  const open=menu.classList.toggle('open');
  btn.setAttribute('aria-expanded',open?'true':'false');
  if(open){
    const r=btn.getBoundingClientRect();
    const mw=Math.max(232,menu.offsetWidth||232);
    const left=Math.min(Math.max(8,r.right-mw),window.innerWidth-mw-8);
    menu.style.top=(r.bottom+6)+'px';
    menu.style.left=left+'px';
  }
}
function closeReviewMenu(){
  const menu=document.getElementById('nav-review-menu');
  const btn=document.getElementById('nav-review-btn');
  if(menu)menu.classList.remove('open');
  if(btn)btn.setAttribute('aria-expanded','false');
}
function openReview(kind){
  closeReviewMenu();
  const map={bloom:showBloomScreen,mistake:showMistakeScreen,bookmark:showBookmarkScreen,skip:showSkipScreen,archive:showArchiveScreen};
  (map[kind]||function(){} )();
}
document.addEventListener('click',e=>{
  const wrap=document.getElementById('nav-review');
  if(wrap&&!wrap.contains(e.target))closeReviewMenu();
});
window.addEventListener('resize',closeReviewMenu);
function bloomEntryDue(entry){
  const t=Date.parse(entry&&entry.nextReviewAt||entry&&entry.addedAt||0);
  return Number.isFinite(t)&&t<=Date.now();
}
function getBloomDue(){
  const out=[];
  Object.entries(getMistakes()).forEach(([uid,e])=>{if(bloomEntryDue(e))out.push(Object.assign({uid,source:'mistake'},e));});
  Object.entries(getSkips()).forEach(([uid,e])=>{if(bloomEntryDue(e))out.push(Object.assign({uid,source:'skip'},e));});
  return out.sort((a,b)=>Date.parse(a.nextReviewAt||a.addedAt||0)-Date.parse(b.nextReviewAt||b.addedAt||0));
}

