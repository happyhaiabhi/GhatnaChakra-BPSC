# PYQ Back-solve — how much of a UPSC paper earlier papers already taught

For every paper from **2015 to 2026** this measures how much of it a candidate
could have handled using **only earlier previous-year questions** (PYQs), with
extra weight on the most recent 20 years. The immediate precedent for each
question is published alongside it, so "solvable from PYQs" is a claim you can
check one question at a time.

- Interactive: **`backsolve.html`** — pick a paper, see each question with the
  earlier papers behind it.
- Data: `data/pyq_backsolve_summary.json`, `data/pyq_backsolve/<DATASET>_<YEAR>.json`,
  `data/pyq_backsolve_summary.csv`.
- Engine: `scripts/pyq_backsolve.py` (standard library only, ~40 s end to end).
- Hand-checked sample: `data/pyq_backsolve_calibration.json`.

### What changed since the first cut, and why

The first version reported 22.8 % of a GS paper as "PYQ-solvable". Reading the
per-question output showed that number was inflated by matches that meant
nothing — a geography question on cyclones was being shown a **CSAT** logic
puzzle because both contained the word *height*. Four fixes:

1. **An ordinary word is never a concept.** Only multi-word entities
   ("liquidity adjustment facility"), proper nouns ("Keoladeo") and acronyms
   can match. A lone common word like *thickness*, *founded* or *replacement*
   is now reported as a labelled topic word with the years it occurs in — never
   dressed up as a matched question.
2. **Paper series are isolated.** CSAT (comprehension / quant / logic) is
   evidence for CSAT and nothing else, in both directions: no CSAT item appears
   under a GS or Mains question, and no GS item appears under a CSAT one.
   Cross-series evidence (Mains → Prelims) survives, but it is shown in its own
   group marked "weaker evidence", and it can never create a *strict* or
   *medium* verdict on its own.
3. **Comprehension passages are not comparable.** A ~1,160-character passage
   matches everything, so passages are never used as evidence, and passage
   questions are counted in their own `passage` bucket instead of inflating
   either "solved" or "novel".
4. **Similarity is not repetition.** Two questions sharing 67 % of their words
   is not a repeat; a verdict of "repeat" now also requires a quarter of the
   target's own clauses to reappear.

The effect is a materially smaller and more honest number: **~17 %** of a GS
paper rather than ~23 %, and **36 % genuinely untouched** by any earlier paper
instead of a near-zero 1.8 %.

---

## 1. Headline

Across the twelve Prelims GS papers from 2015 to 2026 (1,200 questions):

| | share of a 100-question paper |
|---|---|
| **Verbatim repeat, or the decisive concept already asked** ("strict") | **5.9 %** |
| **The concept was asked before, at a different angle** ("medium") | **10.8 %** |
| Topic has recurred, but the question itself is new ("recurring") | 24.2 % |
| One shared concept, usually a coincidence ("loose") | 23.4 % |
| Nothing in any earlier paper touches it ("novel") | **35.9 %** |

The honest answer to "how much of the paper do PYQs give you" is **about one
question in six** — 16.7 % is strict or medium. Another quarter sits on ground
the papers have walked before, which helps with elimination but does not hand
you the answer. And **more than a third is genuinely new ground**: no earlier
paper in the 31-year archive covers it. That is the number that should drive
planning, because it is the part PYQ revision cannot reach at all.

Coverage moves year to year, from **24 % (2015)** down to **8 % (2023)**:

| Year | strict | medium | recurring | loose | novel | PYQ-solvable | 20-yr weighted | decay |
|---|---|---|---|---|---|---|---|---|
| 2015 | 8 | 16 | 23 | 18 | 34 | **24.2 %** | 0.139 | 0.100 |
| 2016 | 4 | 15 | 27 | 26 | 28 | 19.0 % | 0.119 | 0.088 |
| 2017 | 8 | 9 | 26 | 19 | 38 | 17.0 % | 0.097 | 0.073 |
| 2018 | 9 | 12 | 27 | 22 | 30 | 21.0 % | 0.110 | 0.077 |
| 2019 | 5 | 10 | 21 | 22 | 42 | 15.0 % | 0.089 | 0.062 |
| 2020 | 8 | 13 | 23 | 17 | 39 | 21.0 % | 0.091 | 0.064 |
| 2021 | 5 | 12 | 20 | 21 | 42 | 17.0 % | 0.094 | 0.067 |
| 2022 | 4 | 6 | 17 | 31 | 41 | **10.1 %** | 0.091 | 0.063 |
| 2023 | 3 | 5 | 24 | 26 | 42 | **8.0 %** | 0.072 | 0.051 |
| 2024 | 5 | 12 | 27 | 23 | 33 | 17.0 % | 0.089 | 0.060 |
| 2025 | 7 | 11 | 19 | 27 | 36 | 18.0 % | 0.088 | 0.059 |
| 2026 | 4 | 8 | 36 | 28 | 24 | 12.0 % | 0.086 | 0.056 |

