/* UPSC Question Bank — static, dependency-free search and rendering. */
const $ = (id) => document.getElementById(id);
const BATCH_SIZE = 20;
const OPTION_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const FILTER_IDS = ['examFilter', 'yearFilter', 'subjectFilter', 'difficultyFilter'];
const EXAM_ORDER = { Prelims: 0, CSAT: 1, Mains: 2 };
const BROWSE_MODES = ['prelims', 'neutral', 'mains'];

const BROWSE_PAPERS = {
  prelims: [
    {
      key: 'prelims-gs1', exam: 'Prelims', category: '', tone: 'prelims', icon: '◎',
      label: 'General Studies Paper I', shortLabel: 'GS Paper I',
      description: 'History, polity, economy, geography, environment, science and current affairs.'
    },
    {
      key: 'prelims-csat', exam: 'CSAT', category: '', tone: 'csat', icon: '∑',
      label: 'CSAT Paper II', shortLabel: 'CSAT Paper II',
      description: 'Reading comprehension, reasoning, decision making and quantitative aptitude.'
    }
  ],
  mains: [
    {
      key: 'mains-gs1', exam: 'Mains', category: 'GS Paper I', tone: 'mains', icon: 'I',
      label: 'General Studies Paper I', shortLabel: 'GS Paper I',
      description: 'Culture, history, society and geography.'
    },
    {
      key: 'mains-gs2', exam: 'Mains', category: 'GS Paper II', tone: 'mains', icon: 'II',
      label: 'General Studies Paper II', shortLabel: 'GS Paper II',
      description: 'Governance, Constitution, polity and international relations.'
    },
    {
      key: 'mains-gs3', exam: 'Mains', category: 'GS Paper III', tone: 'mains', icon: 'III',
      label: 'General Studies Paper III', shortLabel: 'GS Paper III',
      description: 'Economy, technology, environment, security and disaster management.'
    },
    {
      key: 'mains-gs4', exam: 'Mains', category: 'GS Paper IV', tone: 'mains', icon: 'IV',
      label: 'General Studies Paper IV', shortLabel: 'GS Paper IV',
      description: 'Ethics, integrity, aptitude and case studies.'
    },
    {
      key: 'mains-essay', exam: 'Mains', category: 'Essay', tone: 'essay', icon: '✎',
      label: 'Essay Paper', shortLabel: 'Essay',
      description: 'Previous-year essay topics and themes.'
    },
    {
      key: 'mains-philosophy-1', exam: 'Mains', category: 'Philosophy Paper I', tone: 'optional', icon: 'ΦI',
      label: 'Philosophy Paper I', shortLabel: 'Philosophy I',
      description: 'Optional subject — history and problems of philosophy.'
    },
    {
      key: 'mains-philosophy-2', exam: 'Mains', category: 'Philosophy Paper II', tone: 'optional', icon: 'ΦII',
      label: 'Philosophy Paper II', shortLabel: 'Philosophy II',
      description: 'Optional subject — socio-political and philosophy of religion.'
    }
  ]
};

let questions = [];
let visible = [];
let shown = BATCH_SIZE;
let browseMode = 'neutral';
let selectedPaper = null;
let selectedYear = null;
let switchAnimationTimer = null;
let lastFocusedBeforeSearch = null;
let searchDrawerTimer = null;

const escapeHtml = (value = '') => String(value).replace(
  /[&<>'"]/g,
  (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  })[character]
);

const CATEGORY_LABELS = {
  'art-and-culture': 'Art & Culture',
  'art-culture': 'Art & Culture',
  'current-affairs': 'Current Affairs',
  economy: 'Economy',
  environment: 'Environment',
  geography: 'Geography',
  history: 'History',
  'logical reasoning': 'Logical Reasoning',
  'decision making': 'Decision Making',
  other: 'Other',
  polity: 'Polity & Governance',
  'polity-and-governance': 'Polity & Governance',
  'quantitative aptitude': 'Quantitative Aptitude',
  'reading comprehension': 'Reading Comprehension',
  'science-and-technology': 'Science & Technology',
  'science-technology': 'Science & Technology'
};

const PAPER_LABELS = {
  Essay: 'Essay',
  GS1: 'GS Paper I',
  GS2: 'GS Paper II',
  GS3: 'GS Paper III',
  GS4: 'GS Paper IV',
  Philosophy_Paper_I: 'Philosophy Paper I',
  Philosophy_Paper_II: 'Philosophy Paper II'
};

