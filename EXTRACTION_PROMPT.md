# PDF → Crown Quiz-Engine Extraction Prompt (ALL tests in `New folder/`)

> Repo: `happyhaiabhi/GhatnaChakra-BPSC`
> Source: **all 30 PDFs** in the GitHub folder `New folder/` (branch `main`).
> Series: **“प्रहार” (Prahar) 72nd BPSC Prelims Test Series — Khan Global Studies**.
> Language of OUTPUT: **English only** (question papers are bilingual; extract the English half).
> Target: **one new standalone book per test** under `books/<book_id>/data/`, registered in `books/books.json`.
> Status: **Do not commit, push, open a PR, or deploy until I approve the generated JSON.**

Work on branch `arena/01a02fed-ghatnachakra-bpsc`.

---

## 0. SOURCE INVENTORY (already verified — use this exact map)

The 30 PDFs resolve into **15 tests** (14 have a question paper + an English solution; Test 6 is question-only). One file (`b1ee445b-….pdf`) is a 3-page **test schedule** — **skip it** (it is not a question bank).

Question papers carry a `T.B.C.: 2672xx` code and the subject on page 1. Solutions carry `… Solution English` and answers/explanations.

| Test | Subject (from paper) | T.B.C. | Question Paper (bilingual) | English Solution | Q count |
|---|---|---|---|---|---|
| 1 | BIHAR SPECIAL | 267201 | `Test 1 Question.pdf` | `Test 1 English.pdf` | 150 |
| 2 | WORLD GEOGRAPHY | 267202 | `Test 2 Question.pdf` | `Test 2 English.pdf` | 150 |
| 3 | CURRENT AFFAIRS | 267203 | `Test 3 Question.pdf` | `Test 3 English.pdf` | 150 |
| 4 | INDIAN GEOGRAPHY-I | 267204 | `Test 4.pdf` | `Test 4 English.pdf` | 150 |
| 5 | INDIAN GEOGRAPHY - II | 267205 | `Test 5.pdf` | `Test 5 english.pdf` | 150 |
| 6 | INDIAN ECONOMY | 267206 | `Test 6.pdf` | **NONE (missing)** | 150 |
| 7 | ANCIENT HISTORY | 267207 | `Test 7.pdf` | `Test 7 English.pdf` | 150 |
| 8 | MEDIEVAL HISTORY | 267208 | `Test_08_Medieval_History_Question_Paper_…प्रहार’.pdf` | `Test_08_Medieval_History_Solution_English_…प्रहार’.pdf` | 150 |
| 9 | CURRENT AFFAIRS | 267209 | `Test 9.pdf` | `Test 9 English.pdf` | 150 |
| 10 | BIOLOGY + SCIENCE & TECHNOLOGY | 267210 | `Test - 10 __ Biology + Science and Tech __ Question Paper.pdf` | `Test_10_Biology_+_Science_and_Tech_Solution_English.pdf` | 150 |
| 11 | MODERN HISTORY – I (Arrival of Europeans to 1885) | 267211 | `Test_11_…_Question_Paper.pdf` | `Test_11_…_Solution_English.pdf` | 150 |
| 12 | MODERN HISTORY – II (1885 to 1947 and onwards) | 267212 | `Test_12_…_Question_Paper.pdf` | `Test_12_…_Solution_English.pdf` | 150 |
| 13 (file says “16”) | PHYSICS & CHEMISTRY | 267213 | `Test_16_Physics_+_Chemistry_Question_Paper_…प्रहार’.pdf` | `Test_16_Physics_+_Chemistry_Solution_English_…प्रहार’.pdf` | 150 |
| 14 | CURRENT AFFAIRS (JAN–APR 2026) | 267214 | `Test 14.pdf` | `Test 14 english.pdf` | 150 |
| 15 | POLITY - I | 267215 | `Test 15.pdf` | `Test 15 english.pdf` | 150 |

**Filename numbering mismatch (handle explicitly):** the two `Test_16_…` files are internally **TEST-13** (T.B.C. 267213, solution header “BPSC PRELIMS TEST-13 PHYSICS & CHEMISTRY”). Use `book_id = test_13` and label “Test 13 — Physics & Chemistry” (and note the original filename in the report). Never trust the number in the filename; trust T.B.C. and the internal header.

