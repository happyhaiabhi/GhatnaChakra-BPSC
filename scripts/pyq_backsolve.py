#!/usr/bin/env python3
"""PYQ back-solve engine.

For every target paper (year Y) this measures how much of that paper a candidate
could have handled using ONLY earlier previous-year questions (year < Y), with
extra weight on the most recent 20 years.

Scope
    GS     Prelims General Studies Paper I   1995-2026 (target years 2015-2026)
    CSAT   Prelims CSAT Paper II             2011-2026 (target years 2015-2026)
    MAINS  Mains papers                      2011-2025 (target years 2015-2025)

Method
    1. normalise   strip exam boilerplate ("which of the following", code
                   options "1 and 2 only", statement numbering) so matching
                   runs on content, not template.
    2. concepts    clause-bounded 1-4 grams, kept only if rare enough to be
                   informative (df <= 2% of corpus). Multi-word terms are the
                   named entities that carry a question ("liquidity adjustment
                   facility", "flying fox", "virupaksha temple").
    3. matching    for a target question, each of its concepts is matched
                   against its own best prior question -> "distributed"
                   coverage, because a paper's concept may come from several
                   earlier years, not one.
    4. recency     every match is weighted by the age of the prior paper:
                   cliff  = 1.0 within 20 years, 0.5 beyond
                   decay  = 0.5 ** (age / 15)
    5. tiers       strict / medium / loose / novel (see TIERS below).

Usage
    python scripts/pyq_backsolve.py                 # full run -> data/
    python scripts/pyq_backsolve.py --calibrate     # print a labelled sample
    python scripts/pyq_backsolve.py --check         # quick 2-year smoke test

Only the Python standard library is used.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = DATA / "pyq_backsolve"
OUT_JSON = DATA / "pyq_backsolve_summary.json"
OUT_CSV = DATA / "pyq_backsolve_summary.csv"
OUT_CALIB = DATA / "pyq_backsolve_calibration.json"

TARGET_FROM = 2015
TARGET_TO = 2026
GS_TARGETS = list(range(TARGET_FROM, TARGET_TO + 1))
CSAT_TARGETS = list(range(TARGET_FROM, TARGET_TO + 1))
MAINS_TARGETS = list(range(TARGET_FROM, 2026))

# --------------------------------------------------------------------------
# tuning knobs (locked after calibration - see data/pyq_backsolve_calibration.json)
# --------------------------------------------------------------------------
MAX_DF_FRAC = 0.05      # headroom for frequent-but-real topics (panchayat, money bill)
ENT_MAXDF_FRAC = 0.012  # multi-word entity: appears in <=1.2% of questions
UNI_MAXDF_FRAC = 0.0005 # single word concept: appears in <=0.05% of questions
PARTIAL_RARE_FRAC = 0.004  # a partial match needs >=1 shared word this rare
RARE_ENT_FRAC = 0.002      # an entity this rare is decisive (drives 'strict')
TOPIC_MAXDF_FRAC = 0.015   # above this a term is furniture ("india"), not a topic
NAMED_MAXDF_FRAC = 0.0018  # a proper noun above this is too common to be evidence
N_ENTITIES = 12         # concepts kept per question (rarest / longest first)
DUP_THRESHOLD = 0.62    # content-word containment that means "same question"
SOFT_MIN = 0.70         # partial credit for a near-entity match
SOFT_JACCARD = 0.72     # word overlap needed for a partial match
RECENCY_WINDOW = 20     # "last 20 years" from the target year
RECENCY_OLD = 0.50      # cliff weight for papers older than the window
DECAY_HALFLIFE = 15     # smooth-decay half life, in years

# --------------------------------------------------------------------------
# text normalisation
# --------------------------------------------------------------------------
BOILER = [
    r"which of the following statements?\s*is/are correct",
    r"which of the statements?\s*given above is/are correct",
    r"which of the following (is|are) correct",
    r"which one of the following",
    r"which of the following",
    r"which among the following",
    r"which of the above",
    r"passed by the state legislature",
    r"state legislature",
    r"who among the above",
    r"who among the following",
    r"select the correct answer using the codes? given below",
    r"select the correct answers? using the code given below",
    r"codes? given below",
    r"consider the following statements",
    r"consider the following pairs",
    r"consider the following",
    r"correctly matched",
    r"match list i with list ii",
    r"given below",
    r"in the context of",
    r"with reference to",
    r"recently in the news",
    r"often mentioned in the news",
    r"sometimes seen in the news",
    r"seen in the news",
    r"in the news",
    r"select (the )?(correct )?answers? using the code",
    r"select the answer using the code",
    r"match list i with list ii",
    r"list i \(.*?\)",
    r"in how many of the above rows",
    r"how many of the above",
    r"rows given above",
    r"read the following passage",
    r"your answers? to these items should be based on the passages? only",
    r"examine",
    r"critically",
    r"comment",
    r"discuss",
]
CODE_OPT = re.compile(
    r"^[\d\s,and&]+only$|^[\d\s,and&]+$|^(none|all|both|neither)[a-z0-9\s,]*$", re.I)
STOP = set("""a an the of in on at to for from by with and or is are was were be been being it
its this that these those as which what who whom whose how why when where do does did can could
may might will would shall should not no nor if then than there their they them he she his her i
you your we our us one following given below above only both neither each other more most some
such same into over under about after before between among during against within without also
have has had any all none refers referred known called statement statements correct incorrect
true false following question answer given following above
# Mains instruction verbs and answer-length furniture. These open almost every
# Mains prompt, so leaving them in made "Elucidate" a shared concept between a
# Chandella-sculpture question and a buffer-stock question.
discuss examine examined examining examine critically critical analyse analyze
analysis comment commentary elucidate elucidate describe description evaluate
evaluation explain explanation illustrate illustration assess assessment define
definition distinguish differentiate enumerate highlight outline state justify
suggest bring throw light context reference respect words marks point points
view views salient features main aspects role impact significance importance
implications dimensions||""".replace("||", "").split())
CLAUSE_SPLIT = re.compile(r"[\n;]|\.\s+|\s{2,}|,|\)|\(")
# exam furniture that survives boilerplate stripping and would otherwise be
# treated as a concept ("many pair", "above row", "correctly matched")
GENERIC_ENTITY = re.compile(
    r"\b(many pair|many row|many item|many statement|many number|above pair|above row"
    r"|above item|above statement|given above|above given|correctly matched|not correctly"
    r"|following pair|following statement|list i|list ii|code given|answer using)\b"
    r"|^many |^how many |^number of |^select |^using |^list ")


def singular(w: str) -> str:
    """Crude but consistent stemmer.

    Getting this wrong silently kills recall: "Indices of Eight Core Industries"
    in a 2012 paper must match "Index of Eight Core Industries" in a 2015 one,
    so "indices" has to land on "index".
    """
    if len(w) <= 4:
        return w
    if w.endswith("ices"):            # indices -> index, matrices -> matrix
        return w[:-4] + "ex"
    if w.endswith("ies") and len(w) > 5:   # countries -> country
        return w[:-3] + "y"
    if w.endswith(("sses", "ches", "shes", "xes", "zes")):
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is", "as")):
        return w[:-1]
    return w


def clean(text: str) -> str:
    t = text.lower()
    for p in BOILER:
        t = re.sub(p, " ", t)
    t = re.sub(r"[^a-z0-9 \n]", " ", t)
    t = re.sub(r"^\s*\d+\s*", " ", t, flags=re.M)
    return re.sub(r"[ \t]+", " ", t).strip()


def strip_code_options(options):
    return [o for o in options if not CODE_OPT.match(str(o).strip().lower())]


def clause_terms(text: str, maxn: int = 4):
    """n-grams that never cross a clause boundary."""
    out = []
    for clause in CLAUSE_SPLIT.split(clean(text)):
        words = [singular(w) for w in clause.split()]
        words = [w for w in words if w not in STOP and len(w) > 2 and not w.isdigit()]
        for n in range(1, maxn + 1):
            for i in range(len(words) - n + 1):
                gram = words[i:i + n]
                if n > 1 and (gram[0] in STOP or gram[-1] in STOP):
                    continue
                if n > 1 and len(set(gram)) == 1:      # "difference difference"
                    continue
                out.append(" ".join(gram))
    return out


# --------------------------------------------------------------------------
# dataset loading -> unified records
# --------------------------------------------------------------------------
def load_records(scope):
    recs = []

    def finish(rec):
        rec["is_passage"] = bool(PASSAGE_MARK.search(rec["text"]))
        return rec

    if "gs" in scope:
        raw = json.loads((DATA / "prelims.json").read_text(encoding="utf-8"))
        for year, rows in raw.get("records_by_year", {}).items():
            for r in rows:
                text = (r.get("question") or "").strip()
                opts = [str(o) for o in r.get("options") or []]
                if not text:
                    continue
                recs.append({
                    "dataset": "GS", "year": int(year), "qid": r.get("id"),
                    "subject": (r.get("subject") or "").strip(),
                    "text": text, "options": opts,
                    "answer": opts[r["answer"]] if isinstance(r.get("answer"), int)
                    and 0 <= r["answer"] < len(opts) else None,
                    "url": r.get("reference_url"),
                })

    if "csat" in scope:
        raw = json.loads((DATA / "csat.json").read_text(encoding="utf-8"))
        for r in raw.get("questions", []):
            try:
                year = int(str(r.get("year"))[:4])
            except (TypeError, ValueError):
                continue
            text = (r.get("question") or "").strip()
            if not text:
                continue
            opts = []
            raw_opts = r.get("options")
            if isinstance(raw_opts, str):
                try:
                    raw_opts = ast.literal_eval(raw_opts)
                except (ValueError, SyntaxError):
                    raw_opts = []
            for o in raw_opts or []:
                opts.append(o.get("text", "") if isinstance(o, dict) else str(o))
            key = str(r.get("answer") or "").strip().upper()
            answer = None
            if len(key) == 1 and "A" <= key <= "Z":
                idx = ord(key) - ord("A")
                if 0 <= idx < len(opts):
                    answer = opts[idx]
            recs.append({
                "dataset": "CSAT", "year": year, "qid": r.get("id"),
                "subject": (r.get("subject") or "").strip(),
                "text": text, "options": opts, "answer": answer,
                "url": r.get("url"),
            })

    if "mains" in scope:
        raw = json.loads((DATA / "mains.json").read_text(encoding="utf-8"))
        for year, papers in raw.get("papers_by_year", {}).items():
            for slug, packet in papers.items():
                for q in packet.get("questions", []):
                    text = (q.get("question") or "").strip()
                    if not text:
                        continue
                    recs.append({
                        "dataset": "MAINS", "year": int(year),
                        "qid": f"{year}_{slug}_{q.get('q_no')}",
                        "subject": slug, "text": text, "options": [],
                        "answer": None, "url": q.get("url"),
                    })
    for r in recs:
        r["is_passage"] = bool(PASSAGE_MARK.search(r["text"]))
        r["proper"] = {w for w in proper_nouns(r["text"], set())
                       if w not in PROPER_STOP}
    return recs


ROMAN_NUMERAL = re.compile(r"^[IVXLCDM]+$")
# Words that are capitalised all over exam prose yet name nothing specific.
# "National Park" is furniture; "Keoladeo" is the concept.
PROPER_STOP = set("""national park parks sanctuary sanctuaries reserve reserves forest forests
river rivers mountain mountains island islands lake lakes state states union
government minister ministry council committee commission authority board bank
court supreme president governor act bill policy scheme mission programme program
project plan report index fund world international indian india article schedule
list part section constitution amendment parliament assembly university institute
department development research centre center society company college school
hospital market station airport airports railway railways port ports highway
highways stadium valley plateau desert ocean sea bay gulf strait peninsula
tributary glacier delta basin coast coastal memorial museum festival dance
language religion community tribe population census district city town temple
region range north south east
west central new old first second third fourth fifth sixth seventh eighth ninth
tenth amendment year day week month january february march april may june july
august september october november december""".split())
PASSAGE_MARK = re.compile(r"passage", re.I)


BREAK_BEFORE = (".", "!", "?", '."', ":", ";", "-", "—", "(", "[", '"', "'", "/")


def proper_nouns(text, sentence_initial_ok):
    """Capitalised words and acronyms.

    "Golan", "IUCN" and "Westerlies" are concepts. "height", "founded" and
    "replacement" are not - and treating them as concepts is what made a
    geography question look like it came from a CSAT logic puzzle. Words that
    only ever appear at the start of a sentence are ambiguous ("Which", "The"),
    so they are accepted only if the same word is seen capitalised mid-sentence
    somewhere else in the corpus.
    """
    found = set()
    for m in re.finditer(r"\b([A-Z][a-zA-Z]{3,})\b", text):
        word = m.group(1)
        before = text[:m.start()].rstrip()
        # a colon, dash or bracket starts a new unit too: in "Statement-I :
        # Thickness of the troposphere" the capital T is layout, not a name.
        initial = before == "" or before.endswith(BREAK_BEFORE)
        if initial and word.lower() not in sentence_initial_ok:
            continue
        found.add(singular(word.lower()))
    for m in re.finditer(r"\b([A-Z]{2,6})\b", text):
        word = m.group(1)
        if ROMAN_NUMERAL.match(word):
            continue
        found.add(word.lower())
    return found


def normalise_subject(raw: str) -> str:
    s = (raw or "").strip().lower()
    if not s:
        return "untagged"
    if s.startswith("polity") or s.startswith("governance"):
        return "polity"
    if s.startswith("art") or "culture" in s:
        return "art-culture"
    if s.startswith("science"):
        return "science-tech"
    if s.startswith("geo"):
        return "geography"
    if s.startswith("econ"):
        return "economy"
    if s.startswith("hist"):
        return "history"
    if s.startswith("environ") or s.startswith("ecology"):
        return "environment"
    if "current" in s:
        return "current-affairs"
    return s


# --------------------------------------------------------------------------
# corpus indexing
# --------------------------------------------------------------------------
def build_corpus(recs):
    n = len(recs)
    # A capitalised word that only ever starts a sentence is usually just
    # "Which"/"The"; a real name is capitalised wherever it falls. One stray
    # mid-sentence capital is not enough (a stray "Thickness" in one paper used
    # to make "thickness" a named concept in every paper), so a word must be
    # capitalised mid-sentence at least three times AND more often than not.
    mid_counts, cap_counts = Counter(), Counter()
    for r in recs:
        for m in re.finditer(r"\b([A-Z][a-zA-Z]{3,})\b", r["text"]):
            w = m.group(1).lower()
            cap_counts[w] += 1
            before = r["text"][:m.start()].rstrip()
            if not (before == "" or before.endswith(BREAK_BEFORE)):
                mid_counts[w] += 1
    mid_sentence = {w for w, c in mid_counts.items()
                    if c >= 3 and c >= 0.5 * cap_counts[w]}
    for r in recs:
        r["proper"] = {w for w in proper_nouns(r["text"], mid_sentence)
                       if w not in PROPER_STOP}
    for r in recs:
        body = r["text"] + "\n" + "\n".join(strip_code_options(r["options"]))
        r["terms"] = set(clause_terms(body))
        # an entity that only occurs in the answer options is weaker evidence
        # than one the question itself is built around
        r["stem_terms"] = set(clause_terms(r["text"]))
        r["plain"] = set(singular(w) for w in clean(body).split()
                         if w not in STOP and len(w) > 2 and not w.isdigit())

    df = Counter()
    for r in recs:
        df.update(r["terms"])
    max_df = max(4, int(MAX_DF_FRAC * n))
    ent_maxdf = max(20, int(ENT_MAXDF_FRAC * n))
    uni_maxdf = max(3, int(UNI_MAXDF_FRAC * n))
    inform = {t for t, c in df.items() if c <= max_df}
    idf = {t: math.log((n + 1) / (df[t] + 1)) + 1 for t in inform}

    def pick(cands, k):
        kept = []
        for t in sorted(cands, key=lambda t: (-len(t), -idf[t])):
            if GENERIC_ENTITY.search(t):
                continue
            ws = set(t.split())
            if any(len(ws & set(c.split())) / len(ws | set(c.split())) >= 0.5 for c in kept):
                continue
            kept.append(t)
            if len(kept) >= k:
                break
        return kept

    for r in recs:
        usable = r["terms"] & inform
        ents = [t for t in usable if " " in t and df[t] <= ent_maxdf]
        # single words only count when they are names or acronyms
        unis = [t for t in usable if " " not in t and t in r["proper"]
                and df[t] <= ent_maxdf]
        # recurring-but-frequent multi-word concepts ("money bill", "panchayati
        # raj") sit above the entity cut-off yet are exactly what PYQ revision
        # rests on, so they get their own band and only count as weak evidence
        common = [t for t in usable if " " in t and ent_maxdf < df[t] <= max_df]
        r["ent"] = (pick(ents, N_ENTITIES - 4) + pick(unis, 4) + pick(common, 4))
        r["entset"] = set(r["ent"])
        r["src"] = {t: ("stem" if t in r["stem_terms"] else "option") for t in r["ent"]}
        # ordinary words ("height", "founded", "replacement") are kept only as a
        # last-resort topic signal - they never appear as a matched question
        r["topicword"] = pick([t for t in usable if " " not in t
                               and t not in r["proper"]
                               and df[t] <= max(6, int(0.004 * n))], 3)
        r["w"] = {t: idf[t] * (1 + 0.35 * (len(t.split()) - 1)) for t in r["ent"]}

    winv = defaultdict(set)
    pinv = defaultdict(set)      # 6-char prefix -> questions, for word variants
    for i, r in enumerate(recs):
        for t in r["entset"]:
            for w in t.split():
                winv[w].add(i)
                if len(w) >= 6:
                    pinv[w[:6]].add(i)
    return {"df": df, "idf": idf, "inform": inform, "max_df": max_df,
            "winv": winv, "n": n, "ent_maxdf": ent_maxdf, "uni_maxdf": uni_maxdf,
            "partial_rare_df": max(6, int(PARTIAL_RARE_FRAC * n)),
            "rare_df": max(6, int(RARE_ENT_FRAC * n)), "pinv": pinv,
            "topic_cap": max(40, int(TOPIC_MAXDF_FRAC * n)),
            "named_cap": max(10, int(NAMED_MAXDF_FRAC * n))}


def near_dup(a, b):
    """content-word containment: 1.0 means one question's words sit inside the other."""
    return len(a["plain"] & b["plain"]) / max(1, min(len(a["plain"]), len(b["plain"])))