function titleCase(value) {
  return String(value)
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function categoryLabel(value, fallback = 'General') {
  const clean = String(value || '').trim();
  if (!clean) return fallback;
  return CATEGORY_LABELS[clean.toLowerCase()] || titleCase(clean);
}

function paperLabel(value) {
  return PAPER_LABELS[value] || titleCase(value || 'Paper');
}

function optionText(option) {
  if (option && typeof option === 'object') return option.text ?? option.label ?? '';
  return option ?? '';
}

function optionKey(option, index) {
  if (option && typeof option === 'object' && option.key) return String(option.key).toUpperCase();
  return OPTION_LETTERS[index] || String(index + 1);
}

function questionNumber(question) {
  if (question.exam === 'CSAT') {
    const match = String(question.id || '').match(/(\d{3})$/);
    return match ? Number(match[1]) : question.position || '';
  }
  if (question.exam === 'Prelims') {
    return String(question.id || '').split('_').pop() || '';
  }
  return question.q_no || '';
}

function searchBlob(parts) {
  return parts
    .flat(Infinity)
    .filter((part) => part !== undefined && part !== null)
    .map((part) => String(part))
    .join(' ')
    .toLowerCase();
}

function flattenPrelims(data) {
  /* Four rows in the older GS compilation point to CSAT GS02 pages. The richer
     CSAT dataset contains those questions, so exclude them here to keep the
     collections genuinely separate and avoid duplicate search results. */
  return Object.values(data.records_by_year || {}).flat()
    .filter((question) => !/UPSCCSAT/i.test(String(question.reference_url || '')))
    .map((question) => {
    const category = categoryLabel(question.subject);
    return {
      ...question,
      year: Number(question.year),
      exam: 'Prelims',
      category,
      sourceUrl: question.reference_url,
      search: searchBlob([
        question.id,
        question.question,
        (question.options || []).map(optionText),
        question.subject,
        category
      ])
    };
  });
}

function flattenCSAT(data) {
  return (data.questions || []).map((question) => {
    const category = categoryLabel(question.subject, 'General Aptitude');
    return {
      ...question,
      year: Number(question.year),
      exam: 'CSAT',
      category,
      sourceUrl: question.url,
      search: searchBlob([
        question.id,
        question.question,
        (question.options || []).map(optionText),
        question.answer,
        question.explanation,
        question.subject,
        category,
        'Paper II qualifying aptitude'
      ])
    };
  });
}

function flattenMains(data) {
  const output = [];
  for (const [year, papers] of Object.entries(data.papers_by_year || {})) {
    for (const [paper, packet] of Object.entries(papers || {})) {
      const category = paperLabel(paper);
      for (const question of packet.questions || []) {
        output.push({
          ...question,
          year: Number(year),
          exam: 'Mains',
          category,
          sourceUrl: question.url,
          search: searchBlob([
            question.question,
            paper,
            category,
            question.tags || [],
            question.difficulty,
            question.marks,
            question.words
          ])
        });
      }
    }
  }
  return output;
}

function unique(values) {
  return [...new Set(values.filter((value) => value !== undefined && value !== null && value !== ''))]
    .sort((a, b) => String(a).localeCompare(String(b), undefined, { numeric: true }));
}

function fillSelect(id, values, defaultLabel) {
  const node = $(id);
  const previousValue = node.value;
  node.innerHTML = `<option value="">${escapeHtml(defaultLabel)}</option>${values
    .map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
    .join('')}`;
  node.value = previousValue;
}

function updateFilterLists() {
  const exam = $('examFilter').value;
  const scope = questions.filter((question) => !exam || question.exam === exam);
  const years = unique(scope.map((question) => question.year)).sort((a, b) => b - a);
  const categories = unique(scope.map((question) => question.category));
  const difficulties = unique(scope.map((question) => question.difficulty));

  fillSelect('yearFilter', years, 'All years');
  fillSelect('subjectFilter', categories, 'All subjects & papers');
  fillSelect('difficultyFilter', difficulties, 'All difficulty levels');
  $('difficultyFilter').disabled = difficulties.length === 0;
}

function setStats() {
  const counts = questions.reduce((result, question) => {
    result[question.exam] = (result[question.exam] || 0) + 1;
    return result;
  }, {});
  const total = questions.length.toLocaleString();
  const prelims = (counts.Prelims || 0).toLocaleString();
  const csat = (counts.CSAT || 0).toLocaleString();
  const mains = (counts.Mains || 0).toLocaleString();
  $('questionCount').textContent = total;
  $('prelimsCount').textContent = prelims;
  $('csatCount').textContent = csat;
  $('mainsCount').textContent = mains;
  if ($('browsePrelimsCount')) $('browsePrelimsCount').textContent = prelims;
  if ($('browseCsatCount')) $('browseCsatCount').textContent = csat;
  if ($('browseMainsCount')) $('browseMainsCount').textContent = mains;
}

function paperQuestions(config) {
  return questions.filter((question) => (
    question.exam === config.exam && (!config.category || question.category === config.category)
  ));
}

function configureContextualFinder(config) {
  $('search').classList.remove('system-prelims', 'system-csat', 'system-mains');
  $('search').classList.add(`system-${config.exam.toLowerCase()}`);
  updateFilterLists();
  $('subjectFilterGroup').hidden = false;
  $('difficultyFilterGroup').hidden = false;
  $('subjectFilterLabel').textContent = config.exam === 'Mains' ? 'Paper' : config.exam === 'CSAT' ? 'Skill / category' : 'Subject';
  $('keyword').placeholder = config.exam === 'CSAT'
    ? 'Try “comprehension”, “ratio”, “reasoning”…'
    : config.exam === 'Mains'
      ? `Search ${config.shortLabel} or any Mains topic…`
      : 'Try “federalism”, “monsoon”, “Buddhism”…';
}

function updateContextHeading() {
  if ($('search').hidden) return;
  const exam = $('examFilter').value;
  const year = $('yearFilter').value || 'All years';
  const category = $('subjectFilter').value;
  let system;
  if (!exam) {
    $('questionStageKicker').textContent = 'SEARCH RESULTS';
    $('questionStageTitle').textContent = year === 'All years' ? 'All UPSC questions' : `All UPSC questions — ${year}`;
    return;
  }
  if (exam === 'Prelims') system = 'GS Paper I';
  else if (exam === 'CSAT') system = 'CSAT Paper II';
  else system = category || (selectedPaper?.exam === 'Mains' ? selectedPaper.shortLabel : 'Mains');
  $('questionStageKicker').textContent = exam === 'Mains' ? 'MAINS QUESTION SYSTEM' : 'PRELIMS QUESTION SYSTEM';
  $('questionStageTitle').textContent = `${system} — ${year}`;
}

function openGlobalSearch() {
  clearTimeout(searchDrawerTimer);
  lastFocusedBeforeSearch = document.activeElement;
  $('searchScrim').hidden = false;
  $('globalSearchDrawer').setAttribute('aria-hidden', 'false');
  $('globalSearchButton').setAttribute('aria-expanded', 'true');
  document.body.classList.add('search-drawer-open');
  requestAnimationFrame(() => {
    $('searchScrim').classList.add('is-open');
    $('globalSearchDrawer').classList.add('is-open');
  });
  setTimeout(() => $('keyword').focus(), 120);
}

function closeGlobalSearch(restoreFocus = true) {
  $('searchScrim').classList.remove('is-open');
  $('globalSearchDrawer').classList.remove('is-open');
  $('globalSearchDrawer').setAttribute('aria-hidden', 'true');
  $('globalSearchButton').setAttribute('aria-expanded', 'false');
  document.body.classList.remove('search-drawer-open');
  searchDrawerTimer = setTimeout(() => { $('searchScrim').hidden = true; }, 260);
  if (restoreFocus) lastFocusedBeforeSearch?.focus?.();
}

function showGlobalSearchResults() {
  $('search').hidden = false;
  const exam = $('examFilter').value;
  $('search').classList.remove('system-prelims', 'system-csat', 'system-mains');
  if (exam) $('search').classList.add(`system-${exam.toLowerCase()}`);
  updateActivePath();
  updateContextHeading();
  render();
  closeGlobalSearch(false);
  location.hash = 'search';
  setTimeout(() => $('search').scrollIntoView?.({ behavior: 'smooth', block: 'start' }), 30);
}

function updateBuilderProgress() {
  const hasExamMode = browseMode !== 'neutral';
  const steps = {
    progressExam: hasExamMode ? 'is-complete' : 'is-active',
    progressPaper: hasExamMode ? (selectedPaper ? 'is-complete' : 'is-active') : '',
    progressYear: selectedPaper ? (selectedYear ? 'is-complete' : 'is-active') : '',
    progressQuestions: selectedYear ? 'is-active' : ''
  };
  for (const [id, className] of Object.entries(steps)) {
    $(id).className = className;
  }
}

function renderPaperChoices() {
  const configs = BROWSE_PAPERS[browseMode];
  if (!configs) {
    $('paperChoices').innerHTML = '';
    return;
  }
  $('paperStageKicker').textContent = browseMode === 'prelims' ? 'PRELIMS' : 'MAINS';
  $('paperStageTitle').textContent = browseMode === 'prelims' ? 'Choose GS Paper I or CSAT' : 'Choose a Mains paper';
  $('paperChoices').classList.toggle('mains-paper-grid', browseMode === 'mains');
  $('paperChoices').innerHTML = configs.map((config) => {
    const matches = paperQuestions(config);
    const years = unique(matches.map((question) => question.year));
    const selected = selectedPaper?.key === config.key;
    return `<button class="paper-choice ${escapeHtml(config.tone)}${selected ? ' is-selected' : ''}" type="button" data-paper-key="${escapeHtml(config.key)}" aria-pressed="${selected}">
      <span class="paper-choice-icon" aria-hidden="true">${escapeHtml(config.icon)}</span>
      <span class="paper-choice-copy">
        <strong>${escapeHtml(config.label)}</strong>
        <em>${escapeHtml(config.description)}</em>
        <small>${matches.length.toLocaleString()} questions <span aria-hidden="true">·</span> ${years.length} years</small>
      </span>
      <i aria-hidden="true">→</i>
    </button>`;
  }).join('');
}

function renderYears() {
  if (!selectedPaper) {
    $('yearStage').hidden = true;
    $('yearChoices').innerHTML = '';
    return;
  }

  const matches = paperQuestions(selectedPaper);
  const counts = matches.reduce((result, question) => {
    result[question.year] = (result[question.year] || 0) + 1;
    return result;
  }, {});
  const years = Object.keys(counts).map(Number).sort((a, b) => b - a);

  $('yearStageKicker').textContent = `${browseMode === 'prelims' ? 'PRELIMS' : 'MAINS'} · ${selectedPaper.shortLabel}`;
  $('yearStageTitle').textContent = `Select year — ${selectedPaper.shortLabel}`;
  $('yearChoices').innerHTML = years.map((year) => {
    const count = counts[year];
    const selected = selectedYear === year;
    return `<button class="year-choice${selected ? ' is-selected' : ''}" type="button" data-year="${year}" aria-pressed="${selected}">
      <strong>${year}</strong>
      <small>${count.toLocaleString()} question${count === 1 ? '' : 's'}</small>
      <span aria-hidden="true">→</span>
    </button>`;
  }).join('');
  $('yearStage').hidden = false;
}

function setBrowseMode(mode, animate = true) {
  const modeValues = { prelims: 0, neutral: 1, mains: 2 };
  if (!(mode in modeValues)) return;
  const changed = browseMode !== mode;
  browseMode = mode;
  selectedPaper = null;
  selectedYear = null;
  $('search').hidden = true;
  $('activePath').hidden = true;

  const switchNode = $('examModeSwitch');
  switchNode.classList.remove('is-prelims', 'is-neutral', 'is-mains');
  switchNode.classList.add(`is-${mode}`);
  switchNode.setAttribute('aria-valuenow', String(modeValues[mode]));
  switchNode.setAttribute('aria-valuetext', mode === 'prelims' ? 'Prelims' : mode === 'mains' ? 'Mains' : 'Resting position');

  for (const [buttonId, buttonMode] of [['prelimsMode', 'prelims'], ['mainsMode', 'mains']]) {
    const active = mode === buttonMode;
    $(buttonId).classList.toggle('is-active', active);
    $(buttonId).setAttribute('aria-pressed', String(active));
  }

  $('modeDescription').textContent = mode === 'prelims'
    ? 'Choose between General Studies Paper I and the qualifying CSAT Paper II.'
    : mode === 'mains'
      ? 'Choose a General Studies, Essay or available optional-subject paper.'
      : 'Choose Prelims or Mains. The graduation cap marks the resting position.';

  if (animate && changed) {
    clearTimeout(switchAnimationTimer);
    switchNode.classList.remove('is-switching');
    requestAnimationFrame(() => switchNode.classList.add('is-switching'));
    switchAnimationTimer = setTimeout(() => switchNode.classList.remove('is-switching'), 650);
  }

  $('paperStage').hidden = mode === 'neutral';
  if (mode === 'neutral') {
    $('paperChoices').innerHTML = '';
    renderYears();
    updateBuilderProgress();
    return;
  }

  renderPaperChoices();
  renderYears();
  updateBuilderProgress();
}

function selectPaper(key) {
  const config = (BROWSE_PAPERS[browseMode] || []).find((paper) => paper.key === key);
  if (!config) return;
  selectedPaper = config;
  selectedYear = null;
  $('search').hidden = true;
  $('activePath').hidden = true;
  renderPaperChoices();
  renderYears();
  updateBuilderProgress();

  requestAnimationFrame(() => {
    $('yearStage').classList.remove('stage-arrive');
    requestAnimationFrame(() => $('yearStage').classList.add('stage-arrive'));
  });
}

function openSelectedYear(year) {
  if (!selectedPaper || !Number.isFinite(year)) return;
  selectedYear = year;
  renderYears();
  updateBuilderProgress();

  $('keyword').value = '';
  $('examFilter').value = selectedPaper.exam;
  configureContextualFinder(selectedPaper);
  $('yearFilter').value = String(year);
  $('subjectFilter').value = selectedPaper.category || '';
  $('difficultyFilter').value = '';
  $('search').hidden = false;
  filterQuestions();

  requestAnimationFrame(() => {
    $('search').classList.remove('stage-arrive');
    requestAnimationFrame(() => $('search').classList.add('stage-arrive'));
  });
  location.hash = 'search';
  setTimeout(() => $('search').scrollIntoView?.({ behavior: 'smooth', block: 'start' }), 30);
}

function updateActivePath() {
  const exam = $('examFilter').value;
  const year = $('yearFilter').value;
  const category = $('subjectFilter').value;
  if (!exam || !year) {
    $('activePath').hidden = true;
    return;
  }

  let path;
  if (exam === 'Prelims') path = `Prelims › GS Paper I › ${year}`;
  else if (exam === 'CSAT') path = `Prelims › CSAT Paper II › ${year}`;
  else path = `Mains › ${category || 'All papers'} › ${year}`;
  $('activePathText').textContent = path;
  $('activePath').hidden = false;
}

function sortNumber(question) {
  const match = String(questionNumber(question)).match(/\d+/);
  return match ? Number(match[0]) : 0;
}

function filterQuestions() {
  const term = $('keyword').value.trim().toLowerCase();
  const exam = $('examFilter').value;
  const year = $('yearFilter').value;
  const category = $('subjectFilter').value;
  const difficulty = $('difficultyFilter').value;
  const sort = $('sortFilter').value;

  visible = questions.filter((question) => (
    (!term || question.search.includes(term)) &&
    (!exam || question.exam === exam) &&
    (!year || String(question.year) === year) &&
    (!category || question.category === category) &&
    (!difficulty || question.difficulty === difficulty)
  ));

  visible.sort((a, b) => {
    if (sort === 'old') {
      return a.year - b.year || EXAM_ORDER[a.exam] - EXAM_ORDER[b.exam] || sortNumber(a) - sortNumber(b);
    }
    if (sort === 'paper') {
      return String(a.category).localeCompare(String(b.category)) || b.year - a.year || sortNumber(a) - sortNumber(b);
    }
    return b.year - a.year || EXAM_ORDER[a.exam] - EXAM_ORDER[b.exam] || sortNumber(a) - sortNumber(b);
  });

  $('clearSearch').hidden = term.length === 0;
  shown = BATCH_SIZE;
  updateActivePath();
  updateContextHeading();
  render();
}

function formatInline(value) {
  return escapeHtml(value)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function formatQuestionText(value) {
  let safe = formatInline(String(value || '').replace(/\r/g, ''));
  safe = safe.replace(
    /(^|\n)(\s*)(Statement\s*[-–—]?\s*[IVX]+:?|\(?\d+\)?[.)]|[IVX]+[.)])(?=\s)/gim,
    '$1$2<span class="statement-marker">$3</span>'
  );
  return safe.replace(/\n/g, '<br>');
}

