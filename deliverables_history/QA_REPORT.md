# QA REPORT — Indian History (PREVIEW 2026), Part-2 (26116-C) — Dynamic JSON Question Bank

**Generated:** 2026-08-22 · **Source language:** English · **Output language:** English (same as source)

## 1. Source and page inventory

- Detected PDF page count (reliable library `pypdf`): **760 pages** across 4 attached PDF files:
  - `...Merged-1-8.pdf` → physical pages 1–8 (front matter)
  - `...Merged-9-203.pdf` → physical pages 9–203 (Part I: Ancient History of India)
  - `...Merged-204-347.pdf` → physical pages 204–347 (Part II: Medieval History of India)
  - `...Merged-348-760.pdf` → physical pages 348–760 (Part III: Modern History of India)
- Physical PDF page number equals the printed page number (running headers show B-N); `source_page` is the physical/printed page.
- **All 760 pages processed; none skipped.** The four files contain the complete book (not a preview sample).

## 2. Extraction and reconstruction workflow

- Initial probe: `pypdf` per-page text extraction for all 760 pages (0 zero-text pages).
- Final stream rebuilt with `pdfminer.six` character-level extraction (excludes the rotated `CLICK HERE - JOIN @APNAPDFS` watermark), two-column visual reading order (left column top-to-bottom, then right column), header/footer removal (including mid-question fragments like `l Studies Indian History` and `B–46 Genera`), and symbol cleanup (`Â\x03` bullet artifacts).
- Book-specific handling: `Ans.` + `. (x)` split across lines merged; answer lines like `Ans. (b) & (d)`, `Ans. (a & c)`, `Ans. (*)` parsed; multi-line option text and line-start option markers supported; question numbers without periods (`100.In`, `18 In`) and standalone numbers (`1.` map question) supported; exam labels embedded at the end of the last option (17 cases) split out.
- Cross-references `See the explanation of above question.` resolved by copying the complete applicable explanation (chained).

## 3. Counts and totals

- Total source question occurrences detected: **5006** (every `Ans.` line processed).
- Verified questions emitted: **5005**
- Unverified questions excluded (reported separately): **1**
- Subjects: **3** (Ancient 15, Medieval 25, Modern 55 chapters) · Chapters (leaf units): **95**

| Subject | Chapters | Questions |
|---|---|---|
| Ancient History of India | 15 | 1342 |
| Medieval History of India | 25 | 931 |
| Modern History of India | 55 | 2732 |

## 4. Question types and answer distribution

| Question type | Count |
|---|---|
| Standard MCQ | 3751 |
| Match the Following | 275 |
| Statement-Based (Correct Statement) | 193 |
| Chronological Order | 175 |
| Statement-Based with Code | 174 |
| Standard MCQ (Negative) | 102 |
| Incorrectly Matched Pairs | 102 |
| Assertion and Reason | 67 |
| Correctly Matched Pairs | 59 |
| Statement-Based (Incorrect Statement) | 54 |
| Multiple Correct | 25 |
| Code-Based | 11 |
| Diagram/Figure-Based | 8 |
| Fill in the Blank | 7 |
| Statement-Based (Count) | 2 |

Answer distribution (verified bank): **A: 1193; B: 1320; C: 1280; D: 1049; E: 44; *: 93; multi-key: multi(A+B)(6), multi(A+C)(3), multi(A+D)(1), multi(B+C)(6), multi(B+D)(3), multi(C+D)(7)**

Every verified `answer` is nonblank and its key exists in the question's `options` object. `*` answers (93) are the book's own marker for disputed/ambiguous options; each carries a note.

**Question-type field:** every record in the verified bank (and in `unverified_questions.json`) carries a `type` field (e.g. `Match the Following`, `Assertion and Reason`, `Statement-Based with Code`, `Statement-Based (Correct Statement)`, `Chronological Order`, `Incorrectly Matched Pairs`, `Standard MCQ (Negative)`, `Multiple Correct`, `Fill in the Blank`, …) and a `type_detail` field fully describing how the question is to be answered (see `qa_report.json` → `question_types`).

## 5. Numbering continuity

Question numbering resets at every chapter (verified from the printed index and chapter-title lines). After full reconstruction, **no chapter has a numbering gap or duplicate** — all 95 units are continuous from 1.

## 6. Explanations, notes, and warnings

