#!/usr/bin/env python3
"""UPSC Prelims PYQ Intelligence — Phase 2 engine.

Expert-conceptual annotation SUPPORT engine. It does NOT replace expert
judgement: it tags every question with taxonomy concepts, proposes the best
prior-PYQ link(s) inside a strict 20-year backward window, and scores each
pair on the L0-L5 relationship scale. A human then calibrates a stratified
sample (see --calibrate) and records overrides; the final report numbers are
the calibrated, hand-verified ones.

Stdlib only. Outputs under data/pyq_phase2/.

Usage:
  python scripts/pyq_phase2.py                 # full run
  python scripts/pyq_phase2.py --calibrate     # print fresh labelling sample
  python scripts/pyq_phase2.py --check         # 2-year smoke test
"""
import json, os, re, sys, math, argparse
from collections import defaultdict, Counter
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from phase2_taxonomy1 import CLUSTERS_1
from phase2_taxonomy2 import CLUSTERS_2
from phase2_taxonomy_patch import NEW_CLUSTERS, TERM_ADDITIONS
CLUSTERS = CLUSTERS_1 + CLUSTERS_2 + NEW_CLUSTERS
_BYID = {c["id"]: c for c in CLUSTERS}
for _cid, _field, _terms in TERM_ADDITIONS:
    if _cid in _BYID:
        _BYID[_cid][_field] = list(_BYID[_cid][_field]) + [t for t in _terms if t not in _BYID[_cid][_field]]
CLU = {c["id"]: c for c in CLUSTERS}
# Entity-dependent clusters: different-entity co-membership means nothing -> cap at L2
NEEDS_ENTITY = {c["id"] for c in CLUSTERS if c.get("needs_entity")} | {
    "awards-sports-gk", "personalities-books", "reports-indices", "govt-programmes-misc",
    "sci-institutions", "festivals-fairs", "international-orgs"}

CANON_SUBJECTS = ["Polity", "Economy", "Geography", "History",
                  "Art & Culture", "Environment", "Science & Technology"]
SUBJECT_NORM = {
    "polity-and-governance": "Polity", "polity": "Polity",
    "economy": "Economy",
    "geography": "Geography",
    "history": "History",
    "art-and-culture": "Art & Culture", "art-culture": "Art & Culture",
    "science-and-technology": "Science & Technology",
    "science-technology": "Science & Technology",
    "environment": "Environment",
}
GK_CLUSTERS = {"awards-sports-gk", "personalities-books"}

STOP = set("""a an the of and or to in on for with by from as at is are was were be been being
it its this that these those which who whom whose what when where why how while during
following follow given below above using code codes select correct answer answers option
options statement statements consider respect reference regard india indian among between
one two three four five six seven eight nine ten first second third fourth fifth
i ii iii iv v vi vii viii ix x list match matched list-i list-ii
not only all both each every any some such than then there their they them he she we you
your our his her him has have had having do does did done can could shall should will would may might must
into over under out up down off through per cent percent year years old new archaeological
assertion reason because since although though however therefore thus hence despite
assertiona reasonr individual true false explanation codegivenbelow selectthecorrect
organization organisations organization programme programmes program programs scheme schemes mission missions
initiative initiatives project projects report reports index indices committee committees commission ministry
ministries department departments government governments national agency agencies authority authorities council
councils neither nor none either body bodies board boards panel panels world worlds news affair affairs explain explains explanation
""".replace("-", " ").split())

APT_PATTERNS = [
    r"read the following passage", r"read each of the following",
    r"train of length", r"circular field", r"railway route between",
    r"in a tournament", r"hour hand and a minute hand",
    r"march 1, 2008 was saturday", r"identical items such that product",
    r"league matches", r"stations on the way",
    r"answered as true", r"true \(t\) or false", r"chairs will be made",
    r"can make a chair in", r"no two candidates wrote",
]
APT_RE = re.compile("|".join(APT_PATTERNS), re.I)

CURR_PATTERNS = [
    r"\b(20[01]\d|202[0-6])\b", r"\brecently\b", r"\blast year\b",
    r"\bhas been launched\b", r"\bwas launched in\b", r"\bnewly\b",
    r"\bmission\b.*\b20[01]\d\b",
]

# ---------------- text utils ----------------
def norm_text(s):
    s = (s or "").lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def stem_tok(t):
    if len(t) > 5 and t.endswith("ies"): return t[:-3] + "y"
    if len(t) > 4 and t.endswith("es") and not t.endswith(("ses", "ches", "shes", "xes", "zes")):
        return t[:-1]
    if len(t) > 4 and t.endswith("s") and not t.endswith("ss"): return t[:-1]
    return t

def toks(s, stem=True):
    ts = norm_text(s).split()
    return [stem_tok(t) if stem else t for t in ts]

