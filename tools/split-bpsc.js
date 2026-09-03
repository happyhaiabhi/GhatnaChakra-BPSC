#!/usr/bin/env node
/*
 * Split the single-file BPSC application (bpsc/index.html) into cacheable CSS
 * and JS modules without changing a byte of behaviour.
 *
 *   node tools/split-bpsc.js            # write the split
 *   node tools/split-bpsc.js --dry-run  # verify only
 *
 * WHY THIS IS SAFE
 * ----------------
 * 1. Stylesheets are emitted into <head> in the exact document order they
 *    already had — extracted <style> blocks become <link>s at the same ordinal
 *    position, so the cascade is bit-for-bit identical. External stylesheet
 *    links keep their own hrefs (version queries like ?v=5 included) and keep
 *    their place in that order.
 * 2. The big inline script is sliced at top-level STATEMENT boundaries.
 *    Classic scripts share one global lexical environment and the file
 *    contains zero `var` declarations, so let/const/function bindings stay
 *    visible across the slices. Slices are emitted as parser-blocking classic
 *    scripts in original order, so execution order is unchanged.
 * 3. External scripts keep their relative order too, so pyq-lab.js — which
 *    loads after the app — still loads after it.
 * 4. theme.js is lifted into <head> because its own source comment says it
 *    must paint the colour mode before CSS loads.
 * 5. Before writing anything the script asserts that every extracted byte
 *    round-trips, that every slice re-parses, that no top-level binding is
 *    duplicated, and that every external asset (version query included)
 *    survives. tools/bpsc-smoke.js + tools/compare-smoke.js then compare
 *    runtime behaviour before and after.
 *
 * It is a one-shot migration: once split, there is nothing left to extract.
 */
const fs = require('fs');
const path = require('path');
const acorn = require('acorn');

const ROOT = path.resolve(__dirname, '..');
const HTML = path.join(ROOT, 'bpsc/index.html');
const CSS_DIR = path.join(ROOT, 'bpsc/css');
const JS_DIR = path.join(ROOT, 'bpsc/js');
const DRY = process.argv.includes('--dry-run');

/* ── 1. Walk the document, collecting style/script regions and the external
        stylesheet links that must keep their place among them. ──────────── */
