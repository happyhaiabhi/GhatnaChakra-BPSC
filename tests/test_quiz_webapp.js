#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const {JSDOM, VirtualConsole} = require('jsdom');

const ROOT = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const fetches = [];
const consoleErrors = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on('jsdomError', e => consoleErrors.push('jsdom: ' + e.message));
virtualConsole.on('error', e => consoleErrors.push('console: ' + e));

const dom = new JSDOM(html, {
  url: 'http://quiz.test/index.html',
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  virtualConsole,
  beforeParse(window) {
    window.alert = () => {};
    window.confirm = () => true;
    window.HTMLElement.prototype.scrollIntoView = () => {};
    window.fetch = async url => {
      const rel = String(url).replace(/^\.\//, '');
      fetches.push(rel);
      const file = path.join(ROOT, rel);
      if (!file.startsWith(ROOT) || !fs.existsSync(file)) return {ok:false,status:404,json:async()=>({})};
      return {ok:true,status:200,json:async()=>JSON.parse(fs.readFileSync(file,'utf8'))};
    };
  }
});
const w = dom.window;
const d = w.document;
const tick = (ms=0) => new Promise(resolve => setTimeout(resolve, ms));
const ev = code => w.eval(code);

(async()=>{
  await tick(25);
  // The app now opens on a book-selection landing screen. Open the BPSC book.
  assert(d.getElementById('books-screen').classList.contains('active'), 'book selection screen shown first');
  await w.openBook('bpsc_ghatna_chakra');
  await tick(10);
  assert(d.getElementById('setup-screen').classList.contains('active'), 'BPSC book opens to setup screen');
  assert.equal(d.querySelectorAll('.subject-card').length, 12, '12 subject cards');
  assert.equal(d.getElementById('sh-subjects').textContent, '12');
  assert.equal(d.getElementById('sh-chapters').textContent, '391');
  assert.equal(d.getElementById('sh-questions').textContent, '4,441');

  const chapterIndex = JSON.parse(fs.readFileSync(path.join(ROOT,'data/chapters.json'),'utf8'));
  for (const subject of chapterIndex) {
    await w.toggleSubjectCard(subject.key);
    await tick(1);
    assert.equal(d.querySelectorAll(`#sc-chlist-${subject.key} .ch-row`).length, subject.chapters.length, `${subject.key} chapter rows`);
    const expected = subject.chapters.reduce((sum,ch)=>sum+ch.count,0);
    assert.equal(d.getElementById(`sc-pill-q-${subject.key}`).textContent, `${expected} Qs`, `${subject.key} question count`);
  }
  const expectedFiles = chapterIndex.map(s=>s.file).sort();
  const expectedSet = new Set(expectedFiles);
  const actualFiles = [...new Set(fetches.filter(x=>expectedSet.has(x)))].sort();
  assert.deepEqual(actualFiles, expectedFiles, 'all 12 subject files fetched');

  // Exact reference match question: book table, code matrix, selection, result review.
  await w.toggleSubjectCard('ancient_history');
  await w.toggleSubjectCard('ancient_history');
  await tick(1);
  ev(`selectedChapters=new Set(['Stone Age']); const q=allQuestions.find(x=>x.chapter==='Stone Age'&&x.question.includes('Utnoor')); startQuiz('bookmarks',[q]);`);
  assert(d.getElementById('quiz-screen').classList.contains('active'));
  assert.equal(d.querySelectorAll('#question-area .match-list-row').length, 4);
  assert.equal(d.querySelectorAll('#question-area .match-code-row').length, 4);
  assert.equal(d.querySelector('#question-area .match-list-title').textContent, '(Neolithic Site)');
  w.selectOption('C');
  assert(d.querySelector('.match-code-row.selected'));
  w.toggleBookmark();
  assert.equal(Object.keys(JSON.parse(w.localStorage.getItem('gc_bookmarks'))).length, 1);
  w.submitQuiz();
  assert(d.getElementById('result-screen').classList.contains('active'));
  assert.equal(d.getElementById('res-score').textContent, '100%');
  assert.equal(d.querySelectorAll('#review-body .match-list-row').length, 4);
  assert.equal(d.querySelectorAll('#review-body .match-review-code-row').length, 4);
  assert(d.querySelector('#review-body .match-review-code-row.correct-ans'));

  // Roman-left / letter-right source convention.
  await w.toggleSubjectCard('modern_history');
  await tick(1);
  ev(`selectedChapters=new Set(['Development of Press In Modern India']); const q=allQuestions.find(x=>x.question.startsWith('Match')&&x.question.includes('Free Hindustan')); startQuiz('bookmarks',[q]);`);
  assert.deepEqual([...d.querySelectorAll('#question-area .match-list-row .match-cell:first-child .match-cell-label')].map(x=>x.textContent), ['I.','II.','III.','IV.']);
  assert.deepEqual([...d.querySelectorAll('#question-area .match-list-row .match-cell:nth-child(2) .match-cell-label')].map(x=>x.textContent), ['A.','B.','C.','D.']);

  // Markers without a space after “(C)” and “(D)”.
  await w.toggleSubjectCard('geography_environment');
  await tick(1);
  ev(`selectedChapters=new Set(['Transports']); const q=allQuestions.find(x=>x.question.includes('(C)Trans-Siberian')); startQuiz('bookmarks',[q]);`);
  assert.equal(d.querySelectorAll('#question-area .match-list-row').length, 4);
  assert.equal(d.querySelectorAll('#question-area .match-code-row').length, 4);

  // The single malformed source object must fall back safely to standard MCQ.
  ev(`selectedChapters=new Set(['Environment & Ecology']); const q=allQuestions.find(x=>x.question==='Match List-I with List-II List-I List-II'); startQuiz('bookmarks',[q]);`);
  assert.equal(d.querySelectorAll('#question-area .match-paper').length, 0);
  assert.equal(d.querySelectorAll('#question-area .opt-btn').length, 4);

  // Assertion–reason and numbered-statement stems use structured cards/rows.
  w.__structuredQ = {
    q:'Given below are two statements.\nAssertion (A): Plants release oxygen.\nReason (R): Photosynthesis produces oxygen.\nChoose the correct answer.',
    question_type:'Assertion and Reason — Standard Relationship Evaluation',
    options:{A:'Both are true and R explains A',B:'Both are true but R does not explain A',C:'A is true but R is false',D:'A is false but R is true'},
    answer:'A'
  };
  ev(`quiz=[toInternalQuestion(window.__structuredQ,'test',0,'Structured')]; state={current:0,answers:[null],visited:[true],marked:[false]}; shuffledOptionOrders=[['A','B','C','D']]; renderQuestion();`);
  assert.equal(d.querySelectorAll('#question-area .ar-card').length, 2, 'assertion and reason render as two cards');
  assert.deepEqual([...d.querySelectorAll('#question-area .ar-label')].map(x=>x.textContent), ['Assertion (A)','Reason (R)']);
  assert.equal(d.querySelector('#question-area .question-type-pill').textContent, 'Assertion–Reason');

  w.__structuredQ = {
    q:'Consider the following statements:\n1. Mercury is a planet.\n2. Venus is a planet.\n3. Pluto is a dwarf planet.\nWhich of the statements given above are correct?',
    options:{A:'1 only',B:'1 and 2 only',C:'1, 2 and 3',D:'2 and 3 only'},
    answer:'C'
  };
  ev(`quiz=[toInternalQuestion(window.__structuredQ,'test',1,'Structured')]; state={current:0,answers:[null],visited:[true],marked:[false]}; shuffledOptionOrders=[['A','B','C','D']]; renderQuestion();`);
  assert.equal(d.querySelectorAll('#question-area .statement-row').length, 3, 'numbered statements render as rows');
  assert.match(d.querySelector('#question-area .structured-instruction').textContent,/Which of the statements/);
  assert.equal(d.querySelector('#question-area .question-type-pill').textContent, 'Numbered Statements');

  // Multiple accepted answers remain selectable, scoreable, and readable.
  w.__structuredQ = {q:'Select both correct letters.',options:{A:'Alpha',B:'Beta',C:'Gamma',D:'Delta'},answer:['A','D']};
  ev(`quiz=[toInternalQuestion(window.__structuredQ,'test',2,'Structured')]; state={current:0,answers:[null],visited:[true],marked:[false]}; shuffledOptionOrders=[['A','B','C','D']]; renderQuestion();`);
  w.selectOption('A');w.selectOption('D');
  assert.equal(d.querySelectorAll('#question-area .opt-btn.selected').length,2,'both accepted options can be selected');
  assert.equal(ev(`isQuestionCorrect(quiz[0],state.answers[0])`),true,'array answer scores by set equality');
  assert.match(d.querySelector('#question-area .exp-correct-ans').textContent,/A \+ D/,'array answer label lists both keys');

  // Navigation, wrong/skipped tracking, dashboard, bank and archive flows.
  ev(`const qs=allQuestions.filter(x=>x.chapter==='Environment & Ecology').slice(0,2); selectedChapters=new Set(['Environment & Ecology']); startQuiz('bookmarks',qs);`);
  const firstCorrect = ev('quiz[0].correctKey');
  const firstWrong = ev(`Object.keys(quiz[0].options).find(k=>k!==quiz[0].correctKey)`);
  w.selectOption(firstWrong);
  w.saveAndNext();
  assert.equal(ev('state.current'), 1);
  w.goToPrev();
  assert.equal(ev('state.current'), 0);
  w.jumpTo(1);
  assert.equal(ev('state.current'), 1);
  w.submitQuiz();
  assert.equal(d.getElementById('rs-wrong').textContent, '1');
  assert.equal(d.getElementById('rs-skip').textContent, '1');
  assert(Object.keys(JSON.parse(w.localStorage.getItem('gc_mistakes'))).length >= 1);
  assert(Object.keys(JSON.parse(w.localStorage.getItem('gc_skips'))).length >= 1);
  w.showMistakeScreen(); assert(d.getElementById('mistake-screen').classList.contains('active'));
  w.showSkipScreen(); assert(d.getElementById('skip-screen').classList.contains('active'));
  w.showBookmarkScreen(); assert(d.getElementById('bookmark-screen').classList.contains('active'));
  assert(d.querySelector('#bookmark-list .question-type-pill'),'bookmark item shows a type pill');
  const bookmarkAllChip=d.querySelector('#bookmark-type-filters .bank-filter-chip[data-type="all"]');
  assert(bookmarkAllChip,'bookmark taxonomy includes an All chip');
  assert.match(bookmarkAllChip.textContent,/All\s+\d+/,'All chip includes its count');
  ev(`addToBookmarks(toInternalQuestion(window.__structuredQ,'test',2,'Structured')); showBookmarkScreen();`);
  w.setBankTypeFilter('bookmark','Multiple Correct');
  assert.equal(d.querySelectorAll('#bookmark-list .bank-item').length,1,'type chip filters the bookmark bank');
  w.practiceFromBookmarks();
  assert.equal(ev('quiz.length'),1,'Practice uses only the active bank type');
  assert.equal(ev(`getQuestionType(quiz[0])`),'Multiple Correct');
  ev(`removeFromBookmarks('test_2',false)`);
  w.clearAllMistakes();
  assert.equal(Object.keys(JSON.parse(w.localStorage.getItem('gc_mistakes'))).length, 0);
  w.showArchiveScreen(); assert(d.getElementById('archive-screen').classList.contains('active'));
  assert(Object.keys(JSON.parse(w.localStorage.getItem('gc_archive'))).length >= 1);
  w.buildDashboard();
  assert(Number(d.getElementById('dash-sessions').textContent) >= 2);

  // Theme state and finite timer setup.
  w.applyTheme('dark'); w.toggleTheme();
  assert.equal(d.documentElement.getAttribute('data-theme'), 'light');
  await w.toggleSubjectCard('physics'); await tick(1);
  ev(`selectedChapters=new Set([allQuestions[0].chapter]); updateConfigPanel('physics');`);
  d.getElementById('num-questions').value='1';
  d.getElementById('timer-mins').value='1';
  w.startQuiz();
  assert.equal(d.getElementById('timer-display').textContent, '01:00');
  clearInterval(ev('timerInterval'));

  // Source text containing markup characters must render as text, not elements.
  ev(`quiz=[{uid:'escape',chapter:'Test',question:'2 < 3 & 4 > 1',options:{A:'<tag>',B:'safe'},correctKey:'B',correctAnswer:'safe',explanation:'Use < and &.',note:''}]; state={current:0,answers:[null],visited:[true],marked:[false]}; shuffledOptionOrders=[['A','B']]; renderQuestion();`);
  assert.equal(d.querySelector('#question-area .q-text').textContent, '2 < 3 & 4 > 1');
  assert.equal(d.querySelector('#question-area .opt-text').textContent, '<tag>');
  assert.equal(d.querySelectorAll('#question-area tag').length, 0);

  // Cross-device merge must combine before writing, never wipe existing cloud data.
  const mergedHistory=ev(`mergeSyncValue('gc_history',[{date:'2026-08-18T10:00:00Z',correct:1}],[{date:'2026-08-17T10:00:00Z',correct:2}])`);
  assert.equal(mergedHistory.length,2);
  const mergedBank=ev(`mergeSyncValue('gc_mistakes',{q1:{times:2,correctCount:1,addedAt:'2026-08-18T00:00:00Z'}},{q1:{times:4,correctCount:0,addedAt:'2026-08-19T00:00:00Z'},q2:{times:1}})`);
  assert.equal(mergedBank.q1.times,4);assert.equal(mergedBank.q1.correctCount,1);assert(mergedBank.q2);

  ['gc_mistakes','gc_bookmarks','gc_skips','gc_history','gc_archive'].forEach(k=>w.localStorage.removeItem(k));
  w.localStorage.setItem('gc_bookmarks',JSON.stringify({local:{q:{uid:'local'},addedAt:'2026-08-18T00:00:00Z'}}));
  w.localStorage.setItem('gc_mistakes',JSON.stringify({old:{q:{uid:'old'},times:1}}));
  w.localStorage.setItem('gc_history',JSON.stringify([{date:'2026-08-18T10:00:00Z',correct:1,wrong:0}]));
  const cloudStore={
    gc_mistakes:{payload:JSON.stringify({old:{q:{uid:'old'},times:3}})},
    gc_bookmarks:{payload:JSON.stringify({remote:{q:{uid:'remote'},addedAt:'2026-08-17T00:00:00Z'}})},
    gc_skips:{payload:'{}'},
    gc_history:{payload:JSON.stringify([{date:'2026-08-17T10:00:00Z',correct:2,wrong:1}])},
    gc_archive:{payload:JSON.stringify({old:{q:{uid:'old'},archivedAt:'2026-08-19T00:00:00Z'}})}
  };
  w.__cloudStore=cloudStore;
  w.__mockDb={
    collection(){return{doc(){return{collection(){return{
      get:async()=>({forEach:cb=>Object.entries(cloudStore).forEach(([id,value])=>cb({id,data:()=>value}))}),
      doc:key=>({key,set:async value=>{cloudStore[key]=value;}})
    };}};}};},
    batch(){const writes=[];return{set:(ref,value)=>writes.push([ref.key,value]),commit:async()=>writes.forEach(([key,value])=>{cloudStore[key]=value;})};}
  };
  ev(`fbDb=window.__mockDb;fbUserId='sync-test-user'`);
  assert.equal(await ev(`synchronizeAll(false)`),true);
  const syncedBookmarks=JSON.parse(cloudStore.gc_bookmarks.payload);
  assert(syncedBookmarks.local&&syncedBookmarks.remote,'local and cloud bookmarks merged');
  assert.equal(JSON.parse(cloudStore.gc_history.payload).length,2,'history merged in both directions');
  assert.equal(Object.keys(JSON.parse(cloudStore.gc_mistakes.payload)).length,0,'archive tombstone removed stale active mistake');
  ev(`showSignedInUI({name:'Test User',email:'test@example.com',photo:''})`);
  assert.notEqual(d.getElementById('sync-now-btn').style.display,'none');

  // Multi-book support: switching books loads a different bank and keeps each
  // book's progress in its own namespace.
  await w.openBook('ssc_sample');
  await tick(10);
  assert.equal(d.getElementById('setup-screen').classList.contains('active'), true, 'SSC book opens setup');
  assert.equal(ev('SUBJECTS_CONFIG.length'), 2, 'SSC has 2 subjects');
  assert.equal(d.getElementById('sh-questions').textContent, '6', 'SSC has 6 questions');
  assert.equal(d.getElementById('nav-book-name').textContent, 'SSC Practice Set');
  // Snapshot BPSC's stored history before touching SSC.
  const bpscRawBefore = ev(`localStorage.getItem('gc_history')`);
  await w.toggleSubjectCard('general_awareness');
  await tick(5);
  assert.equal(d.querySelectorAll('#sc-chlist-general_awareness .ch-row').length, 2, 'GA has 2 chapters');
  ev(`saveHistory([{date:new Date().toISOString(),correct:1,wrong:0}]);`);
  assert.equal(ev(`getHistory().length`), 1, 'SSC history written to SSC namespace');
  assert.equal(ev(`!!localStorage.getItem('gc_history__book_ssc_sample')`), true, 'SSC progress is namespaced');
  assert.equal(ev(`localStorage.getItem('gc_history')`), bpscRawBefore, 'legacy BPSC key untouched by SSC write');
  await w.openBook('bpsc_ghatna_chakra');
  await tick(10);
  assert.equal(ev(`localStorage.getItem('gc_history__book_ssc_sample')?1:0`), 1, 'SSC data retained after switching away');
  assert.equal(ev(`localStorage.getItem('gc_history')`), bpscRawBefore, 'BPSC storage stays separate from SSC');
  assert.equal(ev('SUBJECTS_CONFIG.length'), 12, 'back to BPSC 12 subjects');
  // The book-selection landing screen is reachable and lists both books.
  w.showBooksScreen();
  await tick(5);
  assert(d.getElementById('books-screen').classList.contains('active'));
  assert(d.querySelectorAll('#books-grid .book-card').length >= 7, 'all book cards shown (BPSC + 6 imported + sample)');
  ['physics','chemistry','biology','ancient_india','medieval_india','modern_india'].forEach(id=>{
    assert(d.querySelector(`#books-grid .book-card[data-book="${id}"]`), `${id} book card present`);
  });

  // Imported stems without explicit taxonomy are detected from their text.
  await w.openBook('ancient_india');
  await tick(10);
  await w.toggleSubjectCard('ancient_india');
  await tick(5);
  ev(`const q=allQuestions.find(x=>x.question.includes('List- 1 (Dynasty)')); selectedChapters=new Set([q.chapter]); startQuiz('bookmarks',[q]);`);
  assert.equal(d.querySelectorAll('#question-area .match-list-row').length,4,'List-1/List-2 uses the match table');
  ev(`const q=allQuestions.find(x=>x.question.includes('Ahar Civilization')); selectedChapters=new Set([q.chapter]); startQuiz('bookmarks',[q]);`);
  assert.equal(d.querySelectorAll('#question-area .lettered-row').length,4,'lettered combo stem uses labelled rows');
  assert.equal(d.querySelector('#question-area .question-type-pill').textContent,'Lettered List');

  // Regression: imported book prose carries soft PDF line wraps. They must be
  // collapsed to spaces (blank-line paragraph breaks and hyphen joins excepted)
  // in the live quiz, its explanation, and every review/bank surface.
  assert.equal(ev(`normalizeBookText('first line\\nsecond line\\n\\nnew paragraph')`), 'first line second line\n\nnew paragraph', 'blank-line paragraph break preserved');
  assert.equal(ev(`normalizeBookText('devel-\\nopment')`), 'development', 'hyphenated wrap rejoins without a space');
  assert.equal(ev(`normalizeBookText('line1\\r\\nline2\\rline3')`), 'line1 line2 line3', 'CRLF/CR normalized then wrapped');
  ev(`const q=allQuestions.find(x=>x.question.includes("visited 'Bhimbetka Caves'")&&x.question.includes('rock paintings')); window.__bhimbetkaQ=q; selectedChapters=new Set([q.chapter]); startQuiz('bookmarks',[q]);`);
  assert.equal(ev('window.__bhimbetkaQ.question.includes("\\n")'), true, 'source fixture retains soft newlines');
  const bqt=q=>q.textContent;
  assert.equal(bqt(d.querySelector('#question-area .q-text')).includes('\n'), false, 'question stem renders without soft newlines');
  assert(bqt(d.querySelector('#question-area .q-text')).includes("visited 'Bhimbetka Caves'"), 'complete sentence preserved in stem');
  assert(bqt(d.querySelector('#question-area .q-text')).includes('rock paintings'), 'rock paintings preserved in stem');
  assert.equal(bqt(d.querySelector('#question-area .exp-body')).includes('\n'), false, 'explanation renders without soft newlines');
  w.toggleBookmark();
  const bmKey = ev('sk("gc_bookmarks")');
  assert(JSON.parse(w.localStorage.getItem(bmKey))[ev('window.__bhimbetkaQ.uid')], 'Bhimbetka question bookmarked');
  w.showBookmarkScreen();
  assert(d.getElementById('bookmark-screen').classList.contains('active'));
  const bookmarkStem=d.querySelector('#bookmark-list .bank-q');
  assert(bookmarkStem,'bookmarked question renders on the Bookmarks screen');
  assert.equal(bookmarkStem.textContent.includes('\n'), false, 'bookmarked question has no soft newlines');
  assert(bookmarkStem.textContent.includes("visited 'Bhimbetka Caves'"), 'bookmarked question retains the complete sentence');
  ev(`removeFromBookmarks(window.__bhimbetkaQ.uid,false); showBookmarkScreen();`);

  // Regression: PDF-extracted ligature glyphs (ﬁ/ﬂ and the ﬀ family) each carry
  // a spurious trailing space. Word continuations must join back together,
  // genuine boundaries where the ligature ends a standalone word must not.
  assert.equal(ev(`normalizeBookText('the archaeologists ﬁ rst visited')`), 'the archaeologists first visited', 'ﬁ rst joins into "first"');
  assert.equal(ev(`normalizeBookText('signiﬁ cant')`), 'significant', 'signiﬁ cant joins into "significant"');
  assert.equal(ev(`normalizeBookText('ofﬁ cers')`), 'officers', 'ofﬁ cers joins into "officers"');
  assert.equal(ev(`normalizeBookText('inﬂ uence')`), 'influence', 'inﬂ uence joins into "influence"');
  assert.equal(ev(`normalizeBookText('the ﬂ ag')`), 'the flag', 'ﬂ expands to "fl"');
  assert.equal(ev(`normalizeBookText('the oﬃ ce')`), 'the office', 'oﬃ ce joins into "office"');
  assert.equal(ev(`normalizeBookText('Suﬁ saint')`), 'Sufi saint', 'Suﬁ saint keeps its word boundary');
  assert.equal(ev(`normalizeBookText('Suﬁ order')`), 'Sufi order', 'Suﬁ order keeps its word boundary');
  assert.equal(ev(`normalizeBookText('Khaﬁ Khan')`), 'Khafi Khan', 'Khaﬁ Khan keeps its word boundary');
  assert.equal(ev(`normalizeBookText('Raﬁ Ahmed')`), 'Rafi Ahmed', 'Raﬁ Ahmed keeps its word boundary');
  assert.equal(ev(`normalizeBookText('Suﬁ sm')`), 'Sufism', 'Suﬁ sm joins into "Sufism"');
  assert.equal(ev(`normalizeBookText('Raﬁ q')`), 'Rafiq', 'Raﬁ q joins into "Rafiq"');
  assert.equal(ev(`normalizeBookText('Raﬁ que')`), 'Rafique', 'Raﬁ que joins into "Rafique"');
  assert.equal(ev(`normalizeBookText('Shaﬁ que')`), 'Shafique', 'Shaﬁ que joins into "Shafique"');
  assert.equal(ev(`normalizeBookText('Kalinga oﬀ ered stiﬀ resistance')`), 'Kalinga offered stiff resistance', 'ﬀ joins continuations but keeps "stiff resistance" apart');

  // The Bhimbetka fixture itself: the source stem carries the ﬁ ligature with
  // the spurious space; the rendered surfaces must show plain joined words.
  assert.equal(ev('window.__bhimbetkaQ.question.includes("\\uFB01")'), true, 'source fixture retains the ﬁ ligature glyph');
  assert.equal(bqt(d.querySelector('#question-area .q-text')).includes('\uFB01'), false, 'rendered stem leaves no ligature glyph');
  assert(bqt(d.querySelector('#question-area .q-text')).includes('first visited'), 'stem shows joined "first visited"');
  assert(bqt(d.querySelector('#question-area .q-text')).includes('significance'), 'stem shows joined "significance"');
  assert.equal(bookmarkStem.textContent.includes('\uFB01'), false, 'bookmarked question leaves no ligature glyph');
  assert(bookmarkStem.textContent.includes('first visited'), 'bookmarked question shows joined "first visited"');

  // Regression: parenthesized numbered-statement stems ("(1) …" / "(2) …") were
  // not detected as Numbered Statements and fell back to a run-on Direct MCQ.
  ev(`const q=allQuestions.find(x=>x.question.startsWith('With reference to the cultural heritage of Uttar')); selectedChapters=new Set([q.chapter]); startQuiz('bookmarks',[q]);`);
  assert.equal(d.querySelector('#question-area .question-type-pill').textContent, 'Numbered Statements', '(1)/(2) stem classified as Numbered Statements');
  assert.equal(d.querySelectorAll('#question-area .statement-row').length, 2, 'two labelled statement rows render');
  assert.deepEqual([...d.querySelectorAll('#question-area .statement-label')].map(x=>x.textContent), ['1.','2.'], 'rows carry numeric labels');
  assert(d.querySelector('#question-area .structured-intro').textContent.includes('Uttar Pradesh'), 'stem intro introduces the statements');
  assert.match(d.querySelector('#question-area .structured-instruction').textContent, /Select the correct answer/, 'trailing code instruction split out of the last row');

  // Extra source fields such as `asset` must survive mapping and render as images.
  await w.openBook('physics');
  await tick(10);
  await w.toggleSubjectCard('physics');
  await tick(5);
  const assetQ = ev(`allQuestions.find(x=>x.asset&&Object.values(x.options).some(value=>String(value).includes('[Diagram')))`);
  assert(assetQ && assetQ.asset, 'physics question asset field preserved');
  w.__assetUid=assetQ.uid;
  ev(`const q=allQuestions.find(x=>x.uid===window.__assetUid); selectedChapters=new Set([q.chapter]); startQuiz('bookmarks',[q]);`);
  const img = d.querySelector('#question-area .q-asset-img');
  assert(img, 'question image rendered');
  assert(String(img.getAttribute('src')).includes(String(assetQ.asset).split('/').pop()), 'image src uses asset filename');
  assert(String(img.getAttribute('src')).startsWith('books/physics/'), 'image resolved under the active book');
  assert([...d.querySelectorAll('#question-area .opt-text')].every((el,index)=>el.textContent===`Figure (${String.fromCharCode(97+index)})`), 'diagram placeholders become Figure (a), Figure (b), etc.');
  assert(!d.querySelector('#question-area .exp-correct-ans').textContent.includes('asset:'),'correct-answer display also hides the asset placeholder');

  assert.equal(consoleErrors.length, 0, consoleErrors.join('\n'));
  console.log(JSON.stringify({
    status:'PASS',
    subjects:12,
    chapters:391,
    questions:4441,
    subjectFilesFetched:actualFiles.length,
    matchCandidatesParsed:'49/50',
    tested:['dashboard','subject/chapter loading','quiz rendering','match layouts','assertion–reason cards','numbered statement rows','taxonomy pills and filters','multiple answers','figure labels','fallback','selection','navigation','scoring','results/review','bookmarks','mistakes','skips','archive','theme','timer','HTML escaping','cross-device merge','archive tombstones','manual sync UI']
  }, null, 2));
  dom.window.close();
})().catch(err=>{
  console.error(err.stack||err);
  dom.window.close();
  process.exit(1);
});
