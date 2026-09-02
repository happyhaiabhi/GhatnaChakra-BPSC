# Exam Portal — UPSC + BPSC Question Bank

A two-option exam portal with a complete UPSC question bank and the fully
integrated Ghatna Chakra BPSC application.

Live: **https://happyhaiabhi.github.io/GhatnaChakra-BPSC/**

## Pages

- `index.html` — the UPSC/BPSC exam-selection portal (with the shared Night Mode control).
- `upsc.html` — the complete searchable UPSC application.
- `bpsc/index.html` — the locally integrated Ghatna Chakra BPSC application (no iframe, no redirect).
- Both portal cards are connected, and both applications include a route back to the exam portal.

The BPSC browser runtime under `bpsc/` is synced from the public source
repository. The permanent BPSC source (tests, source documents and extraction
tools) lives in the **`bpsc-source`** branch; `main` is the combined portal.
Run `python scripts/sync_bpsc_runtime.py` to refresh the BPSC runtime without
copying Git history, PDFs, reports, tests or extraction artifacts.

- `BPSC_INTEGRATION_GUIDE.md` explains the integration architecture.
- `DEPLOY_TO_GITHUB.md` explains the GitHub Pages deployment and how the
  original BPSC source is preserved in the `bpsc-source` branch.

## Consolidated Physics Notes (A4)