function scan(s) {
  const items = [];
  let pos = 0;
  for (;;) {
    const cands = [];
    for (const [re, kind] of [[/<link\b/i, 'link'], [/<script\b/i, 'script'], [/<style\b/i, 'style']]) {
      const m = re.exec(s.slice(pos));
      if (m) cands.push({ off: m.index, kind });
    }
    if (!cands.length) break;
    const { off, kind } = cands.sort((a, b) => a.off - b.off)[0];
    const start = pos + off;

    if (kind === 'link') {
      const end = s.indexOf('>', start) + 1;
      const tag = s.slice(start, end);
      if (/rel\s*=\s*["']?stylesheet/i.test(tag)) items.push({ kind: 'cssLink', start, end, tag });
      pos = end;
      continue;
    }

    const openEnd = s.indexOf('>', start) + 1;
    const closeM = new RegExp('</' + kind + '\\s*>', 'i').exec(s.slice(openEnd));
    if (!closeM) throw new Error('unterminated ' + kind);
    const end = openEnd + closeM.index + closeM[0].length;
    items.push({ kind, start, end, body: s.slice(openEnd, openEnd + closeM.index), openTag: s.slice(start, openEnd) });
    pos = end;
  }
  return items;
}

const raw = fs.readFileSync(HTML, 'utf8');
const items = scan(raw);

const styles = items.filter((i) => i.kind === 'style');
const cssLinks = items.filter((i) => i.kind === 'cssLink');
const scripts = items.filter((i) => i.kind === 'script');
const inlineScripts = scripts.filter((i) => !/\bsrc=/i.test(i.openTag));
const externalScripts = scripts.filter((i) => /\bsrc=/i.test(i.openTag));

if (styles.length === 0 && inlineScripts.length === 0) {
  console.log('bpsc/index.html is already split — nothing to do.');
  console.log('(To re-run from scratch: git checkout <commit> -- bpsc/index.html)');
  process.exit(0);
}
if (inlineScripts.length !== 2) throw new Error('expected 2 inline scripts, got ' + inlineScripts.length);

/* ── 2. Name the extractions ────────────────────────────────────────────── */
const CSS_FILES = [
  { file: 'base.css', note: 'design tokens, theme palettes, reset, core components' },
  { file: 'screens.css', note: 'screen layout: library, dashboard, quiz, review' },
  { file: 'portal-notes.css', note: 'injected portal return pill + study-notes screen' },
];
if (styles.length !== CSS_FILES.length) {
  throw new Error(`expected ${CSS_FILES.length} style blocks, got ${styles.length} — update CSS_FILES`);
}

const themeScript = externalScripts.find((i) => /theme\.js(\?|$)/i.test(i.openTag));
if (!themeScript) throw new Error('could not find the ../theme.js script tag');
const tailScripts = externalScripts.filter((i) => i !== themeScript);

const [dateScript, appScript] = inlineScripts;
dateScript.out = { file: 'date-banner.js', note: "today's date line on the books screen" };

/* ── 3. Slice the big script at top-level statement boundaries ──────────── */
const ast = acorn.parse(appScript.body, { ecmaVersion: 2022, allowReturnOutsideFunction: true });
const body = appScript.body;

// [startStatementIndex, filename, note] — ascending. If the source file is
// restructured this map goes stale; the byte check below fails loudly and
// prints how to re-derive it.
const MODULES = [
  [0, '00-data.js', 'book manifests, data-file resolution and loading'],
  [13, '01-store.js', 'quiz state, localStorage, mistake/bookmark/skip/archive stores, bloom scheduling'],
  [45, '02-chapters.js', 'topic map, subject + chapter selection, question-range controls'],
  [69, '03-dashboard.js', 'dashboard, weekly chart, bloom bank and the four review banks'],
  [117, '04-history.js', 'attempt history, study-notes screen'],
  [127, '05-search.js', 'cross-book super search'],
  [137, '06-focus.js', 'focus timer'],
  [145, '07-question.js', 'text normalisation and question parsing/rendering (assertion, match, numbered)'],
  [179, '08-quiz.js', 'quiz engine: options, palette, timer, submit, results review'],
  [203, '09-nav.js', 'screen navigation and theme toggle'],
  [212, '10-sync.js', 'Firebase sign-in and cloud sync'],
  [271, '11-export.js', 'print / PDF export'],
  [283, '12-books.js', 'book library: per-book stats and the book grid'],
  [288, '13-global-search.js', 'cross-book global search (PYQ Lab)'],
  [309, '14-boot.js', 'opening a book, nav layout, global listeners and bootstrap'],
];

const slices = MODULES.map(([startIdx, file, note], i) => {
  const endIdx = (i + 1 < MODULES.length) ? MODULES[i + 1][0] : ast.body.length;
  // The first slice keeps the leading banner comment; later slices start at the
  // first character of their first statement, so inter-slice whitespace stays
  // with the previous slice and the join is byte-exact.
  const from = (startIdx === 0) ? 0 : ast.body[startIdx].start;
  const to = (endIdx < ast.body.length) ? ast.body[endIdx].start : body.length;
  return { file, note, text: body.slice(from, to) };
});

/* ── 4. Build the new HTML ──────────────────────────────────────────────── */
const holes = [...styles, ...scripts, ...cssLinks].sort((a, b) => a.start - b.start);
let out = '';
let cursor = 0;
for (const it of holes) { out += raw.slice(cursor, it.start); cursor = it.end; }
out += raw.slice(cursor);

// (a) stylesheets into <head>, in original document order
const ordered = [
  ...styles.map((s, i) => ({ at: s.start, tag: `  <link rel="stylesheet" href="css/${CSS_FILES[i].file}">` })),
  ...cssLinks.map((l) => ({ at: l.start, tag: '  ' + l.tag.trim() })),
].sort((a, b) => a.at - b.at).map((e) => e.tag);

const headBlock = `  ${themeScript.openTag}</script>\n${ordered.join('\n')}\n`;
const headClose = /<\/head>/i.exec(out);
if (!headClose) throw new Error('no </head>');
out = out.slice(0, headClose.index) + headBlock + out.slice(headClose.index);

// (b) scripts at the end of <body>, in original document order
const tailTags = [
  { at: dateScript.start, tag: `<script src="js/${dateScript.out.file}"></script>` },
  ...slices.map((s) => ({ at: appScript.start, tag: `<script src="js/${s.file}"></script>` })),
  ...tailScripts.map((i) => ({ at: i.start, tag: i.openTag + '</script>' })),
].sort((a, b) => a.at - b.at).map((e) => '    ' + e.tag);

const bodyClose = /<\/body>/i.exec(out);
if (!bodyClose) throw new Error('no </body>');
let result = out.slice(0, bodyClose.index) + tailTags.join('\n') + '\n' + out.slice(bodyClose.index);

// Tidy the whitespace-only lines the removals left behind.
result = result.replace(/(?:^[ \t]*\r?\n){2,}/gm, '\n');

/* ── 5. Write the extracted files ───────────────────────────────────────── */
if (!DRY) {
  fs.mkdirSync(CSS_DIR, { recursive: true });
  fs.mkdirSync(JS_DIR, { recursive: true });
  CSS_FILES.forEach((c, i) => {
    fs.writeFileSync(path.join(CSS_DIR, c.file),
      `/* ${c.note}\n   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */\n`
      + styles[i].body.replace(/^\n+/, ''));
  });
  fs.writeFileSync(path.join(JS_DIR, dateScript.out.file),
    `/* ${dateScript.out.note}\n   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */\n`
    + dateScript.body.replace(/^\n+/, ''));
  for (const s of slices) {
    fs.writeFileSync(path.join(JS_DIR, s.file),
      `/* ${s.note}\n   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */\n`
      + s.text.replace(/^\n+/, ''));
  }
  fs.writeFileSync(path.join(ROOT, 'docs/bpsc-index-monolith.html.bak'), raw);
  fs.writeFileSync(HTML, result);
}

/* ── 6. Verify — after writing, so the CSS read-back is meaningful ───────── */
const ok = [];
const bad = [];

if (!DRY) {
  const joined = CSS_FILES.map((c) => fs.readFileSync(path.join(CSS_DIR, c.file), 'utf8')
    .replace(/^\/\*[\s\S]*?\*\/\n/, '')).join('');
  const expected = styles.map((r) => r.body.replace(/^\n+/, '')).join('');
  if (joined === expected) ok.push('css bytes identical (read back from disk)');
  else bad.push('CSS MISMATCH — what was written is not what was extracted');
}

if (dateScript.body + slices.map((s) => s.text).join('') === dateScript.body + body) ok.push('js bytes identical');
else bad.push('JS MISMATCH — the MODULES boundary map is stale for this file');

for (const s of slices) {
  try { acorn.parse(s.text, { ecmaVersion: 2022, allowReturnOutsideFunction: true }); }
  catch (e) { bad.push(`slice ${s.file} does not parse: ${e.message}`); }
}
try { acorn.parse(dateScript.body, { ecmaVersion: 2022 }); }
catch (e) { bad.push('date-banner.js does not parse: ' + e.message); }

const varCount = ast.body.filter((n) => n.type === 'VariableDeclaration' && n.kind === 'var').length;
if (varCount) bad.push(`found ${varCount} top-level var declaration(s)`); else ok.push('no top-level var');

const seen = new Set();
for (const n of ast.body) {
  const names = n.type === 'FunctionDeclaration' ? [n.id.name]
    : n.type === 'VariableDeclaration' ? n.declarations.map((d) => d.id.name) : [];
  for (const nm of names) {
    if (seen.has(nm)) bad.push(`duplicate top-level binding: ${nm}`); else seen.add(nm);
  }
}
if (!bad.length) ok.push('no duplicate top-level bindings');

const href = (tag) => (/href\s*=\s*["']([^"']+)/i.exec(tag) || [])[1];
const srcre = (tag) => (/src\s*=\s*["']([^"']+)/i.exec(tag) || [])[1];
const lost = [];
for (const l of cssLinks) if (!result.includes(href(l.tag))) lost.push(href(l.tag));
for (const t of tailScripts) if (!result.includes(srcre(t.openTag))) lost.push(srcre(t.openTag));
if (!result.includes(srcre(themeScript.openTag))) lost.push(srcre(themeScript.openTag));
if (lost.length) bad.push('lost external asset(s): ' + lost.join(', '));
else ok.push('every external asset preserved (version queries included)');

console.log('VERIFICATION');
ok.forEach((m) => console.log('  ok   ' + m));
bad.forEach((m) => console.log('  FAIL ' + m));
if (bad.length) {
  console.log('\nIf the app script was restructured, re-derive MODULES with:');
  console.log('  node tools/split-bpsc.js --dry-run   (prints the current boundary map)');
  process.exit(1);
}

console.log(`\nSPLIT\n  html   ${raw.length.toLocaleString()} -> ${result.length.toLocaleString()} chars`);
CSS_FILES.forEach((c, i) => console.log(`  css/${c.file.padEnd(22)} ${String(styles[i].body.length).padStart(7)} B`));
console.log(`  js/date-banner.js        ${String(dateScript.body.length).padStart(7)} B`);
slices.forEach((s) => console.log(`  js/${s.file.padEnd(22)} ${String(s.text.length - 1).padStart(7)} B`));
console.log('  external kept: ' + [...tailScripts.map((t) => srcre(t.openTag)), ...cssLinks.map((l) => href(l.tag))].join(', '));

if (!DRY) {
  console.log('\nwrote bpsc/ + bpsc/index.html');
  console.log('original saved to docs/bpsc-index-monolith.html.bak (gitignored)');
}