def softmatch(corpus_recs, target_ent, j, df=None, partial_rare_df=6):
    """exact entity match scores 1.0; a partially overlapping entity scores <1.

    Partial matches (e.g. "nano technology health sector" vs
    "sector information technology health") are only accepted when the two
    entities share at least one genuinely rare word - otherwise generic words
    like "sector", "health" or "technology" manufacture false relationships.
    """
    prior = corpus_recs[j]
    if target_ent in prior["entset"]:
        return 1.0, target_ent
    if (" " not in target_ent and len(target_ent) >= 6
            and any(u[:6] == target_ent[:6] and abs(len(u) - len(target_ent)) <= 3
                    for u in prior["entset"])):
        return 0.9, next(u for u in prior["entset"]
                         if u[:6] == target_ent[:6]
                         and abs(len(u) - len(target_ent)) <= 3)
    ws = set(target_ent.split())
    best, best_u = 0.0, None
    for u in prior["entset"]:
        if " " not in u:
            continue
        uws = set(u.split())
        shared = ws & uws
        jac = len(shared) / len(ws | uws)
        if jac < SOFT_JACCARD:
            continue
        if df is not None and not any(df[w] <= partial_rare_df for w in shared):
            continue
        score = SOFT_MIN * jac
        if score > best:
            best, best_u = score, u
    return best, best_u


