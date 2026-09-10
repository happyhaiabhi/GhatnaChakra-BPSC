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

---

## 1. Headline

Across the twelve Prelims GS papers from 2015 to 2026:

| | share of a 100-question paper |
|---|---|
| **Verbatim repeat or decisive concept already seen** ("strict") | **13.7 %** |
| **PYQ-solvable, strict + distinctive concept seen before** ("medium") | **22.8 %** |
| Topic has recurred in earlier papers, but the question is new ("recurring") | 44.5 % |
| Nothing in any earlier paper touches it ("novel") | 1.8 % |

So the honest answer to "how much of the paper do PYQs give you" is
**roughly one question in five**. A further ~45 % sits on ground the papers have
visited before, which helps with elimination but does not hand you the answer.
The remainder — and this is the number that matters for planning — has to come
from reading, not from PYQ revision.

Coverage is not constant. It ranges from **34 % (2015)** down to **14 % (2022)**:

| Year | strict | PYQ-solvable | topic seen | nothing | 20-yr weighted | decay | Prelims-only pool |
|---|---|---|---|---|---|---|---|
| 2015 | 13 % | **34 %** | 56 % | 3 | 0.214 | 0.151 | 32 % |
| 2016 | 13 % | 22 % | 48 % | 4 | 0.181 | 0.130 | 21 % |
| 2017 | 12 % | 23 % | 47 % | 1 | 0.175 | 0.132 | 20 % |
| 2018 | 14 % | 26 % | 53 % | 1 | 0.175 | 0.124 | 24 % |
| 2019 | 14 % | 21 % | 36 % | 2 | 0.176 | 0.124 | 18 % |
| 2020 | 13 % | 25 % | 45 % | 2 | 0.163 | 0.117 | 23 % |
| 2021 | 11 % | 21 % | 41 % | 2 | 0.185 | 0.129 | 18 % |
| 2022 | 9 % | **14 %** | 37 % | 1 | 0.171 | 0.119 | 13 % |
| 2023 | 13 % | 18 % | 49 % | 0 | 0.159 | 0.109 | 15 % |
| 2024 | 18 % | 23 % | 43 % | 2 | 0.180 | 0.119 | 21 % |
| 2025 | 19 % | 27 % | 44 % | 2 | 0.162 | 0.109 | 24 % |
| 2026 | 15 % | 20 % | 35 % | 1 | 0.144 | 0.097 | 12 % |

*20-yr weighted score* scores each question by the share of its concepts that
earlier papers cover, weighting the last 20 years at 1.0 and anything older at
0.5. *Decay score* uses a smooth 15-year half-life instead. *Prelims-only pool*
is the control: the same paper scored against earlier **Prelims** papers alone,
ignoring Mains and CSAT. It sits 1–8 points lower, which is the size of the
bonus you get from also having read Mains PYQs.

The downward drift is real but gentle, and it is not because UPSC stopped
reusing material: the strict-repeat count actually *rises* later in the series
(19 % in 2025). What falls is the middle band — papers increasingly test
entities that have never appeared before.

## 2. Which subjects repay PYQ work

| Subject | n | strict | PYQ-solvable | topic seen |
|---|---|---|---|---|
| Polity & governance | 294 | 18.7 % | **28.6 %** | 58.5 % |
| Economy | 238 | 15.1 % | 26.1 % | 49.2 % |
| Geography | 278 | 11.5 % | 19.4 % | 38.5 % |
| History | 149 | 10.1 % | 19.5 % | 38.9 % |
| Science & technology | 157 | 11.5 % | 17.2 % | 33.1 % |
| Art & culture | 54 | 7.4 % | 16.7 % | 29.6 % |

Polity and economy repeat; art and culture barely do. If your time is finite,
PYQ revision buys the most in polity, and the least in art and culture —
where the returns come from source reading instead.

## 3. Your recency instinct, measured

Shared concepts by the age of the earlier paper (all GS target years):

```
1y  ██████████████████████████████ 60
2y  ██████████████████████████████ 60
3y  ██████████████████████ 44
4y  █████████████████ 34
5y  █████████████████████████ 49
10y █████████ 18
15y ████████ 15
20y ████████████ 23
25y ███ 6
30y ██████ 12
```

Papers from the last five years supply **247** shared concepts — **49 per
paper**. Everything older than twenty years supplies **136**, or **12 per
paper**. A recent paper is worth about **4×** an old one, which is why the score
weights the last 20 years at 1.0 and anything older at 0.5. The tail is not
empty, though: the 21–31-year band still contributes 136 hits, so old papers
are lower-yield, not worthless.

The cost of the recency constraint is measurable: solving the best *k* papers
from **all** years reaches 11.9 % / 18.9 % / 23.1 % of the next paper for
k = 1 / 3 / 5, against 9.5 % / 15.8 % / 19.4 % if you restrict yourself to the
last 20 years. About 4 points of coverage is what ignoring pre-2006 papers
costs.

