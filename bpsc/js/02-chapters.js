/* topic map, subject + chapter selection, question-range controls
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
function buildSubjectsGrid(){
  const grid=document.getElementById('subjects-grid');grid.innerHTML='';
  SUBJECTS_CONFIG.forEach(subj=>{
    const card=document.createElement('div');card.className='subject-card';card.id='sc-'+subj.id;
    card.innerHTML=`<div class="sc-top" onclick="toggleSubjectCard('${subj.id}')">
      <div class="sc-icon-wrap">${subj.icon}</div>
      <div class="sc-info">
        <div class="sc-name">${subj.name}</div>
        <div class="sc-meta-row">
          <span class="sc-pill" id="sc-pill-ch-${subj.id}">-- chapters</span>
          <span class="sc-pill" id="sc-pill-q-${subj.id}">-- Qs</span>
        </div>
      </div>
      <div class="sc-arrow" id="sc-arrow-${subj.id}">&#x25BE;</div>
    </div>
    <div class="sc-chapters" id="sc-chs-${subj.id}">
      <div class="sc-ch-header">
        <span class="sc-ch-header-lbl">Select Chapters</span>
        <button class="sc-ch-selall" onclick="selectAllChapters('${subj.id}',event)">Select All</button>
        <button class="sc-ch-selall" style="color:var(--text3);margin-left:8px;" onclick="deselectAllChapters('${subj.id}',event)">Clear</button>
      </div>
      <div id="sc-chlist-${subj.id}"><div style="padding:20px;text-align:center;font-size:0.75rem;color:var(--text3);">Loading...</div></div>
    </div>
    <div class="sc-action-row">
      <button class="sc-start-mini" onclick="startFromCard('${subj.id}',event)">Start Quiz &#x2192;</button>
    </div>`;
    grid.appendChild(card);
  });
}

async function toggleSubjectCard(subjId){
  const card=document.getElementById('sc-'+subjId);
  const isExpanded=card.classList.contains('expanded');
  document.querySelectorAll('.subject-card.expanded').forEach(c=>c.classList.remove('expanded'));
  hideConfigPanel();
  if(isExpanded){currentSubjectId=null;selectedChapters.clear();return;}
  card.classList.add('expanded');currentSubjectId=subjId;selectedChapters.clear();
  if(!subjectDataCache[subjId]){
    document.getElementById('sc-chlist-'+subjId).innerHTML='<div style="padding:20px;text-align:center;font-size:0.75rem;color:var(--text3);">&#x23F3; Loading...</div>';
    try{const subj=SUBJECTS_CONFIG.find(s=>s.id===subjId);subjectDataCache[subjId]=await fetchBookData(subj);}
    catch(err){console.error('Subject data load failed ('+subjId+'):',err);const box=document.getElementById('sc-chlist-'+subjId);if(box)box.innerHTML=dataLoadErrorHtml(err);return;}
  }
  processData(subjectDataCache[subjId],subjId);renderChapterList(subjId);updateHeroCounts();
  setTimeout(()=>{card.scrollIntoView({behavior:'smooth',block:'nearest'});},100);
}

const TOPIC_EMOJI={"Census & Population":"📊","Forests & Wildlife":"🦌","Schemes & Policies":"📜","Agriculture & Irrigation":"🌾","Transport":"🚉","Minerals":"⛏️","Rivers, Lakes & Waterfalls":"🌊","Art, Culture & Language":"🎭","Books, Authors & Press":"📚","Polity & Elections":"🏛️","Economy & Industry":"🏭","Modern Bihar & Freedom Struggle":"🇮🇳","Medieval Bihar":"🕌","Ancient Bihar":"🏺","Physical Geography":"⛰️","Current Affairs (Bihar)":"📰","General":"🔹","Environment & Conservation":"🌿","Oceans & Currents":"🌊","Rivers & Lakes":"💧","Climate":"🌦️","Minerals & Resources":"⛏️","Population & Settlement":"🏙️","Agriculture & Economy":"🚜","Physical Landforms":"⛰️","Continents & Regions":"🗺️","Sports":"🏏","Awards & Honours":"🏅","Appointments & Persons in News":"👤","Obituaries":"🕯️","Summits, Conferences & Meetings":"🤝","Defence & Security":"🛡️","Space & Nuclear":"🚀","Science & Technology":"🔬","Economy, Banking & Finance":"💰","Reports, Indices & Data":"📈","Agreements & Appointments (Intl)":"🤝","Environment & Health":"🩺","States & Governance":"🏘️","Books, Days & Misc":"📖","Environment & Wildlife":"🐅","Rivers & Drainage":"🏞️","Climate & Monsoon":"🌧️","Soils & Natural Vegetation":"🌳","Agriculture":"🌾","Minerals & Energy":"⚡","Industry":"🏭","Transport & Communication":"🚛","Population, Census & Settlement":"📊","States, Boundaries & Regions":"🇮🇳","Physical Features & Landforms":"🏔️","International Institutions & Trade Bodies":"🌐","Banking & Finance":"🏦","Budget & Taxation":"🧾","External Sector & Trade":"🚢","Money & Capital Markets":"💱","Agriculture & Rural Economy":"🌾","Industry & Infrastructure":"🏗️","Poverty & Employment":"👥","Growth & National Income":"📈","Art & Architecture":"🛕","Literature":"📜","Buddhism & Jainism":"☸️","Science & Math":"🔢","Indus Valley":"🏺","Vedic Age":"🐄","Mauryan Empire":"🦁","Invasions (Persian & Greek)":"🏹","Post-Mauryan Period":"🏛️","Gupta & Post-Gupta":"👑","South India":"🌴","Mahajanapadas & Magadh":"⚔️","Prehistoric & Stone Age":"🪨","Philosophy & Religion":"🪔","Bhakti & Sufi Movements":"🕌","Art, Culture & Literature":"🎨","Marathas & Sikhs":"⚔️","Vijayanagar & Regional Kingdoms":"🏰","Delhi Sultanate":"👑","Mughal Empire":"🕌","Arrival of Turks & Early Sultanate":"🏇","Administration, Economy & Society":"⚖️","Space & Defence Technology":"🚀","IT, Electronics & New Tech":"💻","Nuclear & Energy Technology":"⚛️","Biotechnology":"🧬","Cell & Biomolecules":"🔬","Genetics & Heredity":"🧪","Human Physiology":"🫀","Plant Biology":"🌱","Diseases & Health":"🦠","Nutrition & Vitamins":"🥗","Ecology & Environment":"🌍","Evolution & Taxonomy":"🐒","Microbiology":"🧫","Revolt of 1857":"⚔️","Socio-Religious Reform":"🕉️","Press, Education & Literature":"📰","Peasant, Tribal & Civil Rebellions":"🔥","European Companies & Conquest":"⛵","Economic Policies & Exploitation":"💸","Governors-General & Administration":"🎩","Early Political Associations":"🏛️","Personalities & Miscellaneous":"👤","Partition & Independence":"🇮🇳","Constitutional Reforms (1892–1935)":"📜","Gandhi & Mass Movements":"🕊️","Revolutionary Nationalism":"💣","Congress & National Movement Phases":"🚩","Peasant, Worker & Tribal Movements":"👥","Princely States & Integration":"🏰","Post-Independence India":"🇮🇳","Personalities & Books":"📖","Bihar & the National Movement":"🌟","Optics":"👁️","Electricity & Magnetism":"⚡","Modern & Nuclear Physics":"⚛️","Sound & Waves":"🔊","Heat & Thermodynamics":"🌡️","Motion, Forces & Mechanics":"⚽","Units, Measurement & Instruments":"📏","Everyday Physics & Scientists":"👨‍🔬","Atomic Structure & Periodic Table":"🧪","Chemical Bonding & Reactions":"🔗","Metals, Non-Metals & Metallurgy":"🪙","Organic & Everyday Chemistry":"🧫","States of Matter & Gas Laws":"🫧","Solutions & Electrochemistry":"🔋","Constitution & Preamble":"📖","Fundamental Rights, Duties & DPSP":"⚖️","Union Executive":"🏛️","Parliament":"🏛️","Judiciary":"⚖️","State Government":"🏢","Local Government":"🏘️","Elections & Representation":"🗳️","Constitutional & Statutory Bodies":"🏛️","Amendments & Special Provisions":"📜","Centre-State & Misc Provisions":"🤝","Planning & Economic Reforms":"📋","Economic Concepts & Public Finance":"💹"};
function topicPillHtml(q){
  const t=(q&& (q.topic||q.sub_topic))||'';
  if(!t)return '';
  return `<span class="subtopic-pill question-topic-pill" title="Topic: ${escapeHtml(t)}">${TOPIC_EMOJI[t]||'📌'} ${escapeHtml(t)}</span>`;
}
function practiceTopic(subjId,encTopic){
  const topic=decodeURIComponent(encTopic);
  const pool=allQuestions.filter(q=>q.topic===topic||q.sub_topic===topic);
  if(!pool.length){alert('No questions found for this topic.');return;}
  currentSubjectId=subjId;
  selectedChapters=new Set([pool[0].chapter?pool[0].chapter+' · '+topic:topic]);
  topicQuizName=topic;
  startQuiz('topic',pool);
}

function renderChapterList(subjId){
  const chList=document.getElementById('sc-chlist-'+subjId);if(!chList)return;
  const chs=Object.keys(chapterMap);
  document.getElementById('sc-pill-ch-'+subjId).textContent=chs.length+' chapters';
  document.getElementById('sc-pill-q-'+subjId).textContent=allQuestions.length+' Qs';
  let html='';
  chs.forEach(name=>{
    const qs=chapterMap[name]||[];const enc=encodeURIComponent(name);
    const subtopics=Array.from(chapterSubtopicsMap[name]||[]);
    const isSel=selectedChapters.has(name);
    html+=`<div class="ch-row-wrap" id="chwrap-${subjId}-${enc}">
      <div class="ch-row ${isSel?'selected':''}" id="chrow-${subjId}-${enc}" onclick="toggleChapterCard('${subjId}','${enc}')">
        <div class="ch-check" id="chck-${subjId}-${enc}">${isSel?'\u2713':''}</div>
        <span class="ch-name">${chapterIconMap[name]?chapterIconMap[name]+' ':''}${escapeHtml(name)}</span>
        ${subtopics.length>0?`<span class="ch-sub-badge" title="${subtopics.length} sub-topics" onclick="toggleChapterSubtopics('${subjId}','${enc}',event)">${subtopics.length} sub-topics &#x25BE;</span>`:''}
        <span class="ch-count">${qs.length}</span>
      </div>
      ${subtopics.length>0?`
        <div class="ch-subtopics-list" id="chsubs-${subjId}-${enc}" style="display:none;">
          ${subtopics.map(st=>{
            const stEnc=encodeURIComponent(st);
            const count=qs.filter(q=>q.sub_topic===st).length;
            const stSel=selectedSubtopics.has(st);
            return `<div class="ch-subtopic-row ${stSel?'selected':''}" id="chsubrow-${subjId}-${stEnc}" onclick="toggleSubtopicCard('${subjId}','${enc}','${stEnc}',event)">
              <div class="ch-sub-check" id="chsubck-${subjId}-${stEnc}">${stSel?'\u2713':''}</div>
              <span class="ch-sub-name">${escapeHtml(st)}</span>
              <span class="ch-sub-count">${count}</span>
            </div>`;
          }).join('')}
        </div>`:''}
    </div>`;
  });
  const topicCounts=new Map();
  allQuestions.forEach(q=>{const t=q.topic||q.sub_topic;if(t)topicCounts.set(t,(topicCounts.get(t)||0)+1);});
  if(chs.length<=2&&topicCounts.size>1){
    html+=`<div class="topic-section">&#127991;&#65039; Topics &#183; tap to practice</div><div class="topic-rows">`;
    [...topicCounts.entries()].sort((a,b)=>b[1]-a[1]).forEach(([topic,n])=>{
      html+=`<button type="button" class="topic-chip" onclick="event.stopPropagation();practiceTopic('${subjId}','${encodeURIComponent(topic)}')">${TOPIC_EMOJI[topic]||'&#128302;'} ${escapeHtml(topic)} <span class="topic-count">${n}</span></button>`;
    });
    html+=`</div>`;
  }
  chList.innerHTML=html;
}

function toggleChapterSubtopics(subjId,enc,e){
  e?.stopPropagation();
  const drawer=document.getElementById('chsubs-'+subjId+'-'+enc);
  if(!drawer)return;
  drawer.style.display=drawer.style.display==='none'?'flex':'none';
}

function toggleSubtopicCard(subjId,chEnc,stEnc,e){
  e?.stopPropagation();
  const chName=decodeURIComponent(chEnc);
  const stName=decodeURIComponent(stEnc);
  const row=document.getElementById('chsubrow-'+subjId+'-'+stEnc);
  const chk=document.getElementById('chsubck-'+subjId+'-'+stEnc);
  if(selectedSubtopics.has(stName)){
    selectedSubtopics.delete(stName);
    row?.classList.remove('selected');
    if(chk)chk.textContent='';
  }else{
    selectedSubtopics.add(stName);
    row?.classList.add('selected');
    if(chk)chk.textContent='\u2713';
    if(!selectedChapters.has(chName)){
      selectedChapters.add(chName);
      document.getElementById('chrow-'+subjId+'-'+chEnc)?.classList.add('selected');
      const parentChk=document.getElementById('chck-'+subjId+'-'+chEnc);
      if(parentChk)parentChk.textContent='\u2713';
    }
  }
  updateConfigPanel(subjId);
}

function toggleConfigSubtopic(subjId,stEnc){
  const stName=decodeURIComponent(stEnc);
  if(selectedSubtopics.has(stName)){
    selectedSubtopics.delete(stName);
  }else{
    selectedSubtopics.add(stName);
  }
  updateConfigPanel(subjId);
}

function clearConfigSubtopics(subjId){
  selectedSubtopics.clear();
  document.querySelectorAll('.ch-subtopic-row.selected').forEach(el=>el.classList.remove('selected'));
  document.querySelectorAll('.ch-sub-check').forEach(el=>el.textContent='');
  updateConfigPanel(subjId);
}

function toggleChapterCard(subjId,enc){
  const name=decodeURIComponent(enc);const row=document.getElementById('chrow-'+subjId+'-'+enc);const chk=document.getElementById('chck-'+subjId+'-'+enc);
  if(selectedChapters.has(name)){
    selectedChapters.delete(name);row?.classList.remove('selected');if(chk)chk.textContent='';
    // Remove selected subtopics of this chapter
    const chSubs=Array.from(chapterSubtopicsMap[name]||[]);
    chSubs.forEach(st=>selectedSubtopics.delete(st));
    const drawer=document.getElementById('chsubs-'+subjId+'-'+enc);
    if(drawer){drawer.querySelectorAll('.ch-subtopic-row.selected').forEach(el=>el.classList.remove('selected'));drawer.querySelectorAll('.ch-sub-check').forEach(el=>el.textContent='');}
  }else{
    selectedChapters.add(name);row?.classList.add('selected');if(chk)chk.textContent='\u2713';
  }
  updateConfigPanel(subjId);
}

function selectAllChapters(subjId,e){
  e?.stopPropagation();selectedChapters.clear();selectedSubtopics.clear();
  Object.keys(chapterMap).forEach(name=>{selectedChapters.add(name);const enc=encodeURIComponent(name);document.getElementById('chrow-'+subjId+'-'+enc)?.classList.add('selected');const chk=document.getElementById('chck-'+subjId+'-'+enc);if(chk)chk.textContent='\u2713';});
  document.querySelectorAll('.ch-subtopic-row.selected').forEach(el=>el.classList.remove('selected'));
  document.querySelectorAll('.ch-sub-check').forEach(el=>el.textContent='');
  updateConfigPanel(subjId);
}

function deselectAllChapters(subjId,e){
  e?.stopPropagation();
  Object.keys(chapterMap).forEach(name=>{const enc=encodeURIComponent(name);document.getElementById('chrow-'+subjId+'-'+enc)?.classList.remove('selected');const chk=document.getElementById('chck-'+subjId+'-'+enc);if(chk)chk.textContent='';});
  selectedChapters.clear();selectedSubtopics.clear();
  document.querySelectorAll('.ch-subtopic-row.selected').forEach(el=>el.classList.remove('selected'));
  document.querySelectorAll('.ch-sub-check').forEach(el=>el.textContent='');
  hideConfigPanel();
}

function buildRangePresetsHtml(totalCount){
  if(totalCount<=20) return '';
  const chunkSize = totalCount <= 100 ? 25 : totalCount <= 300 ? 50 : 100;
  const presets = [];
  for(let start = 1; start <= totalCount; start += chunkSize){
    const end = Math.min(start + chunkSize - 1, totalCount);
    presets.push({start, end});
  }
  return presets.map(p=>`<button type="button" class="cp-preset-pill" id="cp-preset-${p.start}-${p.end}" data-start="${p.start}" data-end="${p.end}" onclick="setQuestionRange(${p.start},${p.end},${totalCount})">Q${p.start}–${p.end}</button>`).join('');
}

function updatePresetPillHighlights(fromVal, toVal, totalCount){
  document.querySelectorAll('.cp-preset-pill').forEach(btn=>{
    const pStart = parseInt(btn.getAttribute('data-start') || btn.id.replace('cp-preset-','').split('-')[0], 10);
    const pEnd = parseInt(btn.getAttribute('data-end') || btn.id.replace('cp-preset-','').split('-')[1], 10);
    if(pStart === fromVal && pEnd === toVal){
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

function setQuestionRange(fromVal, toVal, totalCount){
  const qFrom = document.getElementById('q-from');
  const qTo = document.getElementById('q-to');
  const qRangeText = document.getElementById('q-range-text');
  const numQuestions = document.getElementById('num-questions');
  const qInfo = document.getElementById('q-range-info');

  if(qFrom) qFrom.value = fromVal;
  if(qTo) qTo.value = toVal;
  if(qRangeText) qRangeText.value = `${fromVal}-${toVal}`;

  const count = Math.max(1, toVal - fromVal + 1);
  if(numQuestions) numQuestions.value = count;

  if(qInfo){
    if(fromVal === 1 && toVal === totalCount){
      qInfo.textContent = `Selecting all ${totalCount} Qs (Q#1 to Q#${totalCount})`;
    } else {
      qInfo.textContent = `Selecting ${count} Qs (Q#${fromVal} to Q#${toVal} of ${totalCount})`;
    }
  }
  updatePresetPillHighlights(fromVal, toVal, totalCount);
}

function onQuestionRangeChange(totalCount){
  const qFrom = document.getElementById('q-from');
  const qTo = document.getElementById('q-to');
  const qRangeText = document.getElementById('q-range-text');
  const numQuestions = document.getElementById('num-questions');
  const qInfo = document.getElementById('q-range-info');

  let f = parseInt(qFrom?.value, 10);
  let t = parseInt(qTo?.value, 10);

  if(isNaN(f)) f = 1;
  if(isNaN(t)) t = totalCount;

  f = Math.max(1, Math.min(f, totalCount));
  t = Math.max(1, Math.min(t, totalCount));
  if(f > t) t = f;

  if(qRangeText) qRangeText.value = f === t ? `${f}` : `${f}-${t}`;
  const count = Math.max(1, t - f + 1);
  if(numQuestions) numQuestions.value = count;

  if(qInfo){
    if(f === 1 && t === totalCount){
      qInfo.textContent = `Selecting all ${totalCount} Qs (Q#1 to Q#${totalCount})`;
    } else {
      qInfo.textContent = `Selecting ${count} Qs (Q#${f} to Q#${t} of ${totalCount})`;
    }
  }
  updatePresetPillHighlights(f, t, totalCount);
}

function onQuestionRangeTextChange(totalCount){
  const qRangeText = document.getElementById('q-range-text');
  const val = qRangeText?.value || '';

  const match = val.match(/^\s*(\d+)\s*(?:[-:\u2013\u2014]|to)?\s*(\d+)?\s*$/i);
  if(match){
    let f = parseInt(match[1], 10) || 1;
    let t = match[2] ? parseInt(match[2], 10) : f;

    f = Math.max(1, Math.min(f, totalCount));
    t = Math.max(1, Math.min(t, totalCount));
    if(f > t) t = f;

    const qFrom = document.getElementById('q-from');
    const qTo = document.getElementById('q-to');
    const numQuestions = document.getElementById('num-questions');
    const qInfo = document.getElementById('q-range-info');

    if(qFrom) qFrom.value = f;
    if(qTo) qTo.value = t;

    const count = Math.max(1, t - f + 1);
    if(numQuestions) numQuestions.value = count;

    if(qInfo){
      if(f === 1 && t === totalCount){
        qInfo.textContent = `Selecting all ${totalCount} Qs (Q#1 to Q#${totalCount})`;
      } else {
        qInfo.textContent = `Selecting ${count} Qs (Q#${f} to Q#${t} of ${totalCount})`;
      }
    }
    updatePresetPillHighlights(f, t, totalCount);
  }
}

function onNumQuestionsChange(totalCount){
  const numQuestions = document.getElementById('num-questions');
  const qFrom = document.getElementById('q-from');
  const qTo = document.getElementById('q-to');
  const qRangeText = document.getElementById('q-range-text');
  const qInfo = document.getElementById('q-range-info');

  let count = parseInt(numQuestions?.value, 10);
  if(isNaN(count) || count < 1) count = totalCount;
  count = Math.max(1, Math.min(count, totalCount));

  let f = parseInt(qFrom?.value, 10) || 1;
  f = Math.max(1, Math.min(f, totalCount));
  let t = Math.min(totalCount, f + count - 1);

  if(qTo) qTo.value = t;
  if(qRangeText) qRangeText.value = `${f}-${t}`;

  if(qInfo){
    if(f === 1 && t === totalCount){
      qInfo.textContent = `Selecting all ${totalCount} Qs (Q#1 to Q#${totalCount})`;
    } else {
      qInfo.textContent = `Selecting ${count} Qs (Q#${f} to Q#${t} of ${totalCount})`;
    }
  }
  updatePresetPillHighlights(f, t, totalCount);
}

function resetQuestionRange(totalCount){
  setQuestionRange(1, totalCount, totalCount);
}

function getQuestionSelectionRange(totalCount){
  const qFrom = document.getElementById('q-from');
  const qTo = document.getElementById('q-to');
  const numQuestions = document.getElementById('num-questions');

  let f = parseInt(qFrom?.value, 10);
  let t = parseInt(qTo?.value, 10);
  let n = parseInt(numQuestions?.value, 10);

  if(!isNaN(n) && n > 0 && (!isNaN(t) && !isNaN(f) && n !== (t - f + 1))){
    if(isNaN(f) || f < 1) f = 1;
    t = Math.min(totalCount, f + n - 1);
  }

  if(isNaN(f) || f < 1) f = 1;
  if(isNaN(t) || t < 1) t = totalCount;

  f = Math.max(1, Math.min(f, totalCount));
  t = Math.max(1, Math.min(t, totalCount));

  if(f > t){
    const tmp = f;
    f = t;
    t = tmp;
  }

  return { from: f, to: t, count: t - f + 1 };
}

function updateConfigPanel(subjId){
  if(selectedChapters.size===0){hideConfigPanel();return;}
  const subj=SUBJECTS_CONFIG.find(s=>s.id===subjId);
  let pool=allQuestions.filter(q=>selectedChapters.has(q.chapter));
  const availableSubtopics=new Set();
  pool.forEach(q=>{if(q.sub_topic)availableSubtopics.add(q.sub_topic);});
  const subtopicList=Array.from(availableSubtopics).sort();

  if(selectedSubtopics.size>0){
    pool=pool.filter(q=>selectedSubtopics.has(q.sub_topic));
  }

  const chLabel=selectedChapters.size===Object.keys(chapterMap).length?'All Chapters':null;
  const cp=document.getElementById('config-panel');cp.style.display='';

  let subtopicsSectionHtml='';
  if(subtopicList.length>0){
    const allActive=selectedSubtopics.size===0;
    subtopicsSectionHtml=`<div class="cp-subtopics-section">
      <div class="cp-subtopics-header">
        <span class="cp-subtopics-title">Sub-topics (${subtopicList.length})</span>
        <button class="sc-ch-selall" style="font-size:0.6rem;" onclick="clearConfigSubtopics('${subjId}')">All sub-topics</button>
      </div>
      <div class="cp-subtopic-chips">
        <button class="cp-subtopic-chip ${allActive?'active':''}" onclick="clearConfigSubtopics('${subjId}')">All Sub-topics</button>
        ${subtopicList.map(st=>{
          const stEnc=encodeURIComponent(st);
          const count=allQuestions.filter(q=>selectedChapters.has(q.chapter)&&q.sub_topic===st).length;
          const active=selectedSubtopics.has(st);
          return `<button class="cp-subtopic-chip ${active?'active':''}" onclick="toggleConfigSubtopic('${subjId}','${stEnc}')"><span>${escapeHtml(st)}</span><span style="font-size:0.55rem;opacity:0.8;">(${count})</span></button>`;
        }).join('')}
      </div>
    </div>`;
  }

  cp.innerHTML=`<div class="cp-header"><span class="cp-subject-icon">${subj.icon}</span><div><div class="cp-subject-name">${subj.name}</div><div class="cp-ch-tags">${chLabel?'<span class="cp-ch-tag">\uD83D\uDCDA All Chapters</span>':Array.from(selectedChapters).map(ch=>`<span class="cp-ch-tag">${ch}</span>`).join('')}${selectedSubtopics.size?Array.from(selectedSubtopics).map(st=>`<span class="cp-ch-tag" style="background:var(--purple-dim);color:var(--purple);border-color:var(--purple);">&#x1F4CD; ${st}</span>`).join(''):''}</div></div></div>
  <div class="cp-body">
    <div class="cp-row" style="flex-direction:column;align-items:flex-start;gap:8px;width:100%;">
      <div style="display:flex;align-items:center;gap:8px;width:100%;flex-wrap:wrap;">
        <span class="cp-lbl">Questions</span>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
          <span style="font-size:0.75rem;color:var(--text2);font-weight:600;">From Q#</span>
          <input type="number" class="cp-input" id="q-from" value="1" min="1" max="${pool.length}" style="width:72px;padding:5px 8px;" oninput="onQuestionRangeChange(${pool.length})">
          <span style="font-size:0.75rem;color:var(--text2);font-weight:600;">To Q#</span>
          <input type="number" class="cp-input" id="q-to" value="${pool.length}" min="1" max="${pool.length}" style="width:72px;padding:5px 8px;" oninput="onQuestionRangeChange(${pool.length})">
          <span style="font-size:0.72rem;color:var(--text3);font-weight:500;">or Range:</span>
          <input type="text" class="cp-input" id="q-range-text" placeholder="e.g. 75-150" value="1-${pool.length}" style="width:105px;padding:5px 8px;" oninput="onQuestionRangeTextChange(${pool.length})">
          <input type="number" class="cp-input" id="num-questions" value="${pool.length}" min="1" max="${pool.length}" style="width:65px;display:none;" oninput="onNumQuestionsChange(${pool.length})">
          <button type="button" class="cp-preset-btn" onclick="resetQuestionRange(${pool.length})" style="font-size:0.68rem;background:var(--surface2);border:1px solid var(--border);color:var(--text3);padding:4px 9px;border-radius:6px;cursor:pointer;font-family:'DM Sans',sans-serif;">All (${pool.length})</button>
        </div>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;width:100%;flex-wrap:wrap;gap:8px;padding-left:82px;" class="cp-range-meta-wrap">
        <div id="q-range-info" style="font-size:0.75rem;color:var(--gold);font-weight:600;">
          Selecting all ${pool.length} Qs (Q#1 to Q#${pool.length})
        </div>
        <div class="cp-range-presets" style="display:flex;flex-wrap:wrap;gap:5px;">
          ${buildRangePresetsHtml(pool.length)}
        </div>
      </div>
    </div>
    <div class="cp-row"><span class="cp-lbl">Timer</span><input type="number" class="cp-input" id="timer-mins" value="0" min="0" max="180" style="width:70px;"><span style="font-size:0.72rem;color:var(--text3);">mins (0 = no timer)</span></div>
    <div class="cp-row" style="flex-wrap:wrap;gap:12px;"><label class="toggle-wrap"><label class="toggle"><input type="checkbox" id="toggle-shuffle"><span class="toggle-slider"></span></label><span class="toggle-lbl">Shuffle Questions</span></label><label class="toggle-wrap" style="margin-left:4px;"><label class="toggle"><input type="checkbox" id="toggle-shuffle-opts"><span class="toggle-slider"></span></label><span class="toggle-lbl">Shuffle Options</span></label></div>
    ${subtopicsSectionHtml}
    <div class="cp-row" style="gap:10px;margin-top:6px;flex-wrap:wrap;">
      <button class="start-btn" onclick="startQuiz()">Start Quiz &#x2192;</button>
      <button class="modal-btn modal-btn-secondary" style="font-size:0.78rem;padding:12px 18px;border-radius:10px;" onclick="openExportModal('setup')">&#x1F4C4; Export PDF Practice Sheet</button>
    </div>
  </div>`;
  setTimeout(()=>{cp.scrollIntoView({behavior:'smooth',block:'nearest'});},80);
}

function hideConfigPanel(){const cp=document.getElementById('config-panel');if(cp)cp.style.display='none';}

function startFromCard(subjId,e){
  e?.stopPropagation();
  if(currentSubjectId!==subjId||selectedChapters.size===0)selectAllChapters(subjId);
  setTimeout(()=>startQuiz(),100);
}

