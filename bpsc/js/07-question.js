/* text normalisation and question parsing/rendering (assertion, match, numbered)
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function shuffle(arr){for(let i=arr.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[arr[i],arr[j]]=[arr[j],arr[i]];}return arr;}

function startQuiz(mode,customPool){
  let pool;
  let rangeSuffix = '';
  if(mode==='mistakes'||mode==='wrong'||mode==='skips'||mode==='bookmarks'||mode==='archive'||mode==='bloom'||mode==='supersearch'||mode==='history'||mode==='topic'){pool=shuffle([...customPool]);}
  else{
    let base=[...allQuestions].filter(q=>selectedChapters.has(q.chapter));
    if(selectedSubtopics.size>0)base=base.filter(q=>selectedSubtopics.has(q.sub_topic));

    const totalCount = base.length;
    const range = getQuestionSelectionRange(totalCount);
    if(range.from !== 1 || range.to !== totalCount){
      rangeSuffix = ` (Q${range.from}–${range.to})`;
    }

    let sliced = base.slice(range.from - 1, range.to);
    if(document.getElementById('toggle-shuffle')?.checked) sliced = shuffle(sliced);
    pool = sliced;
  }
  if(!pool.length){alert('No questions found!');return;}
  quiz=pool;
  const selectedList=Array.from(selectedChapters).join(', ');
  const subtopicList=Array.from(selectedSubtopics).join(', ');
  quizMeta={mode,subjectId:currentSubjectId,chapter:(selectedList||'Practice')+rangeSuffix,subtopic:subtopicList,range:rangeSuffix,startTime:new Date()};
  state={current:0,answers:new Array(quiz.length).fill(null),visited:new Array(quiz.length).fill(false),marked:new Array(quiz.length).fill(false)};state.visited[0]=true;
  const doSO=document.getElementById('toggle-shuffle-opts')?.checked||false;shuffledOptionOrders=quiz.map(q=>{const keys=Object.keys(q.options||{});return doSO?shuffle([...keys]):keys;});
  const mins=parseInt(document.getElementById('timer-mins')?.value||0);totalSecs=mins*60;
  const subj=SUBJECTS_CONFIG.find(s=>s.id===currentSubjectId);const chLabel=quizMeta.chapter||'Practice';
  document.getElementById('topbar-bc').innerHTML=`${subj?.name||'Quiz'} <span>&#183; ${mode==='mistakes'?'Mistake Practice':mode==='wrong'?'Retry Wrong':mode==='skips'?'Skip Practice':mode==='bookmarks'?'Bookmark Practice':mode==='archive'?'Archive Practice':mode==='bloom'?'Bloom Review':mode==='supersearch'?'Super Search':mode==='history'?'Re-practice':mode==='topic'?'&#127991;&#65039; '+escapeHtml(topicQuizName||'Topic Practice'):chLabel.substring(0,40)+(chLabel.length>40?'...':'')}</span>`;
  const t=document.documentElement.getAttribute('data-theme')||'light';const qBtn=document.getElementById('theme-btn-q');if(qBtn)qBtn.textContent=t==='light'?'\uD83C\uDF19':'\u2600\uFE0F';
  setPaletteOpen(window.innerWidth > 599);
  showScreen('quiz-screen');renderQuestion();renderPalette();updateStats();clearInterval(timerInterval);paused=false;
  document.getElementById('pause-btn').textContent='Pause';document.getElementById('timer-display').classList.remove('urgent');
  if(totalSecs>0)startTimer();else document.getElementById('timer-display').textContent='\u221E';
}


function escapeHtml(value){
  return String(value??'').replace(/[&<>\"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[ch]));
}
// Soft line wraps left over from PDF extraction must not force artificial row
// breaks. A single newline is treated as a page-width wrap and becomes a space.
// A blank line (two newlines) stays a real paragraph break. A hyphenated word
// split across a wrap joins back together without an added space. Always run
// the result through escapeHtml before inserting it into the HTML.
// PDF extraction also leaves the ligature glyphs ﬁ (U+FB01) and ﬂ (U+FB02),
// and their ﬀ/ﬃ/ﬄ relatives (U+FB00/U+FB03/U+FB04), each followed by a
// spurious space ("ﬁ rst" for "first", "signiﬁ cant" for "significant",
// "oﬃ ce" for "office"). The space is removed so the word rejoins, except
// where the ligature ends a known standalone word and the next word is
// genuinely separate ("Suﬁ saint" stays "Sufi saint", "Khaﬁ Khan" stays
// "Khafi Khan", "stiﬀ resistance" stays "stiff resistance"), while true
// one-word continuations still join ("Suﬁ sm" -> "Sufism", "Raﬁ que" ->
// "Rafique"). Finally the glyphs expand to plain ASCII letter pairs.
const LIGATURE_EXPANSIONS={'\uFB00':'ff','\uFB01':'fi','\uFB02':'fl','\uFB03':'ffi','\uFB04':'ffl'};
const LIGATURE_BOUNDARY_NAMES={
  fi:new Set(['sufi','rafi','khafi','shafi','aufi','kashifi','mustarfi']),
  ff:new Set(['buff','off','staff','stiff','scoff'])
};
const LIGATURE_FOLLOWING_WORDS=new Set(['saint','saints','sage','sages','mystic','mystics','order','sect','sects','silsilah','silsila','khan','ahmed','ahmad','ahamad','kidwai','kalam','naqshbandi','associated','examine','wrote','translated','tradition','pantheism','or','with','called','as','sandstone','resistance','background']);
function keepLigatureBoundary(before,ligature,next){
  const expansion=LIGATURE_EXPANSIONS[ligature];
  const names=LIGATURE_BOUNDARY_NAMES[expansion];
  if(!names||!names.has((before+expansion).toLowerCase()))return false;
  if(/^\d/.test(next))return true;      // "Mustarﬁ 2." — a numbered row follows
  if(/^-+$/.test(next))return true;     // "Suﬁ - 1." — a dash introduces a list
  return LIGATURE_FOLLOWING_WORDS.has(next.toLowerCase().replace(/[^a-z].*$/,''));
}
function normalizeBookText(value){
  let text=String(value??'').replace(/\r\n?/g,'\n');
  text=text.replace(/([A-Za-z\u00C0-\u024F])-\n(?=[A-Za-z\u00C0-\u024F])/g,'$1');
  text=text.replace(/\n{2,}\s*\d{1,2}\s*\n{2,}/g, ' ');
  text=text.replace(/\n{2,}\s*\d{1,2}\s*$/g, '');
  text=text.replace(/^\s*\d{1,2}\s*\n{2,}/g, '');
  text=text.replace(/([^\n])\n(?=[^\n])/g,'$1 ');
  text=text.replace(/(^|\n)\s*3\s+(?=\d+[\.\)])/g, '$1');
  text=text.replace(/(^|\n)\s*3\s+(?=[A-Za-z\u00C0-\u024F])/g, '$1• ');
  text=text.replace(/[^\n\S]+([\.,;:!\?])/g, '$1');
  text=text.replace(/\(\s+/g, '(').replace(/\s+\)/g, ')');
  text=text.replace(/\[\s+/g, '[').replace(/\s+\]/g, ']');
  text=text.replace(/(?<![A-Z]\.[A-Z])(?<!\b[A-Za-z]\.[A-Za-z])(?<!\bi\.e)(?<!\be\.g)(?<!\bNo)(?<!\bno)(?<!\bRs)(?<!\bvs)([\.,;:!\?])([A-Za-z])/g, '$1 $2');
  text=text.replace(/[^\n\S]{2,}/g, ' ');
  text=text.replace(/\n{3,}/g, '\n\n');
  text=text.replace(/^\n(?=[^\n])/,'');
  text=text.replace(/(?<=[^\n])\n$/,'');
  text=text.replace(/([A-Za-z]*)([\uFB00-\uFB04]) (?=\S)/g,(whole,before,ligature,offset,string)=>{
    const next=string.slice(offset+whole.length).match(/^\S+/)[0];
    return before+ligature+(keepLigatureBoundary(before,ligature,next)?' ':'');
  });
  return text.replace(/[\uFB00-\uFB04]/g,ligature=>LIGATURE_EXPANSIONS[ligature]);
}
function bookText(value){
  return escapeHtml(normalizeBookText(value));
}

function questionAssetList(q){
  const out=[];
  const add=value=>{
    if(!value)return;
    if(Array.isArray(value)){value.forEach(add);return;}
    if(typeof value==='object'){add(value.src||value.url||value.path||value.asset||value.image);return;}
    const s=String(value).trim();
    if(s)out.push(s);
  };
  add(q&&q.asset);add(q&&q.image);add(q&&q.image_url);add(q&&q.images);add(q&&q.figure);
  return [...new Set(out)];
}

function resolveAssetUrl(src){
  if(!src)return '';
  if(/^(https?:)?\/\//i.test(src)||src.startsWith('data:')||src.startsWith('blob:'))return src;
  const clean=String(src).replace(/^\.\//,'');
  const dir=((currentBook&&currentBook.dataDir)||bookDataDir||'').replace(/\/data\/?$/,'').replace(/\/$/,'');
  if(dir&&dir!=='.')return dir+'/'+clean;
  return clean;
}

function renderQuestionAsset(q){
  const urls=questionAssetList(q).map(resolveAssetUrl).filter(Boolean);
  if(!urls.length)return '';
  return urls.map((url,index)=>`<figure class="q-asset"><img class="q-asset-img" src="${escapeHtml(url)}" alt="Question figure${urls.length>1?' '+(index+1):''}" loading="lazy"></figure>`).join('');
}

function questionCorrectKeys(q){
  const source=q&&q.correctKeys!=null?q.correctKeys:q&&q.correctKey!=null?q.correctKey:q&&(q.answer??q.correct_option);
  return normalizeAnswerKeys(source,q&&q.options||{});
}
function selectedAnswerKeys(value){return value==null?[]:(Array.isArray(value)?value:[value]).map(key=>String(key).toUpperCase());}
function answerHasKey(value,key){return selectedAnswerKeys(value).includes(String(key).toUpperCase());}
function isSkippedAnswer(value){return selectedAnswerKeys(value).length===0;}
function isQuestionCorrect(q,value){
  const correct=questionCorrectKeys(q).sort(),selected=selectedAnswerKeys(value).sort();
  return correct.length>0&&correct.length===selected.length&&correct.every((key,index)=>key===selected[index]);
}
function questionCorrectAnswerLabel(q){
  const keys=questionCorrectKeys(q),texts=keys.map(key=>optionDisplayText(q&&q.options&&q.options[key],key)).filter(Boolean);
  if(keys.length>1)return `${keys.join(' + ')} — ${texts.join(' • ')}`;
  const explicit=String(q&&q.correctAnswer||'');
  const displayText=texts[0]||'';
  return optionDisplayText(explicit,keys[0]||'A')!==explicit?displayText:String(explicit||displayText||keys[0]||'');
}
function optionDisplayText(value,key){
  const raw=String(value??'').trim();
  return /^\[\s*(?:diagram|figure|image|formula)\b[\s\S]*\]$/i.test(raw)?`Figure (${String(key).toLowerCase()})`:normalizeBookText(raw);
}

function splitTrailingInstruction(value){
  const text=String(value||'').trim();
  const marker=/(?:\n|\s)(Choose\b|Select\b|Which\s+(?:of\s+)?(?:the|these|statement|pair|option)|How\s+many\b|In\s+which\b|With\s+respect\s+to\b|In\s+reference\s+to\b|Code\s*:|Codes\s*:)/i;
  const match=marker.exec(text);
  if(!match)return{body:text,instruction:''};
  return{body:text.slice(0,match.index).trim(),instruction:text.slice(match.index).trim()};
}

function parseAssertionReason(question){
  const text=String(question||'').replace(/\r/g,'').trim();
  const assertionRe=/(?:^|\s)(?:1[.)]\s*)?Assertion\s*\(\s*A\s*\)\s*[:\-–—]\s*/ig;
  const assertionMatches=[...text.matchAll(assertionRe)];
  if(!assertionMatches.length)return null;
  const assertionMatch=assertionMatches[assertionMatches.length-1];
  const reasonRe=/(?:^|\s)(?:2[.)]\s*)?Reason\s*\(\s*R\s*\)\s*[:\-–—]\s*/ig;
  reasonRe.lastIndex=assertionMatch.index+assertionMatch[0].length;
  const reasonMatch=reasonRe.exec(text);
  if(!reasonMatch)return null;
  const assertion=text.slice(assertionMatch.index+assertionMatch[0].length,reasonMatch.index).trim();
  const reasonParts=splitTrailingInstruction(text.slice(reasonRe.lastIndex));
  if(!assertion||!reasonParts.body)return null;
  return{intro:text.slice(0,assertionMatch.index).trim(),assertion,reason:reasonParts.body,instruction:reasonParts.instruction};
}