- Explanations present: **5005**; absent in source: **0**; cross-references resolved to full text: **0**.
- Warning/correction notes retained: **108** (includes the book's `(*)` dispute markers, map-dependency notes, and source-typo reconstructions).
- Visual assets exported and referenced: **8** → assets/p0090_q07_mahajanapadas_map.png, assets/p0104_q32_ashoka_empire_map.png, assets/p0220_q14_malik_kafur_route_map.png, assets/p0231_q03_lodi_map.png, assets/p0290_q09_akbar_empire_map.png, assets/p0306_q01_shahjahan_empire_map.png, assets/p0312_q17_aurangzeb_kingdom_map.png, assets/p0338_q02_maratha_kingdom_map.png.

## 7. Duplicate analysis

- Exact duplicate groups (same question text + same options): **4**
- Near-duplicate groups (same question text, different options): **35**
- All duplicate source occurrences are **retained**; details in `duplicate_report.json`.

## 8. Unverified questions (excluded, with reasons)

- **Page 758, Q15** — Source option labels are corrupted in the PDF text layer: printed as '(c) Lata Mangeshkar (b) Pandit Jasraj / (c) Pandit Ravishankar (d) Ustad Bismillah Khan' — option (a) is missing, option (c) is duplicated, and the labels are out of order, so the answer key (b) cannot be mapped to an unambiguous A–D option set.

## 9. Special source features handled

- **Map-based questions (8)**: questions that depend on a map/figure printed in the book (p90 Q7 sixteen-mahajanapadas map, p104 Q32 Ashoka empire, p220 Q14 route map, p231 Q3 Lodi map, p290 Q9 Akbar empire, p306 Q1 shaded empire, p312 Q17 Aurangzeb kingdom, p338 Q2 Maratha kingdom) each carry an `asset` field pointing to the exported map image under `assets/`, plus a `note` explaining the dependency. Map images were cropped from the PDF at their exact coordinates.
- **Option-label corrections (6)**: questions whose option labels were mis-parsed or had source typos were corrected to canonical A–D with a documenting `note` — p13 Q26 (uppercase `(C)` label), p140 Q55 (`(h)` typo for `(b)`), p160 Q23 (`(d)` printed twice, `(c)` missing), p290 Q9 (options contain inner `(A)`/`(B)` map labels), p473 Q24 (match-list with labelled rows + code matrix), p571 Q2 (`(b)` printed twice, `(c)` missing).
- **Match-the-following** (275): List-I/List-II rows and code matrices preserved in `q`; code options parsed into `options`.
- **Assertion–Reason** (67): A/R text preserved in `q`; standard option sets preserved.
- **Multiple-correct** (25): `answer` stored as an array of verified keys (e.g. `["A", "C"]`); includes `Ans. (a) & (c))` style lines with stray parentheses.
- **Chronological Order** (175): order/sequence questions classified with detail.
- **Out-of-order printed option labels** (page 582 Q5) restored to canonical A–D with a note; **repeated-label typo** (page 502 Q71: `(a)…(b)…(a)…(b)`) reconstructed to A–D with a note; **corrupted labels** (page 758 Q15: `(a)` missing, `(c)` duplicated) reported as unverified.
- **Exam labels embedded in the last option** (17 questions, e.g. `(d) Akbar 39 B.P.S.C. (Pre) 1994 th`) split into the `exam` field.
- **Ligatures** (ﬁ ﬂ ﬀ ﬃ ﬆ) preserved as valid Unicode.

## 10. Validation and integrity

- All JSON files parse with a strict JSON parser.
- Every retained verified source occurrence appears exactly once (one subject file, one chapter, one record).
- Totals reconciled: verified (5005) + unverified (1) = 5006 occurrences; chapter counts sum to 5005; `index.json` totals match the subject files.
- ZIP integrity, file count, size, and SHA-256 are reported in the final response.

## 11. Deliverables

- `index.json` — subject index, hierarchy, filenames, totals
- `subjects/ancient_history_of_india.json`, `subjects/medieval_history_of_india.json`, `subjects/modern_history_of_india.json` — verified question bank per subject
- `unverified_questions.json` — 1 unresolved record with exact reason
- `taxonomy_report.json` — source-led hierarchy and classification decisions
- `duplicate_report.json` — exact and near duplicates with source locations
- `page_processing_ledger.json` — page-by-page processing status
- `qa_report.json` — machine-readable statistics and validation results
- `QA_REPORT.md` — this summary

## 12. Known limitations

- One question (p758 Q15) has corrupted option labels in the source text layer and is reported as unverified.
- One question (p666 Q37) genuinely carries no exam label in the source; `exam` is empty for it.
- The publisher preface describes the compilation; the actual question count in the book is 5006 answer-bearing occurrences (the book does not print a total for this volume).
