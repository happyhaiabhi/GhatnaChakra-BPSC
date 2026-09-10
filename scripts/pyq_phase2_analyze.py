#!/usr/bin/env python3
"""Phase 2 analysis: calibrated census, coverage, taxonomy, Top-100, concept map.
Design: census tiers (auto5/4/2, weight 1) + random samples (auto3/1/0, weighted).
Targeted extras excluded from weighted estimates. Strict no-future-leakage (prior<target).
"""
import json, math
from collections import Counter, defaultdict

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    m = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (max(0.0, (c-m)/d), min(1.0, (c+m)/d))

ov = json.load(open('data/pyq_phase2_overrides.json'))
samp = json.load(open('/tmp/p2/strata.json'))
recs = {}
for y in range(1995, 2027):
    try: d = json.load(open(f'data/pyq_phase2/GS_{y}.json'))
    except FileNotFoundError: continue
    for q in d['questions']: recs[q['qid']] = q

def auto(qid):
    L = recs[qid]['links']; return L[0]['level'] if L else 0

targets = [q for q in recs if 2015 <= int(q[:4]) <= 2026]
pop = Counter(auto(q) for q in targets)
WT = {5: 1.0, 4: 1.0, 2: 1.0, 3: pop[3]/len(samp['L3']), 1: pop[1]/len(samp['L1']), 0: pop[0]/len(samp['L0'])}

# labeled set for design-weighted estimation: census tiers (all) + random strata only
labeled = []
for q in targets:
    a = auto(q)
    if a in (5, 4, 2): labeled.append(q)
    elif any(q in samp[s] for s in samp): labeled.append(q)

def expert(qid): return ov[qid][0] if qid in ov else auto(qid)

def best_link(qid):
    """(link_qid or None, tier, source). Expert link if override else auto best (None if no links or expert-L0)."""
    e = expert(qid)
    if qid in ov:
        return (ov[qid][1], e, 'expert')
    L = recs[qid]['links']
    if not L or e == 0: return (None, e, 'auto')
    return (L[0]['qid'], e, 'auto')

# ---------- 1. calibrated census ----------
census = {}
for e in [5, 4, 3, 2, 1, 0]:
    tot = sum(WT[auto(q)] for q in labeled if expert(q) == e)
    census[e] = tot
print("== calibrated census (weighted) ==")
for e in [5,4,3,2,1,0]:
    print(f"  expert-L{e}: {census[e]:.1f} ({census[e]/1200*100:.1f}%)")

# CIs: exact for census tiers; Wilson-projected for sampled tiers
print("\n== tier shares with 95% CI (design-based) ==")
for thr, name in [(5,'L5'),(4,'L4+'),(3,'L3+'),(2,'L2+'),(1,'L1+')]:
    # census part exact
    cx = sum(1 for q in targets if auto(q) in (5,4,2) and expert(q) >= thr)
    lo = hi = cx
    for s, a in [('L3',3),('L1',1),('L0',0)]:
        qs = samp[s]; k = sum(1 for q in qs if expert(q) >= thr)
        l, h = wilson(k, len(qs))
        lo += l*pop[a]; hi += h*pop[a]
    print(f"  {name}: est={(cx + sum(sum(1 for q in samp[s] if expert(q)>=thr)/len(samp[s])*pop[a] for s,a in [('L3',3),('L1',1),('L0',0)])):.0f}  CI=[{lo:.0f},{hi:.0f}]")

# precision / upgrade rates per auto tier
print("\n== auto-tier precision (P(true>=t|auto)) + upgrade ==")
for a in [5,4,3,2,1,0]:
    src = targets if a in (5,4,2) else samp[{'L3': 'L3', 'L1': 'L1', 'L0': 'L0'}[['L3','L1','L0'][[3,1,0].index(a)]]]
    qs = [q for q in src if auto(q)==a]
    n = len(qs)
    p_ge = {t: sum(1 for q in qs if expert(q)>=t)/n for t in [1,2,3,4,5]}
    print(f"  auto{a} n={n}: " + " ".join(f"P(L{t}+)={p_ge[t]:.2f}" for t in [1,2,3,4,5]))

# ---------- link / lag data (labeled only) ----------
links = []  # (target, tyear, subj, etier, prior|None, pyear|None, lag|None, w)
for q in labeled:
    p, e, src = best_link(q)
    ty = int(q[:4])
    if p is None:
        links.append((q, ty, recs[q].get('subject','?'), e, None, None, None, WT[auto(q)]))
    else:
        py = int(p[:4]); assert py < ty, (q, p)
        links.append((q, ty, recs[q].get('subject','?'), e, p, py, ty-py, WT[auto(q)]))
linked = [l for l in links if l[4] is not None]
print(f"\n== links: labeled={len(links)} linked={len(linked)} ==")
print("max lag:", max(l[6] for l in linked), "| lags>20:", sum(1 for l in linked if l[6]>20))

with open('/tmp/p2/analysis_links.json','w') as f:
    json.dump([dict(t=t,ty=ty,s=s,e=e,p=p,py=py,lag=lag,w=w) for t,ty,s,e,p,py,lag,w in links], f)
print("wrote /tmp/p2/analysis_links.json")