function splitPassage(value, question) {
  const text = String(value || '').replace(/\r/g, '').trim();
  if (question.exam !== 'CSAT' || text.length < 220) return null;

  const explicitQuestion = text.lastIndexOf('\n\nQuestion:');
  if (explicitQuestion > 120) {
    return {
      passage: text.slice(0, explicitQuestion).trim(),
      prompt: text.slice(explicitQuestion + 2).replace(/^Question:\s*/i, '').trim()
    };
  }

  const isLikelyPassage = question.category === 'Reading Comprehension' || /^(?:read|passage)/i.test(text);
  if (!isLikelyPassage) return null;

  const questionStart = /\n+(?=(?:According(?:\s+to)?|Which|What|With reference|Consider|The passage|Why|How|In the context|Based on|The issue|The author)\b)/gi;
  let match;
  while ((match = questionStart.exec(text)) !== null) {
    if (match.index > 120) {
      return {
        passage: text.slice(0, match.index).trim(),
        prompt: text.slice(match.index).trim()
      };
    }
  }
  return null;
}

function renderQuestionBody(question) {
  const split = splitPassage(question.question, question);
  if (!split) return `<div class="question-text">${formatQuestionText(question.question)}</div>`;
  return `
    <div class="passage-block">
      <span class="passage-label">Passage</span>
      <div>${formatQuestionText(split.passage)}</div>
    </div>
    <div class="question-prompt">${formatQuestionText(split.prompt)}</div>`;
}

