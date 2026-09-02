# Consolidated BPSC biology notes — build records

This directory contains the auditable intermediate records for
`BPSC_Biology_Consolidated_Notes.pdf`.

- `content.txt` — topic-first source manuscript (20 units).
- `pyq_analysis.csv` — 141 manually reviewed questions with core/extended scope,
  source answers, study answers, and visible correction/ambiguity status.
- `pyq_summary.json` — full-range topic ranking used in the book.
- `source_coverage.csv` — all 33 source PDFs, page/text counts and SHA-256 values.
- `assets/` + `assets_manifest.json` — reviewed original figures and page-level
  source provenance. No web image is used in the output.

## Rebuild

From the repository root, using the dependency pins in
`scripts/requirements_biology_notes.txt`:

```bash
python scripts/audit_biology_sources.py
python scripts/analyse_biology_pyqs.py
python scripts/build_biology_notes.py
```

The generated PDF is A4, searchable, and includes a complete reviewed-PYQ
appendix. Blue boxes identify assistant-added material; coral boxes identify
editorial corrections. Dynamic current-affairs facts remain explicitly
qualified.