Download the PDFs via the GitHub blob API (they exceed the 1 MB Contents limit). Keep them in a gitignored folder (`source_pdfs/`, already in `.gitignore`); do not commit PDFs.

All PDFs have a real **text layer** — **no OCR is required.** Do not rasterize whole pages for text; use the text layer (e.g. PyMuPDF).

---

## 1. LAYOUT FACTS (reverse-engineered — code to these)

### 1a. Question paper (bilingual)
- **English questions live on the even-numbered printed pages** (PDF index 1, 3, 5, …), headed `Paper I / <n>`. The odd printed pages (PDF index 2, 4, 6, …) are the **Hindi translation** of the SAME questions and must be **ignored for output** (English only).
  - Verify per file: page 2 (index 1) starts `1.  The …` in English; page 3 (index 2) starts `1.` in Devanagari. Extract English from the `Paper I /` pages that contain Latin question text.
- Page 1 is the cover/instructions (`DO NOT OPEN THIS TEST BOOKLET…`, Time 2 Hours, Max Marks 150, “IMPORTANT INSTRUCTIONS”). Skip it for questions but capture exam metadata (exam = “72nd BPSC Prelims”, series = “प्रहार”, test name, subject, max marks, time).
- Each test has **exactly 150 questions**, numbered `1.`–`150.` A question starts with a line `^\d{1,3}\.\t` (number + TAB) at column 0.
- **Options** are `A.\t`, `B.\t`, `C.\t`, `D.\t` (letter + period + TAB), each on its own line, in printed order. Exactly four options per question in these papers.
- There are no question-critical figures in the question papers: the only images are a repeated 1000×1000 watermark, a small logo, and a 486×151 header banner. **Do not extract these.** (The one genuine figure in the whole set is in the Test-13 *solution* — see §6; it is explanatory, not part of a question stem.)
- The Hindi pages contain OCR-fusion artifacts (e.g. `बि᠎हाार`); these never affect the English pages.

### 1b. Solution (English)
- Cover page, then solutions headed like `BPSC TEST-1 BIHAR SPECIAL (SOLUTION)`.
- Each answer block is:
  ```
  Q <n>.\tAns. <LETTER>
  Explanation:
  \t  <paragraph(s) of explanation>
  ```
  - The `Q` line sometimes has extra whitespace/duplicated numbers, e.g. `Q 10.\t Ans. B`, or `Q 15.\t 15.  Ans. C`. Normalize with a tolerant regex that captures the FIRST question number after `Q` and the FIRST A–D after `Ans.`.
  - Answers are a **single letter A–D** (these are single-answer tests). If you ever encounter two letters, treat as malformed → unverified; do not invent multi-select.
  - The explanation runs until the next `Q <n>.` or end-of-file. Collapse line/hyphenation breaks and preserve paragraph meaning. Explanations may contain bullet-like lines (e.g. `3 East Central Railway (ECR)`) — keep them as text.
- Use the solution **only** for `answer` and `explanation`. The question paper is authoritative for stem and options. If the solution’s `Ans.` letter does not exist in A–D or the question is missing, route to unverified (§8).
- A few solution files appear to “miss” a number under a strict regex (Test 1 Q15, Test 3 Q83, Test 4 Q75, Test 14 Q46, Test 15 Q25/Q48, Test 12 Q56/Q97) — these are whitespace/duplicate-number formatting cases; the tolerant parser above recovers them. Re-verify each is found; any genuinely missing answer goes to unverified.

---

## 2. EXTRACTION ALGORITHM (per test)