def content_toks(s):
    return [t for t in toks(s) if t not in STOP and len(t) >= 3 and not t.isdigit()]

# Precompile cluster patterns: (raw, joined_stemmed, is_single, single_tok)
def _compile(pats):
    out = []
    for p in pats:
        t = toks(p)
        if not t:
            continue
        out.append((p, " ".join(t), len(t) == 1, t[0] if len(t) == 1 else None))
    return out
for c in CLUSTERS:
    c["_core"] = _compile(c["core"])
    c["_sup"] = _compile(c["support"])
    c["_veto"] = _compile(c["veto"])

# Rare-entity document frequencies (computed on first load)
DF = Counter()
ENT_DF = Counter()
TAXO_TOKENS = set()
for _c in CLUSTERS:
    for _p in _c["core"]:
        TAXO_TOKENS.update(toks(_p))
RARE_SINGLETON_DF = 25
TAG_SINGLETON_RARE_DF = 40
GENERIC_ENT_DF = 20

def _hit(pat, stem_s, opt_s, stem_set, opt_set):
    raw, joined, single, tok = pat
    if single:
        return (tok in stem_set), (tok in opt_set)
    needle = " " + joined + " "
    return (needle in stem_s), (needle in opt_s)

def tag_question(stem, options_text):
    """Return (clusters dict id->strength, matched_core dict id->set(phrases))."""
    st = toks(stem)
    ot = toks(options_text)
    stem_s, opt_s = " " + " ".join(st) + " ", " " + " ".join(ot) + " " 
    stem_set, opt_set = set(st), set(ot)
    # short-stem questions carry their content in the options: weight options fully
    stem_content_n = sum(1 for t in st if t not in STOP and len(t) >= 3)
    opt_full = stem_content_n < 8
    out, matched, stem_sc = {}, {}, {}
    for c in CLUSTERS:
        if any(_hit(v, stem_s, opt_s, stem_set, opt_set)[0] or _hit(v, stem_s, opt_s, stem_set, opt_set)[1]
               for v in c["_veto"]):
            continue
        score = 0.0
        s_sc = 0.0
        hits = set()
        for pat in c["_core"]:
            hs, ho = _hit(pat, stem_s, opt_s, stem_set, opt_set)
            if hs or ho:
                hits.add(pat[0])
                if not pat[2]:
                    w = 2.0 if (hs or (ho and opt_full)) else 1.0
                    score += w
                    if hs: s_sc += 2.0
                else:
                    rare = DF.get(pat[3], 999) <= TAG_SINGLETON_RARE_DF
                    if hs or (ho and opt_full):
                        w = 2.0 if rare else 1.0
                        score += w
                        if hs: s_sc += w
                    else:
                        score += 1.0 if rare else 0.5
        sup = 0.0
        for pat in c["_sup"]:
            hs, ho = _hit(pat, stem_s, opt_s, stem_set, opt_set)
            if hs or (ho and opt_full):
                sup += 1.0
                if hs: s_sc += 0.5
            elif ho:
                sup += 0.5
        score += 0.5 * sup
        if score >= 2.0:
            out[c["id"]] = round(score, 2)
            matched[c["id"]] = hits
            stem_sc[c["id"]] = round(s_sc, 2)
    return out, matched, stem_sc

def is_aptitude(rec):
    if (rec.get("subject") or "") in ("Reading Comprehension", "Quantitative Aptitude"):
        return True
    return bool(APT_RE.search(rec.get("question", "")))