def recency_weight(age, model, window):
    if model == "flat":
        return 1.0
    if model == "cliff":
        return 1.0 if age <= window else RECENCY_OLD
    return 0.5 ** (age / DECAY_HALFLIFE)


# --------------------------------------------------------------------------
# per-year analysis
# --------------------------------------------------------------------------
def analyse(recs, corpus, target_year, dataset, window=RECENCY_WINDOW, topk=6):
    def usable_source(r):
        # A CSAT reading-comprehension passage is ~1,160 characters of prose and
        # matches everything; an aptitude item ("A is taller than B") shares
        # words with geography questions and means nothing. CSAT is therefore
        # evidence only for CSAT, and passages are never evidence at all.
        if r["is_passage"]:
            return False
        # ...and the reverse is just as misleading: a CSAT table of average
        # marks is not answered by a GS question about the English alphabet.
        if (r["dataset"] == "CSAT") != (dataset == "CSAT"):
            return False
        return True
    pool = {i for i, r in enumerate(recs)
            if r["year"] < target_year and r["dataset"] in POOL_DATASETS
            and usable_source(r)}
    targets = [i for i, r in enumerate(recs)
               if r["year"] == target_year and r["dataset"] == dataset]
    winv, pinv = corpus["winv"], corpus["pinv"]
    results = {}

    for i in targets:
        tgt = recs[i]
        cand_by_ent, allc = {}, set()
        for t in tgt["ent"]:
            words = [w for w in t.split() if w in winv]
            sets = sorted((winv[w] & pool for w in words), key=len)
            if " " not in t and len(t) >= 6:      # panchayat ~ panchayati
                sets.append(pinv.get(t[:6], set()) & pool)
            c = set()
            for s in sorted(sets, key=len):
                c |= s
                if len(c) > 1200:
                    break
            cand_by_ent[t] = c
            allc |= c

        matches = []
        for t, cands in cand_by_ent.items():
            scored = []
            for j in cands:
                s, u = softmatch(recs, t, j, corpus["df"],
                                 corpus["partial_rare_df"])
                if s > 0:
                    scored.append((s, j, u))
            scored.sort(key=lambda x: -x[0])
            # rank 0 (the best earlier paper for this concept) drives the score;
            # ranks 1-2 are kept only so we can see when one earlier paper shares
            # several concepts with the target
            for rank, (s, j, u) in enumerate(scored[:3]):
                matches.append({"ent": t, "j": j, "s": s, "pri": u, "rank": rank})

        total_w = sum(tgt["w"][t] for t in tgt["ent"]) or 1.0
        scores = {}
        best_matches = [m for m in matches if m["rank"] == 0]
        for model in ("flat", "cliff", "decay"):
            got = 0.0
            for m in best_matches:
                age = target_year - recs[m["j"]]["year"]
                got += tgt["w"][m["ent"]] * m["s"] * recency_weight(age, model, window)
            scores[model] = got / total_w

        dup = max(((near_dup(tgt, recs[j]), j) for j in allc), default=(0.0, None))

        df = corpus["df"]
        rare_df = corpus["rare_df"]
        ent_maxdf = corpus["ent_maxdf"]
        uni_maxdf = corpus["uni_maxdf"]
        topic_cap = corpus["topic_cap"]
        proper = tgt["proper"]
        named_cap = corpus["named_cap"]
        src = tgt["src"]

        def classify(subset, dup_pair, cov):
            """Sort a question into strict / medium / recurring / loose / novel.

            Entities are graded by how often they occur in the corpus (df):
              decisive  df <= 0.2%   "liquidity adjustment facility"
              concept   df <= 1.2%   "directive principles of state policy"
              topic     df above that "panchayati raj", "money bill", "westerlies"

            A question only earns 'strict' or 'medium' from decisive/concept
            evidence, and only from the part of the question that carries the
            test - its stem, not its answer options. Topic-level overlap means
            familiar ground, not a known answer, so it stops at 'recurring'.
            """
            exact = [m for m in subset if m["s"] >= 0.999 and " " in m["ent"]]
            # a proper noun is a concept in its own right - "manipuri" and
            # "buddha" carry a question even though they are single words
            # only genuinely distinctive names count ("manipuri", "cornwallis");
            # a common one ("india") is furniture, not evidence
            named = [m for m in subset if " " not in m["ent"]
                     and m["ent"] in proper and df[m["ent"]] <= named_cap]
            concept_mw = [m for m in exact if df[m["ent"]] <= ent_maxdf]
            concept = concept_mw + named
            # topic-level words are usually single words ("panchayat", "westerlies")
            topic = [m for m in subset if m["s"] >= 0.9
                     and df[m["ent"]] > (ent_maxdf if " " in m["ent"] else uni_maxdf)
                     and df[m["ent"]] <= topic_cap]
            rare = [m for m in exact if df[m["ent"]] <= rare_df]
            partial = [m for m in subset if SOFT_MIN * SOFT_JACCARD <= m["s"] < 0.999
                       and " " in m["ent"]]
            unigram = [m for m in subset if " " not in m["ent"]]
            weak_uni = [m for m in unigram if df[m["ent"]] <= uni_maxdf]
            # with ~6,000 prior questions a frequent term matches something by
            # chance, so topic evidence needs two shared concepts in one paper
            topic_density = max(Counter(m["j"] for m in topic).values(), default=0)
            stem = lambda ms: [m for m in ms if src[m["ent"]] == "stem"]
            s_rare, s_concept, s_part = stem(rare), stem(concept), stem(partial)
            s_concept_mw, s_named = stem(concept_mw), stem(named)
            # the real "you have studied this ground" signal: one earlier paper
            # that carries at least two of this question's concepts. Two separate
            # papers each sharing one word is a coincidence, not preparation.
            dens = max(Counter(m["j"] for m in (concept_mw + named)).values(),
                       default=0)
            # two identically worded "consider the following pairs" questions are
            # not the same question, so a near-duplicate needs concept weight too
            # a shared word-bag is not a repeat: at least a quarter of the
            # target's own clauses must reappear before we call it one
            dup_ok = dup_pair[0] >= DUP_THRESHOLD and cov >= 0.25

            if (dup_ok or len(s_rare) >= 2 or (s_rare and cov >= 0.25)
                    or (len(s_rare) == 1 and len(s_concept) >= 3
                        and cov >= 0.35)):
                return "strict", exact, rare, partial, unigram, topic_density
            # names alone are too easy (two questions can both say "Atlantic");
            # a real concept needs a multi-word entity behind it
            if (s_rare or len(s_concept_mw) >= 2 or (s_concept_mw and s_named)
                    or len(s_part) >= 2 or (rare and cov >= 0.15)
                    or (s_named and dens >= 2)):
                # a decisive entity found only among the answer options is still
                # concept overlap, but it cannot be called decisive
                return "medium", exact, rare, partial, unigram, topic_density
            # a single rare *ordinary* word ("thickness") matching a Blu-ray
            # question is noise, not a shared concept - only named entities and
            # genuine multi-word overlap count as even the weakest evidence
            if concept or partial:
                return "loose", exact, rare, partial, unigram, topic_density
            if topic_density >= 2 or len(topic) >= 2:
                return "recurring", exact, rare, partial, unigram, topic_density
            return "novel", exact, rare, partial, unigram, topic_density

        cov_flat = scores["flat"]
        same_matches = [m for m in matches if recs[m["j"]]["dataset"] == dataset]
        cross_matches = [m for m in matches if recs[m["j"]]["dataset"] != dataset]
        same_dup = max(((near_dup(tgt, recs[j]), j) for j in allc
                        if recs[j]["dataset"] == dataset), default=(0.0, None))

        # ordinary shared words, last resort: "this topic word appears earlier".
        # Kept as a named word with the years it occurs in - never dressed up as
        # a matched question, because "height" matching a CSAT puzzle tells the
        # reader nothing.
        topic_words = []
        for w in tgt.get("topicword", []):
            years = sorted({recs[j]["year"] for j in allc
                            if w in recs[j]["entset"] or w in recs[j]["terms"]})[:6]
            if years:
                topic_words.append({"word": w, "years": years})

        # --- headline tier: evidence from the SAME paper series only ---
        if tgt["is_passage"]:
            # a 1,160-character passage has no comparable earlier item
            tier, exact, rare, partial, unigram, topic_density = (
                "passage", [], [], [], [], 0)
        else:
            tier, exact, rare, partial, unigram, topic_density = classify(
                same_matches, same_dup, cov_flat)
        # topic_words stay a labelled hint only - they never promote a tier.
        # Folding them in meant "height" appearing in one CSAT puzzle turned a
        # fresh geography question into a "recurring" one.

        # --- cross-series lift (Mains -> Prelims): needs real weight ---
        cross_exact = [m for m in cross_matches if m["s"] >= 0.999
                       and " " in m["ent"]]
        cross_density = max(Counter(m["j"] for m in cross_exact).values(), default=0)
        cross_decisive = any(df[m["ent"]] <= rare_df for m in cross_exact)
        tier_cross = tier
        if tier in ("novel", "loose", "recurring") and cross_density >= 2:
            tier_cross = "medium" if cross_decisive else "recurring"
        cross_lift = tier_cross != tier

        same_cov = sum(tgt["w"].get(m["ent"], 1.0) * m["s"] for m in same_matches
                       if m["rank"] == 0) / (sum(tgt["w"][t] for t in tgt["ent"]) or 1.0)
        tier_same = tier
        e_dup = dup[0] >= DUP_THRESHOLD and cov_flat >= 0.03
        common_density = topic_density
        ranked = sorted(matches, key=lambda m: -(tgt["w"][m["ent"]] * m["s"]))[:topk]
        results[i] = {
            "tier": tier, "cov_flat": cov_flat, "cov_cliff": scores["cliff"],
            "cov_decay": scores["decay"], "dup": dup[0], "dup_j": dup[1],
            "cov_same": same_cov, "tier_same": tier_same,
            "tier_cross": tier_cross, "cross_lift": cross_lift,
            "cross_density": cross_density, "topic_words": topic_words,
            "n_exact": len(exact), "n_rare": len(rare), "n_partial": len(partial),
            "n_unigram": len(unigram),
            "tier_detail": ("repeat" if e_dup else "decisive" if rare
                            else "concept" if exact or partial else "none"),
            "n_topic": common_density,
            "top": ranked, "cand": len(allc),
            "cover_years": sorted({recs[m["j"]]["year"] for m in matches
                                   if " " in m["ent"]
                                   and m["s"] >= SOFT_MIN * SOFT_JACCARD}),
            "concentration": max(Counter(m["j"] for m in best_matches).values(),
                                 default=0),
        }
    return results


