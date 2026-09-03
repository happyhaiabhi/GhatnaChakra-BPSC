/* screen navigation and theme toggle
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function showScreen(id){document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));document.getElementById(id).classList.add('active');document.body.dataset.activeScreen=id;}
function backToSetup(){clearInterval(timerInterval);showScreen('setup-screen');buildDashboard();}
function goHome(){clearInterval(timerInterval);showScreen('setup-screen');buildDashboard();}
function confirmHome(){const ans=state.answers?.filter(a=>!isSkippedAnswer(a)).length||0;if(ans>0&&!confirm('Exit quiz? Progress will be lost.'))return;backToSetup();}

function applyTheme(t){
  const hasSharedTheme=window.ExamPortalTheme&&typeof window.ExamPortalTheme.apply==='function';
  const safe=hasSharedTheme?window.ExamPortalTheme.apply(t):(t==='dark'?'dark':'light');
  if(!hasSharedTheme){
    document.documentElement.setAttribute('data-theme',safe);
    document.documentElement.style.colorScheme=safe;
  }
  [document.getElementById('theme-btn'),document.getElementById('theme-btn-q'),document.getElementById('theme-btn-books')].forEach(btn=>{if(btn)btn.textContent=safe==='light'?'\uD83C\uDF19':'\u2600\uFE0F';});
}
function toggleTheme(){const cur=document.documentElement.getAttribute('data-theme')||'light';applyTheme(cur==='dark'?'light':'dark');}

document.addEventListener('keydown',function(e){
  const qs=document.getElementById('quiz-screen');if(!qs||!qs.classList.contains('active'))return;if(paused)return;if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;
  if(e.code==='Space'){
    e.preventDefault();const i=state.current,q=quiz[i],keys=(shuffledOptionOrders[i]||Object.keys(q.options||{})).filter(k=>q.options[k]);
    if(questionCorrectKeys(q).length>1){const selected=selectedAnswerKeys(state.answers[i]),next=keys.find(key=>!selected.includes(key));state.answers[i]=next?[...selected,next]:null;}
    else{const cur=state.answers[i],idx=keys.indexOf(cur),next=idx+1;state.answers[i]=next<keys.length?keys[next]:null;}
    renderQuestion();renderPalette();updateStats();
  }
  if(e.code==='Enter'){e.preventDefault();if(state.current===quiz.length-1)submitQuiz();else saveAndNext();}
  if(e.code==='KeyB'){e.preventDefault();toggleBookmark();}
  if(e.code==='KeyP'){e.preventDefault();goToPrev();}
});

// ════════════════════════════════════════════════════════════════
// SIMPLE GOOGLE ACCOUNT SYNC — Firebase stores progress; GitHub Pages hosts UI
// ════════════════════════════════════════════════════════════════
const SYNC_BASE_KEYS=['gc_mistakes','gc_bookmarks','gc_skips','gc_history','gc_archive','gc_attempts'];
const SYNC_ACTIVE_BANK_BASE_KEYS=['gc_mistakes','gc_bookmarks','gc_skips'];
// Resolve the active book's namespaced keys at call time.
