/* print / PDF export
   Extracted verbatim from bpsc/index.html — see tools/split-bpsc.js. */
let currentExportSource = null;
let currentExportConfig = {
  mode: 'with_solutions',
  includeAnswers: true,
  includeExplanations: true,
  includeMetadata: true,
  twoColumn: false,
  fontSize: 'standard'
};

function openExportModal(sourceType, extraParam) {
  currentExportConfig = {
    mode: sourceType === 'setup' ? 'worksheet' : (sourceType === 'result' || sourceType === 'history') ? 'result_report' : 'with_solutions',
    includeAnswers: true,
    includeExplanations: true,
    includeMetadata: true,
    twoColumn: false,
    fontSize: 'standard'
  };

  if (sourceType === 'result') {
    const subj = SUBJECTS_CONFIG.find(s => s.id === currentSubjectId);
    currentExportSource = {
      type: 'result',
      questions: quiz,
      results: lastResults,
      title: `${currentBook ? currentBook.title : 'BPSC'} Quiz Result`,
      subject: subj?.name || 'Quiz',
      chapter: quizMeta.chapter || '',
      subtopic: quizMeta.subtopic || '',
      meta: {
        pct: Math.round(lastResults.filter(r => r.isCorrect).length / (quiz.length || 1) * 100),
        correct: lastResults.filter(r => r.isCorrect).length,
        wrong: lastResults.filter(r => !r.isCorrect && !r.isSkipped).length,
        skip: lastResults.filter(r => r.isSkipped).length,
        durationMs: new Date() - quizMeta.startTime
      }
    };
    finishOpenExportModal();
  } else if (sourceType === 'history') {
    const a = getAttempts().find(x => x.id === extraParam);
    if (!a) { alert('Attempt not found.'); return; }
    buildAttemptResults(a).then(results => {
      currentExportSource = {
        type: 'history',
        questions: results.map(r => r.q),
        results,
        title: `${a.subject || 'Quiz'} Attempt Result`,
        subject: a.subject || 'Quiz',
        chapter: a.chapter || '',
        meta: {
          pct: a.pct ?? Math.round((a.correct || 0) / (results.length || 1) * 100),
          correct: a.correct ?? results.filter(r => r.isCorrect).length,
          wrong: a.wrong ?? results.filter(r => !r.isCorrect && !r.isSkipped).length,
          skip: a.skip ?? results.filter(r => r.isSkipped).length,
          durationMs: a.durationMs || 0
        }
      };
      finishOpenExportModal();
    }).catch(() => { alert('Could not load attempt data.'); });
    return;
  } else if (['mistake', 'bookmark', 'skip', 'archive', 'bloom'].includes(sourceType)) {
    let bank;
    if (sourceType === 'bloom') {
      const bloomDue = bloomFilteredDue();
      bank = Object.fromEntries(bloomDue.map(e => [e.uid, e]));
    } else {
      bank = filteredBank({
        mistake: getMistakes,
        bookmark: getBookmarks,
        skip: getSkips,
        archive: getArchive
      }[sourceType](), sourceType);
    }
    const questions = Object.values(bank).map(e => e.q).filter(Boolean);
    if (!questions.length) { alert('No questions in this filter to export.'); return; }
    const bankLabel = { mistake: 'Mistakes', bookmark: 'Bookmarks', skip: 'Skipped Questions', archive: 'Archive', bloom: 'Bloom Review' }[sourceType];
    currentExportSource = {
      type: sourceType,
      questions,
      results: [],
      title: `${currentBook ? currentBook.title : 'BPSC'} — ${bankLabel} Revision Sheet`,
      subject: currentBook ? currentBook.title : 'Question Bank',
      chapter: chapterFilters[sourceType] || 'All Chapters',
      subtopic: subtopicFilters[sourceType] || ''
    };
    finishOpenExportModal();
  } else if (sourceType === 'setup') {
    let pool = allQuestions.filter(q => selectedChapters.has(q.chapter));
    if (selectedSubtopics.size > 0) pool = pool.filter(q => selectedSubtopics.has(q.sub_topic));
    if (!pool.length) { alert('No questions selected to export.'); return; }
    const range = getQuestionSelectionRange(pool.length);
    const rangeSuffix = (range.from !== 1 || range.to !== pool.length) ? ` (Q${range.from}–${range.to})` : '';
    pool = pool.slice(range.from - 1, range.to);
    const subj = SUBJECTS_CONFIG.find(s => s.id === currentSubjectId);
    currentExportSource = {
      type: 'setup',
      questions: pool,
      results: [],
      title: `${subj ? subj.name : 'Practice Paper'} — Practice Worksheet${rangeSuffix}`,
      subject: subj?.name || 'Practice',
      chapter: (Array.from(selectedChapters).join(', ') || 'All Chapters') + rangeSuffix,
      subtopic: Array.from(selectedSubtopics).join(', ') || ''
    };
    finishOpenExportModal();
  } else if (sourceType === 'supersearch') {
    const results = superSearchState.lastResults || [];
    if (!results.length) { alert('No search results to export.'); return; }
    const qInput = document.getElementById('supersearch-input')?.value || '';
    currentExportSource = {
      type: 'supersearch',
      questions: results.map(r => r.q),
      results: [],
      title: `Search Results — "${qInput}"`,
      subject: 'Search Collection',
      chapter: document.getElementById('supersearch-subject')?.value || 'All Subjects',
      subtopic: document.getElementById('supersearch-subtopic')?.value || ''
    };
    finishOpenExportModal();
  }
}

