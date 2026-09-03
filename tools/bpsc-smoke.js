#!/usr/bin/env node
/*
 * Runtime smoke test for the BPSC application.
 *
 * Loads bpsc/index.html in jsdom (scripts enabled, local resources only),
 * waits for boot, then records:
 *   - uncaught errors / console errors
 *   - observable DOM state (book cards, subject grid, quiz question)
 *   - the behaviour of a fixed set of pure functions and lexical globals,
 *     probed through window.eval() so `let`/`const` bindings are reachable
 *
 * Comparing a before/after pair with tools/compare-smoke.js is what proves a
 * refactor changed nothing.
 *
 * Usage:  node tools/bpsc-smoke.js [url] [out.json]
 *    e.g. node tools/bpsc-smoke.js http://127.0.0.1:8080/bpsc/index.html /tmp/after.json
 */
const { JSDOM, ResourceLoader, VirtualConsole } = require('jsdom');
const fs = require('fs');

const PAGE = process.argv[2] || 'http://127.0.0.1:8080/bpsc/index.html';
const OUT = process.argv[3] || '/tmp/bpsc-smoke.json';
const ORIGIN = PAGE.slice(0, PAGE.indexOf('/', PAGE.indexOf('//') + 2));

/* Only allow the serving origin; block Google Fonts / gstatic so runs are
   deterministic and offline-safe. */
class LocalOnly extends ResourceLoader {
  fetch(url, options) {
    if (!url.startsWith(ORIGIN + '/')) return null;
    return super.fetch(url, options);
  }
}

// Pure / deterministic probes. Each is wrapped so a missing symbol or a throw
// is recorded rather than aborting the run.
const PROBES = {
  'escapeHtml("<b>&\'\\"")': `escapeHtml('<b>&\\'"')`,
  'formatTime(125)': `formatTime(125)`,
  'formatTime(3725)': `formatTime(3725)`,
  'formatDuration(90)': `formatDuration(90)`,
  'normalizeBookText("  a ﬁ b  ")': `normalizeBookText('  a\\uFB01 b  ')`,
  'getQuestionType(stem)': `getQuestionType({question:'Which of the following is correct?',options:{A:'1',B:'2'}})`,
  'getQuestionType(assertion)': `getQuestionType({question:'Assertion (A): x. Reason (R): y.',options:{A:'a',B:'b'}})`,
  'bookFilePath("biology.json")': `bookFilePath('biology.json')`,
  'bookFilePath("data/biology.json")': `bookFilePath('data/biology.json')`,
  'sk("gc_mistakes")': `sk('gc_mistakes')`,
  'MASTERY': `MASTERY`,
  'BLOOM_INTERVALS': `BLOOM_INTERVALS`,
  'SYNC_BASE_KEYS': `SYNC_BASE_KEYS`,
  'Object.keys(TOPIC_EMOJI).length': `Object.keys(TOPIC_EMOJI).length`,
  'TOPIC_EMOJI["Polity"]': `TOPIC_EMOJI['Polity']`,
  'PRINTABLE_CSS.length': `PRINTABLE_CSS.length`,
  'PRINTABLE_CSS.slice(0,40)': `PRINTABLE_CSS.slice(0,40)`,
  'LIGATURE_EXPANSIONS["\\uFB01"]': `LIGATURE_EXPANSIONS['\\uFB01']`,
  'typeof init': `typeof init`,
  'typeof renderQuestionStem': `typeof renderQuestionStem`,
  'questionCorrectAnswerLabel(opts,B)': `questionCorrectAnswerLabel({options:{A:'one',B:'two',C:'three'},answer:'B'})`,
  'optionDisplayText("x","A")': `optionDisplayText('x','A')`,
};

const consoleErrors = [];
const pageErrors = [];

const vc = new VirtualConsole();
vc.on('jsdomError', (e) => pageErrors.push(String((e && e.message) || e)));
vc.on('error', (...a) => consoleErrors.push(a.join(' ')));

