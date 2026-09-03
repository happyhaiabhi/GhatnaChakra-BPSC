/* focus timer
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function fmtFocus(s){const m=Math.floor(s/60),sec=s%60;return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;}
function updateFocusUI(){
  const disp=document.getElementById('focus-display'),cap=document.getElementById('focus-caption'),btn=document.getElementById('focus-start-btn');
  if(disp)disp.textContent=fmtFocus(focusRemaining);
  if(cap)cap.textContent=focusRunning?'Focus session — stay with one question at a time':focusRemaining<focusTotal?'Paused — take a breath':'Ready when you are';
  if(btn)btn.textContent=focusRunning?'Pause':'Start';
}
function setFocusMode(mode){
  clearInterval(focusTimerInterval);focusRunning=false;focusMode=mode;focusTotal=parseInt(mode,10)*60;focusRemaining=focusTotal;
  ['25','15','5'].forEach(m=>{const el=document.getElementById('focus-chip-'+m);if(el)el.classList.toggle('active',m===mode);});
  updateFocusUI();
}
function toggleFocusTimer(){
  if(focusRunning){clearInterval(focusTimerInterval);focusRunning=false;updateFocusUI();return;}
  focusRunning=true;focusTimerInterval=setInterval(()=>{
    if(focusRemaining<=0){
      clearInterval(focusTimerInterval);focusRunning=false;focusBeep();
      const next=focusMode==='5'?'25':'5';
      setFocusMode(next);
      const cap=document.getElementById('focus-caption');
      if(cap)cap.textContent=(next==='5'?'Focus session done — take a 5-minute break 🌿':'Break over — ready for another focus sprint 🌱');
      return;
    }
    focusRemaining--;updateFocusUI();
  },1000);
  updateFocusUI();
}
function resetFocusTimer(){clearInterval(focusTimerInterval);focusRunning=false;focusTotal=parseInt(focusMode,10)*60;focusRemaining=focusTotal;updateFocusUI();}
function openFocusModal(){document.getElementById('focus-modal')?.classList.remove('hidden');updateFocusUI();}
function closeFocusModal(){clearInterval(focusTimerInterval);focusRunning=false;document.getElementById('focus-modal')?.classList.add('hidden');updateFocusUI();}
function focusBeep(){try{const ctx=new (window.AudioContext||window.webkitAudioContext)();const o=ctx.createOscillator(),g=ctx.createGain();o.type='sine';o.frequency.value=659;g.gain.value=0.08;o.connect(g);g.connect(ctx.destination);o.start();setTimeout(()=>{o.stop();ctx.close();},550);}catch(e){}}

