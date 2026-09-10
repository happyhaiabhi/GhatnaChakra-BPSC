#!/usr/bin/env python3
"""Phase 2 part 2: windows, subjects, advantages, taxonomy, Top-100, concepts."""
import json
from collections import Counter, defaultdict

links = json.load(open('/tmp/p2/analysis_links.json'))
W = sum(l['w'] for l in links)  # ~1200
print(f"labeled targets={len(links)} total-weight={W:.0f}")

def sw(pred): return sum(l['w'] for l in links if pred(l))

# ---------- year-by-year ----------
print("\n== YEAR x TIER (weighted %) ==")
years = sorted(set(l['ty'] for l in links))
print("year | n | w | L4+% L3+% L2+% L1+% | meanlag(L2+)")
for y in years:
    yl = [l for l in links if l['ty']==y]
    w = sum(l['w'] for l in yl)
    g = lambda t: sum(x['w'] for x in yl if x['e']>=t)/w*100
    lag = [x['lag'] for x in yl if x['lag'] is not None and x['e']>=2]
    wl = [x['w'] for x in yl if x['lag'] is not None and x['e']>=2]
    ml = sum(a*b for a,b in zip(lag,wl))/sum(wl) if wl else float('nan')
    print(f"{y} | {len(yl):3d} | {w:5.0f} | {g(4):5.1f} {g(3):5.1f} {g(2):5.1f} {g(1):5.1f} | {ml:5.1f}")

# ---------- subject-wise ----------
print("\n== SUBJECT x TIER (weighted %) ==")
subs = sorted(set(l['s'] for l in links))
print("subject | w | L4+% L3+% L2+% L1+% | meanlag(L2+) | lag80(L2+)")
for s in subs:
    sl = [l for l in links if l['s']==s]
    w = sum(l['w'] for l in sl)
    g = lambda t: sum(x['w'] for x in sl if x['e']>=t)/w*100
    lag = sorted((x['lag'],x['w']) for x in sl if x['lag'] is not None and x['e']>=2)
    tot = sum(x[1] for x in lag)
    ml = sum(a*b for a,b in lag)/tot if tot else float('nan')
    c=0; l80='-'
    for a,b in lag:
        c+=b
        if c>=0.8*tot: l80=a; break
    print(f"{s:20s} | {w:5.0f} | {g(4):5.1f} {g(3):5.1f} {g(2):5.1f} {g(1):5.1f} | {ml:5.1f} | {l80}")

# ---------- window marginal value ----------
print("\n== WINDOW COVERAGE: share of targets with best-link lag<=W and tier>=t (weighted %) ==")
print("W\\t | L4+ L3+ L2+ L1+ | (marginal gain vs prev W for L2+)")
prev=None
for Wd in [3,5,7,10,15,20]:
    g = lambda t: sum(x['w'] for x in links if x['lag'] is not None and x['lag']<=Wd and x['e']>=t)/W*100
    m = '' if prev is None else f"+{g(2)-prev:.1f}"
    prev = g(2)
    print(f"{Wd:3d} | {g(4):4.1f} {g(3):4.1f} {g(2):4.1f} {g(1):4.1f} | {m}")

# lag distribution of L2+ links
print("\n== LAG HISTOGRAM (L2+ links, weighted) ==")
h = Counter()
for l in links:
    if l['e']>=2 and l['lag'] is not None: h[l['lag']]+=l['w']
for k in sorted(h): print(f"  lag {k:2d}: {h[k]:6.1f}")

# old-PYQ signal vs noise: prior-year cohorts
print("\n== PRIOR COHORT signal (L2+ share of links from cohort, weighted) ==")
for lo,hi in [(1995,1999),(2000,2004),(2005,2009),(2010,2014),(2015,2019),(2020,2025)]:
    cl=[l for l in links if l['py'] is not None and lo<=l['py']<=hi]
    w=sum(l['w'] for l in cl)
    if not w: continue
    g=lambda t: sum(x['w'] for x in cl if x['e']>=t)/w*100
    print(f"  prior {lo}-{hi}: w={w:5.0f} L4+%={g(4):4.1f} L3+%={g(3):4.1f} L2+%={g(2):4.1f} L1+%={g(1):4.1f}")

json.dump({'W':W}, open('/tmp/p2/coverage_meta.json','w'))
