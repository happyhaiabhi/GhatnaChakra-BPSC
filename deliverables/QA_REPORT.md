# QA REPORT — General Science (PREVIEW 2026), Part-7 (26121-C) — Dynamic JSON Question Bank

**Generated:** 2026-08-22 · **Source language:** English · **Output language:** English (same as source)

## 1. Source and page inventory

- Detected PDF page count (reliable library `pypdf`): **760 pages** across 4 attached PDF files:
  - `Preview General Science Part-7 2026 (26121-C) E-Book (1)-1-8.pdf` → physical pages 1–8 (front matter)
  - `Preview General Science Part-7 2026 (26121-C) E-Book (1)-9-323.pdf` → physical pages 9–323 (Part I: Physics)
  - `Preview General Science Part-7 2026 (26121-C) E-Book (1)-324-457.pdf` → physical pages 324–457 (Part II: Chemistry)
  - `Preview General Science Part-7 2026 (26121-C) E-Book (1)-458-760.pdf` → physical pages 458–760 (Part III: Biology)
- The physical PDF page number equals the printed page number (running headers show G-N). `source_page` is the physical/printed page.
- **All 760 pages were processed; none skipped.** The pages are not a preview sample — the four files together contain the complete book.
- Front matter (pages 1–8): cover, preface, index, series information. Content pages: 9–760.

## 2. Extraction and reconstruction workflow

- Initial probe: `pypdf` per-page text extraction for all 760 pages (0 zero-text pages).
- The PDF stores the body inside Form XObjects with a two-column layout and a rotated watermark (`CLICK HERE - JOIN @APNAPDFS`).
- **Final stream:** rebuilt with `pdfminer.six` character-level extraction (which cleanly excludes the watermark glyphs), reconstructed into lines/words by coordinates, read in visual two-column order (left column top-to-bottom, then right column). This fixes ~51 pages where the PDF content-stream order interleaved columns (e.g., pages 34, 42, 82, 89, 96, 327, 332, 336, 340, 348, 353, 354, 369, 372, 377, 379, 249, 265).
- Watermarks, running headers/footers and page numbers were removed; `∑` (a font-mapping artifact for `=`) was normalized to `=`; the source typo `(b 750` was normalized to `(b) 750` after char-level verification.
- Question blocks are anchored on the book's inline `Ans.` lines (the book provides answer + explanation inline after every question).
- Question starts are disambiguated from numbered statement/list rows using the expected question-number sequence per chapter unit.
- Options are parsed with a sequence-based marker scanner so that inner references such as `Both (a) and (b)` are not mistaken for option starts.
- Cross-references `See the explanation of above question.` were resolved by copying the complete applicable explanation (chained).

## 3. Counts and totals

- Total source question occurrences detected: **4092** (every `Ans.` line in the book was processed; 4091 parsed blocks + 1 diagram-option question [Q43, page 91] reconstructed manually).
- Verified questions emitted: **4089**
- Unverified questions excluded (reported separately): **3**
- The publisher preface states 4134 questions; the actual book content contains 4092 answer-bearing question occurrences. The difference (42) is a publisher compilation-count variance; the count in this bank reflects the actual visible source.
- Subjects: **3** (Physics, Chemistry, Biology) · Chapters (leaf units): **65**

| Subject | Chapters | Questions |
|---|---|---|
| Physics | 17 | 1731 |
| Chemistry | 19 | 757 |
| Biology | 29 | 1601 |

## 4. Question types and answer distribution

| Question type | Count |
|---|---|
| Standard MCQ | 3060 |
| Statement-Based (Correct Statement) | 226 |
| Standard MCQ (Negative) | 196 |
| Match the Following | 130 |
| Statement-Based with Code | 130 |
| Assertion and Reason | 92 |
| Incorrectly Matched Pairs | 78 |
| Statement-Based (Incorrect Statement) | 47 |
| Multiple Correct | 28 |
| Correctly Matched Pairs | 26 |
| Chronological Order | 24 |
| Statement-Based (Count) | 21 |
| Fill in the Blank | 18 |
| Diagram-Based | 6 |
| Diagram/Figure-Based | 3 |
| Odd One Out | 2 |
| Combination Selection | 1 |
| Formula-Based | 1 |

Answer distribution (verified bank): **A: 949; B: 1018; C: 1087; D: 931; E: 25; *: 50; multi-key: multi(A+B)(6), multi(A+C)(4), multi(A+D)(3), multi(B+C)(5), multi(B+D)(4), multi(C+D)(7)**

Every verified `answer` is nonblank and its key exists in the question's `options` object (single key, multi-key array, or the book's `*` dispute marker with a note). `*` answers (50) are the book's own marker for disputed/ambiguous options; each carries a note.

**Question-type field:** every record in the verified bank (and in `unverified_questions.json`) carries a `type` field (e.g. `Match the Following`, `Assertion and Reason`, `Statement-Based with Code`, `Statement-Based (Correct Statement)`, `Standard MCQ (Negative)`, `Chronological Order`, `Incorrectly Matched Pairs`, `Fill in the Blank`, `Diagram-Based`, `Formula-Based`, `Multiple Correct`, …) and a `type_detail` field that fully describes how the question is to be answered. The classification was derived from the question text and answer structure (see `qa_report.json` → `question_types` for the distribution).