1. Open the QP. Read only the English pages (`Paper I / …`, Latin script). Concatenate in page order.
2. Split into questions using `(?m)^\s*(\d{1,3})\.\t` anchors (number+TAB at line start). Reject anchors inside options/body (options are `A.\t` etc., never bare digits). Validate that you get exactly numbers 1–150 in order; report gaps/duplicates.
3. For each question block, separate stem text from options: options begin at the first `(?m)^[A-D]\.\t`; the text before the first option is the stem. Option values run until the next `^[A-D]\.\t` or the next question. Map in order to `A/B/C/D`.
4. Clean text: normalize Unicode (NFC), fix ligatures, replace `\u0007`/control chars, join hard-wrapped lines and hyphenated line breaks (`ener-\ngy` → `energy`), collapse internal whitespace, strip running `Paper I / n` footers and stray TABs. **Do not rewrite wording or “correct” facts.** Preserve typographic characters (₹, –, ’, “ ”).
5. Detect `question_type` per §3 from the cleaned stem + options.
6. Parse the solution into `{n: (answer, explanation)}` with the tolerant regex. Join on question number. Set `answer` to the letter, `explanation` to the cleaned explanation or `""`.
7. Set `exam="72nd BPSC Prelims"`, `year="2026"` (the papers reference 2025–26 events and the schedule is 2026; if a specific test prints a different exam/year on its cover, use that and report it), and `note=""` (or a caveat). Add provenance fields: `original_id` (= printed Q number), `test_number` (internal, e.g. `13`), `tbc` (`267213`), `section`/`topic` if present.
8. Assign the question to a chapter. These are sectional tests on one subject; use the subject as the chapter name, OR if the paper/solution groups questions by sub-topic headings, use those. Do not invent topics. One chapter minimum; preserve question order.

---

## 3. QUESTION-TYPE TAXONOMY (controlled list — engine depends on exact strings)

Every question MUST have a non-empty `question_type` from this list. **Apply structural types BEFORE generic keyword rules.**

- `Standard MCQ — Direct Factual/Conceptual, Single Correct`
- `Multiple Correct — Multiple Options`
- `Assertion and Reason — Standard Relationship Evaluation`
- `Multiple Statements — Correct Combination by Code`
- `Multiple Statements — Incorrect Combination by Code`
- `List and Code — Correct Combination`
- `Match the Following — Two-List Matching — Answer-Code Matrix`
- `Chronological Order — Correct Sequence`
- `Ordering/Ranking — Correct Sequence`
- `Negative/Exception MCQ — Single Correct`
- `Correct Statement — Single Correct`
- `Incorrect Statement — Single Incorrect/Exception`
- `Fill in the Blank — Single Correct`
- `Pair Evaluation — Correctly Matched Pair`
- `Pair Evaluation — Incorrectly Matched Pair`
- `Numerical/Calculation — Single Correct`
- `Data Interpretation — Single Correct`
- `Statement and Conclusion — Logical Inference`
- `Figure/Diagram/Formula — Single Correct`

Detection rules (these papers use several):
1. `Assertion (A):` … `Reason (R):` → **Assertion and Reason** (options are the four standard A/R truth combos).
2. `Match List-I with List-II` (appears as `List-I`/`List-II`, LEFT items labeled `a./b./c./d.`, RIGHT items labeled `1./2./3./4.`, then a code grid `a b c d` over A/B/C/D permutations) → **Match the Following — Two-List Matching — Answer-Code Matrix**.
   - **ENGINE CONVENTION (critical):** the renderer expects **Roman numerals (I,II,III,IV) in the LEFT list and letters (A,B,C,D) in the RIGHT list**. The paper prints lowercase letters on the left and numbers on the right. You MUST relabel when storing the structured lists: left a/b/c/d → I/II/III/IV; right 1/2/3/4 → A/B/C/D. Keep the four answer-code options as A/B/C/D, each being a permutation, and set `answer` to the single option key whose permutation the solution indicates. Store the paper’s raw code (e.g. `a-2,b-1,c-3,d-4`) in `note` for validation.
   - If a match item is malformed (not 4+4, or codes aren’t permutations), fall back to `Standard MCQ` and flag in unverified with reason `malformed_match_matrix` (the app already has a safe fallback for this).
