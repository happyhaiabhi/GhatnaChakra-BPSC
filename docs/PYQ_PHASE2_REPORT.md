# UPSC Prelims PYQ Conceptual-Linkage Analysis (Phase 2) — Final Report

**Targets:** GS Paper 1, 2015–2026 (N = 1200). **Priors:** 1995–2025 with strict 20-year lookback
(max observed lag = 20; zero links exceed it) and strict no-future-leakage (every prior year <
target year, machine-asserted). **Engine:** run13 FROZEN (`scripts/pyq_phase2.py`).
**Expert review:** 349 overrides, 353 design-labeled targets (173 census + 180 random), 26 targeted
extras, 30 rareopt2 pair-checks. Standard: honest, traceable-to-real-questions numbers.

> §-mapping note: the brief asked for §24 order + Appendices A/B. No §24 template file exists in
> the repo, so the 24 sections below follow the brief's deliverable list in logical order. §14/§15
> tables are excerpts; the full machine-readable tables ship alongside this report (§24).

---

## §1 Objective & scope

Measure, **conceptually rather than lexically**, how much of each 2015–2026 UPSC Prelims GS paper
is answerable/helped by prior-year questions (PYQs) within a 20-year lookback. Outputs: L0–L5
relationship annotation + advantage types for target→prior links; knowledge graph; transformation
taxonomy with frequencies; Top 100 high-leverage PYQs; ranked recurring-concept map; year-by-year
and subject-wise coverage with 7/10/15/20-yr marginal value; signal-vs-noise for old PYQs;
conservative/moderate/broad coverage answers; subject PYQ-depth recommendations; a PYQ→Concept
study system; Immortal vs Dead concepts; and future-paper pattern inference (not prediction) —
all with confidence labels.

## §2 Method (engine + expert calibration)

1. **Engine (run13, frozen).** Every 2015–2026 target gets ranked prior-links with features
   (focus-f, shared entities/rare-terms/clusters, option-overlap) and an auto tier L0–L5.
   Population: auto-L5: 15, L4: 115, L3: 564, L2: 43, L1: 270, L0: 193.
2. **Expert calibration (design-based).** Census of auto-L5 (15/15), auto-L4 (115/115), auto-L2
   (43/43) + simple random samples of auto-L3 (80/564), auto-L1 (50/270), auto-L0 (50/193).
   353 labeled targets; each labeled target carries a design weight (1.0 for census tiers; 7.05 /
   5.4 / 3.86 for the L3/L1/L0 samples). All population figures are design-weighted; year/subject
   tables use cell (tier×year, tier×subject) weighting. Only 3 of 120 cells needed tier-mean
   borrowing (flagged in tables).
3. **Targeted extras (26).** Early-review finds in auto-L3/L1 (upward-biased by construction):
   **excluded** from all weighted estimates, **included** in verified counts.
4. **Link selection.** Expert best-link = engine best-link unless the expert found a better ALT
   (then link-switched) or found a missed prior by corpus search (27 engine-missed links, mostly
   in the auto-L0 sample). Every override records tier + link + reason
   (`data/pyq_phase2_overrides.json`, 349 entries).

## §3 Level definitions & boundary rules (expert)

- **L5** — (near-)verbatim repeat: prior determines the answer (e.g. 2021_P_11 × 2019_P_90,
  money-multiplier, identical).
- **L4** — partial-direct overlap: prior answers ≥1 statement/option or refutes one directly
  (e.g. 2026_P_36 boundary-counting excluded; 2025_P_10 capital-receipts × 2016_P_12 capital-budget).
- **L3** — same mechanism/Act/scheme, different provision, effect, or chemical (e.g. PFAS ×
  brominated flame-retardants — same persistence+bioaccumulation logic; GEAC-under-EPA ×
  GEAC-under-ministry).
- **L2** — framework familiarity: prior teaches the framework/topic but not the tested fact
  (e.g. Bollgard × Cas9; Sangam × Mrichchhakatika-scholars).
- **L1** — theme/format familiarity only (e.g. MDR × import-cover; town-pairs × region-pairs).
- **L0** — no meaningful link (incl. false friends: red-tides/algae × ocean-tides; Krishna-river ×
  Lord-Krishna; summit-preamble × Constitution-preamble; Bitcoin × Fanam-coins; Surat-city ×
  Surat-split).