TIER_ORDER = ("strict", "medium", "recurring", "loose", "novel", "passage")
# "PYQ-solvable" = strict + medium; "topic already seen" adds recurring
TIER_SET = {"strict": {"strict"}, "medium": {"strict", "medium"},
            "loose": {"strict", "medium", "recurring", "loose"}}


# --------------------------------------------------------------------------
# greedy "minimum PYQ set" optimiser
# --------------------------------------------------------------------------
def optimise(recs, results_by_year, dataset, targets, k_max=10, window=None):
    """Greedy "which earlier papers should I solve?" - a backtest.

    For every target year Y we may only choose papers published before Y, so
    the recommendation for 2026 never peeks at 2026 itself. A question counts as
    unlocked when at least one of the chosen earlier papers carries one of its
    concepts.
    """
    cover = {}                      # Y -> question index -> years that teach it
    for ty in targets:
        res = results_by_year.get((dataset, ty))
        if not res:
            continue
        cover[ty] = {i: set(y for y in e["cover_years"]
                            if window is None or ty - y <= window)
                     for i, e in res.items()}

    gains, picks_by_year = [], {}
    for ty, qmap in cover.items():
        universe = {i for i, ys in qmap.items() if ys}
        covered, picks = set(), []
        for _ in range(k_max):
            best_year, best_gain = None, -1
            for py in {y for ys in qmap.values() for y in ys}:
                if py in picks:
                    continue
                gain = sum(1 for i in universe if py in qmap[i] and i not in covered)
                if gain > best_gain or (gain == best_gain and best_year is not None
                                        and py > best_year):
                    best_year, best_gain = py, gain
            if best_year is None or best_gain <= 0:
                break
            picks.append(best_year)
            covered |= {i for i in universe if best_year in qmap[i]}
        picks_by_year[ty] = picks
        running, row = set(), []
        for py in picks:
            running |= {i for i in universe if py in qmap[i]}
            row.append(len(running))
        gains.append((ty, row, len(universe), len(qmap)))

    maxk = max((len(g[1]) for g in gains), default=0)
    curve, ceiling = [], []
    for k in range(maxk):
        # the ceiling is averaged over the same subset of years as the curve,
        # otherwise a k that only some years reach looks like it beats it
        gk = [g for g in gains if len(g[1]) > k and g[3]]
        if not gk:
            curve.append(None); ceiling.append(None); continue
        curve.append(round(100 * statistics.mean(g[1][k] / g[3] for g in gk), 1))
        ceiling.append(round(100 * statistics.mean(g[2] / g[3] for g in gk), 1))
    freq = Counter(y for ty in picks_by_year for y in picks_by_year[ty][:6])
    return {"curve_pct": curve, "ceiling_pct": ceiling,
            "ceiling_by_k": ceiling, "window": window, 
            "by_year": {str(ty): picks_by_year[ty] for ty in picks_by_year},
            "most_picked": freq.most_common(12),
            "universe": {str(g[0]): g[2] for g in gains},
            "paper_size": {str(g[0]): g[3] for g in gains}}