3. `Consider the following statements:` with numbered `1. 2. 3.` and options like `Only 1 and 2` / `1, 2 and 3` → **Multiple Statements — Correct Combination by Code**; if it asks which statements are **incorrect** → **Multiple Statements — Incorrect Combination by Code**.
4. `Arrange the following …` / `Select the correct sequence` with numbered items and dash-coded options (e.g. `4-2-3-1`): if it says **chronological** order → **Chronological Order**; otherwise (north→south, increasing, decreasing, etc.) → **Ordering/Ranking**.
5. Stem contains `NOT`, `INCORRECT`, `EXCEPT` (and it is NOT one of the structural multi-statement types above) → **Negative/Exception MCQ**.
6. “Which of the following statements is/are correct?” with a single correct option and no numbered code table → **Correct Statement**; “…is/are incorrect?” → **Incorrect Statement**.
7. A literal blank (`____`) in the stem → **Fill in the Blank**.
8. Requires computation/unit result → **Numerical/Calculation**.
9. Array/multi-letter answers → **Multiple Correct** (only if the key truly lists >1 letter; none expected here).
10. References a figure/table the question depends on → **Figure/Diagram/Formula** (none in these QPs; the Test-13 solution figure is explanatory only).
11. Everything else → **Standard MCQ**.

These papers contain Assertion–Reason, Match-the-Following, numbered statements (correct & incorrect), NOT/except, and ordering/chronological items — expect all of these and validate each renders per `tests/test_quiz_webapp.js`.

---

## 4. OUTPUT LAYOUT & SCHEMA (exact)

For each test, create a book:
```
books/<book_id>/
  data/
    chapters.json
    <book_id>.json
  assets/            # only if a question-critical asset exists (none expected)
```
`book_id` = `test_<n>` using the **internal** test number (so the Physics+Chemistry pair is `test_13`, not `test_16`).

Subject file `<book_id>.json`:
```json
{
  "subject": "Test 1 — Bihar Special",
  "chapters": [
    {
      "chapter_name": "Bihar Special",
      "questions": [
        {
          "q": "Question text",
          "question_type": "Standard MCQ — Direct Factual/Conceptual, Single Correct",
          "options": { "A": "…", "B": "…", "C": "…", "D": "…" },
          "answer": "B",
          "explanation": "From the solution PDF",
          "exam": "72nd BPSC Prelims",
          "year": "2026",
          "note": "",
          "original_id": 1,
          "test_number": 1,
          "tbc": "267201"
        }
      ]
    }
  ]
}
```
`chapters.json`:
```json
[
  {
    "key": "test_1",
    "label": "Test 1 — Bihar Special",
    "emoji": "📝",
    "file": "test_1.json",
    "chapters": [ { "name": "Bihar Special", "count": 150 } ]
  }
]
```
- `label`/`subject` format: `Test <n> — <Subject>` (e.g. `Test 2 — World Geography`).
- Emoji per subject if obvious (History 🏛️/🏰/📜, Geography 🗺️, Economy 💰, Polity 🏛️, Science ⚛️/🧬, Current 📰), else 📝.
- Every chapter `count` MUST equal the number of questions in that chapter.
- For **Test 6 (no solution)**: still generate the book from the QP, but set `answer: null` and `explanation: ""` for every question and put all 150 in the unverified report with reason `missing_answer`. Do not fabricate answers.

### Register all books in `books/books.json`
Append one entry per test (idempotent update if `id` exists), keeping `bpsc_ghatna_chakra` first and not removing/reordering others:
```json
{
  "id": "test_1",
  "title": "Test 1 — Bihar Special",
  "subtitle": "72nd BPSC Prelims · प्रहार Test Series",
  "tag": "TEST 1",
  "emoji": "📝",
  "color": "#7C87C8",
  "dataDir": "books/test_1/data",
  "chaptersFile": "chapters.json",
  "description": "1 chapter · 150 questions"
}
```

---

## 5. FIELD NORMALIZATION RULES

- `question/questionText/text` → `q`.
- Options → object keyed uppercase `A/B/C/D` in printed order (paper already uses these).
- `answer` → single uppercase key present in `options`; `null` if missing/invalid (→ unverified).
- `explanation` → cleaned solution text; `""` if absent. Never fabricate.
- Preserve provenance: `original_id`, `test_number`, `tbc`, `exam`, `year`, and any `section`/`topic`.
- Clean text but do not alter facts; keep `₹`, en/em dashes, smart quotes, degree/percent symbols.
- Strip headers/footers (`Paper I / n`, solution running titles like `BPSC TEST-1 (SOLUTION)`), page numbers, and cover/instructions from question text.

---

## 6. ASSETS