# ---------------- load ----------------
def load_corpus():
    d = json.load(open(os.path.join(ROOT, "data", "prelims.json")))
    rby = d["records_by_year"]
    recs = []
    for y in sorted(rby.keys(), key=int):
        for r in rby[y]:
            q = r["question"] or ""
            opts = r.get("options") or []
            opt_text = " \n ".join(opts)
            ans = r.get("answer")
            ans_text = ""
            if isinstance(ans, int) and 0 <= ans < len(opts):
                ans_text = opts[ans]
            elif isinstance(ans, str):
                ans_text = ans
            recs.append({
                "id": r["id"], "year": int(r["year"]),
                "subject_raw": r.get("subject", ""),
                "question": q, "options": opts,
                "answer_idx": ans if isinstance(ans, int) else None,
                "answer_text": ans_text,
                "url": r.get("reference_url", ""),
                "stem_toks": toks(q), "opt_toks": toks(opt_text),
                "stem_content": set(content_toks(q)),
                "opt_content": set(content_toks(opt_text)),
                "ans_content": set(content_toks(ans_text)),
            })
    # df for singleton rarity (BEFORE tagging: rarity-aware singleton weights)
    for r in recs:
        for t in set(r["stem_toks"]):
            DF[t] += 1
    # subject pass 1: tag + entities
    for r in recs:
        r["aptitude"] = is_aptitude({"subject": r["subject_raw"], "question": r["question"]})
        stem_s = " ".join(r["stem_toks"])
        stem_set = set(r["stem_toks"])
        clusters, matched, stem_sc = tag_question(r["question"], " ".join(r["options"]))
        r["clusters"] = clusters
        r["cl_stem"] = stem_sc
        r["short_stem"] = sum(1 for t in r["stem_toks"] if t not in STOP and len(t) >= 3) < 8
        r["matched_core"] = {k: sorted(v) for k, v in matched.items()}
        ents, singles = set(), set()
        for cid, phrases in matched.items():
            for p in phrases:
                pt = toks(p)
                if len(pt) >= 2:
                    if (" " + " ".join(pt) + " ") in (" " + stem_s + " "):
                        ents.add(p)
                else:
                    if pt[0] in stem_set and DF.get(pt[0], 999) <= RARE_SINGLETON_DF:
                        singles.add(p)
        r["entities"] = ents
        r["rare_singles"] = singles
    for r in recs:
        for e in r["entities"] | r["rare_singles"]:
            ENT_DF[e] += 1
    # subject pass 2: canonical + environment derivation
    for r in recs:
        base = SUBJECT_NORM.get(r["subject_raw"], "")
        env_strength = sum(s for cid, s in r["clusters"].items() if CLU[cid]["subject"] == "Environment")
        geo_strength = sum(s for cid, s in r["clusters"].items() if CLU[cid]["subject"] == "Geography")
        sci_strength = sum(s for cid, s in r["clusters"].items() if CLU[cid]["subject"] == "Science & Technology")
        if base in ("", ) or r["subject_raw"] in ("current-affairs", "other"):
            # keyword fallback: strongest cluster subject
            by_sub = Counter()
            for cid, s in r["clusters"].items():
                by_sub[CLU[cid]["subject"]] += s
            base = by_sub.most_common(1)[0][0] if by_sub else "Other"
        if base in ("Geography", "Science & Technology") and env_strength >= 2.0 and env_strength >= max(geo_strength, sci_strength):
            base = "Environment"
        if base == "Environment" and env_strength < 2.0:
            pass  # keep labelled environment
        r["subject"] = base
    return recs

