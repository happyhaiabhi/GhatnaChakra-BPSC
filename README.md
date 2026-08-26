# Exam Portal + UPSC Question Bank

A two-option exam portal with a complete UPSC question bank and a reserved BPSC website slot.

## Pages

- `index.html` — the UPSC/BPSC exam-selection portal.
- `upsc.html` — the complete searchable UPSC application.
- `bpsc/index.html` — the locally integrated Ghatna Chakra BPSC application.
- Both portal cards are connected, and both applications include a route back to the exam portal.

The BPSC browser runtime was imported from `happyhaiabhi/GhatnaChakra-BPSC`. Run `python scripts/sync_bpsc_runtime.py` to refresh it without copying Git history, PDFs, reports, tests or extraction artifacts.

- `BPSC_INTEGRATION_GUIDE.md` explains the integration architecture.
- `DEPLOY_TO_GITHUB.md` explains how to replace the existing BPSC GitHub Pages deployment safely while preserving the original source in a `bpsc-source` branch.

## Open it

The website works in both supported modes:

1. **Directly:** double-click `index.html`, then select an exam. UPSC supports `file://`; BPSC uses `fetch()` and should be opened through the local server below.
2. **Local server — recommended for both systems:**

```bash
cd upsc-question-bank
python -m http.server 8000
```

Then open **http://localhost:8000**. On Windows, `START_SERVER.bat` does the same thing.

## Features

- Animated academic selector: **P** for Prelims, a graduation-cap resting icon in the centre, and **M** for Mains
- Guided browsing: exam → paper → year → that year's questions
- Prelims branches into GS Paper I and CSAT Paper II; Mains branches into each available paper
- A compact Search button stays in the upper-right header and opens the complete search drawer
- Full-text search across questions, answer options, CSAT solutions, subjects, papers, and Mains tags
- Drawer filters for exam, year, subject/paper, difficulty and sorting, plus a `/` keyboard shortcut
- Guided selections show their question results directly below the selected paper and year
- Prelims and CSAT answer keys
- Detailed expandable solutions for every CSAT question
- A local, question-wise infographic for every CSAT question, with a full-size source link
- Clear passage blocks and statement formatting for long objective questions
- Responsive cards and progressive loading (20 results at a time)

## Data included

| Dataset | Years | Questions |
|---|---:|---:|
| Prelims GS Paper I | 1995–2026 | 3,196 |
| CSAT / GS Paper II | 2011–2026 | 1,211 |
| Mains | 2011–2025 | 2,079 |
| **Unique searchable total** | **1995–2026** | **6,486** |

The CSAT package contains 1,211 explanations and 1,211 local infographics. Four rows in the older 3,200-row Prelims compilation pointed to CSAT pages; the website excludes those duplicate/misclassified rows from the Prelims collection and uses their complete CSAT records instead. The supplied Prelims GS dataset contains answer keys but no full written explanations; those cards link to their original source pages.

## BPSC runtime included

- 10 registered books
- 50 subject data files
- 18,395 detected question objects across all books
- The core Ghatna Chakra book retains 4,441 verified questions across 12 subjects and 391 chapters
- Quiz, review banks, exports, dashboard, focus tools and Firebase/Google sync logic are preserved
- `theme.js` provides one persistent Night Mode control on the portal; dark mode is the low-glare default, and portal, UPSC and BPSC all inherit the same saved setting
- `bpsc-theme.css` gives BPSC matching day/night palettes with a modern minimalist book library, subject dashboard, quiz workspace, review banks and responsive navigation

## Maintenance scripts

- `python scripts/build_data_bundle.py` — rebuilds `data.js` after a UPSC JSON update.
- `python scripts/download_csat_infographics.py` — downloads and optimises all CSAT infographics referenced by `data/csat.json`.
- `python scripts/sync_bpsc_runtime.py` — refreshes the integrated BPSC runtime from its public repository and validates every book/subject data path.