function formatSolution(value) {
  const lines = String(value || '').replace(/\r/g, '').split('\n');
  const output = [];
  let paragraph = [];
  let unordered = [];
  let ordered = [];

  const flushParagraph = () => {
    if (paragraph.length) output.push(`<p>${paragraph.map(formatInline).join('<br>')}</p>`);
    paragraph = [];
  };
  const flushUnordered = () => {
    if (unordered.length) output.push(`<ul>${unordered.map((line) => `<li>${formatInline(line)}</li>`).join('')}</ul>`);
    unordered = [];
  };
  const flushOrdered = () => {
    if (ordered.length) output.push(`<ol>${ordered.map((line) => `<li>${formatInline(line)}</li>`).join('')}</ol>`);
    ordered = [];
  };
  const flushAll = () => {
    flushParagraph();
    flushUnordered();
    flushOrdered();
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      flushAll();
      continue;
    }
    const heading = line.match(/^#{1,4}\s+(.+)$/);
    const bullet = line.match(/^(?:[-*•])\s+(.+)$/);
    const number = line.match(/^\d+[.)]\s+(.+)$/);
    if (heading) {
      flushAll();
      output.push(`<h4>${formatInline(heading[1])}</h4>`);
    } else if (bullet) {
      flushParagraph();
      flushOrdered();
      unordered.push(bullet[1]);
    } else if (number) {
      flushParagraph();
      flushUnordered();
      ordered.push(number[1]);
    } else {
      flushUnordered();
      flushOrdered();
      paragraph.push(line);
    }
  }
  flushAll();
  return output.join('');
}

