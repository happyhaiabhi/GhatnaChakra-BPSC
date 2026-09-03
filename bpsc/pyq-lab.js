(function () {
  const $ = (id) => document.getElementById(id);
  const PYQ_FILES = {
    questions: '../BPSC PYQ/bpsc_parsed.json?v=2',
    categories: '../BPSC PYQ/bpsc_categories_all.json?v=1',
    verifiedAnswers: '../BPSC PYQ/bpsc_verified_answers.json?v=4'
  };
  const PYQ_EXPLORE_BATCH = 12;
  let pyqQuestions = [];
  let pyqFiltered = [];
  let pyqDataPromise = null;
  let pyqMode = 'explore';
  let pyqExploreShown = PYQ_EXPLORE_BATCH;
  let pyqAnswersRevealed = new Set();
  let pyqPractice = createPracticeState([]);
  let pyqReturnScreen = 'books-screen';

  function escapeAttr(value) {
    if (typeof escapeHtml === 'function') return escapeHtml(value);
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[char]);
  }

  function stripInjectedAnswerMeta(value) {
    const raw = String(value ?? '');
    return raw
      .replace(/\s*\*?Correct Answer\s*:\s*\*\*\(?[A-E]\)?\*\*\s*\|\s*Verified Answer\s*:\s*\*\*[^*]+\*\*\*\s*$/i, '')
      .replace(/\n\s*\*?Correct Answer\s*:[\s\S]*$/i, '')
      .replace(/\n\s*\*?Verified Answer\s*:[\s\S]*$/i, '')
      .trim();
  }

  function renderText(value) {
    const clean = stripInjectedAnswerMeta(value);
    return typeof bookText === 'function' ? bookText(clean) : escapeAttr(clean);
  }

  function renderQuestionMarkup(question) {
    const text = stripInjectedAnswerMeta(question?.question || '');
    const model = { question: text, options: question?.options || {} };
    if (typeof renderQuestionStem === 'function') {
      const rendered = renderQuestionStem(model, 'bank');
      if (rendered?.html) return rendered.html;
    }
    return `<div class="bank-q">${renderText(text)}</div>`;
  }

  function normalizePlainText(value) {
    const clean = stripInjectedAnswerMeta(value);
    return typeof normalizeBookText === 'function' ? normalizeBookText(clean) : String(clean ?? '');
  }

  function slugify(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function sanitizeOptionText(value) {
    return stripInjectedAnswerMeta(value);
  }

  function optionEntries(options) {
    return Object.entries(options || {})
      .map(([key, value]) => [String(key).trim().toUpperCase(), sanitizeOptionText(value)])
      .filter(([, value]) => value !== undefined && value !== null && String(value).trim() !== '');
  }

  function normalizeAnswerKey(rawAnswer, options) {
    const entries = optionEntries(options);
    const keys = entries.map(([key]) => key);
    const raw = Array.isArray(rawAnswer) ? rawAnswer.join(' ') : String(rawAnswer ?? '').trim();
    if (!raw || /^none$/i.test(raw) || /missing in source/i.test(raw)) return '';

    let match = raw.match(/\(([A-E])\)/i) || raw.match(/\b([A-E])\b/i);
    if (match) {
      const key = match[1].toUpperCase();
      if (keys.includes(key)) return key;
    }

    const number = raw.match(/^\s*(\d+)\s*$/)?.[1] || raw.match(/option\s*(\d+)/i)?.[1];
    if (number) {
      const candidate = keys[Number(number) - 1];
      if (candidate) return candidate;
    }

    const normalizedRaw = normalizePlainText(raw).toLowerCase();
    const byText = entries.find(([, value]) => normalizePlainText(value).toLowerCase() === normalizedRaw);
    if (byText) return byText[0];

    return '';
  }

  function searchBlob(parts) {
    return parts
      .flatMap((part) => Array.isArray(part) ? part : [part])
      .filter((part) => part !== undefined && part !== null)
      .map((part) => normalizePlainText(part).toLowerCase())
      .join(' ');
  }

  function questionSignature(items) {
    return items.map((item) => item.id).join('|');
  }

  function createPracticeState(pool) {
    return {
      pool: pool.slice(),
      index: 0,
      answers: {},
      correct: 0,
      wrong: 0,
      signature: questionSignature(pool)
    };
  }

  async function fetchJson(path) {
    const response = await fetch(encodeURI(path));
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    return response.json();
  }

  async function ensurePyqData() {
    if (pyqQuestions.length) return pyqQuestions;
    if (pyqDataPromise) return pyqDataPromise;
    pyqDataPromise = Promise.all([
      fetchJson(PYQ_FILES.questions),
      fetchJson(PYQ_FILES.categories),
      fetchJson(PYQ_FILES.verifiedAnswers).catch(() => ({ answers: {} }))
    ]).then(([examPapers, categories, verifiedAnswerBundle]) => {
      const categoryMap = new Map((categories || []).map((item) => [
        `${item.exam}::${Number(item.q_no)}`,
        String(item.category || 'General').trim() || 'General'
      ]));
      const verifiedAnswers = verifiedAnswerBundle?.answers || {};
      pyqQuestions = [];
      (examPapers || []).forEach((packet, examIndex) => {
        const exam = String(packet.exam || 'BPSC');
        (packet.questions || []).forEach((question, index) => {
          const qNo = Number(question.q_no) || (index + 1);
          const options = Object.fromEntries(optionEntries(question.options));
          const verifiedEntry = verifiedAnswers[`${exam}::${qNo}`] || {};
          const answerKey = (verifiedEntry.answerKey && options[verifiedEntry.answerKey] !== undefined)
            ? verifiedEntry.answerKey
            : normalizeAnswerKey(question.answer, options);
          const category = categoryMap.get(`${exam}::${qNo}`) || String(question.category || 'General');
          const stem = question.stem || question.question || question.q || '';
          const type = typeof getQuestionType === 'function'
            ? getQuestionType({ question: stem, options })
            : 'Direct MCQ';
          const answerText = answerKey ? (options[answerKey] || verifiedEntry.answerText || '') : (verifiedEntry.answerText || '');
          pyqQuestions.push({
            id: `pyq_${slugify(exam)}_${qNo}`,
            exam,
            examIndex,
            q_no: qNo,
            category,
            type,
            question: stem,
            options,
            rawAnswer: verifiedEntry.verifiedText || question.answer || '',
            answerKey,
            answerText,
            answerAvailable: Boolean(answerKey),
            search: searchBlob([
              exam,
              category,
              type,
              stem,
              Object.keys(options),
              Object.values(options),
              answerKey,
              answerText,
              verifiedEntry.verifiedText || ''
            ])
          });
        });
      });
      return pyqQuestions;
    }).catch((error) => {
      pyqDataPromise = null;
      throw error;
    });
    return pyqDataPromise;
  }

  function fillSelect(id, values, placeholder) {
    const node = $(id);
    if (!node) return;
    const previous = node.value;
    node.innerHTML = `<option value="">${escapeAttr(placeholder)}</option>${values.map((value) => `
      <option value="${escapeAttr(value)}">${escapeAttr(value)}</option>`).join('')}`;
    node.value = values.includes(previous) ? previous : '';
  }

  function populateFilters() {
    const exams = [...new Set(pyqQuestions.map((item) => item.exam))];
    const categories = [...new Set(pyqQuestions.map((item) => item.category))].sort((a, b) => a.localeCompare(b));
    fillSelect('pyq-exam-filter', exams, 'All exam papers');
    fillSelect('pyq-category-filter', categories, 'All categories');
  }

  function updateHeroStats() {
    const totals = {
      questions: pyqQuestions.length,
      exams: new Set(pyqQuestions.map((item) => item.exam)).size,
      categories: new Set(pyqQuestions.map((item) => item.category)).size
    };
    if ($('pyq-total-count')) $('pyq-total-count').textContent = totals.questions.toLocaleString();
    if ($('pyq-exam-count')) $('pyq-exam-count').textContent = totals.exams.toLocaleString();
    if ($('pyq-category-count')) $('pyq-category-count').textContent = totals.categories.toLocaleString();
  }

  function currentControls() {
    return {
      term: normalizePlainText($('pyq-search')?.value || '').trim().toLowerCase(),
      exam: $('pyq-exam-filter')?.value || '',
      category: $('pyq-category-filter')?.value || '',
      sort: $('pyq-sort-filter')?.value || 'latest'
    };
  }

  function compareQuestions(left, right, sort) {
    if (sort === 'oldest') {
      return left.examIndex - right.examIndex || left.q_no - right.q_no;
    }
    if (sort === 'category') {
      return left.category.localeCompare(right.category) || right.examIndex - left.examIndex || left.q_no - right.q_no;
    }
    return right.examIndex - left.examIndex || left.q_no - right.q_no;
  }

  function syncPracticePool(forceReset) {
    const practicePool = pyqFiltered.filter((item) => item.answerAvailable);
    const signature = questionSignature(practicePool);
    if (forceReset || pyqPractice.signature !== signature) {
      pyqPractice = createPracticeState(practicePool);
      return;
    }
    pyqPractice.pool = practicePool.slice();
    if (pyqPractice.index > pyqPractice.pool.length - 1) {
      pyqPractice.index = Math.max(0, pyqPractice.pool.length - 1);
    }
  }

  function activeFiltersCount() {
    const { term, exam, category } = currentControls();
    return [term, exam, category].filter(Boolean).length;
  }

  function hasActiveQuestionFilter() {
    return activeFiltersCount() > 0;
  }

  function examCollections() {
    const map = new Map();
    pyqQuestions.forEach((item) => {
      const current = map.get(item.exam) || {
        exam: item.exam,
        examIndex: item.examIndex,
        total: 0,
        answerReady: 0,
        categories: new Set()
      };
      current.total += 1;
      if (item.answerAvailable) current.answerReady += 1;
      current.categories.add(item.category);
      map.set(item.exam, current);
    });
    return [...map.values()]
      .sort((left, right) => right.examIndex - left.examIndex)
      .map((item) => ({
        exam: item.exam,
        examIndex: item.examIndex,
        total: item.total,
        answerReady: item.answerReady,
        categoryCount: item.categories.size
      }));
  }

  function latestExamName() {
    return examCollections()[0]?.exam || '';
  }

  function setFiltersOpen(open) {
    const panel = $('pyq-filter-panel');
    const button = $('pyq-filter-toggle');
    if (!panel || !button) return;
    panel.hidden = !open;
    button.setAttribute('aria-expanded', String(open));
    button.innerHTML = `⚙ Filters${activeFiltersCount() ? ` (${activeFiltersCount()})` : ''}`;
  }

  function renderExamChips() {
    const wrap = $('pyq-exam-strip');
    if (!wrap) return;
    const selectedExam = $('pyq-exam-filter')?.value || '';
    const counts = pyqQuestions.reduce((map, item) => {
      map[item.exam] = (map[item.exam] || 0) + 1;
      return map;
    }, {});
    wrap.innerHTML = Object.entries(counts)
      .sort((a, b) => pyqQuestions.find((item) => item.exam === b[0]).examIndex - pyqQuestions.find((item) => item.exam === a[0]).examIndex)
      .map(([exam, count]) => `
        <button type="button" class="pyq-exam-chip${selectedExam === exam ? ' is-active' : ''}" data-pyq-exam="${escapeAttr(exam)}">
          <span>${escapeAttr(exam)}</span>
          <b>${count}</b>
        </button>`)
      .join('');
  }

  function renderActiveFilters() {
    const host = $('pyq-active-filters');
    if (!host) return;
    const { term, exam, category } = currentControls();
    const chips = [];
    if (term) chips.push(`<span class="pyq-active-chip">Search <b>${escapeAttr(term)}</b></span>`);
    if (exam) chips.push(`<span class="pyq-active-chip">Exam <b>${escapeAttr(exam)}</b></span>`);
    if (category) chips.push(`<span class="pyq-active-chip">Category <b>${escapeAttr(category)}</b></span>`);
    host.innerHTML = chips.length
      ? `${chips.join('')}<button type="button" class="pyq-soft-button" data-pyq-action="clear-filters">Reset all</button>`
      : '<span class="pyq-soft-note">Use search, exam chips or filters to narrow the archive.</span>';
  }

  function renderSummary() {
    const answerReady = pyqFiltered.filter((item) => item.answerAvailable).length;
    const label = $('pyq-match-label');
    if (!hasActiveQuestionFilter()) {
      if ($('pyq-match-count')) $('pyq-match-count').textContent = pyqQuestions.length.toLocaleString();
      if (label) label.textContent = 'questions in archive';
      if ($('pyq-mode-copy')) {
        $('pyq-mode-copy').textContent = pyqMode === 'explore'
          ? 'Pick one paper, type a keyword, or use filters to open a smaller slice of the archive. The first page stays clean instead of dumping every question at once.'
          : 'Practice starts after you choose a paper or search result. This keeps the first page focused and makes drills more intentional.';
      }
      return;
    }
    if ($('pyq-match-count')) $('pyq-match-count').textContent = pyqFiltered.length.toLocaleString();
    if (label) label.textContent = 'matching questions';
    if ($('pyq-mode-copy')) {
      $('pyq-mode-copy').textContent = pyqMode === 'explore'
        ? `Explore mode lets you scan papers chapter-free, reveal answer keys where available and jump into practice anytime. ${answerReady.toLocaleString()} of ${pyqFiltered.length.toLocaleString()} filtered questions currently have answer keys.`
        : `Practice mode uses only answer-ready PYQs from your current filter so scoring stays trustworthy. Right now ${answerReady.toLocaleString()} question${answerReady === 1 ? '' : 's'} can be practised.`;
    }
  }

  function renderExploreLanding() {
    const papers = examCollections();
    const latest = papers[0]?.exam || '';
    return `
      <section class="pyq-landing" style="grid-column:1/-1;">
        <div class="pyq-landing-head">
          <div>
            <span class="pyq-landing-kicker">Start with a paper, not the whole archive</span>
            <h3>Choose your BPSC PYQ set</h3>
            <p>Select an exam paper below, or search by keyword above. Once you narrow the set, Explore and Practice both work from that filtered slice.</p>
          </div>
          <button type="button" class="pyq-primary-button" data-pyq-action="practice-latest" ${latest ? '' : 'disabled'}>${latest ? `Practice ${escapeAttr(latest)}` : 'Practice latest paper'}</button>
        </div>
        <div class="pyq-paper-grid">
          ${papers.map((paper) => `
            <button type="button" class="pyq-paper-card${paper.exam === latest ? ' is-featured' : ''}" data-pyq-exam="${escapeAttr(paper.exam)}">
              <span class="pyq-paper-year">${escapeAttr(paper.exam)}</span>
              <strong>${paper.total.toLocaleString()}</strong>
              <span class="pyq-paper-label">questions</span>
              <div class="pyq-paper-meta">
                <span>${paper.answerReady.toLocaleString()} answer-ready</span>
                <span>${paper.categoryCount.toLocaleString()} categories</span>
              </div>
              <span class="pyq-paper-cta">Open paper →</span>
            </button>`).join('')}
        </div>
      </section>`;
  }

  function renderExplore() {
    const wrap = $('pyq-results-grid');
    const loadMore = $('pyq-load-more');
    if (!wrap || !loadMore) return;
    if (!hasActiveQuestionFilter()) {
      wrap.innerHTML = renderExploreLanding();
      loadMore.hidden = true;
      return;
    }
    if (!pyqFiltered.length) {
      wrap.innerHTML = `<div class="pyq-empty" style="grid-column:1/-1"><strong>No matching PYQs found.</strong><p>Try a different keyword, another paper or reset the filters.</p></div>`;
      loadMore.hidden = true;
      return;
    }

    wrap.innerHTML = pyqFiltered.slice(0, pyqExploreShown).map((question) => {
      const revealed = pyqAnswersRevealed.has(question.id);
      const options = Object.entries(question.options).map(([key, value]) => `
        <div class="pyq-option">
          <span class="pyq-option-key">${escapeAttr(key)}</span>
          <span class="pyq-option-copy">${renderText(value)}</span>
        </div>`).join('');
      return `
        <article class="pyq-card">
          <div class="pyq-card-head">
            <span class="pyq-badge exam">${escapeAttr(question.exam)}</span>
            <span class="pyq-badge category">${escapeAttr(question.category)}</span>
            <span class="pyq-badge type">${escapeAttr(question.type || 'Direct MCQ')}</span>
            <span class="pyq-badge qno">Q ${escapeAttr(question.q_no)}</span>
            <span class="pyq-badge qno">${question.answerAvailable ? 'Answer key ready' : 'Answer unavailable'}</span>
          </div>
          <h3>Question ${escapeAttr(question.q_no)}</h3>
          <div class="pyq-card-question">${renderQuestionMarkup(question)}</div>
          <div class="pyq-option-list">${options}</div>
          <div class="pyq-card-foot">
            <button type="button" class="pyq-ghost-button" data-pyq-action="toggle-answer" data-pyq-id="${escapeAttr(question.id)}">${revealed ? 'Hide answer' : 'Reveal answer'}</button>
            <div class="pyq-answer-pill${revealed ? ' is-visible' : ''}${question.answerAvailable ? '' : ' is-missing'}">${question.answerAvailable ? `✔ Answer: <b>${escapeAttr(question.answerKey)}</b>${question.answerText ? ` · ${renderText(question.answerText)}` : ''}` : 'Answer key is not available in the current source for this PYQ.'}</div>
            <button type="button" class="pyq-mini-button" data-pyq-action="practice-one" data-pyq-id="${escapeAttr(question.id)}" ${question.answerAvailable ? '' : 'disabled'}>${question.answerAvailable ? 'Practice this' : 'Need answer key'}</button>
          </div>
        </article>`;
    }).join('');

    const remaining = pyqFiltered.length - pyqExploreShown;
    loadMore.hidden = remaining <= 0;
    loadMore.textContent = `Show ${Math.min(PYQ_EXPLORE_BATCH, remaining)} more question${Math.min(PYQ_EXPLORE_BATCH, remaining) === 1 ? '' : 's'}`;
  }

  function practiceProgressPercent() {
    const total = pyqPractice.pool.length || 1;
    const answered = Object.keys(pyqPractice.answers).length;
    return Math.round((answered / total) * 100);
  }

  function renderPractice() {
    const total = pyqPractice.pool.length;
    const answeredCount = Object.keys(pyqPractice.answers).length;
    const practicePercent = total ? practiceProgressPercent() : 0;
    if ($('pyq-practice-total')) $('pyq-practice-total').textContent = total.toLocaleString();
    if ($('pyq-practice-progress')) $('pyq-practice-progress').textContent = `${practicePercent}%`;
    if ($('pyq-practice-correct')) $('pyq-practice-correct').textContent = pyqPractice.correct.toLocaleString();
    if ($('pyq-practice-wrong')) $('pyq-practice-wrong').textContent = pyqPractice.wrong.toLocaleString();
    if ($('pyq-progress-fill')) $('pyq-progress-fill').style.width = `${practicePercent}%`;

    const card = $('pyq-practice-card');
    if (!card) return;
    if (!hasActiveQuestionFilter()) {
      const latest = latestExamName();
      card.innerHTML = `<div class="pyq-empty"><strong>Pick a paper before starting Practice.</strong><p>Use the exam strip, search box or filters to create a focused PYQ set. This avoids throwing the entire archive onto the first screen.</p><div class="pyq-empty-actions"><button type="button" class="pyq-soft-button" data-pyq-action="go-explore">Browse papers</button><button type="button" class="pyq-primary-button" data-pyq-action="practice-latest" ${latest ? '' : 'disabled'}>${latest ? `Practice ${escapeAttr(latest)}` : 'Practice latest paper'}</button></div></div>`;
      return;
    }
    if (!total) {
      const filteredTotal = pyqFiltered.length;
      card.innerHTML = filteredTotal
        ? `<div class="pyq-empty"><strong>No answer-ready questions in this practice set.</strong><p>The current filter matched ${filteredTotal} question${filteredTotal === 1 ? '' : 's'}, but their answer keys are missing in the source. Try another paper or category in Explore mode.</p></div>`
        : `<div class="pyq-empty"><strong>No questions in this practice set.</strong><p>Use search or filters above, then switch back to practice.</p></div>`;
      return;
    }

    const question = pyqPractice.pool[pyqPractice.index];
    const response = pyqPractice.answers[question.id] || null;
    const options = Object.entries(question.options).map(([key, value]) => {
      let className = 'pyq-practice-option';
      if (response) {
        if (key === response.selected && response.correct) className += ' is-selected is-correct';
        else if (key === response.selected && !response.correct) className += ' is-selected is-wrong';
        else if (key === question.answerKey) className += ' is-answer';
      }
      return `
        <button type="button" class="${className}" data-pyq-action="practice-answer" data-pyq-key="${escapeAttr(key)}" ${response ? 'disabled' : ''}>
          <span class="pyq-option-key">${escapeAttr(key)}</span>
          <span class="pyq-option-copy">${renderText(value)}</span>
        </button>`;
    }).join('');

    let feedback = `<div class="pyq-practice-feedback"><strong>Tip:</strong> Tap one option to check the official answer key for this question.</div>`;
    if (response) {
      feedback = response.correct
        ? `<div class="pyq-practice-feedback is-correct"><strong>Correct.</strong> Official answer key: <b>${escapeAttr(question.answerKey)}</b>${question.answerText ? ` · ${renderText(question.answerText)}` : ''}</div>`
        : `<div class="pyq-practice-feedback is-wrong"><strong>Not this one.</strong> Official answer key: <b>${escapeAttr(question.answerKey)}</b>${question.answerText ? ` · ${renderText(question.answerText)}` : ''}</div>`;
    }

    const endLabel = answeredCount >= total
      ? 'Practise again ↺'
      : pyqPractice.pool.findIndex((item) => !pyqPractice.answers[item.id]) >= 0
        ? 'First unanswered ↺'
        : 'Back to start ↺';

    card.innerHTML = `
      <div class="pyq-practice-head">
        <div>
          <h3>Practice question ${pyqPractice.index + 1} of ${total}</h3>
          <div class="pyq-practice-sub">
            <span class="pyq-badge exam">${escapeAttr(question.exam)}</span>
            <span class="pyq-badge category">${escapeAttr(question.category)}</span>
            <span class="pyq-badge type">${escapeAttr(question.type || 'Direct MCQ')}</span>
            <span class="pyq-badge qno">Q ${escapeAttr(question.q_no)}</span>
          </div>
        </div>
        <div class="pyq-practice-hint">Filtered PYQ drill · ${answeredCount.toLocaleString()} answered so far</div>
      </div>
      <div class="pyq-practice-question">${renderQuestionMarkup(question)}</div>
      <div class="pyq-practice-options">${options}</div>
      ${feedback}
      <div class="pyq-practice-nav">
        <button type="button" class="pyq-soft-button" data-pyq-action="practice-prev" ${pyqPractice.index === 0 ? 'disabled' : ''}>← Previous</button>
        <button type="button" class="pyq-soft-button" data-pyq-action="practice-random">Random question</button>
        <button type="button" class="pyq-primary-button" data-pyq-action="practice-next">${pyqPractice.index === total - 1 ? endLabel : (response ? 'Next question →' : 'Skip for now →')}</button>
      </div>`;
  }

  function renderMode() {
    const switcher = $('pyq-mode-switch');
    const exploreButton = $('pyq-mode-explore');
    const practiceButton = $('pyq-mode-practice');
    const explorePane = $('pyq-explore-pane');
    const practicePane = $('pyq-practice-pane');
    if (switcher) switcher.dataset.mode = pyqMode;
    if (exploreButton) exploreButton.classList.toggle('is-active', pyqMode === 'explore');
    if (practiceButton) practiceButton.classList.toggle('is-active', pyqMode === 'practice');
    if (explorePane) explorePane.hidden = pyqMode !== 'explore';
    if (practicePane) practicePane.hidden = pyqMode !== 'practice';
    renderExplore();
    renderPractice();
  }

  function applyFilters(forceReset = false) {
    const { term, exam, category, sort } = currentControls();
    pyqFiltered = hasActiveQuestionFilter()
      ? pyqQuestions
        .filter((item) => (!term || item.search.includes(term))
          && (!exam || item.exam === exam)
          && (!category || item.category === category))
        .sort((left, right) => compareQuestions(left, right, sort))
      : [];
    if (forceReset) pyqExploreShown = PYQ_EXPLORE_BATCH;
    syncPracticePool(forceReset);
    setFiltersOpen(!$('pyq-filter-panel')?.hidden);
    renderExamChips();
    renderActiveFilters();
    renderSummary();
    renderMode();
  }

  function resetFilters() {
    if ($('pyq-search')) $('pyq-search').value = '';
    if ($('pyq-exam-filter')) $('pyq-exam-filter').value = '';
    if ($('pyq-category-filter')) $('pyq-category-filter').value = '';
    if ($('pyq-sort-filter')) $('pyq-sort-filter').value = 'latest';
    applyFilters(true);
  }

  function practiceLatestPaper() {
    const latest = latestExamName();
    if (!latest) return;
    if ($('pyq-exam-filter')) $('pyq-exam-filter').value = latest;
    pyqMode = 'practice';
    applyFilters(true);
  }

  function setMode(mode) {
    pyqMode = mode === 'practice' ? 'practice' : 'explore';
    renderSummary();
    renderMode();
  }

  function toggleAnswer(questionId) {
    if (pyqAnswersRevealed.has(questionId)) pyqAnswersRevealed.delete(questionId);
    else pyqAnswersRevealed.add(questionId);
    renderExplore();
  }

  function findQuestionById(questionId) {
    return pyqFiltered.find((item) => item.id === questionId) || pyqQuestions.find((item) => item.id === questionId) || null;
  }

  function practiceThisQuestion(questionId) {
    const question = findQuestionById(questionId);
    if (!question?.answerAvailable) return;
    setMode('practice');
    const index = pyqPractice.pool.findIndex((item) => item.id === questionId);
    if (index >= 0) {
      pyqPractice.index = index;
      renderPractice();
      $('pyq-practice-pane')?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
    }
  }

  function shufflePracticePool() {
    const pool = pyqFiltered.filter((item) => item.answerAvailable);
    for (let i = pool.length - 1; i > 0; i -= 1) {
      const swapIndex = Math.floor(Math.random() * (i + 1));
      [pool[i], pool[swapIndex]] = [pool[swapIndex], pool[i]];
    }
    pyqPractice = createPracticeState(pool);
    renderPractice();
  }

  function resetPractice() {
    pyqPractice = createPracticeState(pyqFiltered.filter((item) => item.answerAvailable));
    renderPractice();
  }

  function answerPractice(key) {
    const current = pyqPractice.pool[pyqPractice.index];
    if (!current || pyqPractice.answers[current.id]) return;
    const correct = String(key) === current.answerKey;
    pyqPractice.answers[current.id] = { selected: String(key), correct };
    if (correct) pyqPractice.correct += 1;
    else pyqPractice.wrong += 1;
    renderPractice();
  }

  function movePractice(delta) {
    if (!pyqPractice.pool.length) return;
    if (delta === 'random') {
      if (pyqPractice.pool.length === 1) return;
      let nextIndex = pyqPractice.index;
      while (nextIndex === pyqPractice.index) nextIndex = Math.floor(Math.random() * pyqPractice.pool.length);
      pyqPractice.index = nextIndex;
      renderPractice();
      return;
    }
    if (delta > 0 && pyqPractice.index === pyqPractice.pool.length - 1) {
      const unansweredIndex = pyqPractice.pool.findIndex((item) => !pyqPractice.answers[item.id]);
      pyqPractice.index = unansweredIndex >= 0 ? unansweredIndex : 0;
      renderPractice();
      return;
    }
    pyqPractice.index = Math.max(0, Math.min(pyqPractice.pool.length - 1, pyqPractice.index + delta));
    renderPractice();
  }

  function renderLoading() {
    if ($('pyq-results-grid')) $('pyq-results-grid').innerHTML = `<div class="pyq-loading" style="grid-column:1/-1"><strong>Loading BPSC PYQ archive…</strong><p>Please wait while the previous-year question papers are prepared.</p></div>`;
    if ($('pyq-practice-card')) $('pyq-practice-card').innerHTML = `<div class="pyq-loading"><strong>Preparing practice mode…</strong><p>The same filtered paper set will appear here in a moment.</p></div>`;
  }

  function renderError(error) {
    const message = location.protocol === 'file:'
      ? 'This screen needs the project to be served over HTTP so the JSON files inside BPSC PYQ can be read.'
      : 'The BPSC PYQ JSON files could not be loaded right now.';
    const html = `<div class="pyq-error"><strong>PYQ archive could not be loaded.</strong><p>${message}<br><code>${escapeAttr(error?.message || 'Unknown error')}</code></p></div>`;
    if ($('pyq-results-grid')) $('pyq-results-grid').innerHTML = html;
    if ($('pyq-practice-card')) $('pyq-practice-card').innerHTML = html;
  }

  function ensurePyqScreen() {
    if ($('pyq-screen')) return;
    const host = document.createElement('div');
    host.innerHTML = `
      <div class="screen" id="pyq-screen" style="flex-direction:column;">
        <div class="pyq-shell">
          <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <button class="modal-btn modal-btn-secondary" type="button" onclick="backFromPyq()">← Back</button>
            <h2 style="font-family:'Cormorant Garamond',Georgia,serif;font-size:1.08rem;color:var(--text);margin:0;">📜 BPSC PYQ Lab</h2>
            <span class="pyq-hero-badge">Explore papers · search smarter · practise faster</span>
          </div>
          <section class="pyq-hero">
            <div class="pyq-hero-top">
              <div class="pyq-hero-copy">
                <span class="pyq-eyebrow"><i aria-hidden="true"></i>BPSC PREVIOUS YEAR QUESTION BANK</span>
                <h2>One archive. Two ways to use it.</h2>
                <p>Search across all curated BPSC papers, filter by exam or category, then slide into <b>Explore</b> for browsing or <b>Practice</b> for instant drilling from the same filtered PYQ set.</p>
              </div>
            </div>
            <div class="pyq-stat-grid">
              <div class="pyq-stat"><strong id="pyq-total-count">—</strong><span>Questions</span></div>
              <div class="pyq-stat"><strong id="pyq-exam-count">—</strong><span>Exam papers</span></div>
              <div class="pyq-stat"><strong id="pyq-category-count">—</strong><span>Categories</span></div>
            </div>
          </section>
          <div class="pyq-exam-strip" id="pyq-exam-strip" aria-label="Quick filter by exam paper"></div>
          <div class="pyq-mode-switch" id="pyq-mode-switch" data-mode="explore" role="tablist" aria-label="Switch between explore and practice">
            <span class="pyq-mode-thumb" aria-hidden="true"></span>
            <button type="button" class="pyq-mode-btn is-active" id="pyq-mode-explore" data-pyq-mode="explore">Explore</button>
            <button type="button" class="pyq-mode-btn" id="pyq-mode-practice" data-pyq-mode="practice">Practice</button>
          </div>
          <div class="pyq-toolbar">
            <div class="pyq-searchbox">
              <span aria-hidden="true">🔎</span>
              <input id="pyq-search" type="search" placeholder="Search question text, option, paper or topic…" autocomplete="off">
              <button type="button" class="pyq-search-button" id="pyq-search-button">Search</button>
            </div>
            <button type="button" class="pyq-filter-toggle" id="pyq-filter-toggle" aria-expanded="false">⚙ Filters</button>
          </div>
          <div class="pyq-filter-panel" id="pyq-filter-panel" hidden>
            <label>Exam paper<select id="pyq-exam-filter"><option value="">All exam papers</option></select></label>
            <label>Category<select id="pyq-category-filter"><option value="">All categories</option></select></label>
            <label>Sort by<select id="pyq-sort-filter"><option value="latest">Latest paper first</option><option value="oldest">Oldest paper first</option><option value="category">Category A–Z</option></select></label>
            <div class="pyq-filter-actions">
              <button type="button" class="pyq-soft-button" id="pyq-reset-filters">Reset filters</button>
              <div class="pyq-filter-note">Search scans question text and options. Practice mode always uses the currently filtered set.</div>
            </div>
          </div>
          <div class="pyq-active-filters" id="pyq-active-filters"></div>
          <div class="pyq-summarybar">
            <div>
              <strong id="pyq-match-count">0</strong>
              <span id="pyq-match-label">matching questions</span>
            </div>
            <p id="pyq-mode-copy"></p>
          </div>
          <section id="pyq-explore-pane">
            <div class="pyq-results-grid" id="pyq-results-grid"></div>
            <div class="pyq-load-more-wrap"><button type="button" class="pyq-primary-button" id="pyq-load-more" hidden>Show more</button></div>
          </section>
          <section id="pyq-practice-pane" hidden>
            <div class="pyq-practice-top">
              <div class="pyq-practice-metrics">
                <span class="pyq-metric-pill">Set <b id="pyq-practice-total">0</b></span>
                <span class="pyq-metric-pill">Progress <b id="pyq-practice-progress">0%</b></span>
                <span class="pyq-metric-pill">Correct <b id="pyq-practice-correct">0</b></span>
                <span class="pyq-metric-pill">Wrong <b id="pyq-practice-wrong">0</b></span>
              </div>
              <div class="pyq-practice-actions">
                <button type="button" class="pyq-soft-button" id="pyq-practice-reset">Reset set</button>
                <button type="button" class="pyq-soft-button" id="pyq-practice-shuffle">Shuffle set</button>
              </div>
            </div>
            <div class="pyq-progress-track"><div class="pyq-progress-fill" id="pyq-progress-fill"></div></div>
            <div class="pyq-practice-card" id="pyq-practice-card"></div>
          </section>
        </div>
      </div>`;
    const screen = host.firstElementChild;
    document.body.insertBefore(screen, $('printable-pdf-document') || document.body.lastElementChild);

    $('pyq-screen').addEventListener('click', (event) => {
      const modeButton = event.target.closest('[data-pyq-mode]');
      if (modeButton) {
        setMode(modeButton.dataset.pyqMode);
        return;
      }
      const examChip = event.target.closest('[data-pyq-exam]');
      if (examChip) {
        const exam = examChip.dataset.pyqExam || '';
        const examFilter = $('pyq-exam-filter');
        if (examFilter) examFilter.value = examFilter.value === exam ? '' : exam;
        applyFilters(true);
        return;
      }
      const actionNode = event.target.closest('[data-pyq-action]');
      if (!actionNode) return;
      const action = actionNode.dataset.pyqAction;
      if (action === 'clear-filters') resetFilters();
      else if (action === 'toggle-answer') toggleAnswer(actionNode.dataset.pyqId);
      else if (action === 'practice-one') practiceThisQuestion(actionNode.dataset.pyqId);
      else if (action === 'practice-answer') answerPractice(actionNode.dataset.pyqKey);
      else if (action === 'practice-prev') movePractice(-1);
      else if (action === 'practice-next') movePractice(1);
      else if (action === 'practice-random') movePractice('random');
      else if (action === 'go-explore') setMode('explore');
      else if (action === 'practice-latest') practiceLatestPaper();
    });

    $('pyq-search')?.addEventListener('input', () => applyFilters(true));
    $('pyq-search')?.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        applyFilters(true);
      }
    });
    $('pyq-search-button')?.addEventListener('click', () => applyFilters(true));
    $('pyq-filter-toggle')?.addEventListener('click', () => setFiltersOpen($('pyq-filter-panel')?.hidden));
    $('pyq-exam-filter')?.addEventListener('change', () => applyFilters(true));
    $('pyq-category-filter')?.addEventListener('change', () => applyFilters(true));
    $('pyq-sort-filter')?.addEventListener('change', () => applyFilters(true));
    $('pyq-reset-filters')?.addEventListener('click', resetFilters);
    $('pyq-load-more')?.addEventListener('click', () => {
      pyqExploreShown += PYQ_EXPLORE_BATCH;
      renderExplore();
    });
    $('pyq-practice-reset')?.addEventListener('click', resetPractice);
    $('pyq-practice-shuffle')?.addEventListener('click', shufflePracticePool);
  }

  function placeNavPyqButton() {
    const navButton = $('nav-pyq');
    const searchButton = $('nav-search');
    const chips = $('nav-chips-row');
    if (!navButton || !searchButton || !searchButton.parentNode || !chips) return;
    if (window.innerWidth <= 599) {
      if (navButton.parentElement !== chips) chips.appendChild(navButton);
    } else if (navButton.parentElement !== searchButton.parentNode) {
      searchButton.parentNode.insertBefore(navButton, searchButton);
    }
  }

  function injectPyqTriggers() {
    const booksScreen = $('books-screen');
    const notesButton = booksScreen?.querySelector('.books-notes-fab');
    if (booksScreen && notesButton) {
      let stack = $('books-floating-actions');
      if (!stack) {
        stack = document.createElement('div');
        stack.id = 'books-floating-actions';
        stack.className = 'books-floating-actions';
        booksScreen.appendChild(stack);
      }
      if (notesButton.parentElement !== stack) stack.appendChild(notesButton);
      if (!$('books-pyq-fab')) {
        const pyqButton = document.createElement('button');
        pyqButton.id = 'books-pyq-fab';
        pyqButton.className = 'books-notes-fab books-pyq-fab';
        pyqButton.type = 'button';
        pyqButton.innerHTML = '📜 PYQ';
        pyqButton.title = 'Open BPSC PYQ Lab';
        pyqButton.addEventListener('click', () => openPyqScreen());
        stack.appendChild(pyqButton);
      }
    }

    const searchButton = $('nav-search');
    if (searchButton && !$('nav-pyq')) {
      const navButton = document.createElement('button');
      navButton.id = 'nav-pyq';
      navButton.className = 'nav-btn-pill';
      navButton.type = 'button';
      navButton.title = 'Open BPSC PYQ Lab';
      navButton.innerHTML = '📜 <span class="nav-btn-label">PYQ Lab</span>';
      navButton.addEventListener('click', () => openPyqScreen());
      searchButton.parentNode.insertBefore(navButton, searchButton);
    }

    if (typeof layoutSetupNav === 'function') layoutSetupNav();
    placeNavPyqButton();
  }

  function openPyqScreen() {
    pyqReturnScreen = document.body?.dataset?.activeScreen === 'setup-screen' ? 'setup-screen' : 'books-screen';
    ensurePyqScreen();
    showScreen('pyq-screen');
    renderLoading();
    ensurePyqData().then(() => {
      populateFilters();
      updateHeroStats();
      applyFilters(pyqFiltered.length === 0);
    }).catch(renderError);
  }

  function backFromPyq() {
    if (pyqReturnScreen === 'setup-screen') {
      showScreen('setup-screen');
      if (typeof buildDashboard === 'function') buildDashboard();
      return;
    }
    showScreen('books-screen');
    if (typeof renderBooksScreen === 'function') renderBooksScreen();
  }

  injectPyqTriggers();
  ensurePyqScreen();
  setFiltersOpen(false);
  window.addEventListener('resize', placeNavPyqButton);

  window.openPyqScreen = openPyqScreen;
  window.backFromPyq = backFromPyq;
}());
