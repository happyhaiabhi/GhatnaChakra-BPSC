#!/usr/bin/env python3
"""Top-100 priors over FULL auto-link graph + expert-quality annotations + trends."""
import json
from collections import Counter, defaultdict

ov = json.load(open('data/pyq_phase2_overrides.json'))
samp = json.load(open('/tmp/p2/strata.json'))
recs = {}
for y in range(2015, 2027):
    d = json.load(open(f'data/pyq_phase2/GS_{y}.json'))
    for q in d['questions']: recs[q['qid']] = q

def auto(qid):
    L = recs[qid]['links']; return L[0]['level'] if L else 0
def expert(qid): return ov[qid][0] if qid in ov else auto(qid)
inlab = set(q for q in recs if auto(q) in (5,4,2) or any(q in samp[s] for s in samp))

# full graph: best-links of all 1200 + expert links
prim = Counter()   # prior -> # distinct targets (best-link)
altc = Counter()   # prior -> # ALT appearances
exq = defaultdict(list)  # prior -> expert tiers (labeled targets only)
tspan = defaultdict(set)
for q in recs:
    L = recs[q]['links']
    if L:
        prim[L[0]['qid']] += 1
        tspan[L[0]['qid']].add(int(q[:4]))
        for l in L[1:]:
            altc[l['qid']] += 1
    if q in ov and ov[q][1]:
        p = ov[q][1]
        prim[p] += 0  # expert link may equal auto best; count separately below
        exq[p].append(expert(q))
    if q in inlab and q not in ov and L:
        exq[L[0]['qid']].append(expert(q))
# expert-link targets (override links differ from auto best): add target counts
for q, v in ov.items():
    if v[1]:
        # count target-year span for expert link
        tspan[v[1]].add(int(q[:4]))

def subj(qid): return recs[qid].get('subject','?') if qid in recs else 'pre2015'

rows = []
for p, n in prim.items():
    eq = exq.get(p, [])
    rows.append(dict(p=p, n_best=n, n_alt=altc.get(p, 0),
                     expert_n=len(eq), expert_best=(max(eq) if eq else None),
                     expert_mean=(sum(eq)/len(eq) if eq else None),
                     span=f"{min(tspan[p])}-{max(tspan[p])}" if p in tspan else '',
                     subj=subj(p)))
rows.sort(key=lambda r: (-r['n_best'], -r['n_alt']))
print(f"priors with best-links: {len(rows)}")
print("\n== TOP-40 by distinct-target best-link count ==")
for r in rows[:40]:
    print(f"  {r['p']:10s} n={r['n_best']:2d} alt={r['n_alt']:2d} ex_n={r['expert_n']} ex_best={r['expert_best']} ex_mean={r['expert_mean']} span={r['span']:9s} {r['subj']}")
json.dump(rows[:100], open('/tmp/p2/top100_full.json','w'), indent=1)

# trends: tier mix over time (labeled, weighted) in 3 blocks
print("\n== TIER MIX by block (weighted %) ==")
for name, ys in [('2015-2018', (2015,2018)), ('2019-2022', (2019,2022)), ('2023-2026', (2023,2026))]:
    pop = Counter(auto(q) for q in recs if ys[0] <= int(q[:4]) <= ys[1])
    WT = {5:1.0, 4:1.0, 2:1.0, 3:pop[3]/max(1,sum(1 for q in samp['L3'] if ys[0]<=int(q[:4])<=ys[1])),
          1:pop[1]/max(1,sum(1 for q in samp['L1'] if ys[0]<=int(q[:4])<=ys[1])),
          0:pop[0]/max(1,sum(1 for q in samp['L0'] if ys[0]<=int(q[:4])<=ys[1]))}
    lab = [q for q in inlab if ys[0] <= int(q[:4]) <= ys[1]]
    W = sum(WT[auto(q)] for q in lab)
    g = lambda t: sum(WT[auto(q)] for q in lab if expert(q)>=t)/W*100
    print(f"  {name}: n={len(lab)} L4+%={g(4):.1f} L3+%={g(3):.1f} L2+%={g(2):.1f} L1+%={g(1):.1f}")