function correctAnswerKey(question) {
  if (typeof question.answer === 'string') {
    const answer = question.answer.trim().toUpperCase();
    if (/^[A-Z]$/.test(answer)) return answer;
    if (/^\d+$/.test(answer)) return OPTION_LETTERS[Number(answer)] || answer;
    return answer;
  }
  const index = Number(question.answer);
  return Number.isInteger(index) && index >= 0 ? OPTION_LETTERS[index] || String(index + 1) : '—';
}

function safeWebUrl(value) {
  if (!value) return '';
  try {
    const url = new URL(String(value));
    return ['http:', 'https:'].includes(url.protocol) ? escapeHtml(url.href) : '';
  } catch {
    return '';
  }
}

function safeLocalPath(value) {
  const path = String(value || '').replace(/\\/g, '/');
  if (!path || path.startsWith('/') || path.includes('..') || !/^[\w./-]+$/.test(path)) return '';
  return escapeHtml(path);
}

function renderOptions(question) {
  if (!Array.isArray(question.options) || question.options.length === 0) return '';
  return `<ol class="options">${question.options.map((option, index) => `
    <li>
      <span class="option-key">${escapeHtml(optionKey(option, index))}</span>
      <span>${formatQuestionText(optionText(option))}</span>
    </li>`).join('')}</ol>`;
}

