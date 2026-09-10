#!/usr/bin/env python3
"""Part 3: advantages, transformation taxonomy, Top-100, concept map, appendices."""
import json, csv
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
inlab = set(q for q in targets if auto(q) in (5,4,2) or any(q in samp[s] for s in samp))
pop = Counter(auto(q) for q in targets)
WT = {5:1.0, 4:1.0, 2:1.0, 3:pop[3]/len(samp['L3']), 1:pop[1]/len(samp['L1']), 0:pop[0]/len(samp['L0'])}

def linkobj(qid, pqid):
    for l in recs[qid]['links']:
        if l['qid']==pqid: return l
    return None

def best_link(qid):
    e = expert(qid)
    if qid in ov: return (ov[qid][1], e, 'expert')
    L = recs[qid]['links']
    if not L or e==0: return (None, e, 'auto')
    return (L[0]['qid'], e, 'auto')

def advantage(e, feat):
    """primary advantage (constructed)."""
    if e >= 4: return 'answerability'
    if e == 3: return 'elimination' if feat and len(feat.get('opt_overlap',[]))>=2 else 'conceptual'
    if e == 2: return 'elimination' if feat and len(feat.get('opt_overlap',[]))>=1 else 'conceptual'
    if e == 1: return 'pattern'
    return 'none'

def transform(e, feat, tsubj, psubj):
    if e == 0: return 'spurious'
    if feat is None:
        return 'expert-verified-strong' if e>=3 else 'expert-verified-weak'
    d = feat['detail']
    f = d.get('focus',0) or 0
    ent = d.get('shared_entities',[]) or []
    rare = d.get('shared_rare',[]) or []
    clu = d.get('shared_clusters',[]) or []
    optn = len(d.get('opt_overlap',[]) or [])
    if e == 1: return 'weak-association'
    if f >= 0.7: return 'verbatim-repeat'
    if f >= 0.35: return 'paraphrase-repeat'
    if ent and optn >= 2: return 'same-fact-new-frame'
    if ent or rare: return 'entity-bridge'
    if clu and tsubj != psubj: return 'mechanism-transfer'
    if clu: return 'angle-shift'
    if optn >= 2: return 'option-echo'
    if optn >= 1 or f >= 0.1: return 'surface-echo'
    return 'unclassified-weak'

rows = []
for q in targets:
    p, e, src = best_link(q)
    feat = linkobj(q, p) if p else None
    tsubj = recs[q].get('subject','?')
    prow = {}
    if p:
        py = int(p[:4])
        psubj = recs[p].get('subject','?') if p in recs else '?'
        adv = advantage(e, feat['detail'] if feat else None)
        tr = transform(e, feat, tsubj, psubj)
    else:
        py, psubj, adv, tr = None, None, 'none', 'spurious'
    rows.append(dict(q=q, ty=int(q[:4]), s=tsubj, a=auto(q), e=e if q in inlab else None,
                     p=p, py=py, lag=(int(q[:4])-py) if py else None,
                     adv=adv if q in inlab else None, tr=tr if q in inlab else None,
                     w=WT[auto(q)] if q in inlab else 0, src=src))

lab = [r for r in rows if r['e'] is not None]
print(f"labeled={len(lab)}")

print("\n== ADVANTAGE (primary, weighted over all targets) ==")
for k in ['answerability','conceptual','elimination','pattern','none']:
    w = sum(r['w'] for r in lab if r['adv']==k)
    print(f"  {k:14s}: {w:6.0f} ({w/12:.1f}%)")
print("  -- among linked L2+ only --")
l2 = [r for r in lab if r['e']>=2]
for k in ['answerability','conceptual','elimination','pattern']:
    w = sum(r['w'] for r in l2 if r['adv']==k)
    print(f"  {k:14s}: {w:6.0f} ({w/sum(x['w'] for x in l2)*100:.1f}%)")

print("\n== TRANSFORMATION TAXONOMY (weighted) ==")
for k, v in Counter({k: sum(r['w'] for r in lab if r['tr']==k) for k in set(r['tr'] for r in lab)}).most_common():
    print(f"  {k:24s}: {v:6.0f}")

# Top-100 priors
PTS = {5:5, 4:4, 3:3, 2:2, 1:1, 0:0}
agg = defaultdict(lambda: dict(score=0, w=0, n=0, best=0, tys=[], tes=[]))
for r in lab:
    if not r['p']: continue
    d = agg[r['p']]
    d['score'] += PTS[r['e']]*r['w']; d['w'] += r['w']; d['n'] += 1
    d['best'] = max(d['best'], r['e']); d['tys'].append(r['ty']); d['tes'].append(r['e'])
top = sorted(agg.items(), key=lambda kv: -kv[1]['score'])[:100]
print("\n== TOP-20 priors ==")
for p, d in top[:20]:
    print(f"  {p} score={d['score']:.0f} n={d['n']} best=L{d['best']} tyears={sorted(set(d['tys']))}")
json.dump([{**dict(p=p), **{k:(sorted(set(v)) if k=='tys' else v) for k,v in d.items() if k!='tes'}} for p,d in top],
          open('/tmp/p2/top100.json','w'), indent=1)

# Concept map from shared_clusters
cmap = defaultdict(lambda: dict(w=0, n=0, tiers=Counter(), tyears=set(), priors=set(), ex=[]))
featless = 0
for r in lab:
    if not r['p'] or r['e'] < 1: continue
    f = linkobj(r['q'], r['p'])
    if not f: featless += 1; continue
    for c in f['detail'].get('shared_clusters', []) or []:
        d = cmap[c]
        d['w'] += r['w']; d['n'] += 1; d['tiers'][r['e']] += 1
        d['tyears'].add(r['ty']); d['priors'].add(r['p'])
        if len(d['ex']) < 3: d['ex'].append(f"{r['q']}(L{r['e']})x{r['p']}")
print(f"\nclusters={len(cmap)} featless-links={featless}")
ranked = sorted(cmap.items(), key=lambda kv: -kv[1]['w'])
print("\n== TOP-15 concepts ==")
for c, d in ranked[:15]:
    span = f"{min(d['tyears'])}-{max(d['tyears'])}"
    print(f"  {c:28s} w={d['w']:6.0f} n={d['n']:3d} tiers={dict(sorted(d['tiers'].items()))} span={span} priors={len(d['priors'])}")
json.dump({c: dict(w=d['w'], n=d['n'], tiers=dict(d['tiers']), tyears=sorted(d['tyears']),
                     npriors=len(d['priors']), ex=d['ex']) for c, d in ranked},
          open('/tmp/p2/concepts.json','w'), indent=1)

# Appendix A: all 1200
with open('/tmp/p2/appendixA.csv','w',newline='') as f:
    wr = csv.writer(f)
    wr.writerow(['qid','year','subject','auto_tier','auto_best','expert_tier','expert_link','link_src','advantage','transform','weight','text_snippet'])
    for r in sorted(rows, key=lambda r: r['q']):
        wr.writerow([r['q'], r['ty'], r['s'], r['a'], recs[r['q']]['links'][0]['qid'] if recs[r['q']]['links'] else '',
                     '' if r['e'] is None else r['e'], r['p'] or '', r['src'], r['adv'] or '', r['tr'] or '',
                     f"{r['w']:.2f}", recs[r['q']]['text'][:150].replace('\n',' ')])
print("\nwrote /tmp/p2/appendixA.csv /tmp/p2/top100.json /tmp/p2/concepts.json")
