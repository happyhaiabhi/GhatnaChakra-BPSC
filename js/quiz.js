/* ═══════════════════════════════════════════════════
   quiz.js — Quiz engine
   ═══════════════════════════════════════════════════ */

/* ── State ── */
const state = {
  questions:  [],       // flat array of question objects
  current:    0,
  answers:    [],       // null = unanswered, 'skip', or option key like 'A'
  revealed:   [],       // bool — whether answer shown for each Q
  score:      0,
  subjectKey: '',
  subjectLabel: '',
  chapterLabel: '',
};

/* ── Helpers ── */
const $  = id => document.getElementById(id);
const qs = key => new URLSearchParams(window.location.search).get(key);

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/* ── Boot ── */
async function init() {
  state.subjectKey  = qs('subject') || '';
  const chapterIdx  = qs('chapter');         // null = all chapters

  if (!state.subjectKey) {
    window.location.href = 'index.html';
    return;
  }

  try {
    const res  = await fetch(`data/${state.subjectKey}.json`);
    const data = await res.json();

    state.subjectLabel = data.subject;
    $('quizSubjectLabel').textContent = data.subject;

    let qs_raw = [];
    if (chapterIdx !== null) {
      const ch = data.chapters[parseInt(chapterIdx, 10)];
      state.chapterLabel = ch.chapter_name;
      $('quizChapterLabel').textContent = ch.chapter_name;
      qs_raw = ch.questions;
    } else {
      state.chapterLabel = 'All Chapters';
      $('quizChapterLabel').textContent = 'All Chapters';
      data.chapters.forEach(ch => {
        ch.questions.forEach(q => qs_raw.push({ ...q, _chapter: ch.chapter_name }));
      });
    }

    // Normalise & filter
    state.questions = qs_raw
      .filter(q => q.q && q.options && Object.keys(q.options).length >= 2)
      .map(q => ({ ...q }));

    if (state.questions.length === 0) {
      $('quizLoading').innerHTML = '<p style="color:#f87171">No valid questions found for this chapter.</p>';
      return;
    }

    state.answers  = new Array(state.questions.length).fill(null);
    state.revealed = new Array(state.questions.length).fill(false);
    state.current  = 0;
    state.score    = 0;

    $('quizLoading').hidden = true;
    $('questionWrap').hidden = false;
    $('qTotal').textContent = state.questions.length;
    render();
  } catch (err) {
    console.error(err);
    $('quizLoading').innerHTML = '<p style="color:#f87171">⚠ Failed to load questions.</p>';
  }
}

/* ── Render current question ── */
function render() {
  const i   = state.current;
  const q   = state.questions[i];
  const ans = state.answers[i];
  const rev = state.revealed[i];

  // Progress
  const pct = ((i) / state.questions.length) * 100;
  $('progressFill').style.width = pct + '%';

  // Counter
  $('qCurrent').textContent = i + 1;

  // Meta (exam / year)
  const metaParts = [];
  if (q.exam)    metaParts.push(q.exam);
  if (q.year)    metaParts.push(q.year);
  if (q._chapter && state.chapterLabel === 'All Chapters') metaParts.push(q._chapter);
  $('questionMeta').innerHTML = metaParts.map(p => `<span class="meta-tag">${p}</span>`).join('');

  // Question text
  $('questionText').textContent = q.q;

  // Options
  const grid = $('optionsGrid');
  grid.innerHTML = '';
  Object.entries(q.options).forEach(([key, val]) => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.disabled = rev;

    // State classes
    if (rev) {
      if (key === q.answer) {
        btn.classList.add(ans === key ? 'correct' : 'reveal-correct');
      } else if (key === ans && ans !== q.answer) {
        btn.classList.add('wrong');
      }
    } else {
      if (key === ans) btn.classList.add('selected');
    }

    btn.innerHTML = `<span class="option-key">${key}</span><span class="option-text">${val}</span>`;
    if (!rev) {
      btn.addEventListener('click', () => selectAnswer(key));
    }
    grid.appendChild(btn);
  });

  // Explanation
  const exBox = $('explanationBox');
  if (rev && q.explanation) {
    exBox.hidden = false;
    $('explanationText').textContent = q.explanation;
  } else {
    exBox.hidden = true;
  }

  // Nav buttons
  $('btnPrev').disabled = i === 0;
  $('btnNext').disabled = !rev;
  $('btnSkip').style.display = rev ? 'none' : '';
  $('btnSkip').textContent = ans === null ? 'Skip' : 'Check Answer ✓';

  // Score badge
  $('scoreBadge').textContent = `${state.score} / ${i}`;
}

/* ── Select an answer ── */
function selectAnswer(key) {
  const i = state.current;
  if (state.revealed[i]) return;

  state.answers[i] = key;
  render();

  // Update skip button to "Check Answer"
  $('btnSkip').textContent = 'Check Answer ✓';
}

/* ── Reveal / Skip ── */
function revealOrSkip() {
  const i = state.current;
  if (state.revealed[i]) return;

  const chosen = state.answers[i];
  if (chosen === null) {
    state.answers[i] = 'skip';
  }
  state.revealed[i] = true;

  if (state.answers[i] === state.questions[i].answer) {
    state.score++;
  }

  render();
}

