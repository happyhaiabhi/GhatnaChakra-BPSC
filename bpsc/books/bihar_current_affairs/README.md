# Bihar Current Affairs — Clean Template (PDF Source)

**Status:** Empty template — ready for manual extraction from the original PDF.

- Source PDF: `Eduteria Bihar Current Affairs 2026 Practice Set.pdf` (36 pages, 16.4 MB, scanned/image)
- All 36 pages rendered to `/tmp/pdf_pages/page_01.png` → `page_36.png`
- No embedded text layer — requires manual read from page images or corrected input

## Structure
- `data/chapters.json` — 11 chapter groups (Chapters 1–3 through 32–35), all `count: 0`
- `data/chapter_*.json` — clean empty `questions: []` arrays
- `data/*.json` format matches quiz-engine (`subject`, `chapters`, `questions` with full question schema)

## Next step
Fill questions into the empty arrays using the PDF pages as ground truth (e.g., Set 1 = pages 1–3 ≈ `chapter_1_3.json`).
