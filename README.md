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

- 10 registered books
- 50 subject data files
- 18,395 question objects across all books
- The core Ghatna Chakra book retains 4,441 verified questions across 12 subjects and 391 chapters
- Multi-book selection, subject/chapter/sub-topic practice, quiz ranges and timers, question palette and keyboard controls, structured questions and explanations, mistakes/bookmarks/skips/archive, Bloom spaced review, attempt history and dashboard, search, PDF/print/export tools, focus timer, and Firebase Google sign-in with cloud sync
- `theme.js` provides one persistent Night Mode control on the portal; night mode is the low-glare default, and portal, UPSC and BPSC all inherit the same saved setting (shared `exam_portal_theme` key, synced to BPSC's legacy `gc_theme`)
- `bpsc-theme.css` gives BPSC matching day/night palettes with a modern minimalist book library, subject dashboard, quiz workspace, review banks and responsive navigation

## Maintenance scripts

- `python scripts/build_data_bundle.py` — rebuilds `data.js` (the `file://` fallback bundle) after a UPSC JSON update.
- `python scripts/download_infographics.py` — downloads every infographic referenced by `data/csat.json` and `data/prelims.json` into `infographics/` (run on a machine with internet access; resumable; `--dataset csat|prelims` to limit).
- `python scripts/add_prelims_infographics.py` — re-derives the Prelims infographic references from each question's `reference_url` (already applied; `--check` verifies).
- `python scripts/sync_bpsc_runtime.py` — refreshes the integrated BPSC runtime from the `bpsc-source` branch (with a temporary fallback to `main` until that branch exists) and validates every book/subject data path before replacing `bpsc/`.

## Deployment

`.github/workflows/deploy-pages.yml` deploys the repository root to GitHub
Pages on every push to `main` (Settings → Pages → Source must be set to
**GitHub Actions**). `.nojekyll` keeps underscore-prefixed paths static.
