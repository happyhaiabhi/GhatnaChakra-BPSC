#!/usr/bin/env python3
"""Appendix B: concept timelines + immortal/dead + KG edges."""
import json
from collections import Counter, defaultdict

concepts = json.load(open('/tmp/p2/concepts.json'))
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

# classify concepts
high, low, immortal, dead = [], [], [], []
for c, d in concepts.items():
    tiers = {int(k): v for k, v in d['tiers'].items()}
    n = d['n']; span = max(d['tyears'])-min(d['tyears']) if len(d['tyears'])>1 else 0
    strong = sum(v for t, v in tiers.items() if t >= 3)
    # high confidence: >=4 links, >=3 distinct years, >=1 L3+
    if n >= 4 and len(d['tyears']) >= 3 and strong >= 1: high.append(c)
    else: low.append(c)
    # immortal: span>=8y and L2+ in >=3 distinct years
    # (approx: need per-year tiers; use overall: span>=8, L2+ count>=3)
    l2n = sum(v for t, v in tiers.items() if t >= 2)
    if span >= 8 and l2n >= 3: immortal.append(c)
    # dead/cold: only L1 (no L2+) OR single year
    if l2n == 0 or len(d['tyears']) <= 1: dead.append(c)

print(f"concepts={len(concepts)} high={len(high)} low={len(low)} immortal={len(immortal)} dead={len(dead)}")
print("\nHIGH-CONFIDENCE:", high)
print("\nIMMORTAL:", immortal)
print("\nDEAD/COLD:", dead)

L = ["# Appendix B — Concept timelines (shared-cluster links, labeled targets)", ""]
L.append(f"Covers {len(concepts)} concepts from {sum(d['n'] for d in concepts.values())} labeled best-links with engine features "
         "(27 expert-found links lack engine features and are excluded here). Tiers are EXPERT tiers. "
         "High-confidence = ≥4 links, ≥3 distinct target-years, ≥1 L3+. Immortal = span ≥8y with ≥3 L2+ links.")
L.append("")
for grp, members, title in [("HIGH-CONFIDENCE", sorted(high, key=lambda c: -concepts[c]['w']), "## B1. High-confidence recurring concepts"),
                            ("OTHERS", sorted(low, key=lambda c: -concepts[c]['w']), "## B2. Lower-confidence / thin concepts")]:
    L.append(title); L.append("")
    for c in members:
        d = concepts[c]
        tiers = dict(sorted(((int(k), v) for k, v in d['tiers'].items())))
        tags = []
        if c in immortal: tags.append("IMMORTAL")
        if c in dead: tags.append("COLD")
        L.append(f"### {c} {' '.join('['+t+']' for t in tags)}")
        L.append(f"- weight={d['w']:.0f} links={d['n']} priors={d['npriors']} years={min(d['tyears'])}–{max(d['tyears'])} ({len(d['tyears'])} distinct) tiers={tiers}")
        L.append(f"- examples: {'; '.join(d['ex'])}")
        L.append("")
open('/tmp/p2/appendixB.md','w').write("\n".join(L))
print("\nwrote /tmp/p2/appendixB.md")

# KG edges: all 1200 best-links
edges = []
for q in sorted(recs):
    Lq = recs[q]['links']
    if q in inlab:
        e = expert(q)
        p = ov[q][1] if q in ov else (Lq[0]['qid'] if Lq else None)
        edges.append(dict(t=q, p=p, expert_tier=e, auto_tier=auto(q), labeled=True))
    else:
        edges.append(dict(t=q, p=Lq[0]['qid'] if Lq else None, expert_tier=None, auto_tier=auto(q), labeled=False))
json.dump(edges, open('/tmp/p2/kg_edges.json','w'))
nn = sum(1 for e in edges if e['p'])
print(f"KG edges: {len(edges)} targets, {nn} with best-link")
