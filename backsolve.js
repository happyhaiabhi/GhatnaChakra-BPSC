/* PYQ Back-solve viewer.
   Reads data/pyq_backsolve_summary.json plus one data/pyq_backsolve/<DS>_<year>.json
   per paper, so the browser only downloads the paper being looked at. */
(function () {
  'use strict';

  var SUMMARY_URL = 'data/pyq_backsolve_summary.json';
  var TIERS = ['strict', 'medium', 'recurring', 'loose', 'novel', 'passage'];
  var TIER_LABEL = {
    strict: 'directly answerable',
    medium: 'concept seen before',
    recurring: 'topic recurs',
    loose: 'weak overlap',
    novel: 'nothing earlier',
    passage: 'comprehension passage'
  };
  var DATASETS = [
    { id: 'GS', label: 'Prelims GS I' },
    { id: 'CSAT', label: 'CSAT II' },
    { id: 'MAINS', label: 'Mains' }
  ];

  var state = {
    summary: null,
    yearData: {},
    dataset: 'GS',
    year: null,
    tier: 'all',
    subject: 'all',
    query: '',
    showAnswers: false
  };

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function pct(n) { return (Math.round(n * 10) / 10) + '%'; }

  function yearsFor(ds) {
    if (!state.summary) return [];
    return state.summary.summary
      .filter(function (r) { return r.dataset === ds; })
      .map(function (r) { return r.year; })
      .sort(function (a, b) { return a - b; });
  }
  function rowFor(ds, year) {
    if (!state.summary) return null;
    return state.summary.summary.filter(function (r) {
      return r.dataset === ds && r.year === year;
    })[0] || null;
  }
  function subjectsFor(ds, year) {
    var data = state.yearData[ds + '_' + year];
    if (!data) return [];
    var seen = {};
    data.questions.forEach(function (q) { seen[q.subject || 'untagged'] = 1; });
    return Object.keys(seen).sort();
  }

  /* ------------------------------------------------------------------ load */
  function loadJson(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + ' -> HTTP ' + r.status);
      return r.json();
    });
  }

  function loadYear(ds, year, cb) {
    var key = ds + '_' + year;
    if (state.yearData[key]) { cb(null, state.yearData[key]); return; }
    loadJson('data/pyq_backsolve/' + key + '.json').then(function (data) {
      state.yearData[key] = data;
      cb(null, data);
    }).catch(function (e) { cb(e, null); });
  }

  /* -------------------------------------------------------------- controls */
  function renderDatasetTabs() {
    var box = $('bsDatasets');
    box.innerHTML = '';
    DATASETS.forEach(function (ds) {
      var b = el('button', 'bs-tab', ds.label);
      b.type = 'button';
      b.setAttribute('aria-pressed', String(state.dataset === ds.id));
      b.addEventListener('click', function () {
        state.dataset = ds.id;
        state.subject = 'all';
        var ys = yearsFor(ds.id);
        state.year = ys[ys.length - 1];
        renderAll(true);
      });
      box.appendChild(b);
    });
  }

  function renderYears() {
    var box = $('bsYears');
    box.innerHTML = '';
    yearsFor(state.dataset).forEach(function (y) {
      var b = el('button', 'bs-year', String(y));
      b.type = 'button';
      b.setAttribute('aria-pressed', String(state.year === y));
      b.addEventListener('click', function () {
        state.year = y;
        renderAll(true);
      });
      box.appendChild(b);
    });
  }

  function renderFilters() {
    var ts = $('bsTiers');
    ts.innerHTML = '';
    var opts = [{ id: 'all', label: 'All questions' },
                { id: 'solvable', label: 'PYQ-solvable only' },
                { id: 'gap', label: 'Blind spots (not solvable)' }].concat(
      TIERS.map(function (t) { return { id: t, label: TIER_LABEL[t] }; }));
    opts.forEach(function (o) {
      var b = el('button', 'bs-tab', o.label);
      b.type = 'button';
      b.setAttribute('aria-pressed', String(state.tier === o.id));
      b.addEventListener('click', function () { state.tier = o.id; renderAll(false); });
      ts.appendChild(b);
    });

    var ss = $('bsSubject');
    var keep = state.subject;
    ss.innerHTML = '';
    var all = el('option', null, 'All subjects');
    all.value = 'all';
    ss.appendChild(all);
    subjectsFor(state.dataset, state.year).forEach(function (s) {
      var o = el('option', null, s);
      o.value = s;
      ss.appendChild(o);
    });
    ss.value = subjectsFor(state.dataset, state.year).indexOf(keep) >= 0 ? keep : 'all';
    state.subject = ss.value;
  }

  /* ------------------------------------------------------------ stat strip */
  function renderStats() {
    var row = rowFor(state.dataset, state.year);
    var box = $('bsStats');
    box.innerHTML = '';
    $('bsPaperTitle').textContent = state.dataset + ' ' + state.year +
      ' — what earlier papers already taught';
    if (!row) return;
    var items = [
      { cls: 'strict', v: row.strict_pct + '%', l: 'verbatim repeat or decisive concept' },
      { cls: 'medium', v: row.medium_pct + '%', l: 'PYQ-solvable (strict + concept)' },
      { cls: 'recurring', v: row.recurring_pct + '%', l: 'topic already seen in PYQs' },
      { cls: 'novel', v: (100 - row.loose_pct).toFixed(0) + '%', l: 'no earlier concept at all' },
      { cls: '', v: row.verbatim_repeats, l: 'verbatim repeats of earlier papers' }
    ];
    if (row.passages) {
      items.push({ cls: 'passage', v: row.passages,
                   l: 'comprehension passages, not scored' });
    }
    items.forEach(function (it) {
      var d = el('div', 'bs-stat ' + it.cls);
      d.appendChild(el('b', null, String(it.v)));
      d.appendChild(el('span', null, it.l));
      box.appendChild(d);
    });

    var bar = $('bsBar');
    bar.innerHTML = '';
    TIERS.forEach(function (t) {
      var n = row[t];
      if (!n) return;
      var i = el('i', t);
      i.style.width = (100 * n / row.questions) + '%';
      i.title = t + ': ' + n;
      bar.appendChild(i);
    });
    var legend = $('bsLegend');
    legend.innerHTML = '';
    TIERS.forEach(function (t) {
      if (!row[t]) return;
      var s = el('span');
      var b = el('b'); b.style.background = 'var(--' + t + ')';
      s.appendChild(b);
      s.appendChild(document.createTextNode(TIER_LABEL[t] + ' — ' + (row[t] || 0)));
      legend.appendChild(s);
    });
  }

  /* --------------------------------------------------------------- listing */
  function visibleQuestions(data) {
    if (!data) return [];
    var q = state.query.trim().toLowerCase();
    return data.questions.filter(function (item) {
      if (state.subject !== 'all' && (item.subject || 'untagged') !== state.subject) return false;
      if (state.tier === 'solvable' && item.tier !== 'strict' && item.tier !== 'medium') return false;
      if (state.tier === 'gap' && (item.tier === 'strict' || item.tier === 'medium')) return false;
      if (TIERS.indexOf(state.tier) >= 0 && item.tier !== state.tier) return false;
      if (q) {
        var hay = (item.text + ' ' + (item.answer || '')).toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });
  }

  function matchRow(mt) {
    var rowEl = el('div', 'bs-match');
    rowEl.appendChild(el('div', 'bs-match-yr',
      mt.year + (mt.dataset !== state.dataset ? ' ' + mt.dataset : '')));
    var body = el('div', 'bs-match-body');
    body.appendChild(el('p', 'bs-match-text', mt.text));
    if (mt.ent) {
      var e = el('p', 'bs-match-ent');
      e.appendChild(document.createTextNode('shared concept '));
      e.appendChild(el('code', null, mt.ent));
      if (mt.pri && mt.pri !== mt.ent) {
        e.appendChild(document.createTextNode(' ~ '));
        e.appendChild(el('code', null, mt.pri));
      }
      body.appendChild(e);
    }
    if (mt.answer) body.appendChild(el('p', 'bs-match-ans', 'answer: ' + mt.answer));
    rowEl.appendChild(body);
    return rowEl;
  }

  function renderQuestions(data) {
    var box = $('bsList');
    box.innerHTML = '';
    var list = visibleQuestions(data);
    var count = el('p', 'bs-note');
    count.textContent = list.length + ' of ' + (data ? data.questions.length : 0) +
      ' questions shown.';
    box.appendChild(count);

    list.forEach(function (item, idx) {
      var card = el('div', 'bs-q');
      var head = el('div', 'bs-q-head');
      head.appendChild(el('span', 'bs-q-no', '#' + (idx + 1)));
      var badge = el('span', 'bs-badge ' + item.tier, item.tier);
      badge.title = TIER_LABEL[item.tier] || '';
      head.appendChild(badge);
      head.appendChild(el('span', 'bs-badge subj', item.subject || 'untagged'));
      var cov = el('span', 'bs-cov',
        'coverage ' + (item.cov_flat != null ? item.cov_flat : '-') +
        ' · 20y-weight ' + (item.cov_cliff != null ? item.cov_cliff : '-') +
        ' · decay ' + (item.cov_decay != null ? item.cov_decay : '-'));
      cov.title = 'Share of this question’s concepts that earlier papers cover';
      head.appendChild(cov);
      card.appendChild(head);

      card.appendChild(el('p', 'bs-q-text', item.text));

      if (item.answer) {
        var a = el('p', 'bs-answer');
        a.appendChild(document.createTextNode('Correct answer: '));
        a.appendChild(el('b', null, item.answer));
        card.appendChild(a);
      }

      if (item.matches && item.matches.length) {
        var same = item.matches.filter(function (m) { return m.dataset === state.dataset; });
        var cross = item.matches.filter(function (m) { return m.dataset !== state.dataset; });

        var m = el('div', 'bs-matches');
        if (same.length) {
          m.appendChild(el('h4', null, 'From earlier ' + state.dataset + ' papers'));
          same.slice(0, 5).forEach(function (mt) { m.appendChild(matchRow(mt)); });
        }
        if (cross.length) {
          m.appendChild(el('h4', null, 'Also in ' + cross[0].dataset + ' papers (weaker evidence)'));
          cross.slice(0, 3).forEach(function (mt) { m.appendChild(matchRow(mt)); });
        }
        if (item.topic_words && item.topic_words.length && !same.length) {
          var tw = el('p', 'bs-match-ent');
          tw.appendChild(document.createTextNode('Shared topic words only: '));
          item.topic_words.slice(0, 3).forEach(function (w, i) {
            if (i) tw.appendChild(document.createTextNode(', '));
            tw.appendChild(el('code', null, w.word + ' (' + w.years.join(', ') + ')'));
          });
          m.appendChild(tw);
        }
        card.appendChild(m);
      }

      box.appendChild(card);
    });
    if (!list.length) box.appendChild(el('div', 'bs-empty', 'No questions match these filters.'));
  }

  /* ---------------------------------------------------------------- panels */
  function renderTrend() {
    var box = $('bsTrendBody');
    box.innerHTML = '';
    var rows = state.summary.summary.filter(function (r) { return r.dataset === state.dataset; });
    var t = el('table', 'bs-table');
    var head = el('tr');
    ['Year', 'Q', 'Strict', 'Solvable', 'Topic seen', 'Nothing', 'Mean coverage'].forEach(function (h, i) {
      var th = el('th', i >= 2 ? 'num' : null, h);
      head.appendChild(th);
    });
    t.appendChild(head);
    rows.forEach(function (r) {
      var tr = el('tr');
      tr.appendChild(el('td', null, String(r.year)));
      tr.appendChild(el('td', 'num', String(r.questions)));
      tr.appendChild(el('td', 'num', r.strict_pct + '%'));
      tr.appendChild(el('td', 'num', r.medium_pct + '%'));
      tr.appendChild(el('td', 'num', r.recurring_pct + '%'));
      tr.appendChild(el('td', 'num', (100 - r.loose_pct).toFixed(0) + '%'));
      tr.appendChild(el('td', 'num', String(r.mean_cov_cliff)));
      if (r.year === state.year) tr.style.fontWeight = '700';
      t.appendChild(tr);
    });
    box.appendChild(t);
  }

  function renderOptimizer() {
    var box = $('bsOptBody');
    box.innerHTML = '';
    var opt = state.summary.optimizer && state.summary.optimizer[state.dataset];
    var opt20 = state.summary.optimizer && state.summary.optimizer[state.dataset + '_20y'];
    if (!opt) { box.appendChild(el('p', 'bs-note', 'Not computed for this dataset.')); return; }

    var picks = (opt.by_year || {})[String(state.year)] || [];
    var picks20 = (opt20 && opt20.by_year || {})[String(state.year)] || [];
    var p = el('p', 'bs-note');
    p.innerHTML = 'For <b>' + state.year + '</b> the greedy pick of earlier papers is: <b>' +
      picks.join(', ') + '</b>. Restricted to the most recent 20 years only: <b>' +
      picks20.join(', ') + '</b>.';
    box.appendChild(p);

    var t = el('table', 'bs-table');
    var head = el('tr');
    ['Papers solved (k)', 'Any earlier paper', 'Last 20 years only'].forEach(function (h, i) {
      head.appendChild(el('th', i ? 'num' : null, h));
    });
    t.appendChild(head);
    var n = Math.max((opt.curve_pct || []).length, (opt20 && opt20.curve_pct || []).length);
    for (var i = 0; i < n; i++) {
      var a = (opt.curve_pct || [])[i];
      var b = opt20 && (opt20.curve_pct || [])[i];
      if (a == null && b == null) continue;
      var tr = el('tr');
      tr.appendChild(el('td', null, String(i + 1)));
      tr.appendChild(el('td', 'num', a == null ? '—' : a + '%'));
      tr.appendChild(el('td', 'num', b == null ? '—' : b + '%'));
      t.appendChild(tr);
    }
    box.appendChild(t);

    var cap = el('p', 'bs-note');
    cap.textContent = 'Ceiling: even solving every earlier paper reaches only ' +
      opt.ceiling_pct + '% of a paper at concept level (' +
      (opt20 ? opt20.ceiling_pct : '?') + '% within a 20-year window) — the rest has to come ' +
      'from somewhere other than old papers. This is a backtest: only papers published before ' +
      'the target year are eligible, so nothing peeks ahead.';
    box.appendChild(cap);

    var mp = el('table', 'bs-table');
    var h2 = el('tr');
    h2.appendChild(el('th', null, 'Most frequently picked paper (last 20 years)'));
    h2.appendChild(el('th', 'num', 'Times picked'));
    mp.appendChild(h2);
    ((opt20 && opt20.most_picked) || []).forEach(function (pair) {
      var tr = el('tr');
      tr.appendChild(el('td', null, String(pair[0])));
      tr.appendChild(el('td', 'num', String(pair[1])));
      mp.appendChild(tr);
    });
    box.appendChild(mp);
  }

  function renderFeeders() {
    var box = $('bsFeedBody');
    box.innerHTML = '';
    var key = state.dataset + ' ' + state.year;
    var feed = (state.summary.feeders || {})[key] || [];
    if (!feed.length) { box.appendChild(el('p', 'bs-note', 'No feeder data.')); return; }
    var p = el('p', 'bs-note');
    p.textContent = 'Which earlier papers contribute the most shared concepts to ' +
      state.dataset + ' ' + state.year + ':';
    box.appendChild(p);
    var t = el('table', 'bs-table');
    var head = el('tr');
    head.appendChild(el('th', null, 'Earlier paper'));
    head.appendChild(el('th', 'num', 'Shared concepts'));
    t.appendChild(head);
    feed.forEach(function (pair) {
      var tr = el('tr');
      tr.appendChild(el('td', null, String(pair[0])));
      tr.appendChild(el('td', 'num', String(pair[1])));
      t.appendChild(tr);
    });
    box.appendChild(t);
  }

  function renderAge() {
    var box = $('bsAgeBody');
    box.innerHTML = '';
    var curve = (state.summary.age_curve || {})[state.dataset];
    if (!curve) return;
    var keys = Object.keys(curve).sort(function (a, b) { return a - b; });
    var max = Math.max.apply(null, keys.map(function (k) { return curve[k]; }));
    var chart = el('div', 'bs-age');
    var axis = el('div', 'bs-age-axis');
    keys.forEach(function (k) {
      var bar = el('div');
      bar.style.height = Math.max(2, Math.round(100 * curve[k] / max)) + '%';
      bar.title = k + ' year(s) before: ' + curve[k] + ' shared concepts';
      chart.appendChild(bar);
      var s = el('span', null, (k % 5 === 0 || k === '1') ? k + 'y' : '');
      axis.appendChild(s);
    });
    box.appendChild(chart);
    box.appendChild(axis);
    box.appendChild(el('p', 'bs-note',
      'Shared concepts by the age of the earlier paper. The recent end carries far more weight, ' +
      'which is why the score downweights anything older than 20 years.'));
  }

  function renderMethod() {
    var s = state.summary;
    var box = $('bsMethodBody');
    box.innerHTML = '';
    var tiers = s.tiers || {};
    var t = el('table', 'bs-table');
    var head = el('tr');
    head.appendChild(el('th', null, 'Tier'));
    head.appendChild(el('th', null, 'What it means'));
    t.appendChild(head);
    TIERS.forEach(function (k) {
      var tr = el('tr');
      tr.appendChild(el('td', null, k));
      tr.appendChild(el('td', null, tiers[k] || ''));
      t.appendChild(tr);
    });
    box.appendChild(t);
    var meta = s.meta || {};
    var p = el('p', 'bs-note');
    p.innerHTML = 'Corpus: <b>' + (meta.corpus ? meta.corpus.documents : '?') +
      '</b> questions (' + (meta.scope || []).join(', ').toUpperCase() +
      '). Pool for a target year: every question published <b>before</b> it. ' +
      'Generated ' + (meta.generated_at || '') + '.';
    box.appendChild(p);
  }

  /* ------------------------------------------------------------------ wire */
  function renderAll(reloadYear) {
    renderDatasetTabs();
    renderYears();
    var after = function (err, data) {
      renderFilters();
      renderStats();
      if (err) {
        var box = $('bsList');
        box.innerHTML = '';
        box.appendChild(el('div', 'bs-error',
          'Could not load data/pyq_backsolve/' + state.dataset + '_' + state.year +
          '.json (' + err.message + '). Serve the folder over HTTP, e.g. ' +
          'python -m http.server 8000.'));
        return;
      }
      renderQuestions(data);
      renderTrend();
      renderOptimizer();
      renderFeeders();
      renderAge();
      renderMethod();
    };
    if (reloadYear || !state.yearData[state.dataset + '_' + state.year]) {
      loadYear(state.dataset, state.year, after);
    } else {
      after(null, state.yearData[state.dataset + '_' + state.year]);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    $('bsQuery').addEventListener('input', function (e) {
      state.query = e.target.value;
      renderQuestions(state.yearData[state.dataset + '_' + state.year]);
    });
    $('bsSubject').addEventListener('change', function (e) {
      state.subject = e.target.value;
      renderQuestions(state.yearData[state.dataset + '_' + state.year]);
    });
    document.querySelectorAll('.bs-panel > h2.bs-acc').forEach(function (h) {
      h.addEventListener('click', function () {
        var body = h.nextElementSibling;
        var hidden = body.hasAttribute('hidden');
        if (hidden) body.removeAttribute('hidden'); else body.setAttribute('hidden', '');
        h.setAttribute('aria-expanded', String(hidden));
      });
    });

    loadJson(SUMMARY_URL).then(function (s) {
      state.summary = s;
      var ys = yearsFor(state.dataset);
      state.year = ys[ys.length - 1];
      renderAll(true);
    }).catch(function (e) {
      $('bsStats').innerHTML = '';
      var box = $('bsList');
      box.innerHTML = '';
      box.appendChild(el('div', 'bs-error',
        'Could not load ' + SUMMARY_URL + ' (' + e.message +
        '). Run "python scripts/pyq_backsolve.py" first, and open this page over HTTP ' +
        '(python -m http.server 8000), not from the filesystem.'));
    });
  });
})();