**Boundary rules applied:** partial-direct statement overlap = L4; same-Act-different-provision /
same-mechanism-different-effect = L3 (explanatory-bridge test decides); framework-without-fact =
L2; same-subject theme/format-only = L1 (generous by design); cross-subject word-only = L0.
Zero conflicts between early verdicts and strata verdicts on overlapping questions.

## §4 Calibrated census (headline numbers)

Design-weighted estimates for N = 1200 (95% Wilson CIs, census tiers exact):

| Tier | Est. count | Share | 95% CI (count) |
|----|----------:|------:|---------------|
| L5 (verbatim) | 13 | 1.1% | — (verified 15; upper 72 reflects unsampled mass) |
| **L4+** (answerable) | **85** | **7.1%** | [57, 167] |
| **L3+** (mechanism+) | **235** | **19.6%** | [174, 339] |
| **L2+** (framework+) | **549** | **45.7%** | [449, 666] |
| **L1+** (any signal) | **981** | **81.8%** | [870, 1061] |
| L0 (no link) | 219 | 18.2% | — |

Full split: L5 ≈ 13, L4 ≈ 72, L3 ≈ 150, L2 ≈ 314, L1 ≈ 433, L0 ≈ 219.
**Verified** (seen by expert): 15 L5 + 35 L4 = 50 L4+; the estimate (85) projects sampled rates
onto unsampled mass. Honest reading: roughly **1 in 14 questions is directly answerable from a
PYQ; 1 in 5 shares mechanism; nearly half share framework; 4 in 5 carry at least theme signal.**

## §5 Engine diagnostics (auto vs expert)

| Auto tier | n | P(true L1+) | P(true L2+) | P(true L3+) | P(true L4+) | P(true L5) |
|-----------|---:|---:|---:|---:|---:|---:|
| L5 (census) | 15 | 1.00 | 1.00 | 0.93 | 0.73 | **0.47** |
| L4 (census) | 115 | 1.00 | 0.95 | 0.59 | **0.18** | 0.05 |
| L3 (sample) | 80 | 0.89 | 0.57 | **0.21** | 0.07 | 0.00 |
| L2 (census) | 43 | 0.84 | **0.40** | 0.12 | 0.07 | 0.00 |
| L1 (sample) | 50 | **0.78** | 0.18 | 0.06 | 0.00 | 0.00 |
| L0 (sample) | 50 | 0.54 | 0.18 | 0.06 | 0.04 | 0.00 |

Takeaways: (a) auto-L4 over-fires badly as "L4" (18%) but is an excellent L2+ screen (95%) —
treat auto-L4 as "needs expert triage", not as truth; (b) auto-L3 precision for true L3+ is only
21%, but 57% carry L2+ signal; (c) auto-L0 misses weak links 54% of the time (mostly L1 theme
links found only by active corpus search) — engine-L0 ≠ true-L0; (d) upgrades (missed L4+) hide
in every tier: auto-L3 7.5%, auto-L2 7%, auto-L1 0% (sample), auto-L0 4%.

## §6 Year-by-year conceptual coverage

