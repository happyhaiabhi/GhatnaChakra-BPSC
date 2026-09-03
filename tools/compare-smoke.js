#!/usr/bin/env node
/*
 * Compare two tools/bpsc-smoke.js reports.
 *
 *   node tools/compare-smoke.js /tmp/before.json /tmp/after.json
 *
 * Structural fields (how the page is assembled) are reported as CHANGED and
 * expected to differ after a split. Every behavioural field must be IDENTICAL;
 * any difference is a regression and exits non-zero.
 */
const fs = require('fs');

const A = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const B = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));

const STRUCTURAL = new Set([
  'url', 'styleTags', 'linkCss', 'scriptSrc', 'inlineScripts',
]);
const IGNORE = new Set([]);

const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

let structural = 0, same = 0, diff = 0;
const problems = [];

const keys = [...new Set([...Object.keys(A), ...Object.keys(B)])].sort();

for (const k of keys) {
  if (IGNORE.has(k)) continue;
  const a = A[k], b = B[k];
  if (eq(a, b)) { same++; continue; }
  if (STRUCTURAL.has(k)) {
    structural++;
    console.log(`  CHANGED (expected)  ${k}`);
    console.log(`      before: ${JSON.stringify(a)}`);
    console.log(`      after:  ${JSON.stringify(b)}`);
    continue;
  }
  diff++;
  problems.push(k);
  console.log(`  !! REGRESSION  ${k}`);
  console.log(`      before: ${JSON.stringify(a).slice(0, 600)}`);
  console.log(`      after:  ${JSON.stringify(b).slice(0, 600)}`);
}

console.log(`\n${same} identical · ${structural} structural change(s) · ${diff} regression(s)`);
if (diff) { console.log('FAILED: ' + problems.join(', ')); process.exit(1); }
console.log('PASS — behaviour is identical, only the file layout changed.');
