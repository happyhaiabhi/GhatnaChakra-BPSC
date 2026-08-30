# Bihar Current Affairs — Practice Sets

**Status:** Live. Sets 1–6 are populated with 300 questions (50 per set) converted from
`Bihar_Current_Affairs_Sets1-6 (1).xlsx` (Eduteria Bihar Current Affairs 2026 practice set).
Sets 7–11 exist as empty placeholders, ready for the next workbook drop.

Old page-based chapter groups (`chapter_1_3.json` … `chapter_32_35.json`) have been removed.

## Structure

- `data/chapters.json` — 11 entries, one per set (`set_1` … `set_11`)
- `data/set_<n>.json` — one file per set, each with a single chapter `Set <n>`
- Question schema (same rich schema used by the rest of the bank):

| field | meaning |
| --- | --- |
| `q` | question stem (statements keep their original line breaks) |
| `question_type` | auto-classified: Standard MCQ / Multiple Statements / Negative-Exception / Match the Following / Assertion-Reason |
| `options` | `A`–`D` |
| `answer` | answer-key letter from the workbook |
| `explanation` | empty — to be filled from solution material |
| `exam` / `year` | `Bihar Current Affairs Practice Set` / `2026` |
| `note` | provenance line (set, question number, published answer key) |
| `original_id` | running id across the book (`(set-1) × 50 + qno`) |
| `set_number` / `set_question_no` | position inside the workbook |
| `topic` | one of 19 BPSC current-affairs buckets (keyword scoring + manual overrides) |
| `difficulty`, `keyFact`, `trap`, `section`, `tag` | practice-bank metadata |

## Regenerating

```bash
python3 scripts/import_bihar_ca_sets.py            # writes data/set_*.json + data/chapters.json
python3 scripts/import_bihar_ca_sets.py --total-sets 12   # expose more (empty) sets
```

Requires `openpyxl` (`pip install openpyxl`).

## Known data notes

- Set 5 repeats four questions verbatim in the source workbook (Q26→Q19, Q27→Q20,
  Q28→Q21, Q29→Q22). They are kept for fidelity and flagged through the `duplicate_of`
  field and the question `note`.
- Explanations are intentionally empty: the workbook only ships an answer key.