(async () => {
  const dom = await JSDOM.fromURL(PAGE, {
    runScripts: 'dangerously',
    resources: new LocalOnly(),
    pretendToBeVisual: true,
    virtualConsole: vc,
    beforeParse(window) {
      window.fetch = (input, init) => fetch(new URL(String(input), PAGE).href, init);
      // jsdom implements neither; without stubs they surface as page errors.
      window.alert = () => {}; window.confirm = () => true; window.prompt = () => null;
      window.print = () => {}; window.scrollTo = () => {};
      // jsdom has no layout, so these are no-ops rather than app bugs.
      window.Element.prototype.scrollIntoView = function () {};
      window.HTMLElement.prototype.scrollIntoView = function () {};
      window.matchMedia = window.matchMedia || ((q) => ({
        matches: false, media: q, onchange: null,
        addListener() {}, removeListener() {},
        addEventListener() {}, removeEventListener() {}, dispatchEvent: () => false,
      }));
    },
  });
  const { window } = dom;

  const settle = (ms) => new Promise((r) => setTimeout(r, ms));
  await new Promise((r) => {
    if (window.document.readyState === 'complete') return r();
    window.addEventListener('load', r);
    setTimeout(r, 20000);
  });
  await settle(8000);

  const doc = window.document;
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();

  /* body text EXCLUDING script/style — inline scripts used to inflate it. */
  const bodyText = (() => {
    const c = doc.body.cloneNode(true);
    c.querySelectorAll('script,style').forEach((n) => n.remove());
    return (c.textContent || '').replace(/\s+/g, ' ').trim();
  })();

  const probes = {};
  for (const [label, expr] of Object.entries(PROBES)) {
    try { probes[label] = JSON.stringify(window.eval(expr)); }
    catch (e) { probes[label] = 'THREW: ' + e.name + ': ' + e.message; }
  }

  const report = {
    url: PAGE,
    title: doc.title,
    // --- structure (expected to change when files are split) -------------
    styleTags: doc.querySelectorAll('style').length,
    linkCss: [...doc.querySelectorAll('link[rel="stylesheet"]')].map((l) => l.getAttribute('href')),
    scriptSrc: [...doc.querySelectorAll('script[src]')].map((s) => s.getAttribute('src')),
    inlineScripts: [...doc.querySelectorAll('script:not([src])')].length,
    // --- behaviour (must NOT change) -------------------------------------
    bookCards: doc.querySelectorAll('#books-grid .book-card').length,
    bookTitles: [...doc.querySelectorAll('#books-grid .book-title')].map((e) => clean(e.textContent)),
    bookStats: [...doc.querySelectorAll('#books-grid .book-stats')].map((e) => clean(e.textContent)),
    notesLinks: [...doc.querySelectorAll('#notes-screen a.notes-download')].map((a) => a.getAttribute('href')),
    screens: [...doc.querySelectorAll('.screen')].map((s) => s.id).sort(),
    activeScreen: doc.querySelector('.screen.active')?.id || null,
    cssRuleCount: [...doc.styleSheets].reduce((n, s) => {
      try { return n + s.cssRules.length; } catch { return n; }
    }, 0),
    bodyTextLength: bodyText.length,
    bodyTextHash: require('crypto').createHash('sha1').update(bodyText).digest('hex'),
    fnGlobals: Object.keys(window).filter((k) => {
      try { return typeof window[k] === 'function'; } catch { return false; }
    }).sort(),
    probes,
    // --- interaction: open the core book, then start a quiz --------------
    interaction: {},
    pageErrors,
    consoleErrors,
  };

  try {
    window.eval(`openBook('bpsc_ghatna_chakra')`);
    await settle(6000);
    report.interaction.subjectCards = doc.querySelectorAll('.subject-card, .sc-card, [class*="subject-card"]').length;
    report.interaction.setupText = clean(doc.querySelector('#setup-screen')?.textContent || '').slice(0, 300);
    report.interaction.booksScreenActive = !!doc.querySelector('#books-screen.active');

    // start "all chapters" of the first subject and check the engine came up
    const firstSubj = window.eval(`(SUBJECTS_CONFIG&&SUBJECTS_CONFIG[0]&&SUBJECTS_CONFIG[0].id)||null`);
    report.interaction.firstSubject = firstSubj;
    if (firstSubj) {
      // A subject only loads its questions when its card is expanded.
      window.eval(`toggleSubjectCard(${JSON.stringify(firstSubj)})`);
      await settle(8000);
      report.interaction.chapterRows = doc.querySelectorAll('[id^="chrow-"]').length;
      report.interaction.allQuestions = window.eval(`typeof allQuestions!=='undefined'?allQuestions.length:null`);
      window.eval(`startFromCard(${JSON.stringify(firstSubj)})`);
      await settle(9000);
      // startQuiz() fills the `quiz` array; `state` only holds cursor/answers.
      report.interaction.quizQuestions = window.eval(`typeof quiz!=='undefined'?quiz.length:null`);
      report.interaction.quizIndex = window.eval(`(typeof state==='object'&&state)?state.current:null`);
      report.interaction.quizScreenActive = !!doc.querySelector('#quiz-screen.active');
      report.interaction.questionAreaText = clean(doc.querySelector('#question-area')?.textContent || '').slice(0, 240);
      report.interaction.questionAreaLen = clean(doc.querySelector('#question-area')?.textContent || '').length;
      report.interaction.optionButtons = doc.querySelectorAll('#question-area .opt-btn, #quiz-body .opt-btn, .opt-btn').length;
      report.interaction.quizBodyLen = clean(doc.querySelector('#quiz-body')?.textContent || '').length;
    }
  } catch (e) {
    report.interaction.threw = e.name + ': ' + e.message;
  }

  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));

  console.log(JSON.stringify({
    bookCards: report.bookCards,
    cssRuleCount: report.cssRuleCount,
    fnGlobals: report.fnGlobals.length,
    bodyTextLength: report.bodyTextLength,
    bodyTextHash: report.bodyTextHash.slice(0, 12),
    subjectCards: report.interaction.subjectCards,
    optionCount: report.interaction.optionCount,
    qTotal: report.interaction.qTotal,
    probesOk: Object.values(report.probes).filter((v) => !String(v).startsWith('THREW')).length + '/' + Object.keys(report.probes).length,
    pageErrors: report.pageErrors.length,
    consoleErrors: report.consoleErrors.length,
  }, null, 2));

  if (report.pageErrors.length) console.log('\nPAGE ERRORS:\n' + report.pageErrors.join('\n'));
  if (report.consoleErrors.length) console.log('\nCONSOLE ERRORS:\n' + report.consoleErrors.slice(0, 10).join('\n'));
  const threwProbes = Object.entries(report.probes).filter(([, v]) => String(v).startsWith('THREW'));
  if (threwProbes.length) console.log('\nTHREW PROBES:\n' + threwProbes.map(([k, v]) => k + ' -> ' + v).join('\n'));
  dom.window.close();
  process.exit(0);
})().catch((e) => { console.error('HARNESS FAILURE:', e); process.exit(1); });