- **Do not extract** the watermark/logo/banner images present in every PDF (xrefs repeat across pages; the 1000×1000 and 486×151 images are decorative).
- The only genuine figure is in `Test_16_…_Solution_English…pdf` (page 29, ~1693×929) and it is part of the **explanation** for Q120/Q121, not a question stem. Optionally crop it to `books/test_13/assets/` and reference it from those questions’ explanations/`asset` field; if unsure, report it and skip rather than mislink.
- If any question text says “study the figure/diagram/map/graph,” verify there is a real non-decorative image on the same page before extracting; otherwise don’t invent an asset.
- Every referenced asset must exist on disk and be non-empty; report all assets with source page, bbox, and linked question(s).

---

## 7. VALIDATION (run all, fail loud) then `npm test`

For every book validate:
- [ ] non-empty `q`; non-empty `question_type` from the controlled list;
- [ ] `options` has exactly A/B/C/D with non-empty values;
- [ ] scalar `answer` is a key in `options` (or `null` only for Test 6 / unverified);
- [ ] question numbers 1–150 present, no duplicates, in order;
- [ ] no duplicate questions (normalized stem + sorted options key);
- [ ] all Match items have 4 left (Roman) + 4 right (letter) and 4 permutation code options; selected code matches solution;
- [ ] all A/R items have the four standard truth-combo options;
- [ ] all JSON parses; chapter `count` exact;
- [ ] every referenced asset exists;
- [ ] parsed count = imported + unverified (nothing dropped silently);
- [ ] `books/books.json` valid and includes all 15 test books with correct `dataDir`/`chaptersFile`.

Then run the engine gate from the repo root:
```bash
npm ci && npm test
```
`npm test` MUST pass. It asserts the existing BPSC book totals (12 subjects / 391 chapters / 4,441 Qs) — your changes MUST NOT change those. Do NOT edit the test to hide a regression; fix the data. The new books must not break the jsdom app load.

---

## 8. REPORTS (write at repo root; do not overwrite existing `crown_*` reports)

### `prahar_import_report.json`
- `source_folder`, `pdf_count`, `skipped_files` (the schedule PDF + why),
- per-test block: `book_id`, `internal_test_number`, `tbc`, `subject`, `question_paper`, `solution`, `questions_parsed` (150 expected), `answers_found`, `missing_answers`, `chapters` (name+count), `assets`, `question_type_counts`,
- totals: `total_questions`, `valid_imported`, `unverified`, `subjects`, `books_registered`,
- `filename_numbering_mismatches` (Test-13-from-Test_16),
- `validation` (per-check pass/fail) and `npm_test` (pass/fail + summary).

### `prahar_taxonomy_report.json`
- global count of every controlled `question_type` (include zero-counts), plus per-test/per-chapter breakdown.

### `prahar_unverified_questions.json`
- Array of every record not cleanly imported: `test_number`, `original_id`, `chapter`, parsed `q`/`options`, `answer` (null), `reason` ∈ {`missing_answer` (Test 6), `answer_not_found_in_solution`, `answer_letter_invalid`, `malformed_match_matrix`, `options_malformed`, `duplicate`, `other`}, and a note.

Present all of the above plus every generated `books/test_*/data/*.json` and the `books/books.json` diff for review.

---

## 9. HARD DO-NOTs

- Do not commit, push, open a PR, or deploy until I approve the JSON.
- Do not replace/hand-edit `index.html`; do not touch existing BPSC (`data/`) or other books.
- Do not overwrite existing `crown_import_report.json` / `crown_taxonomy_report.json` / `crown_unverified_questions.json`.
- Do not commit PDFs or full-page renders (they’re gitignored).
- Do not fabricate answers, explanations, chapters, or option text.
- Do not run `eval`/`Function`; parse the PDF text layer directly.
- Do not use the Hindi translation pages for output.
- Do not trust the filename test number (Test_16 = internal Test 13).

---

## 10. PRESENT FOR APPROVAL, THEN STOP

When complete, present:
1. all `books/test_*/data/chapters.json` and subject JSON files (15 books),
2. `books/test_13/assets/` manifest (if any),
3. `prahar_import_report.json`, `prahar_taxonomy_report.json`, `prahar_unverified_questions.json`,
4. the `books/books.json` diff.

Then **stop and wait for my approval** before any commit/push/PR/deploy.
