# Tarkash Annual PYQ Plus — English

Extracted from `Tarkash Annual PYQ Plus English.pdf` (BPSC Concept Wallah, Edition 2026).

- 10 subjects · 655 questions with answer keys and explanations
- Exams covered: 71st BPSC Prelims, ASO, DSO, SDO, AEDO, WMO, Mains
- The book is automatically indexed by `bpsc/books/books.json` and renders in the BPSC quiz app.

## Data files

Every `"file"` in `data/chapters.json` is a bare filename resolved against the book's
`dataDir` (`books/tarkash_annual/data`).

| Subject | File | Questions |
|---|---:|---:|
| Polity | `polity.json` | 72 |
| Physics | `physics.json` | 68 |
| Chemistry | `chemistry.json` | 58 |
| Biology | `biology.json` | 119 |
| Ancient History | `ancient_history.json` | 24 |
| Medieval History | `medieval_history.json` | 24 |
| Modern History | `modern_history.json` | 83 |
| Bihar Special | `bihar_special.json` | 71 |
| Geography | `geography_environment.json` | 87 |
| Economy | `economy_development.json` | 49 |

## Extraction notes

The source PDF uses an embedded font with a non-standard encoding, so the original text
layer is not usable. Text was recovered with OCR, then split into question / options /
answer / explanation using page geometry. A small number of extracted rows may contain
OCR artifacts (merged words, punctuation), but the question intent, answer key and
explanation are preserved. The raw OCR rows are not committed; regenerate the book with
the same pipeline if you want to re-process the PDF.
