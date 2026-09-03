/* Firebase sign-in and cloud sync
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function syncDataKeys(){return SYNC_BASE_KEYS.map(k=>sk(k));}
function syncActiveBankKeys(){return SYNC_ACTIVE_BANK_BASE_KEYS.map(k=>sk(k));}
function isHistoryKey(key){return key===sk('gc_history')||key===sk('gc_attempts');}
const FIREBASE_CFG={
  apiKey:'AIzaSyB5vVuyG2NbMdTUOY78NlZ702mlkmmPuFA',
  authDomain:'mcq-practise-ff181.firebaseapp.com',
  projectId:'mcq-practise-ff181'
};

let fbApp=null,fbDb=null,fbAuth=null,fbUserId=null,syncListeners=[],syncStatus='offline';
const _pushTimers={};

function getSyncConfig(){return LS.get('gc_sync_cfg',null);}
function saveSyncConfig(value){LS.set('gc_sync_cfg',value);}
function defaultSyncValue(key){return isHistoryKey(key)?[]:{};}
function readSyncLocal(key){return LS.get(key,defaultSyncValue(key));}
function isPlainObject(value){return !!value&&typeof value==='object'&&!Array.isArray(value);}
function dateNumber(value,fallback){const n=Date.parse(value||'');return Number.isFinite(n)?n:fallback;}

function mergeHistory(localValue,cloudValue){
  const local=Array.isArray(localValue)?localValue:[];
  const cloud=Array.isArray(cloudValue)?cloudValue:[];
  const byId=new Map();
  [...cloud,...local].forEach((entry,index)=>{
    if(!entry||typeof entry!=='object')return;
    const id=entry.id||entry.date||`legacy-${index}-${JSON.stringify(entry)}`;
    byId.set(id,Object.assign({},byId.get(id)||{},entry));
  });
  return [...byId.values()].sort((a,b)=>dateNumber(b.date,0)-dateNumber(a.date,0)).slice(0,200);
}

function mergeBankObjects(localValue,cloudValue){
  const local=isPlainObject(localValue)?localValue:{};
  const cloud=isPlainObject(cloudValue)?cloudValue:{};
  const merged={};
  new Set([...Object.keys(cloud),...Object.keys(local)]).forEach(uid=>{
    const left=isPlainObject(local[uid])?local[uid]:null;
    const right=isPlainObject(cloud[uid])?cloud[uid]:null;
    if(!left){merged[uid]=right;return;}
    if(!right){merged[uid]=left;return;}
    const item=Object.assign({},right,left);
    if('times' in left||'times' in right)item.times=Math.max(Number(left.times)||0,Number(right.times)||0);
    if('correctCount' in left||'correctCount' in right)item.correctCount=Math.max(Number(left.correctCount)||0,Number(right.correctCount)||0);
    if(left.addedAt||right.addedAt){
      const candidates=[left.addedAt,right.addedAt].filter(Boolean).sort((a,b)=>dateNumber(a,Infinity)-dateNumber(b,Infinity));
      item.addedAt=candidates[0];
    }
    if(left.archivedAt||right.archivedAt){
      const candidates=[left.archivedAt,right.archivedAt].filter(Boolean).sort((a,b)=>dateNumber(b,0)-dateNumber(a,0));
      item.archivedAt=candidates[0];
    }
    merged[uid]=item;
  });
  return merged;
}

function mergeSyncValue(key,localValue,cloudValue){
  return isHistoryKey(key)?mergeHistory(localValue,cloudValue):mergeBankObjects(localValue,cloudValue);
}

// Archive entries are deletion tombstones. They prevent an older device from
// restoring a mastered, removed, or explicitly archived active-bank item.
function reconcileArchivedItems(){
  const archived=readSyncLocal(sk('gc_archive'));
  const archivedIds=new Set(Object.keys(isPlainObject(archived)?archived:{}));
  const changed=[];
  syncActiveBankKeys().forEach(key=>{
    const bank=readSyncLocal(key);let dirty=false;
    archivedIds.forEach(uid=>{if(Object.prototype.hasOwnProperty.call(bank,uid)){delete bank[uid];dirty=true;}});
    if(dirty){LS.set(key,bank);changed.push(key);}
  });
  return changed;
}

function refreshProgressUI(){updateAllBadges();buildDashboard();}
function updateLastSyncLabel(){
  const el=document.getElementById('sync-last-time');if(!el)return;
  const stamp=localStorage.getItem(sk('gc_last_sync'));
  el.textContent=stamp?new Date(stamp).toLocaleString():'Not yet';
}
function markSyncSuccess(){localStorage.setItem(sk('gc_last_sync'),new Date().toISOString());updateLastSyncLabel();}

function setSyncStatus(status){
  syncStatus=status;
  const dot=document.getElementById('sync-status-dot');
  if(dot){dot.className='sync-dot '+status;dot.title=({synced:'Synced ✓',syncing:'Syncing…',error:'Sync error ⚠',offline:'Sync off'})[status]||status;}
  const label=document.querySelector('#sync-nav-btn .nav-btn-label');
  if(label)label.textContent=({synced:'Synced',syncing:'Syncing…',error:'Sync error',offline:'Sync'})[status]||'Sync';
  const live=document.getElementById('sync-live-state');
  if(live){
    live.textContent=({synced:'✓ Synced',syncing:'↻ Syncing…',error:'⚠ Sync error',offline:'Sync off'})[status]||status;
    live.style.color=status==='error'?'var(--red)':status==='syncing'?'var(--gold)':status==='synced'?'var(--green)':'var(--text3)';
  }
}

function loadScript(src){
  return new Promise((resolve,reject)=>{
    const existing=document.querySelector('script[src="'+src+'"]');
    if(existing){
      if(existing.dataset.loaded==='true'){resolve();return;}
      existing.addEventListener('load',resolve,{once:true});existing.addEventListener('error',reject,{once:true});return;
    }
    const script=document.createElement('script');script.src=src;script.async=true;
    script.onload=()=>{script.dataset.loaded='true';resolve();};script.onerror=reject;document.head.appendChild(script);
  });
}

async function ensureFirebaseSDK(){
  if(window.firebase&&window.firebase.auth&&window.firebase.firestore)return true;
  try{
    await loadScript('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
    await loadScript('https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore-compat.js');
    await loadScript('https://www.gstatic.com/firebasejs/10.12.0/firebase-auth-compat.js');
    return true;
  }catch(error){console.error('Firebase SDK load failed:',error);return false;}
}

async function initFirebase(){
  if(fbDb&&fbAuth)return true;
  if(!await ensureFirebaseSDK())return false;
  try{
    fbApp=window.firebase.apps.find(app=>app.name==='ghatnachakra')||window.firebase.initializeApp(FIREBASE_CFG,'ghatnachakra');
    fbDb=window.firebase.firestore(fbApp);fbAuth=window.firebase.auth(fbApp);
    try{await fbAuth.setPersistence(window.firebase.auth.Auth.Persistence.LOCAL);}catch(error){console.warn('Auth persistence unavailable:',error);}
    return true;
  }catch(error){console.error('Firebase init error:',error);return false;}
}

function payloadByteLength(value){
  const text=JSON.stringify(value);
  try{return new Blob([text]).size;}catch(error){return text.length;}
}

// Question text/options already live in the static JSON bank. Firestore only
// needs each question UID and its progress metadata. Omitting the duplicated
// `q` object keeps even all 4,441 skips well below Firestore's 1 MiB limit.
function compactSyncValue(key,value){
  if(isHistoryKey(key))return Array.isArray(value)?value:[];
  if(!isPlainObject(value))return {};
  const compact={};
  Object.entries(value).forEach(([uid,item])=>{
    if(!isPlainObject(item))return;
    const metadata={};
    Object.entries(item).forEach(([field,fieldValue])=>{if(field!=='q')metadata[field]=fieldValue;});
    compact[uid]=metadata;
  });
  return compact;
}

let syncQuestionCatalog=null,syncQuestionCatalogPromise=null;
async function ensureSyncQuestionCatalog(){
  if(syncQuestionCatalog)return syncQuestionCatalog;
  if(syncQuestionCatalogPromise)return syncQuestionCatalogPromise;
  syncQuestionCatalogPromise=Promise.all(SUBJECTS_CONFIG.map(async subj=>{
    let data=subjectDataCache[subj.id];
    if(!data){
      data=await fetchBookData(subj);subjectDataCache[subj.id]=data;
    }
    return [subj,data];
  })).then(pairs=>{
    const catalog={};
    pairs.forEach(([subj,data])=>{
      let idx=0;
      (data.chapters||[]).forEach(ch=>{
        const chName=ch.chapter_name||ch.name||'General';
        (ch.questions||[]).forEach(q=>{
          const internal=toInternalQuestion(q,subj.id,idx++,chName);
          catalog[internal.uid]=internal;
        });
      });
    });
    syncQuestionCatalog=catalog;return catalog;
  }).catch(error=>{syncQuestionCatalogPromise=null;throw error;});
  return syncQuestionCatalogPromise;
}

async function hydrateLocalSyncBanks(keys){keys=keys||syncDataKeys();
  const targets=keys.filter(key=>!isHistoryKey(key)).filter(key=>{
    const value=readSyncLocal(key);
    return Object.values(isPlainObject(value)?value:{}).some(item=>isPlainObject(item)&&!item.q);
  });
  if(!targets.length)return [];
  const catalog=await ensureSyncQuestionCatalog(),changed=[];
  targets.forEach(key=>{
    const value=readSyncLocal(key),hydrated={};let dirty=false,unresolved=0;
    Object.entries(isPlainObject(value)?value:{}).forEach(([uid,item])=>{
      if(!isPlainObject(item)){hydrated[uid]=item;return;}
      if(!item.q&&catalog[uid]){hydrated[uid]=Object.assign({},item,{q:catalog[uid]});dirty=true;}
      else{hydrated[uid]=item;if(!item.q)unresolved++;}
    });
    if(dirty){LS.set(key,hydrated);changed.push(key);}
    if(unresolved)console.warn(`${unresolved} ${key} entries could not be matched to the local question bank.`);
  });
  return changed;
}

function cloudRef(key){return fbDb.collection('users').doc(fbUserId).collection('data').doc(key);}

function isPermissionDenied(error){
  const code=String(error&&error.code||'');
  const message=String(error&&error.message||error||'');
  return code==='permission-denied'||code==='firestore/permission-denied'||/insufficient permissions/i.test(message);
}
function friendlySyncError(error){
  if(isPermissionDenied(error)){
    return 'Missing or insufficient permissions. Publish firestore.rules in Firebase Console → Firestore Database → Rules, then tap Sync now. Progress on this device is safe.';
  }
  return (error&&error.message)||'Sync failed. Please try again.';
}

async function readAllFromCloud(){
  // Read each known key with get() instead of listing the collection. A
  // collection query is denied when live rules attach extra constraints to
  // document ids, which surfaces as "Missing or insufficient permissions".
  const remote={};
  const keys=syncDataKeys();
  if(!fbDb||!fbUserId)throw new Error('Not signed in');
  const docs=await Promise.all(keys.map(async key=>{
    try{return [key,await cloudRef(key).get()];}
    catch(error){if(isPermissionDenied(error))throw error;console.warn('Cloud read skipped:',key,error);return [key,null];}
  }));
  docs.forEach(([key,doc])=>{
    if(!doc||!doc.exists)return;
    const data=typeof doc.data==='function'?doc.data():null;
    if(!data||typeof data.payload!=='string')return;
    try{remote[key]=JSON.parse(data.payload);}catch(error){console.warn('Ignored invalid cloud payload:',key);}
  });
  return remote;
}

async function writeKeysToCloud(keys){keys=keys||syncDataKeys();
  if(!fbDb||!fbUserId)throw new Error('Not signed in');
  // Write documents one at a time. A single batch fails entirely if live
  // rules omit a newer key such as gc_attempts.
  const failures=[];
  for(const key of keys){
    const value=compactSyncValue(key,readSyncLocal(key));
    if(payloadByteLength(value)>850000)throw new Error(`${key} compact progress is unexpectedly too large to sync.`);
    try{await cloudRef(key).set({payload:JSON.stringify(value),updatedAt:Date.now()});}
    catch(error){
      failures.push({key,error});
      if(isPermissionDenied(error))console.warn('Cloud save skipped for',key,error.message);
      else console.error('Cloud save failed for',key,error);
    }
  }
  if(failures.length===keys.length)throw failures[0].error;
  if(failures.length)console.warn('Some sync keys could not be written:',failures.map(item=>item.key).join(', '));
}

async function synchronizeAll(showToast=false){
  if(!fbDb||!fbUserId)return false;
  setSyncStatus('syncing');
  try{
    const remote=await readAllFromCloud();
    syncDataKeys().forEach(key=>LS.set(key,mergeSyncValue(key,readSyncLocal(key),remote[key]??defaultSyncValue(key))));
    reconcileArchivedItems();
    await hydrateLocalSyncBanks();
    await writeKeysToCloud();
    refreshProgressUI();markSyncSuccess();setSyncStatus('synced');
    if(showToast)showSyncToast('✓ Progress synced on all devices');
    return true;
  }catch(error){
    setSyncStatus('error');showConnectedSyncStatus(friendlySyncError(error),'err');console.error('Sync failed:',error);return false;
  }
}

async function finishGoogleSignIn(user,announce=true){
  if(!user)return false;
  fbUserId=user.uid;
  const config={userId:user.uid,email:user.email||'',name:user.displayName||'Google user',photo:user.photoURL||''};
  saveSyncConfig(config);showSignedInUI(config);updateSyncNavBtn(true);
  const ok=await synchronizeAll(false);
  setupRealtimeListeners();
  if(ok&&announce)showSyncToast(`Signed in as ${config.name}`);
  return ok;
}

async function signInWithGoogle(){
  const button=document.getElementById('google-signin-btn');
  if(button){button.disabled=true;button.style.opacity='.7';}
  showSyncModalStatus('Opening Google sign-in…','info');
  if(!await initFirebase()){
    showSyncModalStatus('Firebase could not start. Check your connection and Firebase setup.','err');
    if(button){button.disabled=false;button.style.opacity='1';}return;
  }
  const provider=new window.firebase.auth.GoogleAuthProvider();provider.setCustomParameters({prompt:'select_account'});
  try{
    const result=await fbAuth.signInWithPopup(provider);
    await finishGoogleSignIn(result.user,true);
    setTimeout(closeSyncModal,900);
  }catch(error){
    if(error&&['auth/popup-blocked','auth/operation-not-supported-in-this-environment'].includes(error.code)){
      showSyncModalStatus('Redirecting to Google sign-in…','info');
      await fbAuth.signInWithRedirect(provider);return;
    }
    const message=error&&error.code==='auth/unauthorized-domain'
      ?'This GitHub Pages domain is not authorized in Firebase. Add it under Authentication → Settings → Authorized domains.'
      :(error.message||'Google sign-in failed.');
    showSyncModalStatus(message,'err');
  }finally{
    if(button){button.disabled=false;button.style.opacity='1';}
  }
}

function showSignedInUI(config){
  const signIn=document.getElementById('sync-view-signin'),connected=document.getElementById('sync-view-connected');
  if(signIn)signIn.style.display='none';if(connected)connected.style.display='';
  const signOut=document.getElementById('sync-disconnect-btn'),syncNowButton=document.getElementById('sync-now-btn');
  if(signOut)signOut.style.display='';if(syncNowButton)syncNowButton.style.display='';
  const name=document.getElementById('sync-user-name'),email=document.getElementById('sync-user-email'),photo=document.getElementById('sync-user-photo');
  if(name)name.textContent=config.name||'Google user';if(email)email.textContent=config.email||'';
  if(photo){if(config.photo){photo.src=config.photo;photo.style.display='';}else{photo.removeAttribute('src');photo.style.display='none';}}
  updateLastSyncLabel();
}

function showSignedOutUI(){
  const signIn=document.getElementById('sync-view-signin'),connected=document.getElementById('sync-view-connected');
  if(signIn)signIn.style.display='';if(connected)connected.style.display='none';
  const signOut=document.getElementById('sync-disconnect-btn'),syncNowButton=document.getElementById('sync-now-btn');
  if(signOut)signOut.style.display='none';if(syncNowButton)syncNowButton.style.display='none';
}

function setupRealtimeListeners(){
  syncListeners.forEach(unsubscribe=>unsubscribe());syncListeners=[];
  if(!fbDb||!fbUserId)return;
  syncDataKeys().forEach(key=>{
    const unsubscribe=cloudRef(key).onSnapshot(async doc=>{
      if(!doc.exists||(doc.metadata&&doc.metadata.hasPendingWrites))return;
      try{
        const data=doc.data();if(!data||typeof data.payload!=='string')return;
        const cloudValue=JSON.parse(data.payload),localValue=readSyncLocal(key);
        const merged=mergeSyncValue(key,localValue,cloudValue);
        const changed=JSON.stringify(merged)!==JSON.stringify(localValue);
        if(changed)LS.set(key,merged);
        const reconciled=reconcileArchivedItems();
        const hydrated=await hydrateLocalSyncBanks([key]);
        const currentValue=readSyncLocal(key);
        refreshProgressUI();markSyncSuccess();setSyncStatus('synced');
        if(JSON.stringify(compactSyncValue(key,currentValue))!==JSON.stringify(compactSyncValue(key,cloudValue)))cloudPushKey(key);
        reconciled.forEach(changedKey=>cloudPushKey(changedKey));
        if(changed||hydrated.length||reconciled.length)showSyncToast('☁ Synced from another device');
      }catch(error){setSyncStatus('error');console.error('Realtime sync failed:',error);}
    },error=>{
      console.error('Cloud listener failed:',key,error);
      if(isPermissionDenied(error))return;
      setSyncStatus('error');
    });
    syncListeners.push(unsubscribe);
  });
}

function cloudPushKey(key){
  if(!fbDb||!fbUserId||!syncDataKeys().includes(key))return;
  clearTimeout(_pushTimers[key]);
  _pushTimers[key]=setTimeout(async()=>{
    setSyncStatus('syncing');
    try{
      const value=compactSyncValue(key,readSyncLocal(key));
      if(payloadByteLength(value)>850000)throw new Error(`${key} compact progress is unexpectedly too large to sync.`);
      await cloudRef(key).set({payload:JSON.stringify(value),updatedAt:Date.now()});
      markSyncSuccess();setSyncStatus('synced');
    }catch(error){setSyncStatus('error');showConnectedSyncStatus(error.message||'Sync failed.','err');console.error('Cloud save failed:',error);}
  },700);
}

const _saveHistory0=saveHistory,_saveMistakes0=saveMistakes,_saveBookmarks0=saveBookmarks,_saveSkips0=saveSkips,_saveArchive0=saveArchive,_saveAttempts0=saveAttempts;
saveHistory=value=>{_saveHistory0(value);cloudPushKey(sk('gc_history'));};
saveMistakes=value=>{_saveMistakes0(value);cloudPushKey(sk('gc_mistakes'));};
saveBookmarks=value=>{_saveBookmarks0(value);cloudPushKey(sk('gc_bookmarks'));};
saveSkips=value=>{_saveSkips0(value);cloudPushKey(sk('gc_skips'));};
saveArchive=value=>{_saveArchive0(value);cloudPushKey(sk('gc_archive'));};
saveAttempts=value=>{_saveAttempts0(value);cloudPushKey(sk('gc_attempts'));};

async function syncNow(){
  if(!fbUserId){openSyncModal();return;}
  showConnectedSyncStatus('Merging this device with the cloud…','info');
  const ok=await synchronizeAll(true);
  if(ok)showConnectedSyncStatus('Everything is up to date.','ok');
}
async function pushAllToCloud(){return synchronizeAll(false);}
async function pullFromCloud(){return synchronizeAll(true);}

async function disconnectSync(){
  if(!confirm('Sign out from cloud sync? Your progress will remain on this device.'))return;
  syncListeners.forEach(unsubscribe=>unsubscribe());syncListeners=[];
  Object.values(_pushTimers).forEach(timer=>clearTimeout(timer));
  if(fbAuth)try{await fbAuth.signOut();}catch(error){console.warn('Firebase sign-out failed:',error);}
  fbUserId=null;localStorage.removeItem('gc_sync_cfg');setSyncStatus('offline');updateSyncNavBtn(false);showSignedOutUI();closeSyncModal();showSyncToast('Signed out. Local progress was kept.');
}

function showSyncModalStatus(message,type){
  const el=document.getElementById('sync-modal-status');if(!el)return;
  el.textContent=message;el.className='modal-status show '+type;
}
function showConnectedSyncStatus(message,type){
  const el=document.getElementById('sync-modal-status-connected');if(!el)return;
  el.textContent=message;el.className='modal-status show '+type;
}
function openSyncModal(){
  const config=getSyncConfig();
  if(fbUserId&&config)showSignedInUI(config);else showSignedOutUI();
  const status=document.getElementById('sync-modal-status');if(status)status.className='modal-status';
  document.getElementById('sync-modal').classList.remove('hidden');
}
function closeSyncModal(){document.getElementById('sync-modal').classList.add('hidden');}
function showSyncToast(message){
  const toast=document.getElementById('sync-toast');if(!toast)return;
  toast.textContent=message;toast.style.opacity='1';clearTimeout(toast._to);toast._to=setTimeout(()=>{toast.style.opacity='0';},2800);
}
function updateSyncNavBtn(connected){
  const button=document.getElementById('sync-nav-btn');if(!button)return;
  const label=button.querySelector('.nav-btn-label');if(label)label.textContent=connected?'Synced':'Sync';
  const dot=button.querySelector('.sync-dot');if(dot){dot.className='sync-dot '+(connected?'synced':'offline');dot.title=connected?'Synced ✓':'Sync off';}
}

let _authListenerRegistered=false;
async function initSyncOnLoad(){
  const config=getSyncConfig();if(!config||!config.userId){showSignedOutUI();return;}
  setSyncStatus('syncing');
  if(!await initFirebase()){setSyncStatus('error');return;}
  if(!_authListenerRegistered){
    _authListenerRegistered=true;
    fbAuth.onAuthStateChanged(async user=>{
      if(user){await finishGoogleSignIn(user,false);}
      else{fbUserId=null;setSyncStatus('offline');updateSyncNavBtn(false);showSignedOutUI();}
    });
  }else if(fbAuth.currentUser){
    // Already signed in from a previous book — sync the newly opened book.
    finishGoogleSignIn(fbAuth.currentUser,false);
  }
}



// ════════════════════════════════════════════════════════════════
// EXPORT PDF / PRINTABLE WORKSHEET GENERATOR
// ════════════════════════════════════════════════════════════════