*PYQ-solvable* = strict + medium. *20-yr weighted* scores each question by the
share of its concepts that earlier papers cover, weighting the last 20 years at
1.0 and anything older at 0.5; *decay* uses a smooth 15-year half-life instead.
Both columns fall steadily across the series — from 0.139 in 2015 to 0.086 in
2026 — which is the recency story in Section 3.

The `loose` column deserves a warning: it is a single shared concept, and on
inspection roughly half of it is coincidence (a rivers question matched on the
name *Prayagraj*). Treat anything below `recurring` as "vaguely familiar", not
as preparation.

## 2. Which subjects repay PYQ work

| Subject | n | strict | PYQ-solvable | topic seen | novel |
|---|---|---|---|---|---|
| Economy | 238 | 6.7 % | **22.7 %** | 48.7 % | 32.4 % |
| Art & culture | 54 | 1.9 % | 18.5 % | 33.3 % | 37.0 % |
| History | 149 | 5.4 % | 18.1 % | 33.6 % | 26.2 % |
| Polity & governance | 294 | 7.5 % | 16.0 % | 51.4 % | 25.9 % |
| Geography | 278 | 6.5 % | 13.7 % | 33.8 % | 44.2 % |
| Science & technology | 157 | 1.9 % | 10.2 % | 27.4 % | 58.0 % |

*PYQ-solvable* is strict + medium, cumulative. *novel* is the share no earlier
paper touches at all.

Two things stand out, and they cut in opposite directions.

**Polity is still the safest bet, but for a different reason than before.** Its
strict-repeat rate is the highest of any subject (7.5 %), yet its
PYQ-solvable share is only mid-table, because so many polity questions are
ground the papers revisit without ever repeating. If you want questions you can
actually answer from memory, polity; if you want elimination practice, polity.

**Science & technology is where PYQs stop working.** Nearly six in ten of its
questions (58 %) have no antecedent anywhere in the archive, and only 1.9 % are
verbatim repeats. This is the subject where a PYQ-only strategy fails outright,
and it is a large, growing share of the paper.

The headline ordering here is less stable than it looks — art & culture sits
second on only 54 questions, so a handful of matches moves it several points.
Economy, polity and geography rest on 240–290 questions each and are solid.

## 3. Your recency instinct, measured

Shared concepts by the age of the earlier paper, pooled over all twelve GS
target years, in five-year bands:

```
 1-5y  ██████████████████████████████  290   (58 per source paper)
 6-10y ███████████████████              180   (36)
11-15y █████████                         94   (19)
16-20y ██████████                       102   (20)
21-31y █████████████████████████        245   (22)
```

The instinct is right, with two caveats.

**Yes, recent papers carry far more.** The last five years supply 58 shared
concepts each against 22 for the 21–31-year band — about **2.6×**. That is why
the score weights the last 20 years at 1.0 and anything older at 0.5.

**But the tail is not dead, and the cliff is soft.** The 21–31-year band
contributes 245 hits — more than the 11–15 and 16–20 bands *combined* — because
it contains eleven papers rather than five. Per paper it is the weakest band,
yet it is far from worthless, and the 16–20 band (20 per paper) is statistically
indistinguishable from the 11–15 band (19). A hard 20-year cutoff is a
reasonable planning rule, not a property of the data: the decline is gradual.

The year-by-year figures are noisy (age 8 spikes to 56, age 25 drops to 8)
because each source year has a different mix of subjects, so read the bands and
not the individual bars.

## 4. Which papers should you solve?

Backtested greedy selection — for each target year only papers published before
it are eligible, so nothing peeks ahead. Coverage is the share of the next
paper's questions that land in strict or medium.

