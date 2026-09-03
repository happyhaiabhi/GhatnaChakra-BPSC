/* Minimal check that upsc.html boots and renders questions WITHOUT data.js. */
const { JSDOM, ResourceLoader, VirtualConsole } = require('jsdom');
const PAGE = 'http://127.0.0.1:8080/upsc.html';
class L extends ResourceLoader { fetch(u){ return u.startsWith('http://127.0.0.1:8080/')?super.fetch(u):null; } }
const errs = []; const vc = new VirtualConsole();
vc.on('jsdomError', e => errs.push('jsdomError: ' + String(e.message).slice(0,160)));
vc.on('error', (...a) => errs.push('console.error: ' + a.join(' ').slice(0,160)));
(async () => {
  const dom = await JSDOM.fromURL(PAGE, { runScripts:'dangerously', resources:new L(), pretendToBeVisual:true, virtualConsole:vc,
    beforeParse(w){ w.fetch=(i,init)=>fetch(new URL(String(i),PAGE).href,init); w.alert=()=>{}; w.confirm=()=>true;
      w.Element.prototype.scrollIntoView=function(){}; }});
  const w = dom.window;
  await new Promise(r => w.addEventListener('load', r));
  await new Promise(r => setTimeout(r, 12000));
  const d = w.document;
  const report = {
    loadedDataJs: !!d.querySelector('script[src="data.js"]'),
    offlineBundlePresent: typeof w.UPSC_QUESTION_BANK_DATA !== 'undefined',
    resultCards: d.querySelectorAll('#results .q-card, #results > *').length,
    resultsTextLength: (d.querySelector('#results')?.textContent || '').trim().length,
    statsText: (d.querySelector('#stats, .stats, .hero-stats')?.textContent || '').replace(/\s+/g,' ').trim().slice(0,120),
    errors: errs,
  };
  console.log(JSON.stringify(report, null, 2));
  process.exit(report.errors.length ? 1 : 0);
})();