function renderExplanation(question, answerKey) {
  if (question.exam === 'Mains') return '';
  const sourceUrl = safeWebUrl(question.sourceUrl);

  if (question.exam === 'CSAT') {
    return `<details class="explanation csat-explanation">
      <summary><span class="explain-icon" aria-hidden="true">✦</span> Show detailed solution</summary>
      <div class="explanation-body">
        <div class="answer-callout"><span aria-hidden="true">✓</span><div><small>CORRECT ANSWER</small><strong>Option ${escapeHtml(answerKey)}</strong></div></div>
        <div class="solution-copy">${formatSolution(question.explanation)}</div>
        ${sourceUrl ? `<a class="source-link" href="${sourceUrl}" target="_blank" rel="noopener">Open original question ↗</a>` : ''}
      </div>
    </details>`;
  }

  return `<details class="explanation">
    <summary><span class="explain-icon" aria-hidden="true">✦</span> Show explanation</summary>
    <div class="explanation-body">
      <div class="answer-callout"><span aria-hidden="true">✓</span><div><small>ANSWER KEY</small><strong>Option ${escapeHtml(answerKey)}</strong></div></div>
      <p>The supplied Prelims GS compilation contains the official answer key but not the full written solution.</p>
      ${sourceUrl ? `<a class="source-link" href="${sourceUrl}" target="_blank" rel="noopener">Open original question page ↗</a>` : ''}
    </div>
  </details>`;
}

function renderInfographic(question) {
  if (question.exam !== 'CSAT' && question.exam !== 'Prelims') return '';
  const localUrl = safeLocalPath(question.infographic_local);
  const remoteUrl = safeWebUrl(question.infographic_url);
  const imageUrl = localUrl || remoteUrl;
  if (!imageUrl) return '';
  const number = questionNumber(question);
  const alt = `Solution infographic for UPSC ${question.exam} ${question.year} question ${number}`;

  return `<details class="infographic">
    <summary><span class="infographic-icon" aria-hidden="true">▧</span> View solution infographic</summary>
    <div class="infographic-body">
      <a href="${remoteUrl || imageUrl}" target="_blank" rel="noopener" title="Open full-size infographic">
        <img src="${imageUrl}"${remoteUrl && localUrl ? ` data-fallback="${remoteUrl}"` : ''} loading="lazy" decoding="async" alt="${escapeHtml(alt)}" />
      </a>
      <p>Tap the infographic to open the full-size source image.</p>
    </div>
  </details>`;
}

