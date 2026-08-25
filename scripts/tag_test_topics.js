#!/usr/bin/env node
/**
 * Tag every question in the KGS "प्रहार" test-series files (books/kgs_test_series)
 * with a sub-topic, e.g. Test 1 (Bihar Special) -> Ancient Bihar / Rivers & Lakes /
 * Minerals / Census ... so the app can show topic-wise breakdowns and practice.
 *
 * - Matching is done on question + options + explanation text (first rule wins).
 * - Questions keep their position and fields; only `topic` is added/updated.
 * - Idempotent: re-running simply re-tags.
 *
 * Usage: node scripts/tag_test_topics.js [--report-only]
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DIR = path.join(ROOT, 'books/kgs_test_series/data');
const reportOnly = process.argv.includes('--report-only');
const leftovers = (process.argv.find(a=>a.startsWith('--leftovers='))||'').split('=')[1];

// ─── Rule tables ─────────────────────────────────────────────────────────────
// Each rule: [topic, regex]. Rules are checked in order; FIRST match wins, so
// put the most specific topics at the top and broad catch-alls at the bottom.
// The haystack is `question + option values + explanation` (lower-cased).
const { RULES, TOPIC_EMOJI } = require('./topic_rules.js');



function hay(q, full) {
  const parts=[q.q,q.question,q.stem,Object.values(q.options||{}).join(' ')];
  if(full)parts.push(q.explanation,q.note);
  return parts.filter(Boolean).join(' ').toLowerCase();
}

const tag = (q, rules) => {
  // Pass 1: question + options only (highest precision). Pass 2: add explanation.
  for (const full of [false, true]) {
    const h = hay(q, full);
    for (const [topic, rx] of rules) if (rx.test(h)) return topic;
  }
  return 'General';
};

// ─── Main ────────────────────────────────────────────────────────────────────
const files = fs.readdirSync(DIR).filter(f => /^test_\d+\.json$/.test(f)).sort((a, b) => parseInt(a.match(/\d+/)) - parseInt(b.match(/\d+/)));
const summary = [];
for (const file of files) {
  const full = path.join(DIR, file);
  const data = JSON.parse(fs.readFileSync(full, 'utf8'));
  const rules = RULES[path.basename(file, '.json')] || [];
  const counts = {};
  for (const ch of data.chapters || []) {
    for (const q of ch.questions || []) {
      const topic = rules.length ? tag(q, rules) : 'General';
      if (!reportOnly) q.topic = topic;
      if(leftovers && topic==='General' && path.basename(file,'.json')===leftovers) console.log('  GEN', q.q.slice(0,120));
      counts[topic] = (counts[topic] || 0) + 1;
    }
  }
  if (!reportOnly) fs.writeFileSync(full, JSON.stringify(data, null, 2) + '\n', 'utf8');
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  summary.push({ file, subject: data.subject, total, entries });
}

for (const s of summary) {
  const general = (s.entries.find(([t]) => t === 'General') || ['General', 0])[1];
  const pct = Math.round((s.total - general) / s.total * 100);
  console.log(`\n== ${s.subject} — ${s.total} Q, ${pct}% tagged, ${general} General ==`);
  console.log('   ' + s.entries.map(([t, n]) => `${TOPIC_EMOJI[t] || ''}${t} ${n}`).join(' · '));
}
