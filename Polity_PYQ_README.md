# Chapter-wise Polity PYQ sheet

Open `Polity_PYQ_Laxmikanth_Chapterwise.pdf` for the printable version, or
`Polity_PYQ_Laxmikanth_Chapterwise.xlsx` to filter the single worksheet by chapter. It contains
515 rows: all 324 numbered questions in the supplied KGS polity PDF, JSON records labelled
`polity`, and CSV records labelled `Polity`. Eighty-six records with the same normalized question
**and complete options** were merged, retaining source references. Differently worded versions and
questions with different options remain separate, even where they may refer to the same exam
question.

Every row carries a `Q. No.` that matches the PDF, and three answer-audit columns:

| Column | Meaning |
|---|---|
| `Answer key (source)` | the letter exactly as the source printed it (`*` and `A/C` included) — never altered |
| `Verified key (web)` | the answer **in this sheet's own option order**, filled only where a source was checked |
| `Verification status` | what has been done to that row — verified, corrected, resolved, defective, or explicitly not checked |
| `Web evidence` | the URL and the sentence that decides the answer |

## What is verified, and what is not

**393 of 515 rows have been checked against a published source** (40 printed keys corrected, 332
confirmed, 5 ambiguous keys resolved, 15 rows with no possible answer). The other 122 rows still
carry the key of their source book and are labelled as such in both the workbook and the PDF. Read
those as "the source book says so", not as fact. Details, evidence and the correction table are in
**`POLITY_PYQ_VERIFICATION.md`** and `data/polity_answer_verification.json`.

The three sources are not equally trustworthy:

* **KGS book keys** — 71 rows. A twelve-question random audit found one error (Q47) and two corrupt
  option tables, so expect roughly one wrong key in ten among the rows still carrying them.
* **CSV keys** — 34 rows. Consistent with the verified answer on every spot-check.
* **JSON keys** — 126 rows still carry one (of 134). The letters belong to a different booklet's
  option order, and **28 of the 38 judged were wrong**; in a uniform random sample of untouched rows
  3 of 8 were still wrong. Rows carrying them are marked *source letter unreliable*.

## Chapter classification

The chapter assignment is a best-fit, automated index based on the supplied Laxmikanth text and the
PDF's topic sequence; it is not a verified chapter-by-chapter expert classification. Later chapter
numbers are omitted because the supplied text's index is incomplete. **93 rows are in "Review /
outside Laxmikanth chapter scope"**: the source material includes international affairs, current
affairs, reasoning and other off-topic questions. Check these before using them as a polity-only
list. Other assignments also need review, particularly questions spanning chapters.

## Other known defects

The PDF extraction has OCR defects, including incomplete option tables, stray `(a) (b) (c) (d) (e)`
answer-table fragments glued to option lists, and occasional translation errors. A `*` or a
multi-letter PDF key is retained in `Answer key (source)` as printed. Some questions lost their
statement lists entirely, which is why four rows are recorded as having no defensible answer.
Duplicates may still exist where wording, punctuation or options differ beyond normalization.
Historical answers and facts may no longer be current (Article counts, party status, office-holders).

## Rebuilding

```bash
pip install pypdf openpyxl reportlab
python scripts/compile_polity_pyq.py INPUT_DIRECTORY OUTPUT.xlsx   # from the raw PDF/JSON/CSV
python scripts/apply_polity_verification.py                        # adds the audit columns
python scripts/polity_pyq_pdf.py                                   # renders the PDF
```

`compile_polity_pyq.py` needs an input directory containing the supplied PDF, JSON and CSV; the
Laxmikanth text is used as the chapter reference, not reproduced in the sheet.
`apply_polity_verification.py --check` verifies that every ledger entry still points at the right
question before anything is written.
