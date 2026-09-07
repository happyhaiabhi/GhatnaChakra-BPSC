/* BPSC Complete PYQ Revision — GhatnaChakra-style UI */
(function () {
  'use strict';

  const STORAGE_KEY = 'bpsc_all_pyq_v1';
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  let DATA = null;
  let state = {
    screen: 'books',
    subjectId: null,
    mode: 'practice', // practice | quiz | revise
    selectedChapters: new Set(),
    session: null, // { qs, idx, answers, startTs, timerId, revealed }
  };

  function loadProgress() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch {
      return {};
    }
  }
  function saveProgress(p) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
  }
  function getProg() {
    const p = loadProgress();
    if (!p.subjects) p.subjects = {};
    if (!p.bookmarks) p.bookmarks = {};
    if (!p.history) p.history = [];
    return p;
  }
  function qKey(q) {
    return `${q.exam}::${q.q_no}::${(q.stem || '').slice(0, 40)}`;
  }
  function ensureSubj(p, sid) {
    if (!p.subjects[sid]) {
      p.subjects[sid] = { answered: {}, wrongs: {}, correct: {}, seen: {} };
    }
    return p.subjects[sid];
  }

  function getSubject(id) {
    return DATA.subjects.find((s) => s.id === id);
  }
  function allQuestions(subj) {
    const out = [];
    for (const st of subj.subtopics || []) {
      for (const q of st.questions || []) {
        out.push({ ...q, _subtopic: st.name, _subtopicId: st.id, _subjectId: subj.id, _subject: subj.name });
      }
    }
    return out;
  }
  function chapterQuestions(subj, chapterId) {
    const st = (subj.subtopics || []).find((x) => x.id === chapterId);
    if (!st) return [];
    return (st.questions || []).map((q) => ({
      ...q,
      _subtopic: st.name,
      _subtopicId: st.id,
      _subjectId: subj.id,
      _subject: subj.name,
    }));
  }

  function pct(n, d) {
    if (!d) return 0;
    return Math.round((n / d) * 100);
  }
  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  /* ---------- screens ---------- */
  function showScreen(id) {
    $$('.screen').forEach((el) => el.classList.remove('active'));
    const sc = document.getElementById(id);
    if (sc) sc.classList.add('active');
    state.screen = id.replace('-screen', '');
    window.scrollTo(0, 0);
  }

  window.showBooks = function () {
    stopTimer();
    state.session = null;
    renderBooks();
    showScreen('books-screen');
  };
  window.showPlanScreen = function () {
    renderPlan();
    showScreen('plan-screen');
  };
  window.backToSetup = function () {
    stopTimer();
    state.session = null;
    if (state.subjectId) window.openSubject(state.subjectId);
    else window.showBooks();
  };

  /* ---------- books ---------- */
  function subjectStats(subj) {
    const p = getProg();
    const sp = ensureSubj(p, subj.id);
    const total = subj.count || 0;
    const correct = Object.keys(sp.correct || {}).length;
    const wrong = Object.keys(sp.wrongs || {}).length;
    const answered = Object.keys(sp.answered || {}).length;
    return { total, correct, wrong, answered, progress: pct(answered, total) };
  }

  function renderBooks() {
    const grid = $('#books-grid');
    const banner = $('#books-progress-banner');
    const pills = $('#plan-pills');
    const subjects = [...DATA.subjects].sort((a, b) => a.priority - b.priority);

    let totalAns = 0,
      totalQ = 0,
      totalCorrect = 0;
    subjects.forEach((s) => {
      const st = subjectStats(s);
      totalAns += st.answered;
      totalQ += st.total;
      totalCorrect += st.correct;
    });
    banner.textContent = `Overall progress: ${totalAns} / ${totalQ} attempted · ${totalCorrect} correct · ${pct(totalAns, totalQ)}% covered`;

    pills.innerHTML = subjects
      .map(
        (s) =>
          `<button class="plan-pill" style="border-left:3px solid ${s.accent}" onclick="openSubject('${s.id}')">P${s.priority} ${escapeHtml(s.name)} · ${s.count}</button>`
      )
      .join('');

    grid.innerHTML = subjects
      .map((s) => {
        const st = subjectStats(s);
        return `
        <article class="book-card no-cover" style="--book-accent:${s.accent}" onclick="openSubject('${s.id}')" role="button" tabindex="0">
          <div class="book-top">
            <div class="book-cover-frame">
              <span class="book-emoji book-emoji-fallback">${s.emoji || '📘'}</span>
            </div>
            <div class="book-top-info">
              <span class="book-pill">P${s.priority} · ${escapeHtml(s.code || 'BPSC')}</span>
              <div class="book-title">${escapeHtml(s.name)}</div>
              <div class="book-subtitle">${escapeHtml(s.weight_note || '')}</div>
            </div>
          </div>
          <div class="book-desc">${escapeHtml((s.books || '').split(';')[0] || 'PYQ practice book')}</div>
          <div class="book-stats">
            <span class="book-stat"><b>${s.count}</b> Qs</span>
            <span class="book-stat"><b>${st.answered}</b> done</span>
            <span class="book-stat"><b>${st.progress}%</b> covered</span>
            <span class="book-stat"><b>${st.correct}</b> ✓</span>
          </div>
          <div class="book-progress-bar"><div class="book-progress-fill" style="width:${st.progress}%;background:${s.accent}"></div></div>
          <div class="book-open">Open book →</div>
        </article>`;
      })
      .join('');
  }

  /* ---------- setup / chapters ---------- */
  window.openSubject = function (id) {
    const subj = getSubject(id);
    if (!subj) return;
    state.subjectId = id;
    state.mode = 'practice';
    state.selectedChapters = new Set((subj.subtopics || []).map((c) => c.id));

    const p = getProg();
    const sp = ensureSubj(p, id);
    const st = subjectStats(subj);

    $('#nav-book-tag').textContent = `P${subj.priority} · ${subj.code || 'BPSC'}`;
    $('#nav-book-name').textContent = subj.name;
    $('#mistake-badge').textContent = Object.keys(sp.wrongs || {}).length;
    $('#bookmark-badge').textContent = Object.keys(p.bookmarks || {}).filter((k) => {
      const b = p.bookmarks[k];
      return b && b.subjectId === id;
    }).length;

    $('#setup-hero').innerHTML = `
      <h2>${subj.emoji || ''} ${escapeHtml(subj.name)}</h2>
      <p>${escapeHtml(subj.weight_note || '')}</p>
      <p style="margin-top:6px"><strong>Books:</strong> ${escapeHtml(subj.books || '—')} · <strong>NCERT:</strong> ${escapeHtml(subj.ncert || '—')}</p>
      <div class="hero-stats">
        <div class="hs"><b>${subj.count}</b> questions</div>
        <div class="hs"><b>${(subj.subtopics || []).length}</b> chapters</div>
        <div class="hs"><b>${st.answered}</b> attempted</div>
        <div class="hs"><b>${st.correct}</b> correct</div>
        <div class="hs"><b>${st.wrong}</b> mistakes</div>
        <div class="hs"><b>${st.progress}%</b> covered</div>
      </div>`;

    $$('#setup-mode button').forEach((b) => b.classList.toggle('on', b.dataset.mode === 'practice'));
    renderChapters();
    updateStartMeta();
    showScreen('setup-screen');
  };

  window.setMode = function (mode, btn) {
    state.mode = mode;
    $$('#setup-mode button').forEach((b) => b.classList.remove('on'));
    if (btn) btn.classList.add('on');
    const labels = { practice: 'Start Practice →', quiz: 'Start Quiz →', revise: 'Revise Wrongs →' };
    $('#start-btn').textContent = labels[mode] || 'Start →';
    updateStartMeta();
  };

  window.selectAllChapters = function (on) {
    const subj = getSubject(state.subjectId);
    if (!subj) return;
    if (on) state.selectedChapters = new Set((subj.subtopics || []).map((c) => c.id));
    else state.selectedChapters = new Set();
    renderChapters();
    updateStartMeta();
  };

  function toggleChapter(id) {
    if (state.selectedChapters.has(id)) state.selectedChapters.delete(id);
    else state.selectedChapters.add(id);
    renderChapters();
    updateStartMeta();
  }

  function renderChapters() {
    const subj = getSubject(state.subjectId);
    if (!subj) return;
    const p = getProg();
    const sp = ensureSubj(p, subj.id);
    const list = $('#chapters-list');

    list.innerHTML = (subj.subtopics || [])
      .map((ch) => {
        const qs = ch.questions || [];
        let done = 0,
          right = 0;
        qs.forEach((q) => {
          const k = qKey(q);
          if (sp.answered[k]) done++;
          if (sp.correct[k]) right++;
        });
        const prog = pct(done, qs.length);
        const sel = state.selectedChapters.has(ch.id);
        return `
        <div class="chapter-card ${sel ? 'selected' : ''}" data-ch="${escapeHtml(ch.id)}">
          <div class="chapter-check" data-toggle="${escapeHtml(ch.id)}">✓</div>
          <div class="chapter-body" data-toggle="${escapeHtml(ch.id)}">
            <div class="chapter-title">${escapeHtml(ch.name)}</div>
            <div class="chapter-meta">
              <span>${qs.length} Qs</span>
              <span>${done} done</span>
              <span>${right} ✓</span>
              <span>${prog}%</span>
            </div>
            <div class="chapter-bar"><div class="chapter-fill" style="width:${prog}%;background:${subj.accent}"></div></div>
          </div>
          <button class="chapter-quiz-btn" data-solo="${escapeHtml(ch.id)}">Quiz only</button>
        </div>`;
      })
      .join('');

    list.onclick = (e) => {
      const solo = e.target.closest('[data-solo]');
      if (solo) {
        e.stopPropagation();
        state.selectedChapters = new Set([solo.dataset.solo]);
        state.mode = 'quiz';
        $$('#setup-mode button').forEach((b) => b.classList.toggle('on', b.dataset.mode === 'quiz'));
        $('#start-btn').textContent = 'Start Quiz →';
        renderChapters();
        updateStartMeta();
        window.startSession();
        return;
      }
      const t = e.target.closest('[data-toggle]');
      if (t) toggleChapter(t.dataset.toggle);
    };
  }

  function selectedQuestions() {
    const subj = getSubject(state.subjectId);
    if (!subj) return [];
    let qs = [];
    for (const id of state.selectedChapters) {
      qs = qs.concat(chapterQuestions(subj, id));
    }
    if (state.mode === 'revise') {
      const p = getProg();
      const sp = ensureSubj(p, subj.id);
      qs = qs.filter((q) => sp.wrongs[qKey(q)]);
    }
    return qs;
  }

  function updateStartMeta() {
    const qs = selectedQuestions();
    const nCh = state.selectedChapters.size;
    let note = `${nCh} chapter${nCh === 1 ? '' : 's'} · ${qs.length} questions`;
    if (state.mode === 'revise' && qs.length === 0) note += ' · no mistakes in selection yet';
    $('#start-meta').textContent = note;
    $('#start-btn').disabled = qs.length === 0;
  }

  /* ---------- session / quiz ---------- */
  window.startSession = function () {
    let qs = selectedQuestions();
    if (!qs.length) {
      alert(state.mode === 'revise' ? 'No wrong answers in the selected chapters yet.' : 'Select at least one chapter.');
      return;
    }
    // shuffle lightly for quiz mode
    if (state.mode === 'quiz') {
      qs = [...qs].sort(() => Math.random() - 0.5);
    }
    state.session = {
      qs,
      idx: 0,
      answers: {}, // key -> { chosen, correct, skipped }
      startTs: Date.now(),
      timerId: null,
      revealed: {},
      mode: state.mode,
      subjectId: state.subjectId,
    };
    startTimer();
    renderQuiz();
    showScreen('quiz-screen');
  };

  function startTimer() {
    stopTimer();
    const tick = () => {
      if (!state.session) return;
      const sec = Math.floor((Date.now() - state.session.startTs) / 1000);
      const el = $('#q-timer');
      if (el) el.textContent = formatTime(sec);
    };
    tick();
    state.session.timerId = setInterval(tick, 1000);
  }
  function stopTimer() {
    if (state.session && state.session.timerId) {
      clearInterval(state.session.timerId);
      state.session.timerId = null;
    }
  }

  window.confirmExitQuiz = function () {
    if (!state.session) return window.showBooks();
    if (confirm('Exit this session? Progress on answered questions is already saved.')) {
      finishSession(false);
    }
  };

  window.togglePalette = function () {
    $('#palette-drawer').classList.toggle('hidden');
  };

  window.toggleBookmark = function () {
    if (!state.session) return;
    const q = state.session.qs[state.session.idx];
    if (!q) return;
    const p = getProg();
    const k = qKey(q);
    if (p.bookmarks[k]) delete p.bookmarks[k];
    else
      p.bookmarks[k] = {
        subjectId: q._subjectId,
        exam: q.exam,
        q_no: q.q_no,
        stem: q.stem,
        answer: q.answer,
        options: q.options,
        subtopic: q._subtopic,
        at: Date.now(),
      };
    saveProgress(p);
    updateBookmarkBtn(q);
  };

  function updateBookmarkBtn(q) {
    const p = getProg();
    const on = !!p.bookmarks[qKey(q)];
    const btn = $('#btn-bookmark');
    if (btn) {
      btn.textContent = on ? '🔖✓' : '🔖';
      btn.style.color = on ? 'var(--gold)' : '';
    }
  }

  function renderQuiz() {
    const ses = state.session;
    if (!ses) return;
    const q = ses.qs[ses.idx];
    const n = ses.qs.length;
    const i = ses.idx;
    $('#q-num').textContent = `Q ${i + 1}/${n}`;
    updateBookmarkBtn(q);

    const ans = ses.answers[qKey(q)];
    const isPractice = ses.mode === 'practice' || ses.mode === 'revise';
    // Practice/revise: reveal after Check. Quiz: hide correctness until results.
    const revealed = isPractice ? !!ses.revealed[qKey(q)] : false;

    let optsHtml = (q.options || [])
      .map((o) => {
        let cls = 'opt-btn';
        if (ans && ans.chosen === o.key) cls += ' selected';
        if (revealed) {
          if (o.key === q.answer) cls += ' correct';
          else if (ans && ans.chosen === o.key && ans.chosen !== q.answer) cls += ' wrong';
        }
        return `<button class="${cls}" data-opt="${escapeHtml(o.key)}" ${revealed && isPractice ? 'disabled' : ''}>
          <span class="opt-key">${escapeHtml(o.key)}</span>
          <span class="opt-text">${escapeHtml(o.text)}</span>
        </button>`;
      })
      .join('');

    let feedback = '';
    if (revealed && ans) {
      if (ans.skipped) feedback = `<div class="feedback-line info">Skipped · Answer: ${escapeHtml(q.answer)}</div>`;
      else if (ans.correct) feedback = `<div class="feedback-line ok">Correct ✓</div>`;
      else feedback = `<div class="feedback-line bad">Incorrect · Correct answer: ${escapeHtml(q.answer)}</div>`;
    }

    $('#question-area').innerHTML = `
      <div class="q-meta-row">
        <span class="q-chip exam">${escapeHtml(q.exam || '')}</span>
        <span class="q-chip">Q.${escapeHtml(String(q.q_no))}</span>
        <span class="q-chip">${escapeHtml(q._subtopic || '')}</span>
        <span class="q-chip">${escapeHtml(q._subject || '')}</span>
      </div>
      <div class="q-text">${escapeHtml(q.stem)}</div>
      <div class="opts">${optsHtml}</div>
      ${feedback}
    `;

    $$('#question-area .opt-btn').forEach((btn) => {
      btn.addEventListener('click', () => selectOption(btn.dataset.opt));
    });

    const primary = $('#quiz-primary');
    if (isPractice) {
      if (revealed) {
        primary.textContent = i + 1 >= n ? 'Finish' : 'Next →';
        primary.onclick = () => (i + 1 >= n ? finishSession(true) : window.quizNext());
      } else {
        primary.textContent = 'Check';
        primary.onclick = () => window.quizPrimary();
      }
    } else {
      // quiz mode — no instant reveal until end, or soft reveal after select
      if (i + 1 >= n && ans) {
        primary.textContent = 'Finish';
        primary.onclick = () => finishSession(true);
      } else if (ans) {
        primary.textContent = 'Next →';
        primary.onclick = () => window.quizNext();
      } else {
        primary.textContent = 'Lock & Next';
        primary.onclick = () => window.quizPrimary();
      }
    }

    renderPalette();
  }

  function selectOption(key) {
    const ses = state.session;
    if (!ses) return;
    const q = ses.qs[ses.idx];
    const k = qKey(q);
    if (ses.revealed[k] && (ses.mode === 'practice' || ses.mode === 'revise')) return;

    // temporary selection before check
    ses._pending = key;
    // visual
    $$('#question-area .opt-btn').forEach((b) => {
      b.classList.toggle('selected', b.dataset.opt === key);
    });

    if (ses.mode === 'quiz') {
      // auto-lock on select in quiz for speed
      commitAnswer(key, false);
      renderQuiz();
    }
  }

  function commitAnswer(chosen, skipped) {
    const ses = state.session;
    if (!ses) return;
    const q = ses.qs[ses.idx];
    const k = qKey(q);
    const correct = !skipped && chosen === q.answer;
    ses.answers[k] = { chosen: skipped ? null : chosen, correct, skipped: !!skipped };
    if (ses.mode === 'practice' || ses.mode === 'revise') ses.revealed[k] = true;

    // persist
    const p = getProg();
    const sp = ensureSubj(p, q._subjectId || ses.subjectId);
    sp.answered[k] = { chosen, at: Date.now(), exam: q.exam, q_no: q.q_no };
    sp.seen[k] = true;
    if (skipped) {
      // don't mark wrong/correct
    } else if (correct) {
      sp.correct[k] = true;
      delete sp.wrongs[k];
    } else {
      sp.wrongs[k] = { chosen, answer: q.answer, stem: q.stem, exam: q.exam, q_no: q.q_no, options: q.options, subtopic: q._subtopic, at: Date.now() };
      delete sp.correct[k];
    }
    saveProgress(p);
  }

  window.quizPrimary = function () {
    const ses = state.session;
    if (!ses) return;
    const q = ses.qs[ses.idx];
    const k = qKey(q);
    const isPractice = ses.mode === 'practice' || ses.mode === 'revise';

    if (isPractice) {
      if (ses.revealed[k]) {
        window.quizNext();
        return;
      }
      const pending = ses._pending;
      if (!pending) {
        alert('Select an option first.');
        return;
      }
      commitAnswer(pending, false);
      ses._pending = null;
      renderQuiz();
      return;
    }

    // quiz
    if (!ses.answers[k]) {
      const pending = ses._pending;
      if (!pending) {
        alert('Select an option, or Skip.');
        return;
      }
      commitAnswer(pending, false);
      ses._pending = null;
    }
    if (ses.idx + 1 >= ses.qs.length) finishSession(true);
    else window.quizNext();
  };

  window.quizNext = function () {
    const ses = state.session;
    if (!ses) return;
    if (ses.idx + 1 >= ses.qs.length) {
      finishSession(true);
      return;
    }
    ses.idx++;
    ses._pending = null;
    renderQuiz();
  };
  window.quizPrev = function () {
    const ses = state.session;
    if (!ses || ses.idx <= 0) return;
    ses.idx--;
    ses._pending = null;
    renderQuiz();
  };
  window.quizSkip = function () {
    const ses = state.session;
    if (!ses) return;
    const q = ses.qs[ses.idx];
    const k = qKey(q);
    if ((ses.mode === 'practice' || ses.mode === 'revise') && ses.revealed[k]) {
      window.quizNext();
      return;
    }
    commitAnswer(null, true);
    if (ses.mode === 'quiz') {
      if (ses.idx + 1 >= ses.qs.length) finishSession(true);
      else window.quizNext();
    } else {
      renderQuiz();
    }
  };

  function renderPalette() {
    const ses = state.session;
    if (!ses) return;
    const grid = $('#palette-grid');
    grid.innerHTML = ses.qs
      .map((q, i) => {
        const k = qKey(q);
        const a = ses.answers[k];
        let cls = 'pal-btn';
        if (i === ses.idx) cls += ' current';
        if (a) {
          if (a.skipped) cls += ' skipped';
          else if (ses.mode === 'quiz' && !a.skipped) cls += ' answered';
          else if (a.correct) cls += ' right';
          else cls += ' wronged';
        }
        return `<button class="${cls}" data-i="${i}">${i + 1}</button>`;
      })
      .join('');
    grid.onclick = (e) => {
      const b = e.target.closest('[data-i]');
      if (!b) return;
      ses.idx = +b.dataset.i;
      ses._pending = null;
      renderQuiz();
    };
  }

  function finishSession(showResult) {
    const ses = state.session;
    stopTimer();
    if (!ses) {
      showBooks();
      return;
    }
    const keys = ses.qs.map(qKey);
    let correct = 0,
      wrong = 0,
      skipped = 0,
      answered = 0;
    keys.forEach((k) => {
      const a = ses.answers[k];
      if (!a) return;
      answered++;
      if (a.skipped) skipped++;
      else if (a.correct) correct++;
      else wrong++;
    });
    const total = ses.qs.length;
    const score = pct(correct, total - skipped || total);
    const elapsed = Math.floor((Date.now() - ses.startTs) / 1000);

    const p = getProg();
    p.history.unshift({
      at: Date.now(),
      subjectId: ses.subjectId,
      mode: ses.mode,
      total,
      correct,
      wrong,
      skipped,
      elapsed,
    });
    p.history = p.history.slice(0, 40);
    saveProgress(p);

    if (!showResult) {
      state.session = null;
      if (state.subjectId) window.openSubject(state.subjectId);
      else window.showBooks();
      return;
    }

    $('#res-score').textContent = `${score}%`;
    $('#res-sub').textContent = `${correct} / ${total} correct · ${formatTime(elapsed)}`;
    $('#res-stats').innerHTML = `
      <div class="res-stat"><div class="res-stat-val" style="color:var(--green)">${correct}</div><div class="res-stat-lbl">Correct</div></div>
      <div class="res-stat"><div class="res-stat-val" style="color:var(--red)">${wrong}</div><div class="res-stat-lbl">Wrong</div></div>
      <div class="res-stat"><div class="res-stat-val" style="color:var(--purple)">${skipped}</div><div class="res-stat-lbl">Skipped</div></div>
      <div class="res-stat"><div class="res-stat-val">${answered}</div><div class="res-stat-lbl">Attempted</div></div>
    `;

    const review = ses.qs
      .map((q, i) => {
        const a = ses.answers[qKey(q)];
        if (!a || a.skipped) return '';
        const ok = a.correct;
        return `<div class="rev-item">
          <div><strong>#${i + 1}</strong> <span class="${ok ? 'ok' : 'bad'}">${ok ? '✓' : '✗'}</span>
          · ${escapeHtml(q.exam)} Q.${escapeHtml(String(q.q_no))}</div>
          <div style="color:var(--text2);margin-top:4px">${escapeHtml(q.stem.slice(0, 140))}${q.stem.length > 140 ? '…' : ''}</div>
          <div style="margin-top:4px;font-size:.75rem;color:var(--text3)">Your: ${escapeHtml(a.chosen || '—')} · Ans: ${escapeHtml(q.answer)}</div>
        </div>`;
      })
      .filter(Boolean)
      .join('');
    $('#res-review').innerHTML = review || '<div class="empty-state">No answers to review.</div>';

    showScreen('result-screen');
  }

  window.retryWrongs = function () {
    const ses = state.session;
    if (!ses) return window.backToSetup();
    const wrongs = ses.qs.filter((q) => {
      const a = ses.answers[qKey(q)];
      return a && !a.correct && !a.skipped;
    });
    if (!wrongs.length) {
      alert('No wrongs in this session.');
      return;
    }
    state.mode = 'revise';
    state.session = {
      qs: wrongs,
      idx: 0,
      answers: {},
      startTs: Date.now(),
      timerId: null,
      revealed: {},
      mode: 'revise',
      subjectId: ses.subjectId,
    };
    startTimer();
    renderQuiz();
    showScreen('quiz-screen');
  };
  window.restartSame = function () {
    const ses = state.session;
    if (!ses) return;
    state.session = {
      qs: [...ses.qs],
      idx: 0,
      answers: {},
      startTs: Date.now(),
      timerId: null,
      revealed: {},
      mode: ses.mode,
      subjectId: ses.subjectId,
    };
    startTimer();
    renderQuiz();
    showScreen('quiz-screen');
  };

  /* ---------- review banks ---------- */
  window.openReview = function (kind) {
    const p = getProg();
    const title = kind === 'bookmark' ? 'Bookmarks' : 'Mistake bank';
    $('#review-title').textContent = title;
    const body = $('#review-body');
    let items = [];

    if (kind === 'bookmark') {
      items = Object.entries(p.bookmarks || {}).map(([k, v]) => ({ k, ...v }));
      if (state.subjectId) items = items.filter((x) => x.subjectId === state.subjectId);
    } else {
      const sid = state.subjectId;
      if (sid) {
        const sp = ensureSubj(p, sid);
        items = Object.entries(sp.wrongs || {}).map(([k, v]) => ({ k, subjectId: sid, ...v }));
      } else {
        Object.keys(p.subjects || {}).forEach((sid) => {
          const sp = p.subjects[sid];
          Object.entries(sp.wrongs || {}).forEach(([k, v]) => items.push({ k, subjectId: sid, ...v }));
        });
      }
    }

    if (!items.length) {
      body.innerHTML = `<div class="empty-state">No ${kind === 'bookmark' ? 'bookmarks' : 'mistakes'} yet. Practice a few chapters first.</div>`;
      showScreen('review-screen');
      return;
    }

    body.innerHTML = `
      <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
        <button class="res-btn primary" id="review-practice">Practice these (${items.length}) →</button>
        ${kind === 'wrong' ? '<button class="res-btn" id="review-clear">Clear mistake bank</button>' : ''}
      </div>
      <div class="res-review">
        ${items
          .map((it, i) => {
            const subj = getSubject(it.subjectId);
            return `<div class="rev-item">
              <div><strong>#${i + 1}</strong> · ${escapeHtml(it.exam || '')} Q.${escapeHtml(String(it.q_no || ''))}
              · <span style="color:${subj ? subj.accent : 'var(--gold)'}">${escapeHtml(subj ? subj.name : it.subjectId || '')}</span></div>
              <div style="margin-top:4px;color:var(--text)">${escapeHtml(it.stem || '')}</div>
              <div style="margin-top:4px;font-size:.75rem;color:var(--text3)">Answer: ${escapeHtml(it.answer || '—')}${it.chosen ? ' · You chose: ' + escapeHtml(it.chosen) : ''}</div>
            </div>`;
          })
          .join('')}
      </div>`;

    const practiceBtn = $('#review-practice');
    if (practiceBtn) {
      practiceBtn.onclick = () => {
        // rebuild qs from DATA where possible
        const qs = [];
        const map = new Map();
        DATA.subjects.forEach((s) => {
          allQuestions(s).forEach((q) => map.set(qKey(q), q));
        });
        items.forEach((it) => {
          if (map.has(it.k)) qs.push(map.get(it.k));
          else if (it.stem) {
            qs.push({
              exam: it.exam,
              q_no: it.q_no,
              stem: it.stem,
              options: it.options || [],
              answer: it.answer,
              _subjectId: it.subjectId,
              _subject: (getSubject(it.subjectId) || {}).name || '',
              _subtopic: it.subtopic || '',
            });
          }
        });
        if (!qs.length) return alert('Could not load questions.');
        state.subjectId = state.subjectId || qs[0]._subjectId;
        state.session = {
          qs,
          idx: 0,
          answers: {},
          startTs: Date.now(),
          timerId: null,
          revealed: {},
          mode: 'revise',
          subjectId: state.subjectId,
        };
        startTimer();
        renderQuiz();
        showScreen('quiz-screen');
      };
    }
    const clearBtn = $('#review-clear');
    if (clearBtn) {
      clearBtn.onclick = () => {
        if (!confirm('Clear all mistakes for this subject?')) return;
        const p2 = getProg();
        if (state.subjectId) ensureSubj(p2, state.subjectId).wrongs = {};
        saveProgress(p2);
        window.openReview('wrong');
      };
    }
    showScreen('review-screen');
  };

  window.showHistory = function () {
    const p = getProg();
    const body = $('#review-body');
    $('#review-title').textContent = 'History';
    const hist = p.history || [];
    if (!hist.length) {
      body.innerHTML = `<div class="empty-state">No sessions yet.</div>`;
      showScreen('review-screen');
      return;
    }
    body.innerHTML = `<div class="res-review">${hist
      .map((h) => {
        const s = getSubject(h.subjectId);
        const d = new Date(h.at);
        return `<div class="rev-item">
          <div><strong>${escapeHtml(s ? s.name : h.subjectId)}</strong> · ${escapeHtml(h.mode)} · ${d.toLocaleString()}</div>
          <div style="color:var(--text3);margin-top:4px">${h.correct}/${h.total} correct · ${h.wrong} wrong · ${h.skipped || 0} skipped · ${formatTime(h.elapsed || 0)}</div>
        </div>`;
      })
      .join('')}</div>`;
    showScreen('review-screen');
  };

  /* ---------- plan ---------- */
  function renderPlan() {
    const subjects = [...DATA.subjects].sort((a, b) => a.priority - b.priority);
    const rows = subjects
      .map((s) => {
        const st = subjectStats(s);
        return `<tr>
          <td><strong>P${s.priority}</strong></td>
          <td>${s.emoji || ''} ${escapeHtml(s.name)}<div style="font-size:.7rem;color:var(--text3)">${escapeHtml(s.weight_note || '')}</div></td>
          <td>${s.count}</td>
          <td>${st.progress}%</td>
          <td>${escapeHtml(s.books || '—')}</td>
          <td>${escapeHtml(s.ncert || '—')}</td>
          <td><button class="plan-open-subj" onclick="openSubject('${s.id}')">Open</button></td>
        </tr>`;
      })
      .join('');

    $('#plan-page').innerHTML = `
      <div class="plan-card">
        <h3>How to use this PYQ book</h3>
        <p>Cover subjects in priority order (P1 → P13). Bihar Special and Modern History carry the highest BPSC-unique weight; Current Affairs and Math should stay daily. Practice mode shows answers immediately; Quiz mode scores at the end; Revise wrongs drills your mistake bank.</p>
        <ol>
          <li>Open a book card → select chapters → Practice first pass.</li>
          <li>Mark tough Qs with bookmarks; wrongs auto-save to the mistake bank.</li>
          <li>Use <em>Revise wrongs</em> until the chapter bar is green.</li>
          <li>Pair each subject with the listed standard books / NCERT.</li>
        </ol>
      </div>
      <div class="plan-card">
        <h3>Priority ladder · ${DATA.meta.total} questions · ${DATA.meta.exams}</h3>
        <div style="overflow-x:auto">
          <table class="plan-table">
            <thead><tr><th>P</th><th>Subject</th><th>Qs</th><th>Done</th><th>Books</th><th>NCERT</th><th></th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
      <div class="plan-card">
        <h3>12-week rhythm (summary)</h3>
        <ul>
          <li><strong>Daily:</strong> 20–30 CA + 10 Math + 15 Bihar facts/maps</li>
          <li><strong>Weeks 1–3:</strong> Bihar Special + Modern History deep dive</li>
          <li><strong>Weeks 4–5:</strong> Polity + Geography</li>
          <li><strong>Weeks 6–7:</strong> Economics + Ancient/Medieval</li>
          <li><strong>Weeks 8–9:</strong> Science trio (Bio → Chem → Phys)</li>
          <li><strong>Weeks 10–12:</strong> Full mixed mocks from wrongs + weak chapters</li>
        </ul>
        <p style="margin-top:10px">Full write-up: <a href="BPSC_Complete_Priority_Study_Book.md" style="color:var(--gold)">BPSC_Complete_Priority_Study_Book.md</a>
        · <a href="BPSC_Complete_Priority_Study_Book.pdf" style="color:var(--gold)">PDF</a></p>
      </div>
    `;
  }

  /* ---------- global search ---------- */
  function runGlobalSearch(q) {
    const box = $('#global-results');
    const status = $('#global-search-status');
    const clear = $('#global-search-clear');
    q = (q || '').trim().toLowerCase();
    if (!q) {
      box.hidden = true;
      box.innerHTML = '';
      clear.hidden = true;
      status.textContent = `${DATA.meta.total} Arena-tagged BPSC Prelims PYQs · priority-ranked subjects`;
      return;
    }
    clear.hidden = false;
    const hits = [];
    // subjects
    DATA.subjects.forEach((s) => {
      if (s.name.toLowerCase().includes(q) || (s.code || '').toLowerCase().includes(q) || (s.weight_note || '').toLowerCase().includes(q)) {
        hits.push({ type: 'subject', s, label: s.name, meta: `P${s.priority} · ${s.count} Qs` });
      }
      (s.subtopics || []).forEach((ch) => {
        if (ch.name.toLowerCase().includes(q)) {
          hits.push({ type: 'chapter', s, ch, label: ch.name, meta: `${s.name} · ${ch.count} Qs` });
        }
        (ch.questions || []).forEach((qq) => {
          if (hits.length > 60) return;
          const stem = (qq.stem || '').toLowerCase();
          if (stem.includes(q) || String(qq.q_no).includes(q) || (qq.exam || '').toLowerCase().includes(q)) {
            hits.push({
              type: 'question',
              s,
              ch,
              qq,
              label: qq.stem.slice(0, 120) + (qq.stem.length > 120 ? '…' : ''),
              meta: `${qq.exam} · Q.${qq.q_no} · ${s.name}`,
            });
          }
        });
      });
    });

    status.textContent = `${hits.length} result${hits.length === 1 ? '' : 's'} for “${q}”`;
    if (!hits.length) {
      box.hidden = false;
      box.innerHTML = `<div class="empty-state" style="padding:20px">No matches.</div>`;
      return;
    }
    box.hidden = false;
    box.innerHTML = hits
      .slice(0, 40)
      .map((h, idx) => {
        const icon = h.type === 'subject' ? '📘' : h.type === 'chapter' ? '📑' : '❓';
        return `<button type="button" class="gsearch-item" data-hi="${idx}">
          <span class="gsearch-ico">${icon}</span>
          <span class="gsearch-text"><strong>${escapeHtml(h.label)}</strong><small>${escapeHtml(h.meta)}</small></span>
        </button>`;
      })
      .join('');

    // stash
    box._hits = hits;
    box.onclick = (e) => {
      const b = e.target.closest('[data-hi]');
      if (!b) return;
      const h = box._hits[+b.dataset.hi];
      if (!h) return;
      if (h.type === 'subject') window.openSubject(h.s.id);
      else if (h.type === 'chapter') {
        state.subjectId = h.s.id;
        window.openSubject(h.s.id);
        state.selectedChapters = new Set([h.ch.id]);
        renderChapters();
        updateStartMeta();
      } else if (h.type === 'question') {
        const qn = {
          ...h.qq,
          _subtopic: h.ch.name,
          _subtopicId: h.ch.id,
          _subjectId: h.s.id,
          _subject: h.s.name,
        };
        state.subjectId = h.s.id;
        state.session = {
          qs: [qn],
          idx: 0,
          answers: {},
          startTs: Date.now(),
          timerId: null,
          revealed: {},
          mode: 'practice',
          subjectId: h.s.id,
        };
        startTimer();
        renderQuiz();
        showScreen('quiz-screen');
      }
    };
  }

  /* ---------- boot ---------- */
  function wireSearch() {
    const input = $('#global-search');
    const btn = $('#global-search-btn');
    const clear = $('#global-search-clear');
    let t = null;
    const go = () => runGlobalSearch(input.value);
    input.addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(go, 180);
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') go();
    });
    btn.addEventListener('click', go);
    clear.addEventListener('click', () => {
      input.value = '';
      runGlobalSearch('');
      input.focus();
    });
  }

  function setDateLine() {
    const el = $('#books-date');
    if (!el) return;
    const d = new Date();
    el.textContent = `🌿 ${d.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })} · Cover by priority 🌿`;
  }

  async function boot() {
    try {
      const res = await fetch('data.json');
      DATA = await res.json();
    } catch (e) {
      $('#books-grid').innerHTML = `<div style="grid-column:1/-1;color:var(--red);text-align:center;padding:40px">Failed to load data.json</div>`;
      return;
    }
    setDateLine();
    wireSearch();
    renderBooks();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