# --------------------------------------------------------------------------
# reporting helpers
# --------------------------------------------------------------------------
def answer_conflicts(recs, results_by_year):
    """Verbatim repeats whose stored answer keys disagree -> data to audit.

    Restricted to genuine verbatim repeats (containment >= 0.95) that also share
    concept weight, otherwise identically-worded "consider the following"
    templates produce a stream of false alarms.
    """
    out = []
    for (dataset, ty), res in results_by_year.items():
        for i, e in res.items():
            if e["dup"] < 0.95 or e["dup_j"] is None or e["cov_flat"] < 0.25:
                continue
            a, b = recs[i], recs[e["dup_j"]]
            if not (a["answer"] and b["answer"]):
                continue
            ta = set(w for w in clean(a["answer"]).split() if len(w) > 2)
            tb = set(w for w in clean(b["answer"]).split() if len(w) > 2)
            overlap = len(ta & tb) / max(1, min(len(ta), len(tb)))
            same = a["answer"].strip().lower() == b["answer"].strip().lower()
            if not same and overlap < 0.6:   # "people" vs "population" is not a conflict
                out.append({
                    "year": ty, "dataset": dataset, "qid": a["qid"],
                    "prior_year": b["year"], "prior_qid": b["qid"],
                    "question": a["text"][:300], "answer": a["answer"],
                    "prior_answer": b["answer"], "prior_question": b["text"][:300],
                })
    return out


