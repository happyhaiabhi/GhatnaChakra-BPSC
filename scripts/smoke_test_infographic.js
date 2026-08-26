/* Smoke test: run app.js rendering functions against real data records.
   Extracted ad hoc for CI-less verification; not wired into the page. */
const fs = require('fs');

const source = fs.readFileSync('app.js', 'utf-8');

function extract(name) {
  let start = source.indexOf(`function ${name}(`);
  if (start < 0) start = source.indexOf(`const ${name} =`);
  if (start < 0) throw new Error(`missing function ${name}`);
  let i = source.indexOf('{', start), depth = 0, end = i;
  for (; i < source.length; i++) {
    if (source[i] === '{') depth++;
    else if (source[i] === '}') { depth--; if (!depth) { end = i; break; } }
  }
  let body = source.slice(start, end + 1);
  if (source.slice(start, start + 6) === 'const ') body += ';';
  return body;
}

const helpers = ['safeLocalPath', 'safeWebUrl', 'questionNumber',
  'formatQuestionText', 'optionText', 'optionKey', 'formatSolution',
  'renderInfographic'].map(extract).join('\n');

const escapeHtml = (value = '') => String(value).replace( /* mirrored from app.js */
  /[&<>'"]/g,
  (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));

const sandbox = new Function('escapeHtml', `${helpers}
  return { renderInfographic };`)(escapeHtml);

const prelims = JSON.parse(fs.readFileSync('data/prelims.json', 'utf-8'));
const csat = JSON.parse(fs.readFileSync('data/csat.json', 'utf-8'));

let failures = 0;
function expect(cond, label) {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${label}`);
  if (!cond) failures++;
}

/* Prelims: flatten a record exactly like flattenPrelims does (...question + fields) */
const prelimsRow = prelims.records_by_year['1995'][0];
const prelimsQuestion = { ...prelimsRow, year: Number(prelimsRow.year), exam: 'Prelims' };
const html = sandbox.renderInfographic(prelimsQuestion);
expect(html.includes('infographics/1995/UPSCPRELI1995GS01001.webp'), 'prelims card uses local infographic path');
expect(html.includes('https://storage.googleapis.com/dalvoy-lessons-images/prelims-infographics/1995/UPSCPRELI1995GS01001.webp'), 'prelims card links remote source');
expect(html.includes('alt="Solution infographic for UPSC Prelims 1995 question 1"'), 'prelims alt text includes exam, year, number');
expect(html.includes('data-fallback='), 'prelims img carries remote fallback attribute');

/* CSAT still works */
const csatRow = csat.questions[0];
const csatQuestion = { ...csatRow, year: Number(csatRow.year), exam: 'CSAT' };
const csatHtml = sandbox.renderInfographic(csatQuestion);
expect(csatHtml.includes('infographics/2011/UPSCCSAT2011GS02001.webp'), 'csat card unchanged: local path');
expect(csatHtml.includes('UPSC CSAT 2011 question'), 'csat alt text unchanged');

/* Mains must still render nothing */
expect(sandbox.renderInfographic({ exam: 'Mains', year: 2020 }) === '', 'mains renders no infographic');

/* A prelims row WITHOUT infographic fields (legacy CSAT-pointing row) renders nothing */
const legacy = { ...prelims.records_by_year['2013'][97], year: 2013, exam: 'Prelims' };
expect(sandbox.renderInfographic(legacy) === '', 'legacy CSAT-pointing prelims row renders no infographic');

/* Every prelims row that has a reference renders an infographic */
let withRef = 0, rendered = 0;
for (const questions of Object.values(prelims.records_by_year)) {
  for (const q of questions) {
    if (q.infographic_url) {
      withRef++;
      if (sandbox.renderInfographic({ ...q, year: Number(q.year), exam: 'Prelims' }).includes(q.infographic_local)) rendered++;
    }
  }
}
expect(withRef === rendered && withRef === 3196, `all 3,196 referenced prelims rows render their infographic (${rendered}/${withRef})`);

process.exit(failures ? 1 : 0);
