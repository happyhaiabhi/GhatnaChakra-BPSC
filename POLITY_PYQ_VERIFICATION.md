# Web verification of the Polity PYQ answers

Checked on **27 November 2026** against published solved papers, official BPSC answer keys
and the constitutional text. Every claim below resolves to a URL and a quoted sentence in
`data/polity_answer_verification.json`; the workbook carries the same evidence in its
**Web evidence** column, and the PDF prints a status line under every question.

## Headline

| | Rows |
|---|---|
| Total questions | 515 |
| **Web-checked in this pass** | **313 (60.8 %)** |
| — printed key was wrong, now corrected | 37 |
| — printed key confirmed | 260 |
| — ambiguous printed key (`*`, `A/C`) resolved | 5 |
| — no answer possible (corrupt options / deleted by BPSC) | 4 |
| Not yet web-checked | 202 |

The single most important finding is not the 37 corrections. It is that **the supplied JSON
answer letters are not aligned with the options printed in this sheet**, so about half of the 134
rows that inherit a JSON letter are carrying a wrong answer (28 wrong of the 38 judged, and 3 of 8
in an unbiased random sample). Those rows are now labelled *not web-checked: source letter
unreliable* instead of being shown as answered.

## Why a letter cannot simply be trusted

BPSC prints every paper in four or five booklets (A–D, E–H for the 71st) and shuffles the option
order in each. `Q1 = B` is therefore true only inside the booklet it came from. A key and an
option list taken from different booklets are *both* internally consistent and still disagree.

Concrete example, question 211:

* the sheet prints `(a) Britain (b) USA (c) France (d) More than one of the above (e) None`;
* the 68th BPSC official key says **B** — but in the official Set-B booklet the order is
  `(a) France (b) Britain (c) USA (d) GOI 1935 (e) Canada`, so B means *Britain*;
* the sheet's JSON had copied `B` next to an option list that puts *USA* in position (b).

That is how a correct official key turns into a wrong answer. Every verification in this pass was
therefore done **content first**: identify the correct *option text* from the source, then look up
which letter carries that text **in this sheet's own option list**. The `Verified key (web)` column
is always in the sheet's order, never the booklet's.

## Corrections applied

`*` and `A/C` are keys the KGS book itself printed as ambiguous; "Verified" is the option that is
now keyed.

| Q. No. | Printed | Verified | Correct option | Source |
|---|---|---|---|---|
| 1 | `A` | **C** | 2 and 3 | geniusacademy.org.in |
| 11 | `E` | **A** | 21 years | licchavilyceum.com |
| 36 | `A` | **B** | Any number of times | licchavilyceum.com |
| 37 | `A` | **C** | Yashwant Sinha | testbook.com |
| 34 | `E` | **A** | either directly or through officers subordinate to him | clearias.com |
| 101 | `C` | **D** | Canada | bbc.com |
| 35 | `B` | **C** | Zimbabwe | aljazeera.com |
| 38 | `A` | **C** | Guwahati (IIT Guwahati) | pib.gov.in |
| 47 | `E` | **D** | By Parliament and State Assemblies | testbook.com |
| 91 | `*` | **D** | To the Parliament | prepp.in |
| 102 | `E` | **C** | 25 years | examstocks.com |
| 107 | `E` | **D** | More than one of the above | cracktarget.com |
| 166 | `*` | **B** | 444 sections (articles, as of the 2005 exam date; 448 today) | vajiramandravi.com |
| 111 | `A` | **D** | Andaman and Nicobar | economictimes.indiatimes.com |
| 208 | `E` | **A** | the President | examstocks.com |
| 214 | `A` | **C** | Karachi Session—1931 | nehruarchive.in |
| 216 | `A` | **B** | Kamandaka | testbook.com |
| 211 | `B` | **A** | Britain | testbook.com |
| 233 | `*` | **C** | Right to education | examrobot.com |
| 251 | `E` | **B** | the President of India | bajajfinserv.in |
| 256 | `A/C` | **C** | Attorney General | digitallylearn.com |
| 281 | `E` | **C** | the President | examstocks.com |
| 283 | `A` | **C** | Satyendra Prasanna Sinha | en.wikipedia.org |
| 293 | `D` | **A** | The President | geniusacademy.org.in |
| 297 | `*` | **C** | Guwahati | en.wikipedia.org |
| 301 | `A` | **D** | Ramsay MacDonald | wikiwand.com |
| 303 | `A` | **C** | J. Andrew | maargxupsc.com |
| 310 | `A` | **B** | Article 40 | examstocks.com |
| 314 | `A` | **C** | finance commission | licchavilyceum.com |
| 315 | `A` | **B** | 1, 2 and 4 only | cracktarget.com |
| 316 | `B` | **C** | Block-level body | testbook.com |
| 317 | `A` | **B** | State Legislature | upscsociology.in |
| 414 | `A` | **B** | Kaka Saheb Kalelkar | testbook.com |
| 415 | `A` | **B** | is a part of the Parliament | examstocks.com |
| 430 | `E` | **C** | the Legislative Assembly | testbook.com |
| 432 | `A` | **D** | All of the above | testbook.com |
| 433 | `A` | **C** | Article 17 | geniusacademy.org.in |
| 435 | `A` | **C** | Article 120 (1) | testbook.com |
| 444 | `C` | **A** | Business in the legislature shall be transacted only in official language of the state or in… | saarthik.com |
| 485 | `E` | **C** | the Governor of the State | examstocks.com |
| 490 | `E` | **D** | More than one of the above | licchavilyceum.com |
| 491 | `A` | **D** | 1 and 3 | geniusacademy.org.in |