def dedupe_matches(recs, matches, tgt_w, dataset, limit=5):
    """One entry per earlier question, best concept first."""
    best = {}
    for m in matches:
        j = m["j"]
        score = tgt_w.get(m["ent"], 1.0) * m["s"]
        if j not in best or score > best[j][0]:
            best[j] = (score, m)
    ranked = sorted(best.values(),
                    key=lambda it: (0 if recs[it[1]["j"]]["dataset"] == dataset else 1,
                                    -it[0]))[:limit]
    return [{
        "year": recs[m["j"]]["year"],
        "dataset": recs[m["j"]]["dataset"],
        "qid": recs[m["j"]]["qid"],
        "subject": normalise_subject(recs[m["j"]]["subject"]),
        "s": round(m["s"], 2),
        "ent": m["ent"],
        "pri": m["pri"],
        "text": recs[m["j"]]["text"][:200],
        "answer": (recs[m["j"]]["answer"] or "")[:110],
        "url": recs[m["j"]]["url"],
    } for _, m in ranked]


def feeder_years(recs, results_by_year):
    out = defaultdict(Counter)
    for (dataset, ty), res in results_by_year.items():
        for i, e in res.items():
            for m in e["top"]:
                if m["s"] >= SOFT_MIN and " " in m["ent"]:
                    out[f"{dataset} {ty}"][recs[m["j"]]["year"]] += 1
    return {k: v.most_common(8) for k, v in out.items()}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
POOL_DATASETS = {"GS", "CSAT", "MAINS"}