| Papers solved (k) | share of the next paper covered |
|---|---|
| 1 | 12.1 % |
| 3 | 19.3 % |
| 5 | 23.5 % |
| 10 | 30.9 % |
| every paper (oracle ceiling) | ~31 % |

The two numbers to take away: **one paper bought 12 %**, and **ten papers
bought 31 % — which is essentially all of it**. An oracle allowed to use every
earlier paper reaches ~31 % too, so there is no reservoir of coverage waiting
beyond k = 10. Returns diminish sharply after the fifth paper.

Most-picked papers across the twelve target years: **1995** (8 of 12),
**2015** (8), **2014** (5), **2001** (4), **2011** (4). 1995 and 2015 dominate
for opposite reasons and the difference matters:

- **2015** is the strongest *feeder* — it supplies more shared concepts to later
  papers than any other year, and it is a modern-format paper, so its questions
  resemble what you will actually face.
- **1995** wins on density: 100 short, fact-dense, single-topic questions
  (136 characters on average, against 323 in 2025). It covers more distinct
  concepts per paper, which is exactly what a coverage optimiser rewards — but
  it rewards coverage, not exam value. Solve 2015 first; use 1995 as a
  concept-sweep, not a mock.

Strongest single links found: **2015 → 2017** (24 shared concepts) and
**2015 → 2016** (18). No other year feeds its successors as heavily as 2015
does.

The ceiling is the sobering figure: **solving every earlier paper reaches only
about 31 % of the next paper.** PYQs are necessary and they are not sufficient —
the remaining two-thirds has to come from static reading and current affairs.

## 5. CSAT and Mains

**CSAT is where the isolation rule bites hardest.** Once CSAT is scored only
against earlier CSAT — and once the ~25 comprehension questions in each paper
are set aside as incomparable — the picture is that aptitude questions barely
repeat in content terms:

| Year | non-passage Qs | strict | PYQ-solvable | novel |
|---|---|---|---|---|
| 2015 | 25 | 4.0 % | 4.0 % | 86 % |
| 2017 | 22 | 0.0 % | 2.0 % | 84 % |
| 2019 | 20 | 2.0 % | 4.0 % | 78 % |
| 2021 | 26 | 1.9 % | 1.9 % | 77 % |
| 2022 | 46 | 12.7 % | 19.0 % | 65 % |
| 2023 | 28 | 11.1 % | 18.5 % | 72 % |
| 2024 | 43 | 93.4 % | 93.4 % | 7 % |
| 2025 | 22 | 17.6 % | 25.5 % | 71 % |
| 2026 | 36 | 6.9 % | 10.3 % | 79 % |

**Ignore 2024** — see section 7. Outside it, the honest reading is that CSAT
rewards *technique*, not *recall*: with the exception of 2022–2023, earlier
papers do not teach you the content of the next one. Practise the method; do
not expect the questions to come back.

**Mains runs the other way to Prelims.** Coverage is low in absolute terms but
rises steadily — strict from 0.7 % (2016) to 5.7 % (2025), and
strict + medium from 2.0 % to 9.9 % — and the share with *no* antecedent falls
from 87 % (2015) to 56 % (2025). Part of that is simply a growing archive, but
not all: the 2021–2025 papers revisit themes earlier Mains papers examined far
more than the 2015–2019 papers did. Mains is long-form, so a single concept
match understates how much a previous essay on the same theme would have helped
— read these as a floor, not an estimate.

## 6. What the tiers mean

| Tier | Meaning |
|---|---|
| **strict** | Verbatim or near-verbatim repeat, or two of the question's decisive rare entities appeared earlier, or one plus a quarter of its clauses. A PYQ student should answer these. |
| **medium** | A distinctive concept of the question appeared earlier — a rare multi-word entity, or two of its concepts landing together in one earlier paper — though the angle differs. |
| **recurring** | The broad topic recurs (Panchayati Raj, Money Bill, westerlies) but this question is new. Helps elimination, not recall. |
| **loose** | A single shared name or partial overlap — related, rarely sufficient. About half is coincidence. |
| **novel** | No earlier paper carries even the topic. |
| **passage** | A comprehension passage question. Excluded from the percentages: a 1,160-character passage has no comparable earlier item, so scoring it would only manufacture numbers. |