function parseSequentialRows(question,kind){
  const text=String(question||'').replace(/\r/g,'').trim();
  // Markers accept "1.", "1)" and the parenthesized "(1)" convention (likewise
  // for letters and Roman numerals); a parenthesized marker must close with a
  // parenthesis. Roman is used by several Bihar CA "numbered statement" stems.
  const MARKERS={
    letter:{re:/(^|\n|\s)(?:\(([A-Ea-e])\)|([A-Ea-e])[.)])\s+/g,order:['A','B','C','D','E']},
    number:{re:/(^|\n|\s)(?:\((\d{1,2})\)|(\d{1,2})[.)])\s+/g,order:['1','2','3','4','5','6','7','8','9','10','11','12']},
    roman:{re:/(^|\n|\s)(?:\((VI|IV|III|II|I|V)\)|(VI|IV|III|II|I|V)[.)])\s+/gi,order:['I','II','III','IV','V','VI']}
  };
  const cfg=MARKERS[kind];if(!cfg)return null;
  const markerRe=cfg.re;
  const matches=[];let match;
  while((match=markerRe.exec(text))!==null)matches.push({label:(match[2]||match[3]).toUpperCase(),start:match.index+match[1].length,contentStart:markerRe.lastIndex});
  const firstLabel=cfg.order[0];let sequence=[];
  for(let start=0;start<matches.length;start++){
    if(matches[start].label!==firstLabel)continue;
    const candidate=[matches[start]];
    for(let i=start+1;i<matches.length;i++){
      const expected=cfg.order[candidate.length];
      if(matches[i].label===expected)candidate.push(matches[i]);
      else if(candidate.length>=2)break;
    }
    if(candidate.length>sequence.length)sequence=candidate;
  }
  if(sequence.length<2)return null;
  const rows=sequence.map((item,index)=>({label:item.label,text:text.slice(item.contentStart,sequence[index+1]?.start??text.length).trim()}));
  const trailing=splitTrailingInstruction(rows[rows.length-1].text);
  rows[rows.length-1].text=trailing.body;
  if(rows.some(row=>!row.text))return null;
  return{intro:text.slice(0,sequence[0].start).trim(),rows,instruction:trailing.instruction};
}
function parseNumberedStatements(question){
  // Arabic first, then Roman ("I. II. III. IV.") — both render as a clean
  // numbered statement list.
  let parsed=parseSequentialRows(question,'number');
  if(!parsed)parsed=parseSequentialRows(question,'roman');
  if(!parsed)return null;
  const instruction=(parsed.intro+' '+parsed.instruction).toLowerCase();
  return /\b(?:which|select|choose|how many|arrange|order|consider|code|correct|matched)\b/.test(instruction)?parsed:null;
}
function parseLetteredStem(question,options){
  const parsed=parseSequentialRows(question,'letter');if(!parsed)return null;
  const values=Object.values(options||{}).map(String);
  const combos=values.filter(value=>/\b(?:only|correct|incorrect)\b|\b[A-D]\s*(?:,|&|and)\s*[A-D]\b/i.test(value)).length;
  return combos>=2?parsed:null;
}

