#!/usr/bin/env python3
"""Cell-weighted (auto-tier x year / subject) estimates. Design-correct."""
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

targets = list(recs.keys())
inlab = set()
for q in targets:
    if auto(q) in (5,4,2) or any(q in samp[s] for s in samp): inlab.add(q)

def best_link(qid):
    e = expert(qid)
    if qid in ov: return (ov[qid][1], e)
    L = recs[qid]['links']
    if not L or e == 0: return (None, e)
    return (L[0]['qid'], e)

# cell pop and labeled means
popcell = Counter((auto(q), int(q[:4])) for q in targets)
popsubj = Counter((auto(q), recs[q].get('subject','?')) for q in targets)
labcell = defaultdict(list); labsubj = defaultdict(list)
for q in inlab:
    p, e = best_link(q)
    lag = int(q[:4])-int(p[:4]) if p else None
    labcell[(auto(q), int(q[:4]))].append((e, lag))
    labsubj[(auto(q), recs[q].get('subject','?'))].append((e, lag))

def cell_est(cell, labdict, popdict, fn):
    """weighted mean of fn over cell; fallback to tier-mean if cell empty."""
    items = labdict.get(cell, [])
    if items: return sum(fn(*x) for x in items)/len(items)
    a = cell[0]
    pool = [x for c, x in [(c, v) for c, vs in labdict.items() for v in vs] if c[0]==a]
    return sum(fn(*x) for x in pool)/len(pool)

print("== YEAR (cell-weighted, pop=100/yr) ==")
print("year | L4+% L3+% L2+% L1+% | meanlag(L2+) [flag if any cell borrowed]")
for y in range(2015, 2027):
    tot = sum(popcell[(a,y)] for a in range(6))
    g = lambda t: sum(popcell[(a,y)]*cell_est((a,y), labcell, popcell, lambda e,l: 1 if e>=t else 0) for a in range(6))/tot*100
    num = sum(popcell[(a,y)]*cell_est((a,y), labcell, popcell, lambda e,l: (l if (l is not None and e>=2) else 0)) for a in range(6))
    den = sum(popcell[(a,y)]*cell_est((a,y), labcell, popcell, lambda e,l: 1 if (l is not None and e>=2) else 0) for a in range(6))
    ml = num/den if den else float('nan')
    borrowed = [a for a in range(6) if popcell[(a,y)]>0 and not labcell.get((a,y))]
    print(f"{y} | {g(4):5.1f} {g(3):5.1f} {g(2):5.1f} {g(1):5.1f} | {ml:5.1f} {('borrow:'+str(borrowed)) if borrowed else ''}")

print("\n== SUBJECT (cell-weighted) ==")
print("subject | pop | L4+% L3+% L2+% L1+% | meanlag(L2+) lag80(L2+)")
subjs = sorted(set(recs[q].get('subject','?') for q in targets))
out_subj = {}
for s in subjs:
    tot = sum(popsubj[(a,s)] for a in range(6))
    if tot == 0: continue
    g = lambda t: sum(popsubj[(a,s)]*cell_est((a,s), labsubj, popsubj, lambda e,l: 1 if e>=t else 0) for a in range(6))/tot*100
    # lag distribution for lag80: build weighted lag counts
    lagc = Counter()
    for a in range(6):
        items = labsubj.get((a,s), [])
        if not items:
            pool = [x for c, vs in labsubj.items() if c[0]==a for x in vs]
            items = pool
        w = popsubj[(a,s)]/len(items) if items else 0
        for e, l in items:
            if l is not None and e >= 2: lagc[l] += w
    tot2 = sum(lagc.values())
    ml = sum(k*v for k,v in lagc.items())/tot2 if tot2 else float('nan')
    c=0; l80='-'
    for k in sorted(lagc):
        c+=lagc[k]
        if c>=0.8*tot2: l80=k; break
    borrowed = [a for a in range(6) if popsubj[(a,s)]>0 and not labsubj.get((a,s))]
    print(f"{s:20s} | {tot:3d} | {g(4):5.1f} {g(3):5.1f} {g(2):5.1f} {g(1):5.1f} | {ml:5.1f} {l80} {('borrow:'+str(borrowed)) if borrowed else ''}")
    out_subj[s] = dict(pop=tot, L4=g(4), L3=g(3), L2=g(2), L1=g(1), meanlag=ml, lag80=l80)
json.dump(out_subj, open('/tmp/p2/subj_est.json','w'), indent=1)
