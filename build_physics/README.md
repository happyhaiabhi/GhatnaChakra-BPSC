# Consolidated BPSC physics notes — build records

This directory holds the auditable intermediates for
`BPSC_Physics_Consolidated_Notes_A4.pdf` (the re-arranged, de-duplicated,
PYQ-prioritised A4 edition of the 19 Eduteria physics lectures in
`physic notes eduteria/`).

- `lectures.json` — maps the numeric source-PDF file names to lecture numbers
  and titles (Lecture 1 … 19).
- `content/01_units.txt … 16_modern.txt` — the 16 unit manuscripts in the
  build DSL (one directive per line: `UNIT`, `H2`/`H3`, `P`, `B`, `EQ`, `TBL`,
  `IMG`/`IMGS`, `NOTE` = green de-dup note, `CORR` = coral source correction,
  `ADD` = blue "ADDED BY EDITOR — not in source lectures" box, `PYQ` = amber
  PYQ lens). Every fact of the source lectures appears exactly once; anything
  the editor added is inside an `ADD` box.
- `pyq_analysis.csv` — the 95 physics questions of the 56–59th (2015),
  60–62nd, 63rd … 71st (2025) BPSC Prelims with options, workbook key, study
  answer, unit tag, core/extended scope and status
  (`source-key` / `added-answer` for the 71st paper, which has no key /
  `editor-corrected` where the workbook key disagrees with standard references).
- `pyq_summary.json` — per-unit and per-paper counts and the A/B/C priority
  ranking used in the "PYQ Topic Priority" section of the PDF.
- `figures/` — 186 figure clips (`L{lecture}_p{page}_{n}.png` + a few named
  vector clips) and `manifest.tsv`. **Not committed** (same convention as
  `build_consolidated/figures/`): regenerate in ~15 s with
  `python scripts/extract_physics_figures.py`.
- `fonts/DejaVuSans-Oblique.ttf`, `DejaVuSans-BoldOblique.ttf` — the italic
  faces of DejaVu Sans (Bitstream Vera licence), used by the builder when the
  system font package does not ship them.

## Rebuild

From the repository root:

```bash
pip install pymupdf reportlab pillow openpyxl
python scripts/extract_physics_figures.py   # figures/ + manifest.tsv
python scripts/analyse_physics_pyqs.py      # pyq_analysis.csv + pyq_summary.json
python scripts/build_physics_notes.py       # ../BPSC_Physics_Consolidated_Notes_A4.pdf
```

The builder validates every `IMG`/`IMGS` reference against `figures/` and
raises on any unknown DSL line, so a broken manuscript never produces a
silently incomplete PDF.