function finishOpenExportModal() {
  if (!currentExportSource) return;
  const docTitleInput = document.getElementById('export-doc-title');
  if (docTitleInput) docTitleInput.value = currentExportSource.title || 'Practice Sheet';
  setExportMode(currentExportConfig.mode);
  updateExportSummary();
  document.getElementById('export-pdf-modal')?.classList.remove('hidden');
}

function closeExportModal() {
  document.getElementById('export-pdf-modal')?.classList.add('hidden');
}

function setExportMode(mode) {
  currentExportConfig.mode = mode;
  ['worksheet', 'solutions', 'report'].forEach(m => {
    const id = 'export-mode-' + (m === 'solutions' ? 'solutions' : m === 'report' ? 'report' : 'worksheet');
    const el = document.getElementById(id);
    if (el) el.classList.toggle('active', (m === 'solutions' && mode === 'with_solutions') || (m === 'report' && mode === 'result_report') || (m === 'worksheet' && mode === 'worksheet'));
  });
  updateExportSummary();
}

function updateExportSummary() {
  if (!currentExportSource) return;
  currentExportConfig.title = document.getElementById('export-doc-title')?.value || currentExportSource.title;
  currentExportConfig.includeAnswers = document.getElementById('export-opt-answers')?.checked ?? true;
  currentExportConfig.includeExplanations = document.getElementById('export-opt-explanations')?.checked ?? true;
  currentExportConfig.includeMetadata = document.getElementById('export-opt-metadata')?.checked ?? true;
  currentExportConfig.twoColumn = document.getElementById('export-opt-twocol')?.checked ?? false;

  const count = (currentExportSource.questions || []).length;
  const countEl = document.getElementById('export-summary-count');
  if (countEl) countEl.textContent = `📋 ${count} question${count !== 1 ? 's' : ''} ready to export`;
}