function getQuestionType(q){
  const text=String(q&&q.question||q&&q.q||''),source=String(q&&(q.type||q.question_type)||'');
  const sourceLower=source.toLowerCase().replace(/[_-]+/g,' ');
  // Prefer a meaningful source taxonomy when present, while still inspecting
  // the stem because imported books often do not provide type metadata.
  if(parseMatchQuestion(text,q&&q.options)||/\bmatch\b|two list matching/.test(sourceLower))return'Match Lists';
  if(parseAssertionReason(text)||/assertion.*reason|\ba\s*\/\s*r\b/.test(sourceLower))return'Assertion–Reason';
  if(questionAssetList(q).length||Object.values(q&&q.options||{}).some(value=>/^\[\s*(?:diagram|figure|image|formula)\b/i.test(String(value)))||/visual reasoning|diagram|figure|graph|formula/.test(sourceLower))return'Figure / Formula';
  if(/list and code|lettered (?:list|stem|statements?)/.test(sourceLower))return'Lettered List';
  if(/numbered statements?|multiple statements?|correct statement/.test(sourceLower))return'Numbered Statements';
  if(/negative|exception|incorrect statement/.test(sourceLower))return'Exception';
  if(/chronological|order|sequence|arrangement|ranking|spatial/.test(sourceLower))return'Order / Sequence';
  if(/data interpretation/.test(sourceLower))return'Data Interpretation';
  if(/numerical|calculation/.test(sourceLower))return'Calculation';
  if(/reasoning/.test(sourceLower))return'Reasoning';
  if(/fill in the blank/.test(sourceLower))return'Fill in the Blank';
  if(/pair evaluation/.test(sourceLower))return'Pairs';
  if(/statement and conclusion|logical inference/.test(sourceLower))return'Statement / Logic';
  if(parseLetteredStem(text,q&&q.options))return'Lettered List';
  if(parseNumberedStatements(text))return'Numbered Statements';
  if(questionCorrectKeys(q).length>1)return'Multiple Correct';
  if(/\b(?:not|incorrect|except)\b/i.test(text))return'Exception';
  if(source&&!/standard mcq|direct factual|single correct/.test(sourceLower))return source.split(/\s*[—–-]\s*/)[0].trim()||'Direct MCQ';
  return'Direct MCQ';
}

function renderRowStem(parsed,kind,baseClass){
  const listClass=kind==='number'?'statement-list':'lettered-list',rowClass=kind==='number'?'statement-row':'lettered-row',labelClass=kind==='number'?'statement-label':'lettered-label',textClass=kind==='number'?'statement-text':'lettered-text';
  return `<div class="${baseClass} structured-stem ${kind==='number'?'numbered-stem':'lettered-stem'}">${parsed.intro?`<div class="structured-intro">${bookText(parsed.intro)}</div>`:''}<div class="${listClass}">${parsed.rows.map(row=>`<div class="${rowClass}"><span class="${labelClass}">${escapeHtml(row.label)}.</span><span class="${textClass}">${bookText(row.text)}</span></div>`).join('')}</div>${parsed.instruction?`<div class="structured-instruction">${bookText(parsed.instruction)}</div>`:''}</div>`;
}
function renderQuestionStem(q,context){
  const baseClass=context==='review'?'rev-q':context==='bank'?'bank-q':'q-text';
  const match=parseMatchQuestion(q&&q.question,q&&q.options);
  let stemHtml;
  if(match)stemHtml=renderMatchQuestion(match);
  else{
    const assertion=parseAssertionReason(q&&q.question);
    const numbered=!assertion&&parseNumberedStatements(q&&q.question);
    const lettered=!assertion&&!numbered&&parseLetteredStem(q&&q.question,q&&q.options);
    if(assertion){
      stemHtml=`<div class="${baseClass} structured-stem assertion-reason-stem">${assertion.intro?`<div class="structured-intro">${bookText(assertion.intro)}</div>`:''}<div class="assertion-reason-grid"><div class="ar-card assertion-card"><span class="ar-label">Assertion (A)</span><div class="ar-text">${bookText(assertion.assertion)}</div></div><div class="ar-card reason-card"><span class="ar-label">Reason (R)</span><div class="ar-text">${bookText(assertion.reason)}</div></div></div>${assertion.instruction?`<div class="structured-instruction">${bookText(assertion.instruction)}</div>`:''}</div>`;
    }else if(numbered)stemHtml=renderRowStem(numbered,'number',baseClass);
    else if(lettered)stemHtml=renderRowStem(lettered,'letter',baseClass);
    else stemHtml=`<div class="${baseClass}">${bookText(q&&q.question||'')}</div>`;
  }
  return{html:stemHtml+renderQuestionAsset(q),matchData:match,type:getQuestionType(q)};
}

function parseMatchCode(value,labels){
  const raw=String(value||'').replace(/[–—]/g,'-').trim();
  const pairMap={};
  const symbol='(?:[A-E]|[0-9]+|IX|IV|V?I{1,3}|X)';
  const pairRe=new RegExp('\\b('+symbol+')\\s*-\\s*\\(?('+symbol+')\\)?','gi');
  let pair;
  while((pair=pairRe.exec(raw))!==null)pairMap[pair[1].toUpperCase()]=pair[2];
  if(labels.every(label=>pairMap[label.toUpperCase()]))return labels.map(label=>pairMap[label.toUpperCase()]);
  const tokens=raw.match(/\b(?:[A-E]|[0-9]+|ix|iv|v?i{1,3}|x)\b/gi)||[];
  return tokens.length>=labels.length?tokens.slice(-labels.length):null;
}

function splitMarkedItems(block,kind){
  const re=kind==='letter'?/(\([A-Ea-e]\)|[A-Ea-e][.)])/g:kind==='roman'?/(\((?:VI|IV|III|II|I|V)\)|(?:VI|IV|III|II|I|V)[.)])/g:/(\(\d{1,2}\)|\d{1,2}[.)])/g;
  const found=[];let m,last=null;
  while((m=re.exec(block))!==null){
    if(last)found.push({end:m.index,marker:last});
    last={start:re.lastIndex,raw:m[1]};
  }
  if(last)found.push({end:block.length,marker:last});
  return found.map(f=>{
    const label=f.marker.raw.replace(/[().]/g,'').toUpperCase();
    const text=block.slice(f.marker.start,f.end).replace(/[\s;,:]+$/,'').trim();
    return{label,text};
  }).filter(it=>it.text);
}

