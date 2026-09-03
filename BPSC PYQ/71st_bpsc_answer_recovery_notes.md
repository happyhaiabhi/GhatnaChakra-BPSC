# 71st BPSC (2025) answer recovery notes

This note documents the sources used to fill `71st BPSC (2025)` entries in `bpsc_verified_answers.json`.

## Official web sources

- Final answer key PDF (BPSC):
  - https://bpsc.bihar.gov.in/wp-content/uploads/BPSC_content/Notices/31-10-25-3-Final-Answer-Key-71st-CCE-Pre_BPSC-20251031-bmkwic.pdf
- Provisional answer key PDF (BPSC):
  - https://bpsc.bihar.gov.in/wp-content/uploads/BPSC_content/Notices/19-9-25-2-Provisional-Answer-Key-Integrated-71st-CCE-Pre-Exam.-General-Studies_BPSC-20250919-j3xcma.pdf

## Set used by this repo

The 71st paper in `BPSC PYQ/bpsc_parsed.json` matches **Set E**.

## Deleted questions in the official final key

These remain blank in `bpsc_verified_answers.json` because the final key does not provide a valid answer key for them:

- Q.11
- Q.69
- Q.75
- Q.96
- Q.118

## Local repo corroboration used for rows that were hard to OCR from the final PDF

These question numbers were confirmed from exact 71st-BPSC-labelled local question-bank entries that include answer keys and explanations, and they also match the official provisional Set E key:

- Q.34 — `bpsc/data/current_affairs.json`
- Q.46 — `bpsc/books/tarkash_annual/data/economy_development.json`
- Q.53 — `bpsc/data/bihar_special.json`
- Q.56 — `bpsc/data/polity_governance.json`
- Q.64 — `bpsc/data/polity_governance.json`
- Q.66 — `bpsc/data/polity_governance.json`
- Q.77 — `bpsc/data/modern_history.json`
- Q.94 — `bpsc/books/tarkash_annual/data/medieval_history.json`

## Text-quality repairs applied after answer recovery

The following 71st questions had truncated or mis-arranged text in `bpsc_parsed.json` and were reconstructed from local 71st-tagged repo sources while keeping the verified answer-key alignment used by the app:

- Q.36 — `bpsc/data/economy_development.json`
- Q.50 — `bpsc/data/geography_environment.json`
- Q.54 — `bpsc/data/bihar_special.json`
- Q.59 — `bpsc/data/polity_governance.json`
- Q.61 — `bpsc/data/polity_governance.json`
- Q.65 — `bpsc/data/polity_governance.json`
- Q.67 — `bpsc/data/economy_development.json`
- Q.78 — `bpsc/data/modern_history.json`
- Q.86 — `bpsc/data/ancient_history.json`
- Q.88 — `bpsc/data/ancient_history.json`
- Q.92 — `bpsc/data/medieval_history.json`
- Q.94 — `bpsc/books/tarkash_annual/data/medieval_history.json`
- Q.100 — `bpsc/books/tarkash_annual/data/bihar_special.json`
- Q.127 — missing option text repaired from `bpsc/data/physics.json`

Additional option-text cleanups applied to remove truncated ellipses without changing answer keys:

- Q.38 — exact option wording restored from `https://upscsociology.in/q-according-to-india-state-of-forest-report-2023-isfr-2023/`
- Q.40 — `bpsc/data/current_affairs.json`
- Q.47 — `bpsc/data/economy_development.json`
- Q.53 — `bpsc/data/bihar_special.json`
- Q.62 — `bpsc/data/polity_governance.json`

Special case:

- Q.9 had OCR-split rows in `bpsc_parsed.json`; its grid layout and option text were reconstructed to keep the official final-key letter (`B`) while replacing the broken parsed option text. The recovered option order was cross-checked against the publicly posted 71st question/explanation page at `https://upscsociology.in/q-find-the-missing-number-from-the-given-alternatives-28-20-7-84-12-45-25-9/`.

## Result

- Total 71st questions: 150
- Final keyed answers filled: 145
- Officially deleted / left blank: 5