Cell-weighted shares (% of each year's 100 Qs at/above tier) + mean lag of L2+ links:

| Year | L4+ | L3+ | L2+ | L1+ | mean lag |
|----|----:|----:|----:|----:|---:|
| 2015 | 8.0 | 28.7 | 33.8 | 62.5 | 6.3 |
| 2016 | 5.0 | 6.0 | 46.7 | 89.1 | 4.3 |
| 2017 | 5.0 | 33.1 | 40.1 | 83.8 | 5.8 |
| 2018 | 2.0 | 12.6 | 21.1 | 81.0 | 9.3 |
| 2019 | 1.0 | 8.0 | 68.7 | 75.0 | 8.0 |
| 2020 | 19.9 | 31.5 | 59.0 | 89.5 | 7.1 |
| 2021 | 5.0 | 18.0 | 39.8 | 82.6 | 6.2 |
| 2022 | 8.8 | 24.2 | 51.8 | 83.7 | 8.3 |
| 2023 | 9.0 | 21.0 | 66.3 | 75.0 | 7.7 |
| 2024 | 5.0 | 19.5 | 69.5 | 83.0 | 8.9 |
| 2025 | 2.0 | 11.3 | 29.9 | 70.3 | 7.8 |
| 2026 | 0.0 | 7.9 | 43.5 | 85.1 | 8.8 |

Notes: 2020 is the repeat-peak year (L4+ ≈ 20%: Welfare-State, money-multiplier-in-2021's-prior,
fertigation, sugarcane…). Year cells are small — single-year L3+/L4+ figures are volatile (e.g.
2016 L3+ 6% vs 2017 33%); trust the pooled 19.6% and the block trends (§19), not single-year spikes.

## §7 Subject-wise conceptual coverage

Cell-weighted (pop = target counts 2015–2026):

| Subject | pop | L4+ | L3+ | L2+ | L1+ | mean lag | lag80 |
|---------|----:|----:|----:|----:|----:|---:|---:|
| History | 149 | 12.6 | 27.6 | 57.4 | 86.0 | 6.1 | 6 |
| Economy | 239 | 5.6 | 29.4 | 56.3 | 78.7 | 8.8 | 16 |
| Science & Tech | 153 | 12.1 | 16.9 | 48.1 | 83.1 | 6.1 | 8 |
| Geography | 199 | 5.6 | 17.9 | 46.4 | 77.7 | 7.4 | 12 |
| Art & Culture | 56 | 1.8 | 3.6 | 45.4 | 90.6 | 9.6 | 13 |
| Environment | 100 | 7.7 | 18.3 | 50.3 | 92.4 | 6.6 | 9 |
| Polity | 302 | 5.9 | 15.9 | 29.0 | 79.1 | 6.8 | 11 |

History and S&T have the densest strong-link mass (L4+ ≈ 12–13%); Polity is the weakest
(L2+ only 29% — Polity re-tests fresh provisions yearly); Art & Culture is nearly all weak
familiarity (L3+ 3.6%, L1+ 91%) — theme helps, facts don't repeat. Env-auto0 and S&T-auto1 cells
borrowed tier means (flagged, negligible effect).

## §8 Window analysis: 7/10/15/20-yr marginal value

Share of ALL 1200 targets whose best-link falls within lag ≤ W (weighted %):

| Window | L4+ | L3+ | L2+ (marginal) | L1+ |
|--------|----:|----:|----:|----:|
| 3 yr | 2.4 | 4.7 | 11.8 | 30.4 |
| 5 yr | 4.2 | 8.0 | 18.7 (+6.8) | 42.7 |
| 7 yr | 5.1 | 11.0 | 26.2 (+7.5) | 51.9 |
| 10 yr | 6.3 | 15.3 | 35.4 (+9.3) | 63.9 |
| 15 yr | 6.8 | 17.5 | 41.1 (+5.6) | 73.0 |
| 20 yr | 7.1 | 19.6 | 45.7 (+4.6) | 81.8 |

The 5→10-yr band is the richest marginal zone (+16.8 L2+ points); 10→20 yrs still adds +10.3.
A 10-year PYQ file captures ~3/4 of the 20-year L2+ value (35.4/45.7) and ~4/5 of L3+ value
(15.3/19.6) — the standard "10-year PYQ" advice is roughly right for strong links, but the
second decade carries real weight for framework familiarity.

## §9 Conservative / moderate / broad 20-year coverage answer

- **Conservative (directly answerable, L4+): ≈ 7% — about 7 questions per paper** (CI 5–14%).
- **Moderate (mechanism-level help, L3+): ≈ 20% — about 20 questions per paper** (CI 15–28%).
- **Broad (framework/theme help, L2+/L1+): ≈ 46% / 82%** (CIs 37–56% / 73–88%).
Recommendation: quote the moderate figure (1 in 5) as "PYQs substantially help", the conservative
(1 in 14) as "PYQs directly answer", and never quote L1+ (82%) without the "theme-only" qualifier.

## §10 Advantage types

Primary advantage per target (constructed mapping from expert tier + option-overlap; documented,
not independently expert-verified):

| Advantage | Weighted Qs | Share | Meaning |
|-----------|----------:|------:|---------|
| answerability | 85 | 7.1% | prior (near-)determines the answer (L4–L5) |
| conceptual | 300 | 25.0% | prior teaches the tested mechanism/framework (L3, most L2) |
| elimination | 164 | 13.7% | prior kills ≥1 distractor (L2–L3 with option-overlap) |
| pattern | 433 | 36.1% | theme/format familiarity only (L1) |
| none | 219 | 18.2% | (L0) |

Among linked L2+ questions: 15.5% answerability / 54.6% conceptual / 29.9% elimination.
Multi-label reality: most L3–L4 links also eliminate; the table assigns each link its primary edge.

## §11 Transformation taxonomy (with frequencies)

Constructed classifier on link features (weighted over 1200; expert labels where present):

| Class | W | What it is | Example |
|-------|---:|-----------|---------|
| entity-bridge | 278 | same entity/concept, new question | GEAC-ministry → GEAC-statute |
| mechanism-transfer | 114 | same mechanism, different domain | BFRs → PFAS |
| angle-shift | 45 | same theme, different facet | OMO-RBI-tool → OMO-∈-MP |
| same-fact-new-frame | 20 | same fact, new frame | Swadeshi ⟺ Partition |
| paraphrase-repeat | 19 | reworded repeat | Money-Bill-NOT variants |
| verbatim-repeat | 4 | f ≥ 0.7 near-identical | Buddha-kingdoms 2014→2015 |
| option-echo | 0 | distractor overlap only, no entity/cluster | (never occurs pure in L2+) |
| surface-echo | 23 | thin lexical resemblance | FOBS × asteroids |
| weak-association | 363 | L1 with features | town-pairs × region-pairs |
| expert-verified-weak/strong | 93/12 | expert-found, no engine features | Ashoka × Kanganahalli |
| unclassified-weak | 11 | residual | — |
| spurious | 219 | L0 | red-tides × ocean-tides |

(Entity-bridge dominates strong links; mechanism-transfer is the prized L3 class; pure option-echo
without entity/cluster support does not occur — distractor overlap always rides a real concept.)

## §12 Signal vs noise: old PYQs

L2+ share of best-links by prior cohort (weighted; w = cohort link-mass):

| Prior cohort | w | L4+ | L3+ | L2+ |
|--------------|---:|----:|----:|----:|
| 1995–1999 | 17 | 6.0 | 23.8 | 35.7 |
| 2000–2004 | 77 | 7.8 | 32.5 | 58.6 |
| 2005–2009 | 70 | 4.3 | 23.3 | 60.9 |
| 2010–2014 | 348 | 8.1 | 28.8 | 68.1 |
| 2015–2019 | 326 | 13.8 | 23.1 | 46.8 |
| 2020–2025 | 144 | 1.4 | 9.7 | 45.4 |

Old PYQs are NOT noise: 2000–2009 priors deliver L2+ ≈ 60% — but the mass is thin (w = 147 vs
348 for 2010–14). The 2010–14 block is the golden corpus (68% L2+, 29% L3+). Strongest verbatims
come from 2015–19 priors (13.8% L4+ — adjacent-year repeats). Noise concentrates in: (a) pre-2000
thin mass, (b) cross-subject word-matches (the L0 false-friend catalogue, §3), (c) UNFCCC/GEF-type
"theme hubs" that link everywhere at L1 (international-orgs: 14/19 links L1).

## §13 Subject PYQ-depth recommendations

Optimal lookback = lag80 of L2+ links (captures 80% of framework-level value):

| Subject | Depth | Rationale |
|---------|-------|-----------|
| Economy | **16 yrs** | deepest memory (monetary-policy canon from 2000s still pays) |
| Art & Culture | 13 yrs | weak links only — read for theme, not facts |
| Geography | 12 yrs | place/concept links decay slowly |
| Polity | 11 yrs | provisions churn; depth helps procedure/federalism only |
| Environment | 9 yrs | conventions/protocols recur; facts update |
| Science & Tech | 8 yrs | tech churns; biotech/health mechanisms persist |
| History | 6 yrs (+canon) | 80% of value is recent — BUT the deep tail (lags 15–19) is all L3–L5 freedom-movement canon (Surat, 1813, INM-chrono). Do 6 yrs + the canon list, not 20 yrs flat. |

## §14 Top 100 high-leverage PYQs

Ranked by distinct-target best-link count over the FULL 1200-question graph (732 priors), with
expert-quality annotations where labeled. Top 40 (full 100: `data/pyq_phase2_calibrated_top100.json`):

| Prior | n | ALT | labeled/expert-best | Span | Subject |
|-------|---:|----:|---------------------|------|---------|
| 2010_P_55 (UNFCCC treaty) | 7 | 8 | 2 / L2 | 2015–2026 | pre2015 |
| 2017_P_43 (UPI) | 7 | 6 | 1 / L3 | 2018–2026 | Economy |
| 2013_P_23 (FRA authority) | 7 | 3 | 3 / L3 | 2018–2026 | pre2015 |
| 2016_P_84 (DigiLocker) | 6 | 4 | 1 / L1 | 2017–2023 | Polity |
| 2010_P_20 (malaria vaccine) | 6 | 4 | 0 / — | 2019–2026 | pre2015 |
| 2013_P_61 (kharif season) | 6 | 3 | 1 / L3 | 2019–2024 | pre2015 |
| 2012_P_4 (NGT/Art-21) | 5 | 6 | 2 / L2 | 2016–2024 | pre2015 |
| 2011_P_48 | 5 | 5 | 0 / — | 2015–2018 | pre2015 |
| 2014_P_24 (steel pollutants) | 5 | 5 | 2 / L3 | 2016–2021 | pre2015 |
| 2004_P_78 (foodgrain costs) | 5 | 3 | 1 / L3 | 2016–2020 | pre2015 |
| 2017_P_56 (GIF) | 5 | 3 | 0 / — | 2019–2026 | Economy |
| 2013_P_54 (Ajanta) | 5 | 2 | 1 / L2 | 2016–2026 | pre2015 |
| 2011_P_32 | 5 | 1 | 0 / — | 2017–2025 | pre2015 |
| 2014_P_6 (GEF) | 4 | 6 | 3 / L1 | 2015–2022 | pre2015 |
| 2021_P_13 (G-Sec) | 4 | 6 | 1 / L3 | 2023–2025 | Economy |
| 2004_P_93 (nuclear roles) | 4 | 4 | 1 / L2 | 2015–2019 | pre2015 |
| 2014_P_46 (wetlands) | 4 | 4 | 2 / L2 | 2015–2023 | pre2015 |
| 2017_P_76 (elections) | 4 | 4 | 2 / L2 | 2018–2022 | Polity |
| 2015_P_1 (PMJDY) | 4 | 2 | 3 / L3 | 2016–2024 | Economy |
| 2011_P_75 (mangroves) | 4 | 2 | 2 / L2 | 2016–2026 | pre2015 |
| 2015_P_79 (Fortaleza) | 4 | 2 | 1 / L1 | 2016–2025 | Polity |
| 2010_P_35 (H2 exhaust) | 4 | 1 | 3 / **L5** | 2015–2025 | pre2015 |
| 2003_P_42 (Mrichchhakatika) | 4 | 1 | 2 / L1 | 2020–2022 | pre2015 |
| 2021_P_6 (bonds) | 4 | 1 | 1 / L2 | 2022–2025 | Economy |
| 2003_P_96 | 4 | 0 | 0 / — | 2016–2018 | pre2015 |
| 2016_P_56 (FSDC) | 4 | 0 | 1 / L1 | 2017–2026 | Economy |
| 2007_P_7 (91st Amdt) | 3 | 8 | 2 / **L4** | 2018–2023 | pre2015 |
| 2002_P_21 (WIPO) | 3 | 5 | 1 / L1 | 2015–2017 | pre2015 |
| 2002_P_17 | 3 | 5 | 0 / — | 2017–2022 | pre2015 |
| 2015_P_18 (fly ash) | 3 | 5 | 1 / L2 | 2018–2020 | Environment |
| 2012_P_57 (joint sitting) | 3 | 4 | 2 / L3 | 2016–2023 | pre2015 |
| 2004_P_41 | 3 | 4 | 0 / — | 2016–2023 | pre2015 |
| 2007_P_6 | 3 | 4 | 1 / L1 | 2019–2023 | pre2015 |
| 2020_P_65 (G20) | 3 | 4 | 1 / L1 | 2022–2024 | Economy |
| 
...[truncated 11472 chars]