function parseSequentialMatchRows(text){
  // Many BPSC stems place List-I and List-II as two back-to-back lists
  // (lettered/Roman on the left, numbered on the right) instead of interleaved
  // pairs. Pair them by position so they render as a clean two-column table.
  // The instruction sentence also says "List I ... List II", so use the LAST
  // occurrences — those are the actual list headings.
  const leftAll=[...text.matchAll(/list\s*[-–—]?\s*(?:i|1)\b/gi)];
  const rightAll=[...text.matchAll(/list\s*[-–—]?\s*(?:ii|2)\b/gi)];
  if(!leftAll.length||!rightAll.length)return null;
  const leftIdx=leftAll[leftAll.length-1];
  const rightIdx=rightAll[rightAll.length-1];
  if(rightIdx.index<=leftIdx.index)return null;
  const leftBlock=text.slice(leftIdx.index+leftIdx[0].length,rightIdx.index);
  let rightBlock=text.slice(rightIdx.index+rightIdx[0].length);
  rightBlock=rightBlock.replace(/\s+(?:select|choose|give)\b[\s\S]*$/i,'').replace(/\s+codes?\s*:?[\s\S]*$/i,'').trim();
  const leftLetter=splitMarkedItems(leftBlock,'letter');
  const leftRoman=splitMarkedItems(leftBlock,'roman');
  const left=leftLetter.length>=leftRoman.length?leftLetter:leftRoman;
  const rightNumber=splitMarkedItems(rightBlock,'number');
  const rightLetter=splitMarkedItems(rightBlock,'letter');
  const right=rightNumber.length>=rightLetter.length?rightNumber:rightLetter;
  if(left.length<3||right.length<3||left.length!==right.length)return null;
  return left.map((item,i)=>({leftLabel:item.label,leftText:item.text,rightLabel:right[i].label,rightText:right[i].text}));
}