function buildPrintableDocument(source, config) {
  const questions = source.questions || [];
  const results = source.results || [];
  const title = config.title || source.title || (currentBook ? currentBook.title : 'Practice Question Paper');
  const subjectName = source.subject || (SUBJECTS_CONFIG.find(s => s.id === currentSubjectId)?.name || 'General Studies');
  const chapterName = source.chapter || (Array.from(selectedChapters).join(', ') || 'All Chapters');
  const subtopicName = source.subtopic || '';
  const isResultReport = config.mode === 'result_report';
  const isSolutions = config.mode === 'with_solutions' || isResultReport;
  const isWorksheet = config.mode === 'worksheet';
  const twoCol = config.twoColumn;

  let resultBannerHtml = '';
  if (isResultReport && source.meta) {
    const meta = source.meta;
    resultBannerHtml = `
      <div class="pdf-result-banner">
        <div class="pdf-res-stat"><div class="pdf-res-stat-val" style="color:#b8860b;">${meta.pct ?? (questions.length ? Math.round((meta.correct || 0) / questions.length * 100) : 0)}%</div><div class="pdf-res-stat-lbl">Score</div></div>
        <div class="pdf-res-stat"><div class="pdf-res-stat-val" style="color:#16a34a;">${meta.correct ?? 0}</div><div class="pdf-res-stat-lbl">Correct</div></div>
        <div class="pdf-res-stat"><div class="pdf-res-stat-val" style="color:#dc2626;">${meta.wrong ?? 0}</div><div class="pdf-res-stat-lbl">Wrong</div></div>
        <div class="pdf-res-stat"><div class="pdf-res-stat-val" style="color:#64748b;">${meta.skip ?? 0}</div><div class="pdf-res-stat-lbl">Skipped</div></div>
        <div class="pdf-res-stat"><div class="pdf-res-stat-val" style="color:#0284c7;">${formatDuration(meta.durationMs || 0)}</div><div class="pdf-res-stat-lbl">Time Taken</div></div>
      </div>`;
  }

  const dateStr = new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });

  let questionsHtml = questions.map((q, idx) => {
    const res = results[idx] || (results.find && results.find(r => r.q && r.q.uid === q.uid));
    const userKey = res ? res.userKey : null;
    const isCorrect = res ? res.isCorrect : false;
    const isSkipped = res ? res.isSkipped : (userKey == null);

    const qNum = idx + 1;
    const presentation = renderQuestionStem(q, 'quiz');
    const qType = presentation.type;
    const matchData = presentation.matchData;
    const correctKeys = questionCorrectKeys(q);
    const correctLabel = questionCorrectAnswerLabel(q);
    const options = q.options || {};
    const optKeys = Object.keys(options);

    const tags = [];
    if (config.includeMetadata) {
      if (q.exam) tags.push(`<span class="pdf-tag">${escapeHtml(q.exam + (q.year ? ' ' + q.year : ''))}</span>`);
      if (q.chapter) tags.push(`<span class="pdf-tag">${escapeHtml(q.chapter)}</span>`);
      if (q.sub_topic) tags.push(`<span class="pdf-tag pdf-tag-subtopic">&#x1F4CD; ${escapeHtml(q.sub_topic)}</span>`);
      tags.push(`<span class="pdf-tag">${escapeHtml(qType)}</span>`);
    }

    let optionsHtml = '';
    if (matchData) {
      optionsHtml = `
        <div style="margin-top:6pt;font-weight:700;font-size:7.5pt;text-transform:uppercase;color:#475569;">Answer Codes:</div>
        <div class="pdf-options-list">
          ${matchData.codeRows.map(row => {
            const isUser = isResultReport && answerHasKey(userKey, row.key);
            const isAns = isSolutions && answerHasKey(correctKeys, row.key);
            let cls = 'pdf-opt-row';
            if (isUser && !isCorrect) cls += ' pdf-user-choice';
            if (isAns) cls += ' pdf-correct-choice';
            return `<div class="${cls}">
              <span class="pdf-opt-marker">(${escapeHtml(row.key.toLowerCase())})</span>
              <span>${row.codes ? row.codes.join(' - ') : bookText(row.value)}</span>
              ${isUser && !isAns ? '<b style="color:#dc2626;font-size:7.5pt;margin-left:auto;">[\u2717 Your choice]</b>' : ''}
              ${isAns && isResultReport ? '<b style="color:#16a34a;font-size:7.5pt;margin-left:auto;">[\u2713 Correct]</b>' : ''}
            </div>`;
          }).join('')}
        </div>`;
    } else {
      optionsHtml = `<div class="pdf-options-list">
        ${optKeys.map(k => {
          const val = options[k];
          if (val == null || val === '') return '';
          const isUser = isResultReport && answerHasKey(userKey, k);
          const isAns = isSolutions && answerHasKey(correctKeys, k);
          let cls = 'pdf-opt-row';
          if (isUser && !isCorrect) cls += ' pdf-user-choice';
          if (isAns) cls += ' pdf-correct-choice';
          return `<div class="${cls}">
            <span class="pdf-opt-marker">(${escapeHtml(k)})</span>
            <span class="pdf-opt-text">${escapeHtml(optionDisplayText(val, k))}</span>
            ${isUser && !isAns ? '<b style="color:#dc2626;font-size:7.5pt;margin-left:auto;">[\u2717 Your choice]</b>' : ''}
            ${isAns && isResultReport ? '<b style="color:#16a34a;font-size:7.5pt;margin-left:auto;">[\u2713 Correct]</b>' : ''}
          </div>`;
        }).join('')}
      </div>`;
    }

    let solBoxHtml = '';
    if (isSolutions && (config.includeExplanations || config.includeAnswers)) {
      solBoxHtml = `
        <div class="pdf-solution-box">
          <div class="pdf-sol-header">
            <span>Solution &amp; Explanation</span>
            ${config.includeAnswers ? `<span class="pdf-sol-ans">&#x2713; Correct: ${bookText(correctLabel || correctKeys.join(', '))}</span>` : ''}
          </div>
          ${config.includeExplanations && q.explanation ? `<div style="margin-top:3pt;">${bookText(q.explanation)}</div>` : ''}
          ${q.note ? `<div style="margin-top:3pt;color:#92400e;font-size:8pt;"><b>Note:</b> ${bookText(q.note)}</div>` : ''}
        </div>`;
    }

    return `
      <div class="pdf-q-item">
        <div class="pdf-q-top">
          <span class="pdf-q-num">Q${qNum}.</span>
          <div class="pdf-q-tags">${tags.join('')}</div>
        </div>
        <div class="pdf-q-stem">${presentation.html}</div>
        ${optionsHtml}
        ${solBoxHtml}
      </div>`;
  }).join('');

  let answerKeyHtml = '';
  if (isWorksheet && config.includeAnswers) {
    answerKeyHtml = `
      <div class="pdf-page-break">
        <div class="pdf-section-title">Answer Key</div>
        <div class="pdf-key-grid">
          ${questions.map((q, idx) => {
            const correctKeys = questionCorrectKeys(q);
            return `
              <div class="pdf-key-cell">
                <div class="pdf-key-qnum">Q${idx + 1}</div>
                <div class="pdf-key-ans">${escapeHtml(correctKeys.join('+') || '—')}</div>
              </div>`;
          }).join('')}
        </div>
      </div>`;
  }

  let explanationsAppendixHtml = '';
  if (isWorksheet && config.includeExplanations) {
    explanationsAppendixHtml = `
      <div class="pdf-page-break">
        <div class="pdf-section-title">Detailed Explanations</div>
        <div style="display:flex;flex-direction:column;gap:10pt;margin-top:10pt;">
          ${questions.map((q, idx) => {
            const correctLabel = questionCorrectAnswerLabel(q);
            if (!q.explanation && !correctLabel) return '';
            return `
              <div class="pdf-solution-box" style="page-break-inside:avoid;break-inside:avoid;">
                <div class="pdf-sol-header">
                  <span>Question ${idx + 1}</span>
                  <span class="pdf-sol-ans">&#x2713; Answer: ${bookText(correctLabel)}</span>
                </div>
                ${q.explanation ? `<div style="margin-top:3pt;">${bookText(q.explanation)}</div>` : ''}
                ${q.note ? `<div style="margin-top:3pt;color:#92400e;font-size:8pt;"><b>Note:</b> ${bookText(q.note)}</div>` : ''}
              </div>`;
          }).join('')}
        </div>
      </div>`;
  }

  return `
    <div class="pdf-document ${twoCol ? 'pdf-layout-2col' : ''}">
      <div class="pdf-doc-header">
        <div class="pdf-header-top">
          <div>
            <div class="pdf-doc-brand">${escapeHtml(currentBook ? currentBook.title : 'MCQ Practise')} &middot; Ghatna Chakra BPSC</div>
            <div class="pdf-doc-title">${escapeHtml(title)}</div>
            <div class="pdf-doc-subtitle">${escapeHtml(subjectName)}${chapterName ? ' &middot; ' + escapeHtml(chapterName) : ''}${subtopicName ? ' &middot; &#x1F4CD; ' + escapeHtml(subtopicName) : ''}</div>
          </div>
          <div class="pdf-header-meta-box">
            <span class="pdf-meta-pill">${dateStr}</span>
            <span class="pdf-meta-pill">${questions.length} Question${questions.length !== 1 ? 's' : ''}</span>
            <span class="pdf-meta-pill">${isWorksheet ? 'Time: ' + Math.ceil(questions.length * 1.2) + ' mins' : (isResultReport ? 'Result Sheet' : 'Study Guide')}</span>
          </div>
        </div>
      </div>
      ${resultBannerHtml}
      <div class="pdf-questions-list">
        ${questionsHtml}
      </div>
      ${answerKeyHtml}
      ${explanationsAppendixHtml}
      <div class="pdf-doc-footer">
        <span>Ghatna Chakra BPSC &middot; MCQ Practise &middot; Prepared on ${dateStr}</span>
        <span>Page 1 of 1</span>
      </div>
    </div>`;
}

function executePrint() {
  if (!currentExportSource) return;
  updateExportSummary();
  const btn = document.getElementById('export-print-btn');
  const originalHtml = btn ? btn.innerHTML : null;
  if (btn) { btn.disabled = true; btn.innerHTML = '&#9203; Preparing&hellip;'; }
  // Yield to the browser so the "Preparing…" state paints before the
  // (potentially large) printable document is built.
  setTimeout(() => {
    let frame = null;
    try {
      const docHtml = buildPrintableDocument(currentExportSource, currentExportConfig);
      const fullHtml = buildPrintableFullHtml(docHtml);
      frame = document.createElement('iframe');
      frame.setAttribute('aria-hidden', 'true');
      frame.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;visibility:hidden;';
      document.body.appendChild(frame);
      const doc = frame.contentDocument || frame.contentWindow.document;
      doc.open(); doc.write(fullHtml); doc.close();
      if (btn) { btn.disabled = false; btn.innerHTML = originalHtml; }
      closeExportModal();
      // Print from the lightweight iframe document instead of the full app
      // document, so the browser does not have to render the app's heavy DOM
      // and stylesheet — this makes the print dialog open much faster.
      setTimeout(() => {
        try { frame.contentWindow.focus(); frame.contentWindow.print(); }
        catch (e) { alert('Could not open the print dialog. Please try again.'); }
        setTimeout(() => { if (frame && frame.parentNode) frame.parentNode.removeChild(frame); }, 1000);
      }, 250);
    } catch (e) {
      console.error('PDF export failed:', e);
      if (btn) { btn.disabled = false; btn.innerHTML = originalHtml; }
      if (frame && frame.parentNode) frame.parentNode.removeChild(frame);
      alert('Could not prepare the document for print. Please try again.');
    }
  }, 60);
}

// Shared, self-contained print/export stylesheet. Kept deliberately small so a
// hidden iframe document lays out quickly, and kept black & white for print.
const PRINTABLE_CSS = `
@page{ size:A4 portrait; margin:12mm 14mm 14mm 14mm; }
*{ box-sizing:border-box; }
body{ background:#fff !important; color:#0f172a !important; padding:0; margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; font-size:9.5pt; line-height:1.45; }
#printable-pdf-document{ display:block !important; }
.pdf-doc-header{ border-bottom:2px solid #0f172a; padding-bottom:8pt; margin-bottom:12pt; display:flex; flex-direction:column; gap:4pt; }
.pdf-header-top{ display:flex; align-items:flex-start; justify-content:space-between; gap:10pt; }
.pdf-doc-brand{ font-size:8pt; letter-spacing:1.5px; text-transform:uppercase; color:#94a3b8; font-weight:700; }
.pdf-doc-title{ font-size:16pt; font-weight:800; color:#0f172a; line-height:1.2; margin-top:2pt; }
.pdf-doc-subtitle{ font-size:9.5pt; color:#475569; margin-top:2pt; font-weight:600; }
.pdf-header-meta-box{ text-align:right; font-size:8pt; color:#475569; display:flex; flex-direction:column; gap:2pt; flex-shrink:0; }
.pdf-meta-pill{ display:inline-block; background:#f1f5f9; border:1px solid #cbd5e1; padding:2pt 6pt; border-radius:4pt; font-weight:600; }
.pdf-result-banner{ background:#f8fafc; border:1.5px solid #cbd5e1; border-radius:6pt; padding:8pt 12pt; margin-bottom:12pt; display:flex; align-items:center; justify-content:space-around; break-inside:avoid; }
.pdf-res-stat{ text-align:center; }
.pdf-res-stat-val{ font-size:13pt; font-weight:800; line-height:1; }
.pdf-res-stat-lbl{ font-size:7pt; text-transform:uppercase; letter-spacing:0.8px; color:#64748b; margin-top:2pt; font-weight:600; }
.pdf-layout-2col .pdf-questions-list{ column-count:2; column-gap:16pt; }
.pdf-q-item{ margin-bottom:12pt; padding-bottom:8pt; border-bottom:0.5pt solid #e2e8f0; break-inside:avoid; }
.pdf-q-top{ display:flex; align-items:baseline; gap:6pt; margin-bottom:4pt; }
.pdf-q-num{ font-weight:800; font-size:10pt; color:#0f172a; flex-shrink:0; }
.pdf-q-tags{ display:flex; gap:4pt; flex-wrap:wrap; font-size:6.5pt; margin-left:auto; }
.pdf-tag{ border:0.5pt solid #cbd5e1; padding:1pt 4pt; border-radius:3pt; color:#475569; font-weight:600; text-transform:uppercase; }
.pdf-tag-subtopic{ background:#faf5ff; border-color:#d8b4fe; color:#6b21a8; }
.pdf-q-stem{ font-size:9.5pt; color:#0f172a; line-height:1.45; margin-bottom:6pt; white-space:normal; }
.pdf-q-stem img{ max-height:140pt; max-width:90%; display:block; margin:6pt auto; border:0.5pt solid #cbd5e1; border-radius:4pt; }
.pdf-options-list{ display:grid; grid-template-columns:1fr 1fr; gap:3pt 8pt; margin-top:4pt; }
.pdf-opt-row{ display:flex; align-items:baseline; gap:5pt; font-size:9pt; line-height:1.35; padding:2pt 4pt; border-radius:3pt; }
.pdf-opt-marker{ font-weight:700; color:#475569; font-size:8pt; flex-shrink:0; }
.pdf-opt-text{ color:#0f172a; }
.pdf-opt-row.pdf-user-choice{ background:#fee2e2; border-left:2pt solid #dc2626; }
.pdf-opt-row.pdf-correct-choice{ background:#dcfce7; border-left:2pt solid #16a34a; font-weight:600; }
.pdf-solution-box{ margin-top:6pt; background:#f8fafc; border:0.75pt solid #cbd5e1; border-left:3pt solid #0284c7; border-radius:3pt; padding:5pt 8pt; font-size:8.5pt; line-height:1.4; break-inside:avoid; }
.pdf-sol-header{ display:flex; align-items:center; justify-content:space-between; font-size:7.5pt; font-weight:700; text-transform:uppercase; color:#0369a1; margin-bottom:3pt; }
.pdf-sol-ans{ color:#16a34a; font-weight:800; }
.pdf-page-break{ page-break-before:always; margin-top:20pt; }
.pdf-section-title{ font-size:13pt; font-weight:800; color:#0f172a; border-bottom:1.5pt solid #0f172a; padding-bottom:4pt; margin:14pt 0 10pt 0; }
.pdf-key-grid{ display:grid; grid-template-columns:repeat(10,1fr); gap:4pt; margin-top:8pt; font-size:8.5pt; text-align:center; }
.pdf-key-cell{ border:0.5pt solid #cbd5e1; border-radius:3pt; padding:3pt 2pt; background:#f8fafc; }
.pdf-key-qnum{ font-size:7pt; color:#64748b; }
.pdf-key-ans{ font-size:9pt; font-weight:800; color:#0f172a; margin-top:1pt; }
.pdf-doc-footer{ margin-top:20pt; padding-top:6pt; border-top:0.5pt solid #cbd5e1; display:flex; align-items:center; justify-content:space-between; font-size:7pt; color:#94a3b8; }
/* Structured stems (assertion/reason, numbered & lettered statements, match lists) */
.q-text{ white-space:normal; }
.structured-stem{ white-space:normal; display:flex; flex-direction:column; gap:6pt; }
.structured-intro,.structured-instruction{ white-space:pre-wrap; line-height:1.5; }
.structured-instruction{ padding:5pt 8pt; border-left:2.5pt solid #64748b; background:#f1f5f9; border-radius:0 3pt 3pt 0; font-weight:600; font-size:8.5pt; }
.assertion-reason-grid{ display:grid; grid-template-columns:1fr 1fr; gap:6pt; }
.ar-card{ background:#f8fafc; border:0.75pt solid #cbd5e1; border-radius:4pt; padding:5pt 8pt; min-width:0; }
.ar-card.assertion-card{ border-top:2.5pt solid #334155; }
.ar-card.reason-card{ border-top:2.5pt solid #64748b; }
.ar-label{ display:block; font-size:7pt; font-weight:800; letter-spacing:0.5px; text-transform:uppercase; color:#475569; margin-bottom:3pt; }
.ar-text{ white-space:pre-wrap; line-height:1.5; overflow-wrap:anywhere; }
.statement-list,.lettered-list{ display:flex; flex-direction:column; gap:4pt; }
.statement-row,.lettered-row{ display:grid; grid-template-columns:20pt minmax(0,1fr); gap:6pt; align-items:start; padding:4pt 7pt; background:#f8fafc; border:0.75pt solid #cbd5e1; border-radius:3pt; }
.statement-label,.lettered-label{ display:flex; align-items:center; justify-content:center; min-width:16pt; height:16pt; border-radius:3pt; background:#e2e8f0; color:#0f172a; font-weight:700; font-size:7.5pt; }
.lettered-label{ background:#f1f5f9; color:#334155; }
.statement-text,.lettered-text{ white-space:pre-wrap; line-height:1.5; overflow-wrap:anywhere; }
.match-paper{ border:0.75pt solid #cbd5e1; border-radius:4pt; padding:5pt 8pt; background:#f8fafc; }
.match-prompt{ font-weight:600; margin-bottom:4pt; font-size:8.5pt; }
.match-list-heads,.match-list-row{ display:grid; grid-template-columns:1fr 1fr; gap:6pt; }
.match-list-head{ font-weight:700; font-size:7.5pt; text-transform:uppercase; color:#475569; border-bottom:0.75pt solid #cbd5e1; padding-bottom:2pt; }
.match-list-rows{ display:flex; flex-direction:column; gap:2pt; margin-top:3pt; }
.match-cell{ display:flex; gap:4pt; font-size:8.5pt; }
.match-cell-label{ font-weight:700; flex-shrink:0; }
.match-list-title{ font-weight:600; text-transform:none; font-size:7.5pt; color:#64748b; margin-left:4pt; }
.q-asset{ margin:6pt 0 0; padding:0; }
.q-asset img{ display:block; max-width:100%; height:auto; border-radius:3pt; border:0.5pt solid #cbd5e1; background:#fff; padding:4pt; }
`;

function buildPrintableFullHtml(docHtml) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeHtml(currentExportConfig.title || 'Document')}</title>
<style>${PRINTABLE_CSS}</style>
</head>
<body>
<div id="printable-pdf-document">${docHtml}</div>
</body>
</html>`;
}

function downloadPrintableHtml() {
  if (!currentExportSource) return;
  updateExportSummary();
  const docHtml = buildPrintableDocument(currentExportSource, currentExportConfig);
  const fullHtml = buildPrintableFullHtml(docHtml);
  try {
    const blob = new Blob([fullHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (currentExportConfig.title || 'Question_Paper').replace(/[^a-z0-9_-]+/gi, '_') + '.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e) {
    console.warn('HTML download fallback:', e);
  }
}

// Configure the running app for a chosen book: point data paths at its folder,
// rebuild SUBJECTS_CONFIG from its chapters.json, and reset all caches/state.
