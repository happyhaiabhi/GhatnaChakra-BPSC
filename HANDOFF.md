# Handoff Documentation: Sub-Topics & Export PDF Features

This document details the architecture, design, and verification of the **Sub-topics** and **Export PDF** features implemented in this branch.

---

## 📌 1. Executive Summary

This update adds two major study and offline capabilities to the Ghatna Chakra & MCQ Practise quiz platform:
1. **Sub-topics**: Full hierarchical support for granular sub-topics across books, chapter expanders, quiz setup filters, question cards, review screens, question banks (Mistakes, Bookmarks, Skips, Archive, Bloom Review), and Super Search.
2. **Export PDF & Printable Worksheets**: A comprehensive, zero-dependency PDF generation and printing engine with customizable modes (Practice Worksheet, Study Guide with Inline Solutions, and Attempt Performance Score Report), printable Answer Key matrices, 2-column paper-saving layouts, and standalone offline HTML downloads.

---

## 🏷️ 2. Sub-topics Architecture

### 2.1 Data Model & Normalization
- In `toInternalQuestion(q, subjId, idx, chName)`:
  * Automatically normalizes `q.sub_topic`, `q.subtopic`, `q.topic`, or `q.subTopic` into both `sub_topic` and `topic` properties on the internal question object.
  * Preserved across question bank storage, bookmark notes, attempt history, and Super Search index.
  * Real-world fixture: **Crown Bihar General Studies** (`books/crown/`) contains 867 questions mapped across 149 distinct sub-topics (e.g. *Inscriptions*, *Archaeology*, *Buddhist Texts*, *Vedic Sources*, *Ashokan Edicts*, *Mauryan Administration*).

### 2.2 Setup Screen & Chapter View
- **Expandable Sub-topic Drawers**: When a chapter has questions categorized by sub-topic, a sub-topic badge (e.g. `5 sub-topics ▾`) is rendered on the chapter row. Clicking the badge expands a clean list of sub-topics with individual question counts.
- **Fine-Grained Selection**: Users can select either the whole chapter or toggle specific sub-topics. Selecting a sub-topic automatically selects the parent chapter.
- **Config Panel Filter Chips**: When selected chapters contain sub-topics, a dedicated "Sub-topics" section renders in the Config Panel with interactive chips, showing real-time question counts and enabling one-click scoping of the practice test.

### 2.3 UI Badges & Question Presentation
- Whenever a question has a `sub_topic`, a sleek purple petal pill (`📌 {sub_topic}`) is rendered alongside the chapter name and question type badge across:
  * Active Quiz cards (`#question-area`)
  * Result Review items (`#review-body`)
  * Mistakes, Bookmarks, Skips, Archive, and Bloom Review cards
  * Super Search result items

### 2.4 Question Bank & Super Search Filtering
- **Bank Dropdown Filters**: Mistakes, Bookmarks, Skips, and Archive screens now feature a dynamic `Sub-topic` filter dropdown that populates based on the active bank and selected chapter.
- **Super Search**: Super Search indexes `sub_topic` in the full-text search string and provides a dedicated Sub-topic dropdown filter in the search scope bar.

---

## 📄 3. Export PDF & Printable Worksheets

### 3.1 Supported Export Surfaces
Users can trigger the Export PDF workflow from anywhere in the app:
1. **Result Screen**: `📄 Export PDF` button exports the completed test with user answers, correct answers, performance summary, and full explanations.
2. **Attempt History**: Each past attempt in the History list and Details view has a `📄 PDF` / `📄 Export PDF` action.
3. **Question Banks**: `📄 Export PDF` button on Mistakes, Bookmarks, Skips, Archive, and Bloom Review screens exports the currently filtered collection.
4. **Setup Screen (Config Panel)**: `📄 Export PDF Practice Sheet` button exports selected chapters and sub-topics as an offline mock test paper.
5. **Super Search**: `📄 Export PDF` button exports active search results.

### 3.2 Export Modes & Customization
The `export-pdf-modal` allows candidates and teachers to customize the output before printing or downloading:
- **📝 Practice Paper (`worksheet`)**:
  * Clean mock test question paper format.
  * Numbered questions with options `(A)`, `(B)`, `(C)`, `(D)`.
  * Clean whitespace for rough work.
  * Separate **Answer Key** grid on a dedicated page (`page-break-before: always;`).
  * Optional **Detailed Explanations** appendix on subsequent pages.
- **📖 Study Guide (`with_solutions`)**:
  * Revision booklet format.
  * Verified correct answer highlighted with shaded explanation callout box immediately below each question.
- **📊 Score Report (`result_report`)**:
  * Candidate performance summary banner (Score %, Correct, Wrong, Skipped, Duration).
  * Color-coded user choices (`[✗ Your choice]`, `[✓ Correct]`) and comprehensive explanations.
- **Custom Options**:
  * Toggle Answer Key table.
  * Toggle Detailed Explanations.
  * Toggle Metadata & Sub-topic tags.
  * Toggle 2-Column layout (paper-saving format).

### 3.3 Print Styling (`@media print`)
- Standardized `@page { size: A4 portrait; margin: 12mm 14mm 14mm 14mm; }`.
- Complete suppression of navigation bars, sidebars, modals, floating buttons, and background decorative grids.
- `page-break-inside: avoid;` applied to all question cards to prevent questions from breaking across pages awkwardly.
- Standalone HTML export: `downloadPrintableHtml()` packages the document into a self-contained offline `.html` file with embedded styling and auto-download.

---

## 🧪 4. Testing & Verification

### 4.1 Automated Test Suite (`npm test`)
Run the test suite with:
```bash
npm test
```
The test suite in `tests/test_quiz_webapp.js` validates:
- [x] Loading all 12 BPSC subjects (391 chapters, 4,441 questions).
- [x] Sub-topic parsing and extraction in the Crown book (867 questions, 149 sub-topics).
- [x] Expandable sub-topic drawer in chapter selection.
- [x] Sub-topic selection and question pool scoping.
- [x] Sub-topic pill rendering in Quiz, Review, and Bank items.
- [x] Bank filtering by sub-topic.
- [x] Super Search sub-topic indexing and filtering.
- [x] Export PDF modal opening from Result, Bank, Setup, History, and Super Search.
- [x] Export PDF modes (`worksheet`, `with_solutions`, `result_report`).
- [x] Printable document DOM structure, Answer Key appendix, and Explanations appendix.
- [x] Standalone offline HTML download generation.
- [x] All 10 books in `books/books.json` loading with zero console/JSDOM errors.

---

## 🛠️ 5. Maintenance & Extension Guide

### Adding Sub-topics to New Question Banks
To include sub-topics in any existing or new JSON book file:
```json
{
  "q": "Which inscription mentions the victory of Pulakeshin II over Harsha?",
  "options": {
    "A": "Aihole Inscription",
    "B": "Allahabad Pillar Inscription",
    "C": "Junagadh Inscription",
    "D": "Hathigumpha Inscription"
  },
  "answer": "A",
  "topic": "Inscriptions",
  "explanation": "The Aihole inscription composed by Ravikirti describes the defeat of Harsha by Pulakeshin II on the banks of Narmada."
}
```
The application will automatically detect the `topic` (or `sub_topic`) field, compute counts, render expander drawers, provide filter chips, and display sub-topic tags.