## 4. Which papers should you solve?

Backtested greedy selection — for each target year only papers published before
it are eligible, so nothing peeks ahead.

| Papers solved (k) | any earlier paper | last 20 years only |
|---|---|---|
| 1 | 11.9 % | 9.5 % |
| 3 | 18.9 % | 15.8 % |
| 5 | 23.1 % | 19.4 % |
| 10 | 28.6 % | 28.7 % |
| ceiling | **29 %** | 24 % |

Most frequently picked, within a 20-year window: **2015** (8 times), **2014**
(6), **2010** (5), **2012** (5), **2008** (4), **2011** (4). Allowing any year,
**1995** is picked first for half the target years — but note *why*: it is a
paper of 100 short, fact-dense, single-topic questions (136 characters on
average, against 323 in 2025), so it covers more distinct concepts per paper
than a modern paper of long statement-sets. That maximises concept coverage
without necessarily maximising exam value; the 20-year column is the more
practical recommendation.

The ceiling figure is the important one: **even solving every earlier paper
reaches only ~29 % of the next paper at concept level** (24 % within a 20-year
window). PYQs are necessary and
they are not sufficient — the rest has to come from static reading and current
affairs.

Feeder papers (which earlier papers feed a given paper) are listed per year in
`backsolve.html`. The strongest single links found are **2015 → 2017** (24
shared concepts) and **2015 → 2016** (18) — no other year feeds its successors
as heavily as 2015 does.

## 5. CSAT and Mains

**CSAT** is far more repetitive than GS — 37 % in 2023 and 2025, 29 % in 2022,
26 % in 2026, against 17 % back in 2015 — but read the caveat in section 7
before trusting 2024.

**Mains** questions are long-form, so concept-matching understates them; the
trend is still informative and it points the other way from Prelims — Mains
coverage *rises* over the period, from 13 % (2015) to 23 % (2025), because the
GS papers increasingly revisit themes already examined in earlier Mains.

## 6. What the tiers mean

| Tier | Meaning |
|---|---|
| **strict** | Verbatim or near-verbatim repeat, or the question's decisive named entity appeared earlier. A PYQ student should get these. |
| **medium** | A distinctive concept or entity of the question appeared earlier, though the angle differs. |
| **recurring** | The broad topic recurs in earlier papers (Panchayati Raj, Money Bill, westerlies) but this exact question is new. |
| **loose** | Partial or single-word overlap — related, not sufficient. |
| **novel** | No earlier paper carries even the topic. |

Method, briefly: exam boilerplate is stripped ("which of the following",
"select the correct answer using the code given below", statement numbering),
concepts are clause-bounded 1–4-grams kept only when rare enough to be
informative, and each concept is matched against **its own** best earlier paper
— a paper's concepts usually come from several earlier years, not one. Every
match is then weighted by the age of the earlier paper. Only multi-word
entities can make a question "strict", and only concepts drawn from the
question itself (not its answer options) can do so.

## 7. How far to trust it

Hand-checked: **48 sampled matches**, stratified by tier, each judged on one
question — *does the earlier PYQ materially help answer the target?*
(`data/pyq_backsolve_calibration.json`.)

| Tier | judged genuinely useful |
|---|---|
| strict | 60 % (6/10) |
| medium | 70 % (7/10) |
| **strict + medium** | **65 % (13/20)** |
| recurring | 30 % |
| loose | 30 % |
| novel verdicts that were right | 75 % (6/8) |

So roughly **two thirds of the headline tier survives human review**, and the
looser tiers are exactly as weak as advertised — treat them as "worth a look",
not as coverage.

Known limits, in order of importance:

1. **Papers before 2011 are truncated in this dataset** — only 100 of the 150
   questions in each pre-2011 paper are present. Coverage for target years
   2015–2020 is therefore understated by an unknown amount.
2. **The "novel" rate is a floor, not a ceiling.** Two of eight sampled novel
   verdicts were wrong: the 2012 paper does cover the *Index of Eight Core
   Industries* question that 2015 asked, and the 2024 chewing-gum question does
   cover 2025's cigarette-butt question. Both were missed because the shared
   wording sits above the frequency cut-off. Nothing before 1995 is in the data
   at all.
3. **CSAT 2024 is a data problem, not a finding.** It reports 96 % coverage
   because 70 of its 79 questions are verbatim copies of the 2022 and 2023
   papers in the source dataset. Verify against the official UPSC paper before
   drawing conclusions from that year.
4. **Morphology costs recall.** "indices/index", "panchayat/panchayati" and
   similar variants only match after stemming and prefix rules; some pairs still
   slip through.
5. **The optimizer maximises concept coverage, not exam value** — see the 1995
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