`BPSC_Physics_Consolidated_Notes_A4.pdf` is a **re-arranged, de-duplicated,
PYQ-prioritised A4 edition** of the 19 lecture PDFs in `physic notes eduteria/`
(Physics by Sakshi Ma'am, 72nd BPSC batch, 84 pages). The 19 lectures are
consolidated into 16 topic-wise units (Units & dimensions → Light I–III → Waves
→ Sound → Heat & thermodynamics → Kinematics → Laws of motion & WPE → Gravitation
→ Fluids → Electricity → Electrical power & domestic electricity → Magnetism →
Modern & nuclear physics). Repeated topics are merged (each merge documented in
a green "De-dup note"), every source chart/diagram is kept as a clipped figure,
garbled formulas are re-typed, and obvious slips in the lectures are fixed
visibly in coral "Source correction" strips.

The PYQ layer: all **95 physics questions** of the 56–59th (2015), 60–62nd,
63rd … 71st (2025) BPSC Prelims (from the two workbooks in the repo) were
classified by unit. The PDF opens with a **PYQ Topic Priority** section
(ranking table, paper-by-paper load, most-repeated stems), every unit carries
an amber "PYQ lens" strip quoting the exact exam/question numbers, and
Appendix A lists every question with its options, study answer and status.
Anything that is *not* in the source lectures (extra data, derivations,
context) sits in a blue **"ADDED BY EDITOR — not in source lectures"** box.

Regenerate it with:

```bash
pip install pymupdf reportlab pillow openpyxl
python scripts/extract_physics_figures.py   # rebuilds build_physics/figures/
python scripts/analyse_physics_pyqs.py      # rebuilds build_physics/pyq_analysis.csv + pyq_summary.json
python scripts/build_physics_notes.py       # typesets the A4 PDF
```

- `scripts/extract_physics_figures.py` — clips every content figure out of the
  19 lecture PDFs (cover art, watermark and decorative frames skipped).
- `scripts/analyse_physics_pyqs.py` — pulls the physics questions out of the
  56–59th paper and the 60th–71st master question bank, assigns each to a unit
  and writes the ranking used by the PDF.
- `scripts/build_physics_notes.py` — typesets the PDF from the content DSL in
  `build_physics/content/*.txt` (`build_physics/fonts/` holds the DejaVu
  oblique face used for italics when the system lacks it).

## Consolidated Chemistry Notes (A4)

`BPSC_Chemistry_Consolidated_Notes_A4.pdf` is a **re-arranged, de-duplicated A4
edition** of *Eduteria Chem Notes Class Wise.pdf* (Chemistry by Sakshi Ma'am,
157 pages / 12 lecture files). All 12 lectures are consolidated into 12
topic-wise units — repeated topics merged (each merge documented in a green
"De-dup note"), every original chart, table, equation and visual explanation
kept, plus a linked table of contents.

Regenerate it with:

```bash
pip install pymupdf reportlab pillow
python scripts/extract_chem_figures.py   # rebuilds build_consolidated/figures/
python scripts/build_consolidated_notes.py
```

- `scripts/extract_chem_figures.py` — clips every content figure out of the
  source PDF (headers/watermarks skipped, labels kept).
- `scripts/build_consolidated_notes.py` — typesets the A4 PDF from the
  content DSL in `build_consolidated/content/*.txt`.

## Open it

The website works in both supported modes:

1. **Directly:** double-click `index.html`, then select an exam. UPSC supports `file://`; BPSC uses `fetch()` and should be opened through the local server below.
2. **Local server — recommended for both systems:**

```bash
python -m http.server 8000
```

Then open **http://localhost:8000** from the repository root.

## Features

- Animated academic selector: **P** for Prelims, a graduation-cap resting icon in the centre, and **M** for Mains
- Guided browsing: exam → paper → year → that year's questions
- Prelims branches into GS Paper I and CSAT Paper II; Mains branches into each available paper
- A compact Search button stays in the upper-right header and opens the complete search drawer (`/` opens it, `Esc` closes it)
- Full-text search across questions, answer options, CSAT solutions, subjects, papers, and Mains tags
- Drawer filters for exam, year, subject/paper, difficulty and sorting, plus clear-all and a live result count
- Guided selections show their question results directly below the selected paper and year, with a “Refine search” action
- Prelims and CSAT answer keys
- Detailed expandable solutions for every CSAT question
- A question-wise infographic for every CSAT and Prelims GS question: served from `infographics/` when bundled locally, with an automatic fallback to the original full-size source URL
- Clear passage blocks and statement formatting for long objective questions
- Responsive cards and progressive loading (20 results at a time)

## Data included

| Dataset | Years | Questions |
|---|---:|---:|
| Prelims GS Paper I | 1995–2026 | 3,196 |
| CSAT / GS Paper II | 2011–2026 | 1,211 |
| Mains | 2011–2025 | 2,079 |
| **Unique searchable total** | **1995–2026** | **6,486** |

The CSAT package contains 1,211 complete explanations and 1,211 solution
infographic references. Every Prelims GS question also carries a solution
infographic reference (3,196 of 3,200 rows). Four rows in the older 3,200-row
Prelims compilation pointed to CSAT pages; the website excludes those
duplicate/misclassified rows from the Prelims collection and uses their
complete CSAT records instead. The Prelims GS dataset contains answer keys but
no full written explanations; those cards link to their original source pages.

## BPSC runtime included

- 12 registered books
- 50+ subject data files
- 19,050+ question objects across all books, including the new **Tarkash Annual PYQ Plus** book
- The core Ghatna Chakra book retains 4,441 verified questions across 12 subjects and 391 chapters
- Multi-book selection, subject/chapter/sub-topic practice, quiz ranges and timers, question palette and keyboard controls, structured questions and explanations, mistakes/bookmarks/skips/archive, Bloom spaced review, attempt history and dashboard, search, PDF/print/export tools, focus timer, and Firebase Google sign-in with cloud sync
- `theme.js` provides one persistent Night Mode control on the portal; night mode is the low-glare default, and portal, UPSC and BPSC all inherit the same saved setting (shared `exam_portal_theme` key, synced to BPSC's legacy `gc_theme`)
- `bpsc-theme.css` gives BPSC matching day/night palettes with a modern minimalist book library, subject dashboard, quiz workspace, review banks and responsive navigation

## Tarkash Annual PYQ Plus book

`bpsc/books/tarkash_annual/` contains the fully extracted **Annual PYQ Plus (English)** book from the
Tarkash Annual PDF — 655 recent BPSC questions with options, answer keys and detailed explanations
across Polity, Physics, Chemistry, Biology, Ancient/Medieval/Modern History, Bihar Special,
Geography and Economy (71st Prelims, ASO, DSO, AEDO, WMO and Mains). It appears automatically as
a book in the BPSC app, and `bpsc/books/tarkash_annual/Tarkash_Annual_PYQ_Plus_Book.html` is a
self-contained, searchable study copy of the whole book.

## Maintenance scripts

- `python scripts/build_data_bundle.py` — rebuilds `data.js` (the `file://` fallback bundle) after a UPSC JSON update.
- `python scripts/download_infographics.py` — downloads every infographic referenced by `data/csat.json` and `data/prelims.json` into `infographics/` (run on a machine with internet access; resumable; `--dataset csat|prelims` to limit).
- `python scripts/add_prelims_infographics.py` — re-derives the Prelims infographic references from each question's `reference_url` (already applied; `--check` verifies).
- `python scripts/sync_bpsc_runtime.py` — refreshes the integrated BPSC runtime from the `bpsc-source` branch (with a temporary fallback to `main` until that branch exists) and validates every book/subject data path before replacing `bpsc/`.

## Deployment

`.github/workflows/deploy-pages.yml` deploys the repository root to GitHub
Pages on every push to `main` (Settings → Pages → Source must be set to
**GitHub Actions**). `.nojekyll` keeps underscore-prefixed paths static.