function parseMatchQuestion(question,options){
  const text=String(question||'').replace(/\s+/g,' ').trim();
  if(!/(?:\bmatch\b|correctly\s+match)/i.test(text))return null;
  if(!/(?:list\s*[-–—]?\s*(?:i|1)\b|match\s+the\s+following)/i.test(text))return null;

  // Prefer the final adjacent "List I/List 1  List II/List 2" heading.
  // Earlier occurrences are normally part of the instruction sentence.
  const pairRe=/list\s*[-–—]?\s*(?:i|1)\s*(?:[:\-–—]*)\s*list\s*[-–—]?\s*(?:ii|2)\b/gi;
  let heading=null,m;
  while((m=pairRe.exec(text))!==null)heading={index:m.index,end:pairRe.lastIndex};

  let prompt='',content=text;
  if(heading){prompt=text.slice(0,heading.index).trim();content=text.slice(heading.end).trim();}

  // The books chiefly use A-D opposite 1-4, but some tables use I-IV
  // opposite A-D. Select the scheme whose first row marker occurs first.
  const alphaLeftRe=/(?:^|\s)(?:\(([A-Ea-e])\)|([A-Ea-e])[.)])\s*/g;
  const romanLeftRe=/(?:^|\s)(?:\((IV|III|II|I|V)\)|(IV|III|II|I|V)[.)])\s*/gi;
  const alphaFirst=alphaLeftRe.exec(content),romanFirst=romanLeftRe.exec(content);
  let scheme='',firstLeft=null,leftRe=null;
  if(alphaFirst&&(!romanFirst||alphaFirst.index<romanFirst.index)){scheme='alpha';firstLeft=alphaFirst;leftRe=alphaLeftRe;}
  else if(romanFirst){scheme='roman';firstLeft=romanFirst;leftRe=romanLeftRe;}
  if(!firstLeft)return null;

  let preamble=content.slice(0,firstLeft.index).trim();
  if(!heading){
    const prefix=preamble;
    const titleMatches=[...prefix.matchAll(/\(([^)]+)\)/g)];
    if(titleMatches.length>=2){
      const titleStart=titleMatches[titleMatches.length-2].index;
      prompt=prefix.slice(0,titleStart).trim();
      preamble=prefix.slice(titleStart).trim();
    }else{
      const stop=Math.max(prefix.lastIndexOf('.'),prefix.lastIndexOf(':'));
      if(stop>=0){prompt=prefix.slice(0,stop+1).trim();preamble=prefix.slice(stop+1).trim();}
      else{prompt=prefix||'Match the following:';preamble='';}
    }
    content=content.slice(firstLeft.index).trim();
  }

  leftRe.lastIndex=0;
  const first=leftRe.exec(content);
  if(!first)return null;
  if(heading)preamble=content.slice(0,first.index).trim();
  let body=content.slice(first.index).trim();

  // Remove answer-code instructions and repeated column labels after the list.
  body=body.replace(/\s+(?:select|choose|give)\b[\s\S]*$/i,'');
  body=body.replace(/\s+codes?\s*:[\s\S]*$/i,'');
  body=body.replace(/\s+[A-E](?:\s+[A-E]){2,4}\s*$/i,'');
  body=body.replace(/\s+(?:IV|III|II|I|V)(?:\s+(?:IV|III|II|I|V)){2,4}\s*$/i,'').trim();

  let leftTitle='',rightTitle='';
  const titleGroups=[...preamble.matchAll(/\(([^)]+)\)/g)].map(x=>x[1].trim()).filter(Boolean);
  if(titleGroups.length>=2)[leftTitle,rightTitle]=titleGroups.slice(-2);
  if(!leftTitle||!rightTitle){
    const titled=text.match(/list\s*[-–—]?\s*(?:i|1)\s*\(([^)]+)\)[\s\S]*?list\s*[-–—]?\s*(?:ii|2)\s*\(([^)]+)\)/i);
    if(titled){leftTitle=leftTitle||titled[1].trim();rightTitle=rightTitle||titled[2].trim();}
  }
  if(!leftTitle&&!rightTitle){
    const bareTitles=preamble.match(/^([\w&/-]+)\s+([\w&/-]+)$/);
    if(bareTitles){leftTitle=bareTitles[1];rightTitle=bareTitles[2];}
  }

  let rows=[];
  let row;
  if(scheme==='alpha'){
    const rowRe=/(?:^|\s)(?:\(([A-Ea-e])\)|([A-Ea-e])[.)])\s*(.*?)(?:\s+[-–—]\s*)?(?:\(([0-9]+|[ivx]+)\)|([0-9]+|[ivx]+)[.)])\s*(.*?)(?=(?:\s+)(?:\([A-Ea-e]\)|[A-Ea-e][.)])\s*|$)/gi;
    while((row=rowRe.exec(body))!==null){
      const leftLabel=(row[1]||row[2]||'').toUpperCase();
      const rightLabel=(row[4]||row[5]||'').toUpperCase();
      const leftText=row[3].replace(/^[-–—\s]+|[-–—\s]+$/g,'').trim();
      const rightText=row[6].replace(/^[-–—\s]+|[-–—\s]+$/g,'').trim();
      if(leftLabel&&rightLabel&&leftText&&rightText)rows.push({leftLabel,leftText,rightLabel,rightText});
    }
  }else{
    const rowRe=/(?:^|\s)(?:\((IV|III|II|I|V)\)|(IV|III|II|I|V)[.)])\s*(.*?)\s+(?:\(([A-Ea-e])\)|([A-Ea-e])[.)])\s*(.*?)(?=(?:\s+)(?:\((?:IV|III|II|I|V)\)|(?:IV|III|II|I|V)[.)])\s*|$)/gi;
    while((row=rowRe.exec(body))!==null){
      const leftLabel=(row[1]||row[2]||'').toUpperCase();
      const rightLabel=(row[4]||row[5]||'').toUpperCase();
      const leftText=row[3].replace(/^[-–—\s]+|[-–—\s]+$/g,'').trim();
      const rightText=row[6].replace(/^[-–—\s]+|[-–—\s]+$/g,'').trim();
      if(leftLabel&&rightLabel&&leftText&&rightText)rows.push({leftLabel,leftText,rightLabel,rightText});
    }
  }
  if(rows.length<3){
    const seq=parseSequentialMatchRows(text);
    if(seq&&seq.length>=3)rows=seq;
  }
  if(rows.length<3)return null;
  // Drop a trailing "List-I (...):" that leaked into the prompt so the rendered
  // intro doesn't duplicate the column header.
  prompt=String(prompt||'').replace(/[\s;:]*list\s*[-–—]?\s*(?:i|1)\b\s*(?:\([^)]*\))?\s*:?\s*$/i,'').replace(/[\s:;]+$/,'').trim()||'Match the following:';

  const labels=rows.map(r=>r.leftLabel);
  const codeRows=Object.entries(options||{}).map(([key,value])=>({key,value:String(value),codes:parseMatchCode(value,labels)}));
  if(codeRows.filter(r=>r.codes).length<2)return null;
  return{prompt:prompt||'Match the following:',leftTitle,rightTitle,rows,labels,codeRows};
}

