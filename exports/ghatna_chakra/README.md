# Ghatna Chakra — Ancient, Medieval & Modern India (AI-readable export)

Every previous-year objective question from the three Ghatna Chakra history books
used by the BPSC app, flattened into plain, self-describing records that a script
or an LLM can read without any custom parser.

| Subject | Chapters | Questions | Clean |
|---|---|---|---|
| Ancient India | 15 | 1,342 | 1,318 |
| Medieval India | 25 | 931 | 908 |
| Modern India | 55 | 2,732 | 2,666 |
| **Total** | **95** | **5,005** | **4,892** |

Source: `bpsc/books/{ancient_india,medieval_india,modern_india}/data/*.json`
Regenerate: `python scripts/export_ghatna_chakra_ai.py`

## Files

| File | Format | What it is |
|---|---|---|
| `ghatna_chakra_all_india.jsonl` | JSON Lines | **Start here.** All 5,005 questions, one complete JSON object per line. |
| `ghatna_chakra_all_india_clean.jsonl` | JSON Lines | The 4,892 records safe for training/eval (see *Quality flags*). |
| `ghatna_chakra_ancient_india.jsonl` | JSON Lines | The 1,342 Ancient India questions. |
| `ghatna_chakra_medieval_india.jsonl` | JSON Lines | The 931 Medieval India questions. |
| `ghatna_chakra_modern_india.jsonl` | JSON Lines | The 2,732 Modern India questions. |
| `ghatna_chakra_all_india.json` | JSON | One document: dataset metadata, subject → chapter index, then every question. |
| `ghatna_chakra_all_india.csv` | CSV | Spreadsheet / pandas export (`option_a` … `option_e`, `answer_key`, `flags`). |
| `ghatna_chakra_all_india.md` | Markdown | Reading copy — question, options, answer, explanation, exam. Ideal to paste into an LLM. |
| `manifest.json` | JSON | Counts, per-subject chapter index, quality-flag census, file sizes and SHA-256 hashes. |

A JSONL file is the friendliest format for AI work: it streams line by line, so a
5 MB file loads without building one giant array, and one corrupt line can be
skipped instead of failing the whole file.

## Record schema

```json
{
  "id": "anc-0001",
  "subject": "Ancient India",
  "period": "Ancient India",
  "chapter_no": 1,
  "chapter": "1. Stone Age",
  "question_no": 1,
  "question": "Robert Bruce Foote, who discovered first Palaeolithic tool in India, was a/an -",
  "options": { "A": "Geologist", "B": "Archaeologist", "C": "Paleobotanist", "D": "Historian" },
  "num_options": 4,
  "answer_key": ["A", "B"],
  "answer_text": ["Geologist", "Archaeologist"],
  "answer_raw": ["A", "B"],
  "multi_correct": true,
  "explanation": "According to Encyclopaedia Britannica, Robert Bruce Foote was ...",
  "exam": "U.P. Lower Sub. (Pre) 2015",
  "year": 2015,
  "years": [2015],
  "note": null,
  "asset": null,
  "quality": { "clean": true, "flags": ["multi_answer"], "removed_option_text": null }
}
```

| Field | Meaning |
|---|---|
| `id` | Stable id: `anc-` / `med-` / `mod-` + running number within the book. |
| `subject`, `period` | Book name (same value; `period` keeps the Ancient/Medieval/Modern grouping explicit). |
| `chapter_no`, `chapter`, `question_no` | Position in the source book, 1-based. |
| `question` | Question stem, PDF line wrapping and ligatures repaired. |
| `options` | Letter → option text. Always `A`–`D`; 388 BPSC questions carry a fifth `E` ("None of the above / More than one of the above"). |
| `answer_key` | Correct option letters. Empty when the book prints no key. |
| `answer_text` | Those options resolved to text — handy when you do not want to map letters. |
| `answer_raw` | Exactly what the source held (e.g. `"*"` when the book gave no answer). |
| `multi_correct` | `true` when more than one option is keyed correct. |
| `explanation` | The book's own explanation. Never empty in this dataset. |
| `exam` | Exam the question was asked in, as printed ("65th B.P.S.C. (Pre) 2019"). 929 distinct exams. |
| `year`, `years` | Year(s) parsed out of `exam`/`year`; `years` keeps every occurrence for multi-exam questions. |
| `note` | Editorial note from the extraction, usually about a figure. |
| `asset` | Relative path to a scanned map/figure when the question cannot be answered without it. |
| `quality.clean` | `true` when no blocking flag is set. |
| `quality.flags` | Machine-detectable issues, listed below. |
| `quality.removed_option_text` | Exam label that had been pasted into an option and was stripped out. |