Method, briefly: exam boilerplate is stripped ("which of the following",
"select the correct answer using the code given below", statement numbering),
concepts are clause-bounded 1–4-grams kept only when rare enough to be
informative, and each concept is matched against **its own** best earlier paper
— a paper's concepts usually come from several earlier years, not one. Every
match is then weighted by the age of the earlier paper.

Three rules do most of the work in keeping the output honest:

- **Only multi-word entities, proper nouns and acronyms are matchable.**
  A single ordinary word — *height*, *thickness*, *founded* — is never shown as
  a matched question. It appears, if at all, as a labelled topic word with the
  years it occurs in, and it cannot promote a question's tier.
- **Stem, not options.** Only concepts drawn from the body of the question count
  towards strict or medium. Matches found solely in the answer options can only
  reach `recurring`.
- **Series isolation.** CSAT is scored against CSAT alone; GS and Mains may
  cross-reference each other, and when they do the cross-series matches appear
  in a separate group labelled "weaker evidence" and can never, by themselves,
  make a question strict or medium.

## 7. How far to trust it

Hand-checked in two independent passes over **50 sampled questions** (25 per
pass, 5 per tier, GS and Mains, 2015–2026), each judged on one question —
*would studying the earlier PYQ materially help answer this?* Five were left
unjudged because the sampled text was truncated.
(`data/pyq_backsolve_calibration.json`, `label` field.)

| Tier | judged genuinely useful |
|---|---|
| strict | **80 % (8/10)** |
| medium | 60 % (6/10) |
| **strict + medium** | **70 % (14/20)** |
| recurring | 38 % (3/8) |
| loose | 67 % (6/9) |
| novel verdicts that were right | 67 % (6/9) |

**Seven in ten of the headline tier survives human review**, and the ordering is
the right way round: strict beats medium, medium beats recurring. The first cut
of this study scored 65 % on the same question, so the number went *down* while
the accuracy went *up* — the discarded matches were the wrong ones.

`recurring` is the weak link at 38 %, which is consistent with what it is:
shared vocabulary, not shared knowledge. The `loose` figure is flattered by
Mains essay questions whose topic word really is the question (*Hume*, *Austin*,
*Chola*); on GS it is closer to half noise. The two `novel` misses were both
cases where the earlier paper covered the topic in different words — the
Harappan seals question against "salient features of Harappan architecture",
and a 2016 Mains question on faith and reason — which is why the novel rate is
better read as a ceiling than a measurement.

These are 45 judgements, so treat every row as ±15 points. They are a spot
check, not a confidence interval.

Known limits, in order of importance:

1. **Papers before 2011 are truncated in this dataset** — only 100 of the 150
   questions in each pre-2011 paper are present. Coverage for target years
   2015–2020 is understated by an unknown amount, and nothing before 1995
   exists at all.
2. **The "novel" rate is a ceiling, not a measurement.** Two of the sampled
   novel verdicts were wrong in the same way: a Mains question on
   multidimensional poverty was scored novel even though the 2012 paper asks
   about the MPI directly, and "salient features of Harappan architecture" was
   scored novel against a 2001 question on Harappan seals. Wording that differs
   enough — or entities just above the frequency cut-off — reads as new when a
   human would call it covered. The true novel share is below 36 %; how far
   below, this method cannot say.
3. **CSAT 2024 is a data problem, not a finding.** It reports 93 % coverage
   because 38 of its questions are verbatim copies of the 2022 and 2023 papers
   in the source dataset. Verify against the official UPSC paper before drawing
   conclusions from that year, and read the CSAT column without it.
4. **Morphology costs recall.** "indices/index", "panchayat/panchayati" and
   similar variants only match after stemming and prefix rules; some pairs still
   slip through.
5. **CSAT itself is poorly suited to this method.** Aptitude questions repeat in
   *form*, and form is not what concept matching measures. The low CSAT numbers
   say more about the method than about the paper.
6. **The optimizer maximises concept coverage, not exam value** — see the 1995
   note in section 4.

## 8. Regenerating

```bash
python scripts/pyq_backsolve.py                 # full run  -> data/
python scripts/pyq_backsolve.py --check         # 2-year smoke test
python scripts/pyq_backsolve.py --calibrate     # print a fresh labelling sample
```

Then open `backsolve.html` over HTTP (`python -m http.server 8000`) — the page
fetches `data/pyq_backsolve_summary.json` plus one file per paper, so it only
downloads what you are looking at.
