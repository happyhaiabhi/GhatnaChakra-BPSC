/* book manifests, data-file resolution and loading
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
// ===== MULTI-BOOK SUPPORT =====
// Books are defined in books/books.json. The first book keeps its original
// localStorage/Firestore keys so existing users never lose progress. Every
// other book gets namespaced keys, keeping its progress separate.
let BOOKS=[];
const LEGACY_BOOK_ID='bpsc_ghatna_chakra';
let currentBook=null;          // active book manifest object
let SUBJECTS_CONFIG=[];        // rebuilt per book from that book's chapters.json
let currentChaptersIndex=[];   // raw chapters.json for the active book
let chapterIconMap={};         // chapter name -> emoji icon, from chapters.json
let bookDataDir='data';        // base path for the active book's data files

function sk(baseKey){
  if(!currentBook||currentBook.id===LEGACY_BOOK_ID)return baseKey;
  return baseKey+'__book_'+currentBook.id;
}
function bookFilePath(file){
  // A subject "file" entry is resolved against the active book's dataDir, so a
  // chapters index may use either a bare filename ("biology.json") or a path
  // ("data/biology.json") — both mean "this file inside the book's data dir".
  // The legacy BPSC book declares dataDir "." and keeps its original
  // repository-root-relative paths ("data/biology.json").
  if(/^(https?:)?\/\//.test(file))return file;
  let clean=String(file).replace(/^(\.\/)+/,'').replace(/^\/+/,'');
  const dir=String(bookDataDir||'').replace(/\/+$/,'');
  if(!dir||dir==='.')return clean;                        // legacy book: paths stay as written
  if(clean===dir||clean.indexOf(dir+'/')===0)return clean; // already inside the book dir (idempotent)
  return dir+'/'+clean.replace(/^data\//,'');              // drop a stray "data/" prefix
}

// Every plausible location for a subject's data file, best guess first. Used by
// fetchBookData() so one stale path in a chapters index cannot blank out a book.
function bookDataCandidates(subj){
  // Always resolve from the RAW manifest value: subj.file may already carry a
  // book's dataDir, and re-resolving that against a different dataDir would
  // stack the prefixes.
  const raw=String((subj&&(subj.rawFile||subj.file))||'').replace(/^(\.\/)+/,'');
  const dir=String(bookDataDir||'').replace(/\/+$/,'');
  const base=raw.split('/').pop();
  const key=subj&&subj.id?String(subj.id):'';
  const list=[];
  const add=p=>{if(p&&list.indexOf(p)===-1)list.push(p);};
  add(bookFilePath(raw));
  add(raw);
  if(dir&&dir!=='.'){
    if(base)add(dir+'/'+base);
    if(key)add(dir+'/'+key+'.json');
  }
  if(subj)add(subj.file);
  return list;
}

// Fetch + parse a subject data file, falling back through bookDataCandidates().
// Throws an Error whose message names every URL tried and why each one failed.
async function fetchBookData(subj){
  const label=(subj&&subj.name)||(subj&&subj.id)||'subject';
  const tried=[];
  const candidates=bookDataCandidates(subj);
  for(let i=0;i<candidates.length;i++){
    const url=candidates[i];
    let resp;
    try{resp=await fetch(url);}
    catch(err){tried.push(url+' (network error)');continue;}
    if(!resp.ok){tried.push(url+' (HTTP '+resp.status+')');continue;}
    let data;
    try{data=await resp.json();}
    catch(err){tried.push(url+' (not valid JSON)');continue;}
    if(data&&typeof data==='object')return data;
    tried.push(url+' (unexpected payload)');
  }
  const err=new Error('Could not load '+label+' questions. Tried: '+tried.join(', '));
  err.attempts=tried;
  throw err;
}

function dataLoadErrorHtml(err){
  const detail=escapeHtml((err&&err.message)||'Unknown error');
  const hint=location.protocol==='file:'
    ?'This page is open as a local file, and browsers block data file reads from file:// URLs. Serve the folder instead (e.g. <code>python3 -m http.server</code>) or open the deployed site.'
    :'The data file(s) for this subject could not be fetched. The URLs that were tried are listed below.';
  return '<div style="padding:18px;text-align:left;font-size:0.72rem;line-height:1.65;color:var(--red);">'
    +'&#x26A0; Could not load this subject.<br>'+hint
    +'<br><span style="color:var(--text3);word-break:break-all;">'+detail+'</span></div>';
}
function resolveBookChaptersUrl(book){
  const dir=book.dataDir&&book.dataDir!=='.'?book.dataDir.replace(/\/$/,'')+'/':'';
  return dir+book.chaptersFile;
}