def run(scope=("gs", "csat", "mains"), targets=True, do_optimise=True,
        window=RECENCY_WINDOW, verbose=True):
    t0 = time.time()
    recs = load_records(scope)
    if verbose:
        print(f"loaded {len(recs)} records "
              f"({Counter(r['dataset'] for r in recs)})", flush=True)
    corpus = build_corpus(recs)
    if verbose:
        print(f"indexed: {corpus['n']} docs, informative terms(df<={corpus['max_df']}) "
              f"{len(corpus['inform'])}, avg concepts/question "
              f"{statistics.mean(len(r['ent']) for r in recs):.1f}", flush=True)

    plan = []
    if "gs" in scope:
        plan += [("GS", y) for y in GS_TARGETS]
    if "csat" in scope:
        plan += [("CSAT", y) for y in CSAT_TARGETS]
    if "mains" in scope:
        plan += [("MAINS", y) for y in MAINS_TARGETS]

    results_by_year = {}
    for dataset, ty in plan:
        t1 = time.time()
        res = analyse(recs, corpus, ty, dataset, window=window)
        results_by_year[(dataset, ty)] = res
        if verbose:
            c = Counter(e["tier"] for e in res.values())
            print(f"  {dataset:<5} {ty}  strict {c['strict']:>3}  medium {c['medium']:>3}  "
                  f"recurring {c['recurring']:>3}  loose {c['loose']:>3}  "
                  f"novel {c['novel']:>3}  passage {c['passage']:>3}   "
                  f"[{time.time()-t1:.1f}s]", flush=True)

    # ---- summary table -------------------------------------------------
    summary_rows, by_subject = [], defaultdict(lambda: Counter())
    for (dataset, ty), res in sorted(results_by_year.items()):
        c = Counter(e["tier"] for e in res.values())
        # comprehension passages have no comparable earlier item, so they are
        # counted separately rather than inflating the "novel" figure
        n = sum(v for k, v in c.items() if k != "passage")
        n = n or 1
        for i, e in res.items():
            by_subject[(dataset, normalise_subject(recs[i]["subject"]))][e["tier"]] += 1
        cs = Counter(e["tier_same"] for e in res.values())
        row = {
            "dataset": dataset, "year": ty, "questions": n,
            "strict": c["strict"], "medium": c["medium"], "recurring": c["recurring"],
            "loose": c["loose"], "novel": c["novel"], "passages": c["passage"],
            "strict_pct": round(100 * c["strict"] / n, 1),
            "medium_pct": round(100 * (c["strict"] + c["medium"]) / n, 1),
            "recurring_pct": round(
                100 * (c["strict"] + c["medium"] + c["recurring"]) / n, 1),
            "loose_pct": round(100 * (c["strict"] + c["medium"] + c["recurring"]
                                      + c["loose"]) / n, 1),
            "verbatim_repeats": sum(1 for e in res.values() if e["dup"] >= 0.95),
            "medium_pct_same_dataset": round(
                100 * (cs["strict"] + cs["medium"]) / n, 1),
            "mean_cov_cliff": round(statistics.mean(e["cov_cliff"] for e in res.values()), 4),
            "mean_cov_decay": round(statistics.mean(e["cov_decay"] for e in res.values()), 4),
            "mean_cov_flat": round(statistics.mean(e["cov_flat"] for e in res.values()), 4),
        }
        summary_rows.append(row)

    # ---- per-question records -----------------------------------------
    questions_out = []
    for (dataset, ty), res in sorted(results_by_year.items()):
        for i, e in sorted(res.items()):
            r = recs[i]
            questions_out.append({
                "dataset": dataset, "year": ty, "qid": r["qid"],
                "subject": normalise_subject(r["subject"]),
                "text": r["text"][:420],
                "answer": (r["answer"] or "")[:200],
                "url": r["url"],
                "tier": e["tier"],
                "cov_flat": round(e["cov_flat"], 3),
                "tier_same": e["tier_same"], "cov_same": round(e["cov_same"], 3),
                "cov_cliff": round(e["cov_cliff"], 3),
                "cov_decay": round(e["cov_decay"], 3),
                "dup": round(e["dup"], 3),
                "n_exact": e["n_exact"], "n_partial": e["n_partial"],
                "matches": dedupe_matches(recs, e["top"], recs[i]["w"], dataset),
                "topic_words": e["topic_words"],
                "cross_lift": e["cross_lift"],
            })

    subject_rows = []
    for (dataset, subj), c in sorted(by_subject.items()):
        n = sum(c.values())
        subject_rows.append({
            "dataset": dataset, "subject": subj, "questions": n,
            "strict_pct": round(100 * c["strict"] / n, 1),
            "medium_pct": round(100 * (c["strict"] + c["medium"]) / n, 1),
            "recurring_pct": round(100 * (c["strict"] + c["medium"] + c["recurring"]) / n, 1),
            "loose_pct": round(100 * (c["strict"] + c["medium"] + c["recurring"]
                                      + c["loose"]) / n, 1),
        })

    # per-year detail files, so the web page only downloads the year it shows
    OUT_DIR.mkdir(exist_ok=True)
    for old in OUT_DIR.glob("*.json"):
        old.unlink()
    by_key = defaultdict(list)
    for q in questions_out:
        by_key[(q["dataset"], q["year"])].append(q)
    for (dataset, ty), rows in sorted(by_key.items()):
        (OUT_DIR / f"{dataset}_{ty}.json").write_text(
            json.dumps({"dataset": dataset, "year": ty, "questions": rows},
                       ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    del questions_out

    payload = {
        "meta": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scope": sorted(scope),
            "target_years": {"GS": GS_TARGETS, "CSAT": CSAT_TARGETS,
                             "MAINS": MAINS_TARGETS},
            "pool": "all questions with year < target year, across "
                    + "+".join(sorted(POOL_DATASETS)),
            "tuning": {"max_df_frac": MAX_DF_FRAC,
                       "ent_maxdf": corpus["ent_maxdf"],
                       "uni_maxdf": corpus["uni_maxdf"],
                       "partial_rare_df": corpus["partial_rare_df"],
                       "dup_threshold": DUP_THRESHOLD, "soft_min": SOFT_MIN,
                       "soft_jaccard": SOFT_JACCARD, "recency_window": window,
                       "recency_old": RECENCY_OLD, "decay_halflife": DECAY_HALFLIFE},
            "corpus": {"documents": corpus["n"],
                       "informative_terms": len(corpus["inform"]),
                       "avg_concepts_per_question": round(
                           statistics.mean(len(r["ent"]) for r in recs), 1)},
            "runtime_seconds": round(time.time() - t0, 1),
        },
        "tiers": {
            "strict": "verbatim/near repeat, or the decisive named entity of the "
                      "question appeared before - a PYQ student should get these",
            "medium": "a distinctive concept/entity of the question appeared in an "
                      "earlier paper, though the angle differs",
            "recurring": "the broad topic recurs in earlier papers (Panchayati Raj, "
                         "Money Bill, westerlies) but this exact question is new",
            "loose": "partial or single-word overlap - related, not sufficient",
            "novel": "no earlier PYQ carries even the topic",
            "passage": "comprehension passage - no comparable earlier item",
        },
        "summary": summary_rows,
        "by_subject": subject_rows,
    }

    if do_optimise:
        opt = {}
        for dataset in ("GS", "CSAT"):
            if dataset not in [d for d, _ in results_by_year]:
                continue
            years = sorted(y for d, y in results_by_year if d == dataset)
            opt[dataset] = optimise(recs, results_by_year, dataset, years)
            opt[dataset + "_20y"] = optimise(recs, results_by_year, dataset, years,
                                             window=RECENCY_WINDOW)
            if verbose:
                print(f"  optimiser {dataset}: coverage@k {opt[dataset]['curve_pct']}")
        payload["optimizer"] = opt

    # where does the help come from? age of the earlier paper behind each match
    age_curve, age_weighted = defaultdict(Counter), defaultdict(float)
    for (dataset, ty), res in results_by_year.items():
        for i, e in res.items():
            for m in e["top"]:
                if " " not in m["ent"]:
                    continue
                age = min(31, max(0, ty - recs[m["j"]]["year"]))
                age_curve[dataset][age] += 1
                age_weighted[(dataset, age)] += recs[i]["w"].get(m["ent"], 1.0) * m["s"]
    payload["age_curve"] = {d: {str(k): v for k, v in sorted(c.items())}
                            for d, c in age_curve.items()}
    payload["age_weighted"] = {d: {str(k): round(v, 1) for (dd, k), v
                                   in age_weighted.items() if dd == d}
                               for d in age_curve}
    payload["feeders"] = feeder_years(recs, results_by_year)
    payload["answer_conflicts"] = answer_conflicts(recs, results_by_year)

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        cols = ["dataset", "year", "questions", "strict", "medium", "recurring",
                "loose", "novel", "strict_pct", "medium_pct", "recurring_pct",
                "loose_pct", "medium_pct_same_dataset", "verbatim_repeats",
                "mean_cov_cliff", "mean_cov_decay", "mean_cov_flat"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(summary_rows)
    if verbose:
        print(f"\nwrote {OUT_JSON.relative_to(ROOT)} "
              f"({OUT_JSON.stat().st_size/1e6:.2f} MB) and "
              f"{OUT_CSV.relative_to(ROOT)} in {time.time()-t0:.1f}s")
    return payload, recs, corpus, results_by_year


def calibrate(sample=25, seed=11):
    """Print a stratified sample of matches for human labelling."""
    recs = load_records(("gs", "csat", "mains"))
    corpus = build_corpus(recs)
    rng = random.Random(seed)
    buckets = defaultdict(list)
    for ty in range(2015, 2027):
        for ds in ("GS", "MAINS"):
            res = analyse(recs, corpus, ty, ds)
            for i, e in res.items():
                buckets[e["tier"]].append((ty, ds, i, e))
    out = []
    graded = [t for t in TIER_ORDER if t != "passage"]
    per_tier = max(1, round(sample / len(graded)))
    for tier in graded:
        items = buckets[tier][:]
        rng.shuffle(items)
        for ty, ds, i, e in items[:per_tier]:
            m = e["top"][0] if e["top"] else None
            ents = [(m["ent"], m["pri"], round(m["s"], 2), recs[m["j"]]["year"],
                     recs[m["j"]]["dataset"]) for m in e["top"][:3] if " " in m["ent"]]
            out.append({
                "id": len(out) + 1, "tier": tier, "target_year": ty, "evidence": ents,
                "target": recs[i]["text"][:400],
                "prior_year": recs[m["j"]]["year"] if m else None,
                "prior_dataset": recs[m["j"]]["dataset"] if m else None,
                "prior": recs[m["j"]]["text"][:400] if m else None,
                "entity": m["ent"] if m else None,
                "matched": m["pri"] if m else None,
                "score": round(m["s"], 2) if m else 0,
                "cov": round(e["cov_flat"], 3),
                "label": None,
            })
    rng.shuffle(out)
    OUT_CALIB.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for o in out:
        print(f"\n[{o['id']:>2}] tier={o['tier']:<7} cov={o['cov']}  "
              f"({o['target_year']} <- {o['prior_year']} {o['prior_dataset']})")
        print(f"  Q  {o['target'][:260]}")
        print(f"  P  {(o['prior'] or '')[:260]}")
        for e0 in o["evidence"]:
            print(f"  E  {e0[0]} ~ {e0[1]}  (s={e0[2]}, {e0[3]} {e0[4]})")
    print(f"\n{len(out)} pairs -> {OUT_CALIB.relative_to(ROOT)} "
          f"(label each with true/false in the 'label' field)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", default="gs,csat,mains")
    ap.add_argument("--window", type=int, default=RECENCY_WINDOW)
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args(argv)

    if args.calibrate:
        calibrate(seed=args.seed)
        return 0
    if args.check:
        global GS_TARGETS, CSAT_TARGETS, MAINS_TARGETS
        GS_TARGETS = [2015, 2024]
        CSAT_TARGETS = []
        MAINS_TARGETS = []
        run(scope=tuple(args.scope.split(",")), do_optimise=False)
        return 0
    run(scope=tuple(args.scope.split(",")), window=args.window)
    return 0


if __name__ == "__main__":
    sys.exit(main())