Confirmed as already correct: **Q205** (Peer Muhammad Moonis), **Q212** (Nizamuddin Ahmad),
**Q222** (alphabetical order — a reasoning question misfiled under polity), **Q272** (Article 280),
**Q308** (Panchayati Raj is in the State List), **Q370** (Governor decides MLA disqualification,
Article 192), **Q395** (Article 210 language of business), **Q412** (PURA — Abdul Kalam),
**Q442** (Article 98), **Q445** (prorogation), **Q495** (Article 32/226).

In the second sweep the KGS/CSV/merged block of Q7–Q380 was checked row by row; the printed key held
in **196** of those rows. Notable confirmations: **Q7/Q10** (73rd Amendment traces to the 64th
Amendment Bill), **Q22** (Sarkaria report submitted 1987), **Q62/Q69** (2022 Vice-Presidential
electoral college = 788, per the ECI press note), **Q71/Q73** (Constitution Day, 26 November),
**Q74–Q79** (Constituent Assembly, 9 December 1946; 2 years 11 months 18 days; adopted by the
Assembly), **Q95** (Article 102(1)(a) office of profit) and **Q96** (Bihar, 40 Lok Sabha seats).

Open, with the reason recorded in the sheet: **Q48** (both (b) and (c) are true under Article 55(3)
and there is no "both" option), **Q146** (no printed option describes Zero Hour), **Q397** (question
deleted by BPSC in the 71st final key), **Q498** (the sanctioned strength in 1992-93 was 26; the
options offer 24/20/18/0).

## Source reliability, measured

| Source of the printed letter | Rows inspected | Wrong |
|---|---|---|
| Supplied JSON, rows flagged as JSON↔CSV conflicts (163 JSON rows in total) | 30 | **25 (83 %)** |
| Supplied JSON, uniform random sample of untouched rows | 8 | **3 (38 %)** |
| Supplied CSV (36 rows) | 2 | 0 |
| KGS book PDF (315 rows) | 12-row random audit | 1 (Q47, now corrected); 2 further rows have corrupt option tables |

* **JSON.** The letters behave like a different booklet's key. The conflict rows are naturally the
  worst (25 of 30 wrong), but a uniform random sample of eight rows that had never been flagged still
  produced three wrong answers (Q37, Q283, Q301), so the overall error rate is around 30–50 %. No
  JSON-derived letter should be used without content matching.
* **CSV.** Every spot-check agreed (Q1, Q102, Q395, …), and its `answer_text` matched the verified
  option each time. It is the most trustworthy of the three sources.
* **KGS.** The book's keys held up much better than the JSON's: nine of twelve sampled rows matched
  the constitutional position, one was wrong (Q47), one could not be settled (Q296) and one has a
  corrupt option table (Q498). Roughly a one-in-ten error rate is the working assumption for the
  306 rows that still carry a KGS key.

## Also found (not fixed, because they are content defects rather than key errors)

* Questions whose statement lists were lost in extraction, e.g. Q222's neighbour set and the many
  rows whose options end in stray `(a) (b) (c) (d) (e)` artefacts from the answer-table column.
* Reasoning, current-affairs, history and science questions filed under polity — 93 rows in the
  "Review / outside Laxmikanth chapter scope" section.
* Chapter assignment is still a best-fit keyword classifier, not an expert map.

## What "web-checked" means here, and what it does not

It means: a named, reachable page states the answer to *this* question, and that statement is
quoted in the ledger. It does not mean the rest of the sheet has been looked at. 474 rows still
print the key of their source book and are labelled as such in the workbook and the PDF. Nothing in
this file should be read as "the whole sheet is now verified".

## Continuing the job

The workflow is built to be extended, one ledger entry at a time:

```bash
# 1. add evidence entries to data/polity_answer_verification.json
#    { "row": <PDF question number>, "q": "<first words of the question>",
#      "printed": "E", "verified_key": "C", "verified_text": "...",
#      "status": "corrected", "source": "https://...", "evidence": "quoted sentence" }
python scripts/apply_polity_verification.py          # rewrites the workbook columns
python scripts/polity_pyq_pdf.py                     # re-renders the PDF
```

`apply_polity_verification.py --check` fails if a ledger entry's stated question does not match the
sheet, or if an entry marked *corrected* has a printed key that already equals the "verified" one,
so a mistyped row number cannot silently corrupt an answer.

Suggested next pass, in order of value:

1. the 126 remaining JSON-derived rows, exam by exam (64th, 68th, 69th, 70th, 71st solved papers
   cover most of them) — expect 40–60 wrong answers in this group alone;
2. the 306 KGS-key rows, where the expected error count is around thirty;
3. the 34 CSV rows, last, since they have been consistent everywhere so far.
