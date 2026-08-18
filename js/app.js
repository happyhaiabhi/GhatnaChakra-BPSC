/* ═══════════════════════════════════════════════════
   app.js — Home page: subject + chapter selection
   ═══════════════════════════════════════════════════ */

let chaptersData = [];
let activeSubject = null;

async function init() {
  try {
    const res = await fetch('data/chapters.json');
    chaptersData = await res.json();
    renderStats();
    renderSubjects();
  } catch (err) {
    console.error('Failed to load chapters.json:', err);
    document.getElementById('subjectGrid').innerHTML =
      '<p style="color:#f87171;grid-column:1/-1">⚠ Could not load subjects. Run from a local server or GitHub Pages.</p>';
  }
}

function renderStats() {
  const totalQ = chaptersData.reduce((s, sub) => s + sub.total, 0);
  const totalCh = chaptersData.reduce((s, sub) => s + sub.chapters.length, 0);
  animateCount(document.getElementById('totalSubjects'), chaptersData.length);
  animateCount(document.getElementById('totalChapters'), totalCh);
  animateCount(document.getElementById('totalQuestions'), totalQ);
}

function animateCount(el, target) {
  let start = 0;
  const step = Math.ceil(target / 40);
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = start.toLocaleString();
    if (start >= target) clearInterval(timer);
  }, 30);
}

function renderSubjects() {
  const grid = document.getElementById('subjectGrid');
  grid.innerHTML = '';
  chaptersData.forEach((sub, idx) => {
    const card = document.createElement('button');
    card.className = 'subject-card';
    card.style.animationDelay = `${idx * 0.06}s`;
    card.innerHTML = `
      <div class="card-top">
        <span class="card-emoji">${sub.emoji}</span>
        <span class="card-label">${sub.label}</span>
      </div>
      <div class="card-meta">
        <span class="card-tag">${sub.chapters.length} chapters</span>
        <span class="card-tag">${sub.total} Qs</span>
      </div>
      <span class="card-arrow">→</span>`;
    card.addEventListener('click', () => openSubject(sub));
    grid.appendChild(card);
  });
}

function openSubject(sub) {
  activeSubject = sub;
  document.getElementById('subjectGrid').style.display = 'none';
  document.getElementById('chapterPanel').removeAttribute('hidden');

  document.getElementById('panelEmoji').textContent = sub.emoji;
  document.getElementById('panelSubject').textContent = sub.label;
  document.getElementById('allChCount').textContent = `${sub.total} questions`;

  // All chapters button
  document.getElementById('btnAllChapters').onclick = () => {
    goToQuiz(sub.key, null);
  };

  // Chapter list
  const list = document.getElementById('chapterList');
  list.innerHTML = '';
  sub.chapters.forEach((ch, idx) => {
    const btn = document.createElement('button');
    btn.className = 'chapter-card';
    btn.innerHTML = `
      <span class="ch-icon">📖</span>
      <span class="ch-name">${ch.name}</span>
      <span class="ch-count">${ch.count} Qs</span>
      <span class="ch-arrow">→</span>`;
    btn.addEventListener('click', () => goToQuiz(sub.key, idx));
    list.appendChild(btn);
  });

  // Scroll into view
  document.getElementById('chapterPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function goToQuiz(subjectKey, chapterIndex) {
  const params = new URLSearchParams({ subject: subjectKey });
  if (chapterIndex !== null) params.set('chapter', chapterIndex);
  window.location.href = `quiz.html?${params.toString()}`;
}

// Back button
document.getElementById('btnBack').addEventListener('click', () => {
  document.getElementById('chapterPanel').setAttribute('hidden', '');
  document.getElementById('subjectGrid').style.display = '';
  activeSubject = null;
});

// Boot
init();