function renderDetails(question) {
  const parts = [];
  if (question.exam === 'Prelims') parts.push(`Subject: ${escapeHtml(question.category)}`);
  if (question.exam === 'CSAT') parts.push('Paper II (qualifying)', `Subject: ${escapeHtml(question.category)}`);
  if (question.exam === 'Mains') {
    if (question.marks) parts.push(`${escapeHtml(question.marks)} marks`);
    if (question.words) parts.push(`${escapeHtml(question.words)} words`);
    if (Array.isArray(question.tags) && question.tags.length) parts.push(escapeHtml(question.tags.join(', ')));
  }
  if (question.id) parts.push(`ID: ${escapeHtml(question.id)}`);
  return parts.join(' <span aria-hidden="true">·</span> ');
}

function card(question) {
  const objective = question.exam === 'Prelims' || question.exam === 'CSAT';
  const answerKey = objective ? correctAnswerKey(question) : '';
  const examClass = question.exam.toLowerCase();
  const number = questionNumber(question);
  const label = `Question${number !== '' ? ` ${number}` : ''}`;
  const sourceUrl = safeWebUrl(question.sourceUrl);

  return `<article class="question-card ${examClass}-question">
    <div class="q-head">
      <span class="badge ${examClass}">${escapeHtml(question.exam)}</span>
      <span class="badge year">${escapeHtml(question.year)}</span>
      <span class="badge subject">${escapeHtml(question.category)}</span>
      ${question.difficulty ? `<span class="badge diff">${escapeHtml(titleCase(question.difficulty))}</span>` : ''}
    </div>
    <h3 class="question-label">${escapeHtml(label)}</h3>
    ${renderQuestionBody(question)}
    ${objective ? renderOptions(question) : ''}
    ${objective ? `<div class="answer">Answer key: <strong>${escapeHtml(answerKey)}</strong></div>` : ''}
    ${renderExplanation(question, answerKey)}
    ${renderInfographic(question)}
    <div class="card-meta">
      <p class="details">${renderDetails(question)}</p>
      ${sourceUrl && question.exam === 'Mains' ? `<a href="${sourceUrl}" target="_blank" rel="noopener">Original source ↗</a>` : ''}
    </div>
  </article>`;
}