# ---------------- pair scoring ----------------
def jaccard(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

QFORMAT_RES = {
    "statement": re.compile(r"consider the following|statements? (given )?(above|below)|statement-i|statement-1", re.I),
    "match": re.compile(r"match list|correctly matched|pairs? .* matched", re.I),
    "assertion": re.compile(r"assertion\s*\(?a", re.I),
    "chrono": re.compile(r"chronolog|correct sequence|arrange .* order", re.I),
    "map": re.compile(r"\bmap\b|mark.*places|locate", re.I),
    "which_of": re.compile(r"which of the following|which one of the following", re.I),
}
def qformat(q):
    return {k: bool(rx.search(q)) for k, rx in QFORMAT_RES.items()}

def is_explanation(q):
    t = q.lower()
    return bool(re.search(r"assertion\s*\(?a", t)) or \
        (("statement-i" in t or "statement-1" in t or "statement i" in t) and
         ("statement-ii" in t or "statement-2" in t or "statement ii" in t))

def current_markers(q):
    return bool(re.search("|".join(CURR_PATTERNS), q, re.I))

TRANS_LABELS = {
    "verbatim-repeat": "Same fact, near-verbatim repeat",
    "same-fact-reworded": "Same fact, different wording",
    "fact-to-statement": "Fact recast as statement-based question",
    "statement-to-fact": "Statement-based recast as direct question",
    "same-concept-new-example": "Same concept, different example/application",
    "same-concept-new-angle": "Same entity/concept, transformed question angle",
    "institution-to-function": "Institution/location to function/membership",
    "static-to-current": "Static knowledge applied to current-affairs context",
    "event-to-chronology": "Event/personality to chronology or association",
    "definition-to-application": "Definition to application",
    "cause-to-consequence": "Cause to consequence (or reverse)",
    "location-to-map": "Location knowledge to map/places question",
    "comparison": "Single fact to comparison/distinction",
    "same-cluster": "Same knowledge cluster, new question",
    "elimination-only": "Elimination advantage only",
}

def classify_transformation(T, P, shared_ents, shared_clusters, focus):
    tf, pf = qformat(T["question"]), qformat(P["question"])
    if focus >= 0.55 and len(T["stem_content"] & P["stem_content"]) >= 5:
        return "verbatim-repeat"
    if shared_ents and tf["statement"] and not pf["statement"]:
        return "fact-to-statement"
    if shared_ents and pf["statement"] and not tf["statement"]:
        return "statement-to-fact"
    if tf["map"] or "places in news" in T["question"].lower()[:80]:
        return "location-to-map"
    if tf["chrono"] or pf["chrono"]:
        return "event-to-chronology"
    if shared_ents and (tf["match"] or pf["match"]) and focus >= 0.25:
        return "comparison" if focus < 0.45 else "same-fact-reworded"
    if shared_ents and focus >= 0.35:
        return "same-fact-reworded"
    if shared_ents and T["year"] - P["year"] >= 8 and current_markers(T["question"]):
        return "static-to-current"
    if shared_ents:
        # institution -> function heuristic
        if re.search(r"function|objective|purpose|mandate|responsible for", T["question"], re.I) and \
           re.search(r"which (one|of)|headquarter|located|established|set up", P["question"], re.I):
            return "institution-to-function"
        if re.match(r"\s*(what is|a |an )", P["question"], re.I) and len(P["question"]) < 120:
            return "definition-to-application"
        return "same-concept-new-angle"
    if shared_clusters and T["year"] - P["year"] >= 8 and current_markers(T["question"]):
        return "static-to-current"
    if shared_clusters:
        return "same-concept-new-example"
    return "elimination-only"

def score_pair(T, P, cluster_prior_counts):
    """Return (level, score, detail) for target T vs prior P."""
    shared_clusters = [c for c in T["clusters"] if c in P["clusters"]]
    shared_clusters_nongk = [c for c in shared_clusters if c not in GK_CLUSTERS]
    shared_ents = set(T["entities"]) & set(P["entities"])
    shared_rare = set(T["rare_singles"]) & set(P["rare_singles"])
    focus = jaccard(T["stem_content"], P["stem_content"])
    shared_content = T["stem_content"] & P["stem_content"]
    opt_overlap = (T["opt_content"] & (P["stem_content"] | P["opt_content"])) | \
                  (P["opt_content"] & (T["stem_content"] | T["opt_content"]))
    opt_overlap = {t for t in opt_overlap if DF.get(t, 999) <= 25 and len(t) >= 4}
    rare_opt = {t for t in opt_overlap if DF.get(t, 999) <= 12}
    ans_in_target_opts = bool(P["ans_content"] & T["opt_content"]) and len(P["ans_content"]) >= 1
    base_score = (
        3.0 * len(shared_ents) + 2.0 * len(shared_rare) +
        1.5 * len(shared_clusters_nongk) + 0.5 * len(shared_clusters) +
        4.0 * focus + 1.0 * min(len(opt_overlap), 3)
    )
    level = 0
    why = []
    def _qual(side, c):
        return side["cl_stem"].get(c, 0) >= 1.0 or side["clusters"].get(c, 0) >= 3.0
    qual_clusters = [c for c in shared_clusters if _qual(T, c) and _qual(P, c)]
    concept_clusters = [c for c in qual_clusters if c not in GK_CLUSTERS and c not in NEEDS_ENTITY]
    id_clusters = [c for c in qual_clusters if c in NEEDS_ENTITY or c in GK_CLUSTERS]
    has_ent = bool(shared_ents or shared_rare)
    strong_ent = bool(shared_ents) or len(shared_rare) >= 2 or (len(shared_rare) == 1 and focus >= 0.25)
    nonspecific_only = has_ent and all(ENT_DF.get(e, 999) > GENERIC_ENT_DF for e in (shared_ents | shared_rare))
    _tf, _pf = qformat(T["question"]), qformat(P["question"])
    same_format = (_tf["statement"] and _pf["statement"]) or (_tf["match"] and _pf["match"]) or \
                  (_tf["chrono"] and _pf["chrono"]) or (_tf["assertion"] and _pf["assertion"])
    min_stem = min(len(T["stem_content"]), len(P["stem_content"]))
    ans_match = T["ans_content"] & P["ans_content"]
    # L5: near-direct repeat (tight: verbatim needs token mass; entity paths need focus+support)
    if ((focus >= 0.55 and len(shared_content) >= 5) or (focus >= 0.9 and len(shared_content) >= 3)) or \
       (len(shared_ents) >= 2 and focus >= 0.30 and shared_clusters) or \
       (len(shared_ents) == 1 and focus >= 0.45 and shared_clusters and
            (len(rare_opt) >= 1 or len(shared_content) >= 5)) or \
       (len(ans_match) >= 3 and concept_clusters and focus >= 0.20) or \
       (len(ans_match) >= 3 and focus >= 0.40):
        level = 5; why.append("shared decisive entity + high focus overlap")
    elif (concept_clusters or id_clusters) and (
            (bool(shared_ents) and focus >= 0.20) or
            (len(shared_rare) >= 2 and focus >= 0.20) or
            (len(shared_rare) == 1 and not shared_ents and focus >= 0.25 and len(shared_content) >= 3) or
            (len(shared_ents) >= 2 and focus >= 0.18) or
            (concept_clusters and focus >= 0.30) or
            (same_format and strong_ent and focus >= 0.16) or
            (is_explanation(T["question"]) and is_explanation(P["question"]) and
             concept_clusters and shared_rare and focus >= 0.15) or
            (concept_clusters and focus >= 0.03 and
             bool(rare_opt & TAXO_TOKENS & T["ans_content"] & P["stem_content"])) or
            (len(ans_match) >= 2 and concept_clusters and
             (focus >= 0.05 or shared_ents or shared_rare))):
        level = 4; why.append("same concept/entity, transformed angle")
    elif concept_clusters and ((shared_ents and focus >= 0.04) or rare_opt or focus >= 0.05):
        level = 3; why.append("same knowledge cluster")
    elif id_clusters:
        level = 1; why.append("same identifier family only (GK/acts/committees/orgs)")
    if level >= 3 and nonspecific_only and focus < 0.35:
        level = min(level, 3 if concept_clusters else 2)
        why.append("capped: only generic shared entities")
        if len(shared_content) < 4 and not rare_opt:
            level = min(level, 1)
            why.append("capped: generic entity, negligible overlap")
    if level == 3 and min_stem <= 5 and len(shared_ents) <= 1 and not shared_rare \
            and len(shared_content) < 3 and not rare_opt:
        level = 2
        why.append("capped: short stems, thin evidence")
    if level == 0:
        # L2 via option-level distinctive entity or lone rare singleton
        opt_ent = (T["entities"] | T["rare_singles"]) & (P["stem_content"] | P["opt_content"])
        opt_ent = {e for e in opt_ent if (len(e.split()) >= 2 or DF.get(toks(e)[0], 999) <= RARE_SINGLETON_DF)}
        lone_rare = (T["rare_singles"] & P["rare_singles"]) | (T["entities"] & P["entities"])
        if (opt_ent and len(opt_overlap) >= 1) or len(opt_overlap) >= 3:
            level = 2; why.append(f"option entity {sorted(opt_ent)[:2]} seen before")
            base_score += 1.5
        elif lone_rare and focus >= 0.05:
            level = 2; why.append(f"lone shared entity {sorted(lone_rare)[:2]}")
            base_score += 1.0
        elif T["subject"] == P["subject"] and T["subject"] in CANON_SUBJECTS and \
                len(T["stem_content"] & P["stem_content"]) >= 2:
            level = 1; why.append("same subject + shared vocabulary")
    # advantages
    adv = {"A": False, "B": False, "C": False, "D": False}
    if level >= 3:
        adv["B"] = True
    if level == 5:
        adv["A"] = True
        adv["C"] = True
    elif level == 4:
        if ans_in_target_opts or focus >= 0.35 or len(shared_ents) >= 2:
            adv["A"] = True
        if opt_overlap:
            adv["C"] = True
    elif level == 3:
        if opt_overlap and len(opt_overlap) >= 2:
            adv["C"] = True
    elif level == 2:
        adv["C"] = True
    if level >= 3 and concept_clusters:
        # pattern advantage: established recurrence (>=3 prior Qs in window on that cluster)
        for c in concept_clusters:
            if cluster_prior_counts.get(c, 0) >= 3:
                adv["D"] = True
                break
    trans = classify_transformation(T, P, shared_ents, shared_clusters_nongk, focus) if level >= 2 else "—"
    detail = {
        "level": level, "score": round(base_score, 3), "focus": round(focus, 3),
        "shared_clusters": shared_clusters,
        "qual_clusters": qual_clusters,
        "shared_entities": sorted(shared_ents)[:6],
        "shared_rare": sorted(shared_rare)[:6],
        "opt_overlap": sorted(opt_overlap)[:8],
        "ans_in_target_opts": ans_in_target_opts,
        "advantages": "".join(k for k in "ABCD" if adv[k]) or "—",
        "transformation": trans,
        "why": "; ".join(why),
    }
    return level, base_score, detail

# ---------------- main analysis ----------------
def build_index(recs):
    by_cluster = defaultdict(list)
    by_ent = defaultdict(list)
    by_tok = defaultdict(list)
    for r in recs:
        for c in r["clusters"]:
            by_cluster[c].append(r)
        for e in r["entities"] | r["rare_singles"]:
            by_ent[e].append(r)
        for t in r["stem_content"]:
            by_tok[t].append(r["id"])
    return by_cluster, by_ent, by_tok

def analyse_targets(recs, target_years, window=20, topn=3, verbose=False):
    by_year = defaultdict(list)
    for r in recs:
        by_year[r["year"]].append(r)
    by_cluster, by_ent, by_tok = build_index(recs)
    by_id = {r["id"]: r for r in recs}
    results = {}
    for ty in target_years:
        yres = []
        priors = [r for r in recs if ty - window <= r["year"] < ty and not r["aptitude"]]
        # cluster prior counts for pattern advantage
        cpc = Counter()
        for p in priors:
            for c in p["clusters"]:
                cpc[c] += 1
        for T in sorted(by_year[ty], key=lambda r: r["id"]):
            if T["aptitude"]:
                yres.append({"qid": T["id"], "tier": "aptitude"})
                continue
            cands = {}
            for c in T["clusters"]:
                for p in by_cluster[c]:
                    if ty - window <= p["year"] < ty and not p["aptitude"]:
                        cands[p["id"]] = p
            for e in T["entities"] | T["rare_singles"]:
                for p in by_ent[e]:
                    if ty - window <= p["year"] < ty and not p["aptitude"]:
                        cands[p["id"]] = p
            # token-recall: priors sharing >=4 stem content tokens (catches untagged verbatims)
            tok_hits = Counter()
            for t in T["stem_content"]:
                for pid in by_tok.get(t, ()):
                    tok_hits[pid] += 1
            for pid, n in tok_hits.items():
                if n >= 4 and pid not in cands:
                    p = by_id[pid]
                    if ty - window <= p["year"] < ty and not p["aptitude"]:
                        cands[pid] = p
            scored = []
            for p in cands.values():
                lvl, sc, det = score_pair(T, p, cpc)
                if lvl >= 1:
                    scored.append((lvl, sc, p, det))
            scored.sort(key=lambda x: (x[0], x[1], x[2]["year"]), reverse=True)
            best_lvl = scored[0][0] if scored else 0
            if best_lvl < 2 and topn:
                # L1 fallback: same-subject prior with shared vocabulary (theme signal)
                l1cands = []
                for p in priors:
                    if p["subject"] == T["subject"] and p["subject"] in CANON_SUBJECTS:
                        sh = T["stem_content"] & p["stem_content"]
                        if len(sh) >= 3:
                            l1cands.append((len(sh), p["year"], p))
                if l1cands:
                    l1cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
                    _, _, p = l1cands[0]
                    _, _, det = score_pair(T, p, cpc)
                    det = dict(det); det["level"] = 1
                    det["advantages"] = "D" if det["advantages"] == "\u2014" else det["advantages"]
                    det["transformation"] = "\u2014"; det["why"] = "same-subject theme signal"
                    scored.append((1, 0.0, p, det))
                    scored.sort(key=lambda x: (x[0], x[1], x[2]["year"]), reverse=True)
            links = []
            for (lvl, sc, p, det) in scored[:topn]:
                links.append({
                    "qid": p["id"], "year": p["year"], "subject": p["subject"],
                    "level": lvl, "score": det["score"],
                    "text": p["question"][:360], "answer_text": p["answer_text"][:160],
                    "url": p["url"], "detail": det,
                })
            # best L1 fallback note (subject-only): most recent same-subject prior
            best = links[0]["level"] if links else 0
            if best == 0:
                links = []
            yres.append({
                "qid": T["id"], "year": ty, "subject": T["subject"],
                "text": T["question"][:600], "options": T["options"],
                "answer_text": T["answer_text"][:200], "url": T["url"],
                "clusters": sorted(T["clusters"].keys()),
                "tier": best, "links": links,
            })
        results[ty] = yres
        if verbose:
            c = Counter(q["tier"] for q in yres)
            print(ty, dict(sorted(c.items(), key=str)))
    return results

def depth_analysis(recs, target_years, depths=(7, 10, 15, 20)):
    """Best level per target restricted to priors within k years."""
    by_year = defaultdict(list)
    for r in recs:
        by_year[r["year"]].append(r)
    by_cluster, by_ent, by_tok = build_index(recs)
    by_id = {r["id"]: r for r in recs}
    out = {}
    for ty in target_years:
        per_depth = {k: [] for k in depths}
        cpc_full = Counter()
        for p in recs:
            if ty - 20 <= p["year"] < ty and not p["aptitude"]:
                for c in p["clusters"]:
                    cpc_full[c] += 1
        for T in sorted(by_year[ty], key=lambda r: r["id"]):
            if T["aptitude"]:
                for k in depths:
                    per_depth[k].append("apt")
                continue
            cands = {}
            for c in T["clusters"]:
                for p in by_cluster[c]:
                    if ty - 20 <= p["year"] < ty and not p["aptitude"]:
                        cands[p["id"]] = p
            for e in T["entities"] | T["rare_singles"]:
                for p in by_ent[e]:
                    if ty - 20 <= p["year"] < ty and not p["aptitude"]:
                        cands[p["id"]] = p
            tok_hits = Counter()
            for t in T["stem_content"]:
                for pid in by_tok.get(t, ()):
                    tok_hits[pid] += 1
            for pid, n in tok_hits.items():
                if n >= 4 and pid not in cands:
                    p = by_id[pid]
                    if ty - 20 <= p["year"] < ty and not p["aptitude"]:
                        cands[pid] = p
            scored = []
            for p in cands.values():
                lvl, sc, _ = score_pair(T, p, cpc_full)
                scored.append((p["year"], lvl, sc))
            for k in depths:
                elig = [(l, s) for (y, l, s) in scored if ty - k <= y < ty and l >= 1]
                per_depth[k].append(max([l for l, s in elig]) if elig else 0)
        out[ty] = per_depth
    return out

# ---------------- outputs ----------------
def summarise(results, target_years):
    tiers = Counter()
    by_year, by_sub = {}, defaultdict(Counter)
    for ty in target_years:
        c = Counter(q["tier"] for q in results[ty])
        by_year[ty] = {str(k): v for k, v in sorted(c.items(), key=str)}
        tiers.update(c)
        for q in results[ty]:
            by_sub[q.get("subject", "?")][q["tier"]] += 1
    return tiers, by_year, {k: {str(kk): vv for kk, vv in sorted(v.items(), key=str)} for k, v in by_sub.items()}

def concept_map(recs, results, target_years):
    cmap = {}
    for c in CLUSTERS:
        qs = [r for r in recs if c["id"] in r["clusters"] and not r["aptitude"]]
        years = sorted(set(r["year"] for r in qs))
        subs = Counter(r["subject"] for r in qs)
        cmap[c["id"]] = {
            "name": c["name"], "subject": c["subject"],
            "n": len(qs), "years": years,
            "earliest": min(years) if years else None,
            "latest": max(years) if years else None,
            "distinct_years": len(years),
            "subjects": dict(subs),
            "recent_n": sum(1 for r in qs if 2015 <= r["year"] <= 2026),
            "old_n": sum(1 for r in qs if 1995 <= r["year"] <= 2004),
            "sample": [r["id"] for r in sorted(qs, key=lambda r: r["id"])[:6]],
        }
    # link roles: how often cluster is the shared cluster of L3+ best links
    role = Counter()
    trans_by_cluster = defaultdict(Counter)
    for ty in target_years:
        for q in results[ty]:
            if q.get("links"):
                L = q["links"][0]
                if L["level"] >= 3:
                    for sc in L["detail"]["shared_clusters"]:
                        role[sc] += 1
                        trans_by_cluster[sc][L["detail"]["transformation"]] += 1
    for cid in cmap:
        cmap[cid]["downstream_links"] = role[cid]
        cmap[cid]["transformations"] = dict(trans_by_cluster[cid])
    return cmap

LVL_W = {5: 3.0, 4: 4.0, 3: 2.0, 2: 1.0}
def leverage_ranking(recs, results_all, target_years):
    """Score every prior PYQ by downstream best-link value."""
    agg = defaultdict(lambda: {"links": [], "years": set()})
    for ty in target_years:
        for q in results_all[ty]:
            if not q.get("links"):
                continue
            L = q["links"][0]
            if L["level"] >= 2:
                agg[L["qid"]]["links"].append((q["year"], q["qid"], L["level"], L["detail"]["transformation"],
                                               ",".join(L["detail"]["shared_clusters"][:2])))
                agg[L["qid"]]["years"].add(q["year"])
    by_id = {r["id"]: r for r in recs}
    rows = []
    for qid, v in agg.items():
        r = by_id.get(qid)
        if r is None: continue
        n5 = sum(1 for l in v["links"] if l[2] == 5)
        n4 = sum(1 for l in v["links"] if l[2] == 4)
        n3 = sum(1 for l in v["links"] if l[2] == 3)
        n2 = sum(1 for l in v["links"] if l[2] == 2)
        base = n5*LVL_W[5] + n4*LVL_W[4] + n3*LVL_W[3] + n2*LVL_W[2]
        div = 1 + 0.25 * (len(v["years"]) - 1)
        score = round(base * div, 2)
        rows.append({
            "qid": qid, "year": r["year"], "subject": r["subject"],
            "text": r["question"][:400], "answer_text": r["answer_text"][:160],
            "url": r["url"], "clusters": sorted(r["clusters"].keys()),
            "n_links": len(v["links"]), "n_years": len(v["years"]),
            "n5": n5, "n4": n4, "n3": n3, "n2": n2,
            "score": score,
            "downstream": sorted(v["links"])[:25],
        })
    rows.sort(key=lambda r: (r["score"], r["n_links"], r["n_years"]), reverse=True)
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--sample", type=int, default=72)
    args = ap.parse_args()
    recs = load_corpus()
    print(f"loaded {len(recs)} questions; {sum(1 for r in recs if r['aptitude'])} aptitude items")
    print("subject distribution:", dict(Counter(r['subject'] for r in recs if not r['aptitude'])))
    tagged = sum(1 for r in recs if r["clusters"] and not r['aptitude'])
    print(f"concept-tagged: {tagged} ({100*tagged/max(1,len(recs)):0.1f}%)")
    untagged_sub = Counter(r["subject"] for r in recs if not r["clusters"] and not r["aptitude"])
    print("untagged by subject:", dict(untagged_sub))
    focus_years = [2025, 2026] if args.check else list(range(2015, 2027))
    if args.calibrate:
        import random
        res = analyse_targets(recs, focus_years, verbose=False)
        random.seed(11)
        pool = defaultdict(list)
        for ty in focus_years:
            for q in res[ty]:
                if q["tier"] not in ("aptitude",):
                    pool[q["tier"]].append((ty, q))
        n_per = max(2, args.sample // 6)
        sample = []
        for lvl in [5, 4, 3, 2, 1, 0]:
            cands = pool.get(lvl, [])
            sample.extend(random.sample(cands, min(n_per, len(cands))))
        print(f"\n=== CALIBRATION SAMPLE ({len(sample)}) — label each: agree? true level? ===\n")
        for (ty, q) in sorted(sample, key=lambda x: (x[1]["tier"], x[0])):
            print(f"--- {q['qid']} subj={q['subject']} AUTO_TIER=L{q['tier']} clusters={','.join(q['clusters'][:4])}")
            print("T:", q["text"][:450].replace("\n", " | "))
            print("   opts:", " / ".join(o[:70] for o in q["options"][:4]))
            print("   ans:", q["answer_text"][:120])
            for L in q.get("links", [])[:2]:
                d = L["detail"]
                print(f"   -> L{L['level']} {L['qid']} ({L['year']},{L['subject']}) adv={d['advantages']} trans={d['transformation']} focus={d['focus']}")
                print("      P:", L["text"][:300].replace("\n", " | "))
                print("      Pans:", L["answer_text"][:120], "| shared_ent:", d["shared_entities"], "| shared_clu:", d["shared_clusters"][:3])
            print()
        return
    all_years = list(range(1996, 2027)) if not args.check else focus_years
    results_all = analyse_targets(recs, all_years, verbose=not args.check)
    results = {ty: results_all[ty] for ty in focus_years}
    tiers, by_year, by_sub = summarise(results, focus_years)
    print("overall tiers:", {str(k): v for k, v in sorted(tiers.items(), key=str)})
    print("by subject:", json.dumps(by_sub, indent=1)[:1500])
    outdir = os.path.join(ROOT, "data", "pyq_phase2")
    os.makedirs(outdir, exist_ok=True)
    # depth analysis
    depths = depth_analysis(recs, focus_years)
    depth_cov = {}
    for ty in focus_years:
        depth_cov[str(ty)] = {}
        for k, arr in depths[ty].items():
            denom = sum(1 for x in arr if x != "apt")
            for name, lo in (("direct_L45", 4), ("strong_L35", 3), ("elim_L25", 2)):
                n = sum(1 for x in arr if x != "apt" and x >= lo)
                depth_cov[str(ty)][f"{name}_{k}y"] = round(100*n/max(1, denom), 1)
    lev = leverage_ranking(recs, results_all, all_years)
    cmap = concept_map(recs, results_all, all_years)
    json.dump({"meta": {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "window": 20, "target_years": focus_years,
                         "levels": {"5": "direct/near-direct repeat", "4": "same concept, transformed",
                                    "3": "same knowledge cluster", "2": "elimination/indirect",
                                    "1": "pattern/theme signal", "0": "no meaningful connection"}},
               "tiers": {str(k): v for k, v in tiers.items()},
               "by_year": by_year, "by_subject": by_sub, "depth": depth_cov},
              open(os.path.join(ROOT, "data", "pyq_phase2_summary.json"), "w"), indent=1)
    for ty in focus_years:
        json.dump({"dataset": "GS", "year": ty, "questions": results[ty]},
                  open(os.path.join(outdir, f"GS_{ty}.json"), "w"), indent=1)
    json.dump(cmap, open(os.path.join(ROOT, "data", "pyq_phase2_concepts.json"), "w"), indent=1)
    json.dump(lev[:300], open(os.path.join(ROOT, "data", "pyq_phase2_top300.json"), "w"), indent=1)
    print(f"wrote data/pyq_phase2_summary.json, {len(focus_years)} year files, concepts, top300")
    print("top leverage:")
    for r in lev[:15]:
        print(f"  {r['score']:6.1f} {r['qid']} L5={r['n5']} L4={r['n4']} L3={r['n3']} L2={r['n2']} yrs={r['n_years']} | {r['text'][:90]}")

if __name__ == "__main__":
    main()