## Quality flags

Informational — the record is still usable and stays in the *clean* set:

| Flag | Count | Meaning |
|---|---|---|
| `five_options` | 388 | Has a fifth option (BPSC "None of the above" style). |
| `multi_answer` | 26 | More than one option is correct. |
| `option_exam_text_removed` | 85 | An exam name + year had been glued onto an option; removed. |
| `exam_recovered_from_option` | 69 | The exam field was mangled ("rd th") and was rebuilt from that stripped text. |

Blocking — the record is kept in the full files, excluded from `*_clean.jsonl`:

| Flag | Count | Meaning |
|---|---|---|
| `answer_missing` | 93 | The book prints `*` instead of a key. |
| `malformed_question` | 8 | A whole note block was glued onto the stem by the PDF extraction. |
| `image_dependent` | 8 | Needs a map/figure (`asset` path) to answer. |
| `duplicate_question` | 4 | Same stem *and* same options appear earlier in the same book. |
| `exam_missing` | 17 | No exam name recoverable. |
| `year_missing` | 17 | No year recoverable. |

## Reading it

```python
import json

with open("ghatna_chakra_all_india_clean.jsonl", encoding="utf-8") as fh:
    for line in fh:
        q = json.loads(line)
        print(q["question"], q["answer_key"])
```

A ready-made supervised pair:

```python
def as_prompt_completion(q):
    options = "\n".join(f"{k}. {v}" for k, v in q["options"].items())
    prompt = f"{q['question']}\n{options}\nAnswer:"
    completion = ", ".join(q["answer_text"])
    return prompt, completion
```

Filtering examples:

```python
ancient  = [q for q in rows if q["subject"] == "Ancient India"]
bpsc     = [q for q in rows if "B.P.S.C." in q["exam"]]
recent   = [q for q in rows if (q["year"] or 0) >= 2015]
four_opt = [q for q in rows if q["num_options"] == 4 and len(q["answer_key"]) == 1]
```

## How the text was cleaned

The three source files were produced by PDF extraction, so the exporter repairs
what is mechanically detectable and flags the rest instead of guessing:

- **Ligatures** — `ﬁ rst` → `first`, `diﬀ erent` → `different`, `oﬃ cial` → `official`.
  Split words are re-joined only when the glued word exists elsewhere in the
  repo's question-bank corpus, so real word pairs ("most of", "west Bengal")
  are never merged.
- **Wrapped lines** — newlines inside a sentence collapse to single spaces; the
  explanation keeps its paragraph breaks.
- **Hyphenated line breaks** — `headquar- ters` → `headquarters`, `fol- lowing` →
  `following`; a hyphen is kept when the join is not a known word but the left
  half is a real prefix (`Non- cooperation` → `Non-cooperation`).
- **Option pollution** — exam labels pasted onto the last option
  ("Sikandar Lodi 44 B.P.S.C. (Pre) 2000 th") are cut off and kept in
  `quality.removed_option_text`; the exam/year is reused if the record's own
  `exam` field was mangled.
- **Ordinal debris** — exam strings such as `"rd th; 47th B.P.S.C. (Pre) 2005"`
  are cleaned to `"47th B.P.S.C. (Pre) 2005"`.
- **Answer keys** — `"A"`, `["A","B"]`, and `"*"` are normalised to
  `answer_key` lists; `"*"` becomes `answer_missing` rather than a fake answer.
- **Deduplication** — on stem *plus* options, so the many distinct questions that
  share a stock stem ("Which of the following is not correctly matched?") are
  not collapsed.

Nothing is deleted from the full exports: every question in the source appears
in `ghatna_chakra_all_india.jsonl` and its per-subject file.

## Source and caveats

Compiled study material from the Ghatna Chakra series (Purvavalokan), as used by
the BPSC app in this repository. Exam names and years come from the book's
marginal labels and are occasionally incomplete. This is a study aid, not an
authoritative text — verify factual claims against the original book before
relying on them.