function renderMatchQuestion(match){
  const heads=`<div class="match-list-heads"><div class="match-list-head">List - I${match.leftTitle?`<span class="match-list-title">(${bookText(match.leftTitle)})</span>`:''}</div><div class="match-list-head">List - II${match.rightTitle?`<span class="match-list-title">(${bookText(match.rightTitle)})</span>`:''}</div></div>`;
  const rows=match.rows.map(row=>`<div class="match-list-row"><div class="match-cell"><span class="match-cell-label">${escapeHtml(row.leftLabel)}.</span><span class="match-cell-text">${bookText(row.leftText)}</span></div><div class="match-cell"><span class="match-cell-label">${escapeHtml(row.rightLabel)}.</span><span class="match-cell-text">${bookText(row.rightText)}</span></div></div>`).join('');
  return `<div class="match-paper"><div class="match-prompt">${bookText(match.prompt)}</div>${heads}<div class="match-list-rows">${rows}</div></div>`;
}

function renderMatchOptions(match,optionKeys,answered){
  const labels=match.labels;
  const header=`<div class="match-code-header" style="--match-cols:${labels.length}"><span></span>${labels.map(label=>`<span>${escapeHtml(label)}</span>`).join('')}</div>`;
  const rows=optionKeys.map(key=>{
    const item=match.codeRows.find(row=>row.key===key);
    if(!item){const val=q.options[key];if(val==null||val==='')return'';return `<button class="opt-btn" onclick="selectOption('${escapeHtml(key)}')" aria-label="Option ${escapeHtml(key)}: ${escapeHtml(optionDisplayText(val,key))}"><span class="opt-text">${escapeHtml(optionDisplayText(val,key))}</span></button>`;}
    const cls='opt-btn match-code-row'+(answerHasKey(answered,key)?' selected':'');
    const cells=item.codes?item.codes.map(code=>`<span class="match-code-value">${escapeHtml(code)}</span>`).join(''):`<span class="match-code-free">${bookText(item.value)}</span>`;
    return `<button class="${cls}" style="--match-cols:${labels.length}" onclick="selectOption('${escapeHtml(key)}')" aria-label="Option ${escapeHtml(key)}: ${bookText(item.value)}"><span class="match-option-key">(${escapeHtml(key.toLowerCase())})</span>${cells}</button>`;
  }).join('');
  return header+rows;
}

function renderMatchReviewOptions(match,optionKeys,correctKey,userKey,isCorrect){
  const labels=match.labels;
  const header=`<div class="match-code-header" style="--match-cols:${labels.length}"><span></span>${labels.map(label=>`<span>${escapeHtml(label)}</span>`).join('')}</div>`;
  const rows=optionKeys.map(key=>{
    const item=match.codeRows.find(row=>row.key===key);if(!item)return'';
    let cls='match-code-row match-review-code-row';
    if(answerHasKey(correctKey,key))cls+=' correct-ans';else if(answerHasKey(userKey,key)&&!isCorrect)cls+=' user-wrong';
    const cells=item.codes?item.codes.map(code=>`<span class="match-code-value">${escapeHtml(code)}</span>`).join(''):`<span class="match-code-free">${bookText(item.value)}</span>`;
    return `<div class="${cls}" style="--match-cols:${labels.length}"><span class="match-option-key">(${escapeHtml(key.toLowerCase())})</span>${cells}</div>`;
  }).join('');
  return header+rows;
}