function render() {
  const exam = $('examFilter').value;
  const resultDescription = `${visible.length.toLocaleString()}${exam ? ` ${exam}` : ''} question${visible.length === 1 ? '' : 's'} found`;
  $('resultsLabel').textContent = resultDescription;
  $('resultsHeading').textContent = resultDescription;
  $('results').innerHTML = visible.length
    ? visible.slice(0, shown).map(card).join('')
    : '<div class="empty"><b>No matching questions.</b><br>Try another keyword or clear a filter.</div>';

  const remaining = Math.max(0, visible.length - shown);
  $('loadMore').hidden = remaining === 0;
  $('loadMore').textContent = `Show ${Math.min(BATCH_SIZE, remaining)} more question${Math.min(BATCH_SIZE, remaining) === 1 ? '' : 's'}`;
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

async function loadData() {
  const fallback = window.UPSC_QUESTION_BANK_DATA;
  if (location.protocol === 'file:') {
    if (!fallback) throw new Error('Offline data bundle is missing.');
    return fallback;
  }

  try {
    const [prelims, csat, mains] = await Promise.all([
      fetchJson('data/prelims.json'),
      fetchJson('data/csat.json'),
      fetchJson('data/mains.json')
    ]);
    return { prelims, csat, mains };
  } catch (error) {
    if (fallback) {
      console.warn('JSON fetch failed; using bundled fallback.', error);
      return fallback;
    }
    throw error;
  }
}

async function init() {
  try {
    const { prelims, csat, mains } = await loadData();
    questions = [
      ...flattenPrelims(prelims || {}),
      ...flattenCSAT(csat || {}),
      ...flattenMains(mains || {})
    ];
    setStats();
    setBrowseMode('neutral', false);
    updateFilterLists();
    filterQuestions();
  } catch (error) {
    $('results').innerHTML = '<div class="error"><b>Data could not be loaded.</b><br>Keep <code>data.js</code> beside <code>index.html</code>, or serve the complete project folder with <code>python -m http.server 8000</code>.</div>';
    $('resultsLabel').textContent = 'Unable to load data';
    $('resultsHeading').textContent = 'Unable to load data';
    console.error(error);
  }
}

$('keyword').addEventListener('input', filterQuestions);
FILTER_IDS.forEach((id) => $(id).addEventListener('change', () => {
  if (id === 'examFilter') {
    updateFilterLists();
    const exam = $('examFilter').value;
    $('subjectFilterLabel').textContent = exam === 'Mains' ? 'Paper' : exam === 'CSAT' ? 'Skill / category' : 'Subject / paper';
    $('subjectFilterGroup').hidden = false;
    $('difficultyFilterGroup').hidden = false;
  }
  filterQuestions();
}));
$('sortFilter').addEventListener('change', filterQuestions);
$('clearSearch').addEventListener('click', () => {
  $('keyword').value = '';
  $('keyword').focus();
  filterQuestions();
});
$('resetFilters').addEventListener('click', () => {
  FILTER_IDS.forEach((id) => { $(id).value = ''; });
  $('keyword').value = '';
  $('subjectFilterLabel').textContent = 'Subject / paper';
  $('subjectFilterGroup').hidden = false;
  $('difficultyFilterGroup').hidden = false;
  updateFilterLists();
  filterQuestions();
});
$('loadMore').addEventListener('click', () => {
  shown += BATCH_SIZE;
  render();
});

$('globalSearchButton').addEventListener('click', openGlobalSearch);
$('closeSearchDrawer').addEventListener('click', () => closeGlobalSearch());
$('searchScrim').addEventListener('click', () => closeGlobalSearch());
$('refineSearchButton').addEventListener('click', openGlobalSearch);
$('viewSearchResults').addEventListener('click', showGlobalSearchResults);
$('keyword').addEventListener('keydown', (event) => {
  if (event.key === 'Enter') showGlobalSearchResults();
});
document.addEventListener('keydown', (event) => {
  const target = event.target;
  const typing = target?.matches?.('input, textarea, select, [contenteditable="true"]');
  if (event.key === '/' && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
    event.preventDefault();
    openGlobalSearch();
  } else if (event.key === 'Escape' && $('globalSearchDrawer').classList.contains('is-open')) {
    closeGlobalSearch();
  }
});

$('examModeSwitch').addEventListener('click', (event) => {
  const rect = event.currentTarget.getBoundingClientRect?.();
  if (event.detail !== 0 && rect?.width && Number.isFinite(event.clientX)) {
    const ratio = Math.max(0, Math.min(0.999, (event.clientX - rect.left) / rect.width));
    setBrowseMode(BROWSE_MODES[Math.floor(ratio * 3)]);
  } else {
    setBrowseMode(BROWSE_MODES[(BROWSE_MODES.indexOf(browseMode) + 1) % BROWSE_MODES.length]);
  }
});
$('examModeSwitch').addEventListener('keydown', (event) => {
  let nextIndex = BROWSE_MODES.indexOf(browseMode);
  if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') nextIndex = Math.max(0, nextIndex - 1);
  else if (event.key === 'ArrowRight' || event.key === 'ArrowUp') nextIndex = Math.min(BROWSE_MODES.length - 1, nextIndex + 1);
  else if (event.key === 'Home') nextIndex = 0;
  else if (event.key === 'End') nextIndex = BROWSE_MODES.length - 1;
  else return;
  event.preventDefault();
  setBrowseMode(BROWSE_MODES[nextIndex]);
});
$('prelimsMode').addEventListener('click', () => setBrowseMode('prelims'));
$('mainsMode').addEventListener('click', () => setBrowseMode('mains'));
$('paperChoices').addEventListener('click', (event) => {
  const button = event.target.closest('[data-paper-key]');
  if (button) selectPaper(button.dataset.paperKey);
});
$('yearChoices').addEventListener('click', (event) => {
  const button = event.target.closest('[data-year]');
  if (button) openSelectedYear(Number(button.dataset.year));
});
$('changePath').addEventListener('click', () => {
  selectedYear = null;
  $('search').hidden = true;
  $('activePath').hidden = true;
  renderYears();
  updateBuilderProgress();
  location.hash = selectedPaper ? 'yearStage' : 'browse';
  const target = selectedPaper ? $('yearStage') : $('browse');
  setTimeout(() => target.scrollIntoView?.({ behavior: 'smooth', block: 'start' }), 30);
});

/* If a local infographic is unavailable, fall back to its original HTTPS source. */
$('results').addEventListener('error', (event) => {
  const image = event.target;
  if (!(image instanceof HTMLImageElement)) return;
  if (image.dataset.fallback && image.src !== image.dataset.fallback) {
    image.src = image.dataset.fallback;
    image.dataset.fallback = '';
  } else {
    image.closest('.infographic-body')?.classList.add('image-unavailable');
  }
}, true);

init();