## 5. Numbering continuity

Question numbering resets at every chapter/sub-chapter (verified from the printed index and 'Notes' headings). After full reconstruction, exactly one unit retains a genuine source numbering quirk: Biology ch.11 (Miscellaneous) prints two questions numbered 88 and skips 89 (the second Q88, page 744: "The substances which can be used as anaesthetic are –"). These are preserved as printed; the full numbering analysis is in `qa_report.json` and the ledger.

## 6. Explanations, notes, and warnings

- Explanations present: **4089**; absent in source: **0**; cross-references resolved to full text: **2**.
- Warning/correction notes retained: **65** (includes the book's `(*)` dispute markers, official answer-key corrections/cancellations, and blank-option warnings).
- Visual assets exported and referenced: **10** → assets/p0043_q19_graph.png, assets/p0043_q20_plane.png, assets/p0053_q24_fountain.png, assets/p0053_q25_flow.png, assets/p0088_q22_temperature.png, assets/p0089_q30_liquids_graph.png, assets/p0091_q43_bimetallic.png, assets/p0121_q3_energy_formulas.png, assets/p0246_q53_geostationary.png, assets/p0254_q100_space_map.png.

## 7. Duplicate analysis

- Exact duplicate groups (same question text + same options): **0**
- Near-duplicate groups (same question text, different options): **43**
- All duplicate source occurrences are **retained** in the bank (per the extraction rules); details with every source page are in `duplicate_report.json`.

## 8. Unverified questions (excluded, with reasons)

- **Page 269, Q188** — Source option markers are corrupted in the PDF text layer: extracted as (a) 4 and 1 (d) 1 and 2 / (c) 2 and 3 (d) 3 and 4 — the sequence is not (a)(b)(c)(d), option (b) is missing and (d) is duplicated, so option keys cannot be mapped unambiguously and answer key (c) cannot be verified against a unique option key.
- **Page 440, Q24** — Source option markers are corrupted in the PDF text layer: extracted as (a) An insecticide (b) An explosive / (c) A fungicide (b) A herbicide — the sequence is not (a)(b)(c)(d); option (d) is missing and (b) is duplicated, so answer key (d) cannot be mapped to a unique option.
- **Page 440, Q26** — Source option markers are corrupted in the PDF text layer: extracted as (a) Chlorpyrifos (b) Carbendazim / (c) Quinolphos (b) Butachlor — the sequence is not (a)(b)(c)(d); option (d) is missing and (b) is duplicated, so answer key (d) cannot be mapped to a unique option.

These three questions have non-sequential/corrupted option markers in the source text layer (e.g. `(a)…(d)…(c)…(d)` or `(b)` duplicated with `(d)` missing), so option keys cannot be mapped unambiguously and the printed answer key cannot be verified against a unique option. Full extracted content is preserved in `unverified_questions.json`.

## 9. Special source features handled

- **Match-the-following** (124): List-I/List-II rows and `Code :` matrices preserved in `q`; code options parsed into `options`.
- **Assertion–Reason** (92): Assertion/Reason text preserved in `q`; standard option sets preserved.
- **Multiple-correct** (29): `answer` stored as an array of verified keys (e.g. `["A", "B"]`).
- **Diagram/graph options**: Q43 (p91), Q19/Q20 (p43), Q25 (p53), Q22 (p88), Q53 (p246) have diagram options that are vector drawings/images in the PDF; their options are placeholders pointing to exported assets. Q3 (p121) has two formula-image options (B, C); Q24 (p53), Q30 (p89), Q100 (p254) depend on a figure — assets exported and referenced.
- **Formula-heavy content**: The `∑`→`=` normalization; one un-recoverable formula in the Notes on page 9 (theory only, not a question).

## 10. Validation and integrity

- All JSON files parse with a strict JSON parser (no comments, trailing commas, or control characters in output).
- Every retained verified source occurrence appears exactly once in the bank (one subject file, one chapter, one record).
- Totals reconciled: verified (4089) + unverified (3) = 4092 occurrences; chapter question counts sum to 4089; `index.json` totals match the subject files.
- All `asset` references point to existing files under `assets/`.
- ZIP integrity: file count, size, and SHA-256 are reported in the final response.

## 11. Deliverables

- `index.json` — subject index, hierarchy, filenames, totals
- `subjects/physics.json`, `subjects/chemistry.json`, `subjects/biology.json` — verified question bank per subject
- `assets/` — 10 visual assets required by questions
- `unverified_questions.json` — 3 unresolved records with exact reasons
- `taxonomy_report.json` — source-led hierarchy and classification decisions
- `duplicate_report.json` — exact and near duplicates with source locations
- `page_processing_ledger.json` — page-by-page processing status
- `qa_report.json` — machine-readable statistics and validation results
- `QA_REPORT.md` — this summary

## 12. Known limitations

- The PDF text layer has no usable text for a handful of diagram/formula options; those are covered by exported assets and explicit notes.
- The rotated watermark is excluded from text; three questions carry corrupted option markers in the source text layer and are reported as unverified.
- 24 questions contain dates/years inside option text (e.g. "May 29th, 1998"); these were verified to be option content, not exam labels.