/* ── Navigation ── */
function goNext() {
  if (state.current < state.questions.length - 1) {
    state.current++;
    render();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    showResults();
  }
}
function goPrev() {
  if (state.current > 0) {
    state.current--;
    render();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

/* ── Event listeners ── */
$('btnNext').addEventListener('click', goNext);
$('btnPrev').addEventListener('click', goPrev);
$('btnSkip').addEventListener('click', revealOrSkip);

// Keyboard shortcuts
document.addEventListener('keydown', e => {
  if ($('resultsScreen') && !$('resultsScreen').hidden) return;
  if ($('reviewScreen') && !$('reviewScreen').hidden) return;

  if (e.key === 'ArrowRight' || e.key === 'Enter') {
    if (!$('btnNext').disabled) goNext();
  }
  if (e.key === 'ArrowLeft') goPrev();
  if (e.key === ' ') { e.preventDefault(); revealOrSkip(); }

  // A/B/C/D/E for options
  const keyMap = ['a','b','c','d','e'];
  if (keyMap.includes(e.key.toLowerCase())) {
    const upper = e.key.toUpperCase();
    const q = state.questions[state.current];
    if (q && q.options[upper] && !state.revealed[state.current]) {
      selectAnswer(upper);
    }
  }
});

/* ── Results ── */
function showResults() {
  $('questionWrap').hidden = true;
  $('progressFill').style.width = '100%';

  const total   = state.questions.length;
  const correct = state.score;
  const skipped = state.answers.filter(a => a === null || a === 'skip').length;
  const wrong   = total - correct - skipped;
  const pct     = Math.round((correct / total) * 100);

  $('resultsScreen').hidden = false;
  $('rsCorrect').textContent = correct;
  $('rsWrong').textContent   = wrong;
  $('rsSkipped').textContent = skipped;
  $('ringPercent').textContent = pct + '%';
  $('scoreBadge').textContent = `${correct} / ${total}`;

  // Emoji based on score
  $('resultEmoji').textContent =
    pct >= 80 ? '🏆' : pct >= 60 ? '🎯' : pct >= 40 ? '📚' : '💪';

  // Animate ring
  setTimeout(() => {
    const circumference = 326.73;
    const offset = circumference - (pct / 100) * circumference;
    $('ringProgress').style.strokeDashoffset = offset;
    // Color by score
    if (pct >= 75) $('ringProgress').style.stroke = 'var(--green)';
    else if (pct >= 50) $('ringProgress').style.stroke = 'var(--gold)';
    else $('ringProgress').style.stroke = 'var(--red)';
  }, 100);

  // Buttons
  $('btnRetry').addEventListener('click', () => {
    state.answers  = new Array(state.questions.length).fill(null);
    state.revealed = new Array(state.questions.length).fill(false);
    state.current  = 0;
    state.score    = 0;
    $('resultsScreen').hidden = true;
    $('questionWrap').hidden = false;
    $('progressFill').style.width = '0%';
    $('ringProgress').style.strokeDashoffset = 326.73;
    render();
  });
  $('btnReview').addEventListener('click', showReview);
}

/* ── Review ── */
function showReview() {
  $('resultsScreen').hidden = true;
  $('reviewScreen').hidden = false;

  const list = $('reviewList');
  list.innerHTML = '';

  state.questions.forEach((q, i) => {
    const ans = state.answers[i];
    const isCorrect = ans === q.answer;
    const isSkipped = ans === null || ans === 'skip';
    const cls = isCorrect ? 'ri-correct' : isSkipped ? 'ri-skipped' : 'ri-wrong';
    const icon = isCorrect ? '✓' : isSkipped ? '—' : '✗';

    const div = document.createElement('div');
    div.className = `review-item ${cls}`;

    const yourAns = isSkipped
      ? `<span class="ri-pill skipped">${icon} Skipped</span>`
      : isCorrect
        ? `<span class="ri-pill correct-a">✓ ${ans}: ${q.options[ans] || ''}</span>`
        : `<span class="ri-pill your">${icon} ${ans}: ${q.options[ans] || 'N/A'}</span>`;

    const correctAns = (!isCorrect && !isSkipped)
      ? `<span class="ri-pill correct-a">✓ ${q.answer}: ${q.options[q.answer] || ''}</span>`
      : '';

    div.innerHTML = `
      <div class="ri-num">Q${i + 1} ${q.exam ? '· ' + q.exam : ''} ${q.year ? '· ' + q.year : ''}</div>
      <div class="ri-question">${q.q}</div>
      <div class="ri-answers">${yourAns}${correctAns}</div>
      ${q.explanation ? `<div class="ri-expl">💡 ${q.explanation}</div>` : ''}`;

    list.appendChild(div);
  });
}

$('btnBackResult').addEventListener('click', () => {
  $('reviewScreen').hidden = true;
  $('resultsScreen').hidden = false;
});

/* ── Start ── */
init();
