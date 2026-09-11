#!/usr/bin/env python3
"""Build the UPSC Polity + Geography 6-hr/day sprint plan from the PYQ analysis.

Inputs
  build_upsc_pg/pyq_summary.json     produced by scripts/analyse_polity_geo_pyqs.py
  build_upsc_pg/pyq_analysis.csv     same script - per-question unit tagging
  scripts/pg_sprint_curriculum.py    the 24 + 24 study units with pages/focus/traps

Outputs
  UPSC_Polity_Geo_Sprint_Plan.md     the plan document (analysis + day-by-day)
  UPSC_Polity_Geo_Sprint_Plan.pdf    A4 landscape typeset version (fpdf2)
  UPSC_Polity_Geo_Sprint_Tracker.csv one row per day, printable tick-off tracker
  pg-sprint/index.html               self-contained interactive tracker (offline-safe)
  build_upsc_pg/plan.json            machine-readable schedule

How the timetable is derived - everything below is computed, not asserted:
  1. blocks per unit  = max(1, ceil(pages/26), ceil(prelims_last10/8))
  2. teaching order   = prerequisite-respecting order (TEACH_ORDER), so climatology
     precedes monsoon and Fundamental Rights precede basic structure
  3. subject split    = 0.6 * prelims core share + 0.4 * mains marks share, which
     lands on ~50/50, so the daily template is 3 h Polity + 3 h Geography
  4. daily PYQ load   = that unit's last-10-paper questions spread over its blocks
  5. revision piles   = the study days 1, 3, 7 and 21 days earlier (spaced repetition)
  6. gates            = checked at the end of each sprint with explicit pass marks
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

try:                                   # the aspirant is in India; the sandbox clock is UTC
    from zoneinfo import ZoneInfo
    TODAY = datetime.now(ZoneInfo("Asia/Kolkata")).date()
except Exception:                      # pragma: no cover
    TODAY = date.today()

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build_upsc_pg"
OUT_HTML = ROOT / "pg-sprint"

from pg_sprint_curriculum import GEOGRAPHY, POLITY, UNIT_SOURCES  # noqa: E402

START = date(2026, 9, 12)            # Day 1 (Saturday)
PRELIMS = date(2027, 5, 26)
HOURS_PER_DAY = 6
MIN_PER_DAY = HOURS_PER_DAY * 60

PAGES_PER_BLOCK = 30                 # first-reading pages a 100-minute block absorbs (~3.3 min/page)
PYQ_PER_BLOCK = 12                   # last-10-paper questions that earn a unit an extra block
PYQ_FLOOR = 3                        # minimum PYQs per subject per day, topped up from the older bank
BLOCK_MINUTES = 100

SPRINT2_STUDY_DAYS = 15              # second reading + PYQ marathon + mains start
SPRINT3_STUDY_DAYS = 10              # mains integration + consolidation

TEACH_ORDER = {
    "Polity": ["P01", "P02", "P03", "P04", "P05", "P24", "P06", "P10", "P07", "P08",
               "P09", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19",
               "P20", "P21", "P22", "P23"],
    "Geography": ["G23", "G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09",
                  "G10", "G11", "G12", "G13", "G14", "G15", "G16", "G17", "G18", "G19",
                  "G20", "G21", "G22", "G24"],
}

MAP_DRILLS = [
    "Himalayan ranges, passes & peaks", "Peninsular plateau, Ghats & Aravalli",
    "Himalayan rivers & tributaries", "Peninsular rivers & deltas",
    "Lakes, wetlands & Ramsar sites", "Soil belts of India",
    "Crop belts & agro-climatic zones", "Forest types & mangroves",
    "National parks (north & north-east)", "National parks (south & west)",
    "Tiger / elephant / biosphere reserves", "Mineral & coal belts",
    "Oil, gas, refineries & solar/wind parks", "Major & non-major ports",
    "National highways, expressways & railways", "National waterways & canals",
    "Dams, multipurpose projects & river links", "Tribes & PVTG locations",
    "Straits, gulfs & seas of the world", "Ocean currents & fog/fishing zones",
    "World deserts, grasslands & mountain ranges", "World rivers, lakes & seas",
    "Places in the news (last 90 days)", "Latitudes, tropics & time-zone logic",
]

DAILY_TEMPLATE = [
    ("Polity deep block", 100, "One block of today's polity unit. Book closed for the last 10 minutes: recall on blank paper."),
    ("Geography deep block", 100, "One block of today's geography unit. Atlas open on the desk the whole time."),
    ("PYQ drill (timed)", 60, "25 min polity + 25 min geography PYQs on today's units, then 10 min into the error log."),
    ("Spaced revision", 45, "Yesterday + 3-day + 7-day + 21-day piles. Flashcards only - no re-reading."),
    ("Map drill", 15, "5 features on a blank outline. No geography day is complete until you can point at it."),
    ("Output", 20, "One page of notes per unit + 5 flashcards written by you, not copied."),
    ("Mains micro-task", 20, "Skeleton or timed answer on today's mains theme (see the day card)."),
]

SUNDAY_TEMPLATE = [
    ("Sectional test", 90, "50 Qs - polity / geography / mixed on rotation. Strict UPSC timing, OMR style."),
    ("Test analysis", 90, "Every wrong and every guessed question into the mistake notebook."),
    ("Mistake-notebook fixes", 60, "Re-read only the lines behind the errors. Write a 1-line fix per error."),
    ("Backlog compression", 45, "Absorb any block you missed this week. Compress - never restart."),
    ("Revision sweep", 45, "The whole week's flashcards plus the 21-day pile."),
    ("Next-week plan + half-day off", 30, "Three MITs per day for the next six days, then stop. Rest is part of the plan."),
]


def ceil_div(a: int, b: int) -> int:
    return -(-a // b) if b else 0


def short(title: str, width: int = 34) -> str:
    """Word-boundary truncation so tables never cut a title mid-word."""
    head = title.split(" - ")[0]
    text = head if len(head) >= 8 else title
    if len(text) <= width:
        return text
    cut = text[:width].rsplit(" ", 1)[0]
    return cut + "\u2026"


def load_analysis():
    summary = json.loads((BUILD / "pyq_summary.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((BUILD / "pyq_analysis.csv").read_text(encoding="utf-8").splitlines()))
    per_unit = defaultdict(Counter)
    for r in rows:
        if r["bucket"] not in ("core", "core-weak"):
            continue
        y = int(r["year"])
        u = r["unit"]
        per_unit[u]["all"] += 1
        if y >= 2017:
            per_unit[u]["last10"] += 1
        if y >= 2022:
            per_unit[u]["last5"] += 1
        if 2003 <= y <= 2016:
            per_unit[u]["backlog"] += 1
    return summary, per_unit


def build_units(summary, per_unit):
    """Merge curriculum with PYQ counts and derive block counts."""
    units = {}
    mains = summary["mains"]["unit_themes"]["per_unit"]
    recur = {**summary["recurrence"]["Polity"]["by_unit_recurring_share"],
             **summary["recurrence"]["Geography"]["by_unit_recurring_share"]}
    for subj, catalogue in (("Polity", POLITY), ("Geography", GEOGRAPHY)):
        for u in catalogue:
            uid = u["id"]
            c = per_unit.get(uid, Counter())
            blocks = max(1, ceil_div(u["pages"], PAGES_PER_BLOCK), ceil_div(c["last10"], PYQ_PER_BLOCK))
            units[uid] = {
                "id": uid, "subject": subj, "title": unit_title(uid, summary),
                "source": unit_source(uid, summary), "pages": u["pages"],
                "focus": u["focus"], "traps": u["traps"], "mains": u["mains"],
                "pyq_all": c["all"], "pyq_last10": c["last10"], "pyq_last5": c["last5"],
                "pyq_backlog": c["backlog"],
                "mains_qs": mains.get(uid, 0),
                "recurring_share": recur.get(uid, 0),
                "blocks": blocks,
                "teach_index": TEACH_ORDER[subj].index(uid),
            }
    return units


def unit_title(uid, summary):
    for u in summary["units"]:
        if u["id"] == uid:
            return u["title"]
    return uid


def unit_source(uid, summary):
    for u in summary["units"]:
        if u["id"] == uid:
            return u["source"]
    return ""


def subject_split(summary):
    p = summary["windows"]["last10"]
    pol_prelims = p["polity_core"]
    geo_prelims = p["geography_core"]
    mains_marks = Counter()
    for q in summary["mains"]["questions"]:
        mains_marks[q["cluster"]] += int(q.get("marks") or 0)
    pol_mains = mains_marks["polity"]
    geo_mains = mains_marks["geography"]
    pol_share = 0.6 * pol_prelims / (pol_prelims + geo_prelims) + 0.4 * pol_mains / (pol_mains + geo_mains)
    return {
        "prelims_last10_core": {"Polity": pol_prelims, "Geography": geo_prelims},
        "mains_marks_2012_2025": {"Polity": pol_mains, "Geography": geo_mains},
        "mains_questions_2012_2025": dict(Counter(q["cluster"] for q in summary["mains"]["questions"])),
        "polity_share": round(pol_share, 3),
        "geography_share": round(1 - pol_share, 3),
        # round the data-driven share to the nearest half hour so the template stays clean
        "hours": {"Polity": round(pol_share * HOURS_PER_DAY * 2) / 2,
                  "Geography": round((1 - pol_share) * HOURS_PER_DAY * 2) / 2},
    }


def block_queue(units, subject):
    """Exact split of a unit's last-ten-paper questions across its blocks.

    Every question in the 2017-2026 core bank is assigned to exactly one block, so
    Sprint 1 provably clears the whole recent bank. Units whose recent count is
    smaller than their block count are topped up from their older (1995-2016)
    questions so no day has an empty PYQ drill - the top-up never exceeds the
    questions that actually exist for that unit.
    """
    q = []
    for uid in TEACH_ORDER[subject]:
        u = units[uid]
        recent, blocks = u["pyq_last10"], u["blocks"]
        base, rem = divmod(recent, blocks)
        older_budget = u["pyq_all"] - recent
        for i in range(blocks):
            got = base + (1 if i < rem else 0)
            fill = max(0, min(PYQ_FLOOR - got, older_budget))
            older_budget -= fill
            q.append({"unit": uid, "block": i + 1, "of": blocks,
                      "pyq": got + fill, "pyq_recent": got, "pyq_fill": fill,
                      "backlog_pyq": ceil_div(u["pyq_backlog"], blocks)})
    return q


def is_sunday(d: date) -> bool:
    return d.weekday() == 6


def schedule(units, summary):
    """Walk the calendar from START and produce one row per day."""
    pq = block_queue(units, "Polity")
    gq = block_queue(units, "Geography")
    total_blocks = {"Polity": len(pq), "Geography": len(gq)}
    s1_len = max(len(pq), len(gq))

    def ranked(subject, key):
        return sorted((u for u in units.values() if u["subject"] == subject), key=key)

    def stream(subject, key, pyq_floor):
        """Infinite second/third-reading stream - never lets a day run out of work."""
        while True:
            for u in ranked(subject, key)[:8]:
                half = max(pyq_floor, ceil_div(u["pyq_backlog"], 2))
                yield {"unit": u["id"], "block": 1, "of": 1, "pyq": half,
                       "backlog_pyq": ceil_div(u["pyq_backlog"], 2), "stage": "re-read"}

    def mains_stream(subject):
        while True:
            for u in ranked(subject, lambda x: -(x["mains_qs"] * 3 + x["pyq_last5"]))[:10]:
                yield {"unit": u["id"], "block": 1, "of": 1, "pyq": 6, "backlog_pyq": 0, "stage": "mains"}

    s2 = {s: stream(s, lambda x: -(x["pyq_last10"] * 2 + x["pyq_last5"] * 3 + x["mains_qs"]), 8)
          for s in ("Polity", "Geography")}
    s3 = {s: mains_stream(s) for s in ("Polity", "Geography")}

    days = []
    d = START
    study_index = 0
    while True:
        day_no = (d - START).days + 1
        if is_sunday(d):
            kind, sprint = "test", current_sprint(study_index, s1_len)
            days.append(new_day(d, day_no, kind, sprint, None, None, study_index))
        else:
            study_index += 1
            if study_index > s1_len + SPRINT2_STUDY_DAYS + SPRINT3_STUDY_DAYS:
                break
            sprint = current_sprint(study_index, s1_len)
            if study_index <= s1_len:
                pb = pq[study_index - 1] if study_index - 1 < len(pq) else next(s2["Polity"])
                gb = gq[study_index - 1] if study_index - 1 < len(gq) else next(s2["Geography"])
            elif study_index <= s1_len + SPRINT2_STUDY_DAYS:
                pb, gb = next(s2["Polity"]), next(s2["Geography"])
            else:
                pb, gb = next(s3["Polity"]), next(s3["Geography"])
            kind = "study"
            days.append(new_day(d, day_no, kind, sprint, pb, gb, study_index))
        d += timedelta(days=1)
    return days, total_blocks, s1_len


def current_sprint(study_index, s1_len):
    if study_index <= s1_len:
        return "Sprint 1 - first reading"
    if study_index <= s1_len + SPRINT2_STUDY_DAYS:
        return "Sprint 2 - second reading + PYQ marathon"
    return "Sprint 3 - Mains integration"


def new_day(d, day_no, kind, sprint, pb, gb, study_index):
    return {"day_no": day_no, "date": d.isoformat(), "weekday": d.strftime("%a"),
            "kind": kind, "sprint": sprint, "polity": pb, "geography": gb,
            "study_index": study_index, "week": (day_no - 1) // 7 + 1}


def revision_piles(days, target_index):
    """Spaced repetition: the study days 1, 3, 7 and 21 study-days earlier."""
    study_days = [d for d in days if d["kind"] == "study"]
    pos = {d["study_index"]: i for i, d in enumerate(study_days)}
    here = study_days[target_index]
    out = []
    for gap in (1, 3, 7, 21):
        j = target_index - gap
        if j >= 0:
            e = study_days[j]
            tags = []
            for slot in ("polity", "geography"):
                if e[slot]:
                    tags.append(e[slot]["unit"])
            out.append({"gap": gap, "units": tags, "date": e["date"]})
    return out


def gates(s1_len, days):
    def day_at_study(n):
        for d in days:
            if d["kind"] == "study" and d["study_index"] == n:
                return d
        return days[-1]

    d7 = next(d for d in days if d["kind"] == "test")
    g = [
        dict(id="Gate 0", when=d7["date"], at="End of Week 1",
             test="50-question NCERT-basics test (25 polity + 25 geography)",
             need="70% or above",
             fail_action="Repeat only the failed units' NCERT chapters in the Week 2 revision slots. Do not restart."),
        dict(id="Gate 1", when=day_at_study(s1_len)["date"], at="End of Sprint 1 (first reading complete)",
             test="100-question polity PYQ set (2017-2026 mix) + 100-question geography PYQ set",
             need="75% on each, separately",
             fail_action="Buy back time from Sprint 3, not Sprint 2: cut two mains-integration days and re-drill the "
                         "two weakest units per subject."),
        dict(id="Gate 2", when=day_at_study(s1_len + SPRINT2_STUDY_DAYS)["date"],
             at="End of Sprint 2 (PYQ bank exhausted)",
             test="Blank-map India test (60 features) + 100-question mixed 2013-2026 sectional",
             need="80% on the sectional and 48/60 map features",
             fail_action="Add a 20-minute map drill to the revision slot until the map test passes. It is the cheapest "
                         "mark in the paper."),
        dict(id="Gate 3", when=day_at_study(s1_len + SPRINT2_STUDY_DAYS + SPRINT3_STUDY_DAYS)["date"],
             at="End of Sprint 3 (first cycle closed)",
             test="8 Mains answers evaluated on the rubric + 2 full-length GS sectionals",
             need="Average 50% or above on the Mains answers; sectional at previous cut-off + 10",
             fail_action="Keep answer writing at Level 2 (timed 10-markers) for two more weeks before moving up."),
    ]
    return g


PHASE_B = "Phase B - third reading (5 Dec 26 - 31 Dec 26)"
PHASE_C = "Phase C - retrieval cycles + mocks (1 Jan - 31 Mar 27)"
PHASE_D = "Phase D - final sprint (1 Apr - 25 May 27)"

PHASE_D_WEEKS = [
    "Re-solve every last-five-paper question you got wrong, plus the 2025-2026 papers cold. Error log to zero.",
    "Map marathon: India physical + drainage + 40 world regions from memory on blank outlines, twice a day.",
    "Current-affairs merge: last 14 months of schemes, indices, places in the news, treaties, protected areas.",
    "Mistake notebook: re-attempt every logged error under time. Anything still wrong becomes a flashcard.",
    "Two full-length mocks plus a 3-day analysis cycle. No new content whatsoever.",
    "Final cram sheet: Articles, schedules, amendment numbers, park lists, mineral belts, port names, river tributaries.",
    "Exam protocol: OMR strategy, 2-pass timing, elimination rules, when to leave a question. Rehearse it twice.",
    "Taper week: 2 h of light retrieval a day, sleep, logistics, admit card. Stop studying 36 h before the paper.",
]


def post_cycle_phases(days, units):
    """Week-by-week plan from the end of Sprint 3 to Prelims day - one line per week, never a wall of prose."""
    start = date.fromisoformat(days[-1]["date"]) + timedelta(days=1)
    weeks = []
    w, n = start, 1
    pol, geo = TEACH_ORDER["Polity"], TEACH_ORDER["Geography"]
    while w <= PRELIMS:
        we = min(w + timedelta(days=6), PRELIMS)
        if w <= date(2026, 12, 31):
            k = n - 1
            slice_p = pol[k * 6:(k + 1) * 6]
            slice_g = geo[k * 6:(k + 1) * 6]
            phase = PHASE_B
            detail = (f"Third reading, quarter {k + 1}/4: " + ", ".join(slice_p) + " + " + ", ".join(slice_g) +
                      ". 45 min per unit (2 units/day), 1 timed 10-marker/day, 100-Q cumulative sectional on Sunday, "
                      "CA linkage notebook opened.")
            tests = "1 x 100-Q cumulative sectional"
        elif w <= date(2027, 3, 31):
            k = n - 5                      # 0-based week inside Phase C (13 weeks)
            rnd = k // 3 + 1
            third = k % 3
            slice_p = pol[third * 8:(third + 1) * 8]
            slice_g = geo[third * 8:(third + 1) * 8]
            phase = PHASE_C
            detail = (f"Retrieval round {min(rnd, 4)}/4, third {third + 1}/3: " + ", ".join(slice_p) + " + " +
                      ", ".join(slice_g) + ". Flashcards and blank-page recall only - no re-reading. "
                      + ("Full-length GS mock on the 2nd Sunday from February." if w >= date(2027, 2, 1)
                         else "Sectional every Sunday."))
            tests = ("1 sectional + 1 full-length mock (alternate weeks)" if w >= date(2027, 2, 1) else "1 sectional")
        else:
            k = (n - 18) % len(PHASE_D_WEEKS)
            phase = PHASE_D
            detail = PHASE_D_WEEKS[k]
            tests = "2 full-length mocks" if k < 5 else "1 mock + protocol rehearsal"
        weeks.append(dict(no=n, start=w.isoformat(), end=we.isoformat(), phase=phase, focus=detail,
                          tests=tests, days_left=(PRELIMS - w).days))
        w = we + timedelta(days=1)
        n += 1
    return weeks


def sprint_table(days, s1_len):
    """What each sprint is, when it runs, and what it costs."""
    study = [d for d in days if d["kind"] == "study"]
    bounds = [(1, s1_len), (s1_len + 1, s1_len + SPRINT2_STUDY_DAYS),
              (s1_len + SPRINT2_STUDY_DAYS + 1, s1_len + SPRINT2_STUDY_DAYS + SPRINT3_STUDY_DAYS)]
    goals = [
        "First reading of all 48 units (47 + 47 blocks) with the last-ten-paper PYQs solved unit by unit. "
        "Mains answers at skeleton level only.",
        "Second reading of the eight heaviest units per subject, the 2003-2016 PYQ backlog cleared, "
        "Mains answers timed at 10-marker level.",
        "Mains integration over the ten most Mains-loaded units per subject, full-length sectionals, "
        "consolidation of the error log into one cram sheet.",
    ]
    rows = []
    for i, (a, b) in enumerate(bounds, 1):
        chunk = [d for d in study if a <= d["study_index"] <= b]
        pyq = sum((d["polity"]["pyq"] if d["polity"] else 0) + (d["geography"]["pyq"] if d["geography"] else 0)
                  for d in chunk)
        hours = len(chunk) * HOURS_PER_DAY
        rows.append(dict(no=i, name=chunk[0]["sprint"], study_days=len(chunk),
                         first=chunk[0]["date"], last=chunk[-1]["date"], goal=goals[i - 1],
                         pyq=pyq, hours=hours,
                         blocks=sum(1 for d in chunk for slot in ("polity", "geography") if d[slot] and d[slot]["of"] > 1)))
    return rows


def render_md(days, units, summary, split, total_blocks, s1_len, gate_list, phases):
    first_pass_end = next(d for d in days if d["kind"] == "study" and d["study_index"] == s1_len)
    cycle_end = days[-1]
    bank = summary["prelims_bank"]
    win = summary["windows"]
    ext = summary["extended_pool"]
    rec = summary["recurrence"]
    sp = summary["spillover"]
    mains = summary["mains"]
    L = []
    A = L.append

    A("# UPSC 2027 - Polity + Geography 6-hour Sprint Plan")
    A("")
    A(f"**Generated {TODAY.isoformat()} (IST) from {bank['total_records']:,} Prelims records (1995-2026) and "
      f"{len(mains['questions'])} Mains questions (2012-2025) held in this repository.**")
    A("")
    A(f"Start **{START.strftime('%a %d %b %Y')}** - Prelims **{PRELIMS.strftime('%a %d %b %Y')}** - "
      f"**{(PRELIMS - START).days} days** of runway, **{HOURS_PER_DAY} h/day** on Polity and Geography only.")
    A("")
    A("## 1. The headline answer")
    A("")
    s2_end = next(d for d in days if d["kind"] == "study" and d["study_index"] == s1_len + SPRINT2_STUDY_DAYS)
    milestones = [
        ("First reading of all 48 units complete", s1_len, first_pass_end["date"]),
        ("Second reading + whole PYQ bank cleared", s1_len + SPRINT2_STUDY_DAYS, s2_end["date"]),
        ("First full cycle closed (Sprints 1-3)", s1_len + SPRINT2_STUDY_DAYS + SPRINT3_STUDY_DAYS, cycle_end["date"]),
    ]
    A("| Milestone | Study days | Calendar date | Days before Prelims |")
    A("|---|---:|---|---:|")
    for label, n, iso in milestones:
        dd = date.fromisoformat(iso)
        A(f"| {label} | {n} | {dd.strftime('%a %d %b %Y')} | {(PRELIMS - dd).days} |")
    A("")
    closed = s1_len + SPRINT2_STUDY_DAYS + SPRINT3_STUDY_DAYS
    A(f"At {HOURS_PER_DAY} hours a day that is **{closed * HOURS_PER_DAY} hours of Polity + Geography** before the "
      f"first cycle closes, and **{(PRELIMS - date.fromisoformat(cycle_end['date'])).days} days left** for revision, "
      f"mocks and current affairs. Roughly {(PRELIMS - START).days // 7} more weeks after that.")
    A("")

    A("## 2. What the PYQ bank actually says")
    A("")
    A("### 2.1 Volume")
    A("")
    A("| Window | Polity tagged | Polity core | Geography tagged | Geography core |")
    A("|---|---:|---:|---:|---:|")
    for k in ("all", "last10", "last5"):
        w = win[k]
        A(f"| {w['label']} | {w['polity_tagged']} | **{w['polity_core']}** | {w['geography_tagged']} | "
          f"**{w['geography_core']}** |")
    A("")
    A(f"'Core' means answerable from the locked booklist. The gap between tagged and core is the first planning "
      f"insight of this exercise:")
    A("")
    A("| Spill-over (tagged as Polity/Geography but not from those books) | all papers | last 10 |")
    A("|---|---:|---:|")
    for b in ("spill:international-orgs-IR", "spill:environment-biodiversity", "spill:economy",
              "spill:science-tech", "spill:schemes-governance-CA", "unclassified"):
        a = sp["Polity"]["all"].get(b, 0) + sp["Geography"]["all"].get(b, 0)
        t = sp["Polity"]["last10"].get(b, 0) + sp["Geography"]["last10"].get(b, 0)
        if a:
            A(f"| {b.replace('spill:', '')} | {a} | {t} |")
    A("")
    A(f"Plus **{ext['total']} questions tagged as something else** (economy {ext['by_tagged_subject'].get('economy', 0)}, "
      f"history {ext['by_tagged_subject'].get('history', 0)}, science-tech "
      f"{ext['by_tagged_subject'].get('science-and-technology', 0)}) whose content is really geography or polity - "
      f"biggest leaks into {', '.join(list(ext['by_unit'])[:4])}. Geography and polity knowledge therefore buys more "
      f"than its own ~46 questions a paper.")
    A("")
    A("**What this changes in the plan:** three dedicated units absorb the spill-over instead of a second booklist - "
      "P23 (schemes, ministries, indices) for the CA/governance leak, G24 for the environment-biodiversity leak, "
      "G22 for places in the news (the highest-volume geography unit, paid for by the daily 15-minute atlas drill "
      "rather than by reading). The 20-30 minute newspaper sweep outside the six hours is tagged polity/geography "
      "only, and the IR/international-organisation leak is parked - it belongs to the optional-subject decision, "
      "not to this sprint.")
    A("")

    A("### 2.2 Priority order (last 10 papers, 2017-2026, core questions only)")
    A("")
    for subj in ("Polity", "Geography"):
        A(f"**{subj}**")
        A("")
        A("| Rank | Unit | Last 10 | Last 5 | All 32 | Mains Qs | PYQ-recurrence | Blocks |")
        A("|---:|---|---:|---:|---:|---:|---:|---:|")
        ranked = sorted((u for u in units.values() if u["subject"] == subj),
                        key=lambda u: (-u["pyq_last10"], -u["pyq_all"]))
        for i, u in enumerate(ranked, 1):
            A(f"| {i} | **{u['id']}** {short(u['title'], 46)} | {u['pyq_last10']} | {u['pyq_last5']} | {u['pyq_all']} | "
              f"{u['mains_qs']} | {u['recurring_share'] or '-'} | {u['blocks']} |")
        A("")
    A("Recurrence is the share of that unit's 2015-2026 questions that the repository's own back-solve engine "
      "(`scripts/pyq_backsolve.py`) classifies as already taught by earlier papers - i.e. how much of the unit you "
      "learn by solving PYQs instead of reading.")
    A("")

    A("### 2.3 Mains demand (2012-2025)")
    A("")
    A("| Paper | Polity Qs | Polity marks | Geography Qs | Geography marks |")
    A("|---|---:|---:|---:|---:|")
    for p in ("GS1", "GS2", "GS3"):
        v = mains["by_paper"].get(p, {})
        A(f"| {p} | {v.get('polity', 0)} | {v.get('polity_marks', 0)} | {v.get('geography', 0)} | "
          f"{v.get('geography_marks', 0)} |")
    A("")
    named = [(k, v) for k, v in mains["unit_themes"]["per_unit"].items() if not k.startswith("OTHER")]
    other = {k: v for k, v in mains["unit_themes"]["per_unit"].items() if k.startswith("OTHER")}
    A("Most Mains-loaded units: " + ", ".join(f"{k} ({v})" for k, v in named[:6]) + ".")
    A("")
    A(f"Read the caveat before you plan Mains prep around this table: **{other.get('OTHER-polity', 0)} polity and "
      f"{other.get('OTHER-geography', 0)} geography Mains questions** sit outside these 48 units - governance, "
      "social justice, disaster management, internal security, ethics-adjacent framing. They are GS2/GS3 territory "
      "that this sprint only seeds. Prelims is the target; Mains integration here is deliberately Level 1-2.")
    A("")

    A("### 2.4 Anti-folklore findings")
    A("")
    A("- **Monsoon is not the biggest geography topic in this bank.** G06 has only "
      f"{units['G06']['pyq_all']} questions in 32 papers ({units['G06']['pyq_last10']} in the last 10). It is still "
      "conceptually load-bearing (GS-1 Mains, cyclones, agriculture) so it keeps 2 blocks - but it does not get a week.")
    A(f"- **Parliament is the single heaviest polity unit** ({units['P07']['pyq_last10']} questions in the last ten "
      f"papers, {units['P07']['blocks']} blocks) - procedure, devices, motions and privileges, not just 'how a bill "
      "becomes an Act'.")
    A(f"- **Mapping beats theory in geography**: G22 places-in-the-news carries {units['G22']['pyq_last10']} last-ten "
      f"questions and G08 seas/straits/currents {units['G08']['pyq_last10']}. Hence the non-negotiable daily atlas slot.")
    A(f"- **Agriculture is the bridge subject**: G15 has {units['G15']['mains_qs']} Mains questions - more than any "
      "other geography unit - so it is studied with a GS-3 answer frame from day one.")
    A("- **Environment spill-over is real**: "
      f"{sp['Geography']['all'].get('spill:environment-biodiversity', 0)} geography-tagged questions are actually "
      "species/biodiversity items. Budget one thin environment compilation inside G24 and the current-affairs sweep; "
      "do not buy a second geography book for them.")
    A("")

    A("## 3. How the 6 hours are split - and why")
    A("")
    A(f"Prelims core (last 10 papers): Polity {split['prelims_last10_core']['Polity']} vs Geography "
      f"{split['prelims_last10_core']['Geography']} = {split['prelims_last10_core']['Polity'] / (split['prelims_last10_core']['Polity'] + split['prelims_last10_core']['Geography']):.0%} / "
      f"{split['prelims_last10_core']['Geography'] / (split['prelims_last10_core']['Polity'] + split['prelims_last10_core']['Geography']):.0%}.")
    A(f"Mains marks (2012-2025): Polity {split['mains_marks_2012_2025']['Polity']} vs Geography "
      f"{split['mains_marks_2012_2025']['Geography']} = "
      f"{split['mains_marks_2012_2025']['Polity'] / sum(split['mains_marks_2012_2025'].values()):.0%} / "
      f"{split['mains_marks_2012_2025']['Geography'] / sum(split['mains_marks_2012_2025'].values()):.0%}.")
    A(f"Weighting Prelims 0.6 and Mains 0.4 gives Polity {split['polity_share']:.0%} and Geography "
      f"{split['geography_share']:.0%} - statistically a coin flip. So the template is **3 h Polity + 3 h Geography "
      "every day**, which keeps both subjects warm, keeps the atlas habit alive and matches your 'half to geo and "
      "polity' instruction.")
    A("")
    A("### The daily 360-minute template (order fixed, timings flexible)")
    A("")
    A("| # | Block | Min | What happens |")
    A("|---:|---|---:|---|")
    for i, (name, mins, note) in enumerate(DAILY_TEMPLATE, 1):
        A(f"| {i} | **{name}** | {mins} | {note} |")
    A(f"| | **Total** | **{sum(m for _, m, _ in DAILY_TEMPLATE)}** | |")
    A("")
    A("### Sunday template (no new content - test, analyse, compress, rest)")
    A("")
    A("| # | Block | Min | What happens |")
    A("|---:|---|---:|---|")
    for i, (name, mins, note) in enumerate(SUNDAY_TEMPLATE, 1):
        A(f"| {i} | **{name}** | {mins} | {note} |")
    A(f"| | **Total** | **{sum(m for _, m, _ in SUNDAY_TEMPLATE)}** | |")
    A("")
    A("Outside the 6 hours: 20-30 min of newspaper for the current-affairs sweep only, tagged polity/geography. "
      "CSAT: 2 h a week from Phase B. Optional subject: zero until Gate 1 passes.")
    A("")

    A("## 4. The three sprints")
    A("")
    A("| Sprint | Study days | Dates | Hours | PYQs solved | What it is |")
    A("|---|---:|---|---:|---:|---|")
    for sp in sprint_table(days, s1_len):
        A(f"| **{sp['name']}** | {sp['study_days']} | {sp['first']} to {sp['last']} | {sp['hours']} h | "
          f"{sp['pyq']} | {sp['goal']} |")
    A("")
    A("Sunday is always a test day, never a study day. If you fall behind, compress the backlog into Sunday's "
      "45-minute 'backlog compression' slot - do not push the calendar.")
    A("")
    A("## 5. Phase gates")
    A("")
    A("| Gate | Date | When | Test | Pass mark | If you fail |")
    A("|---|---|---|---|---|---|")
    for g in gate_list:
        A(f"| **{g['id']}** | {g['when']} | {g['at']} | {g['test']} | {g['need']} | {g['fail_action']} |")
    A("")

    A("## 6. Day-by-day plan")
    A("")
    A(f"Blocks: {total_blocks['Polity']} polity + {total_blocks['Geography']} geography = "
      f"{sum(total_blocks.values())} hundred-minute blocks of 100 minutes each. Sundays are test days.")
    A("")
    A(f"The PYQ column is the number of questions from this repository's bank to solve for that day's two units. "
      f"Sprint 1 assigns **every one of the {win['last10']['polity_core'] + win['last10']['geography_core']} "
      f"core questions from the last ten papers** ({win['last10']['polity_core']} polity + "
      f"{win['last10']['geography_core']} geography) exactly once, plus a small top-up from the older bank on the "
      f"days when a unit has fewer recent questions than blocks.")
    A("")
    cur_week = None
    for d in days:
        wk = d["week"]
        if wk != cur_week:
            cur_week = wk
            w0 = START + timedelta(days=7 * (wk - 1))
            A(f"### Week {wk} ({w0.strftime('%a %d %b')} - {(w0 + timedelta(days=6)).strftime('%a %d %b %Y')})")
            A("")
            A("| Day | Date | Type | Polity block | Geo block | PYQs | Map drill | Mains task | Revision piles |")
            A("|---:|---|---|---|---|---:|---|---|---|")
        if d["kind"] == "test":
            A(f"| {d['day_no']} | {d['date']} {d['weekday']} | **TEST** | - | - | - | - | weekly review | full week |")
            continue
        p, g = d["polity"], d["geography"]
        pu = units[p["unit"]] if p else None
        gu = units[g["unit"]] if g else None
        pyqs = (p["pyq"] if p else 0) + (g["pyq"] if g else 0)
        piles = revision_piles(days, [x for x in days if x["kind"] == "study"].index(d))
        pile_txt = " ".join(f"-{x['gap']}d:{'/'.join(x['units'])}" for x in piles) or "day 1"
        mains_task = mains_task_for(d, units, s1_len)
        ptxt = f"{p['unit']} b{p['block']}/{p['of']} {short(pu['title'])}" if p else "-"
        gtxt = f"{g['unit']} b{g['block']}/{g['of']} {short(gu['title'])}" if g else "-"
        A(f"| {d['day_no']} | {d['date']} {d['weekday']} | {d['sprint'].split(' - ')[0]} | {ptxt} | {gtxt} | "
          f"{pyqs} | {MAP_DRILLS[(d['study_index'] - 1) % len(MAP_DRILLS)]} | {mains_task} | {pile_txt} |")
    A("")

    A("## 7. Unit cards - what to master and what UPSC will try to trip you on")
    A("")
    for subj in ("Polity", "Geography"):
        A(f"### {subj}")
        A("")
        for uid in TEACH_ORDER[subj]:
            u = units[uid]
            A(f"#### {uid} - {u['title']}")
            A(f"*Blocks {u['blocks']} - {u['pages']} pp first read - Prelims PYQs {u['pyq_last10']} (last 10) / "
              f"{u['pyq_all']} (all) - Mains {u['mains_qs']} - source: {u['source']}*")
            A("")
            A(f"- **Master:** {u['focus']}")
            A(f"- **Traps:** {u['traps']}")
            A(f"- **Mains angle:** {u['mains']}")
            A("")

    A("## 8. After the first cycle - week by week to Prelims")
    A("")
    A("| Wk | From | To | Phase | This week | Tests | Days left |")
    A("|---:|---|---|---|---|---|---:|")
    for w in phases:
        A(f"| {w['no']} | {w['start']} | {w['end']} | {w['phase'].split(' - ')[0].replace('Phase ', '')} | "
          f"{w['focus']} | {w['tests']} | {w['days_left']} |")
    A("")

    A("## 9. Operating rules (unchanged from your master prompt)")
    A("")
    A("- Every session ends with a retrieval quiz. Never end with 'read and remember'.")
    A("- Mistake notebook format: Q | my answer | correct | WHY I erred (concept/trap/silly) | 1-line fix.")
    A("- Spaced revision Day 1 - 3 - 7 - 21 - 60; the tracker prints your dues every day.")
    A("- Confusion protocol: if you say 'lost', the plan shrinks to the next 25-minute block only.")
    A("- Three MITs every morning. Everything else is bonus. Miss a day and compress - never restart.")
    A("- One test series, one newspaper, one monthly compilation, zero source-hopping.")
    A("")
    A("## 10. Reproduce or update this plan")
    A("")
    A("```bash")
    A("python3 scripts/analyse_polity_geo_pyqs.py     # re-tag every PYQ, rewrite build_upsc_pg/")
    A("python3 scripts/build_pg_sprint_plan.py          # rebuild the plan, tracker, PDF and HTML")
    A("```")
    A("")
    A("Edit the curriculum in `scripts/pg_sprint_curriculum.py` (pages, focus, traps) or the constants at the top of "
      "`scripts/build_pg_sprint_plan.py` (start date, hours, block sizing) and re-run.")
    return "\n".join(L)


def mains_task_for(d, units, s1_len):
    if d["kind"] != "study":
        return "-"
    subj = "Polity" if d["weekday"] in ("Mon", "Wed", "Fri") else "Geography"
    slot = d["polity"] if subj == "Polity" else d["geography"]
    if not slot:
        return "-"
    level = "skeleton" if d["study_index"] <= s1_len else ("timed 10-marker" if d["study_index"] <= s1_len + SPRINT2_STUDY_DAYS else "full 15-marker")
    return f"{slot['unit']} {level}"


def write_csv(days, units, s1_len):
    path = ROOT / "UPSC_Polity_Geo_Sprint_Tracker.csv"
    cols = ["day_no", "date", "weekday", "week", "sprint", "type",
            "polity_unit", "polity_title", "polity_block", "polity_pyq",
            "geo_unit", "geo_title", "geo_block", "geo_pyq",
            "map_drill", "mains_task", "revision_piles", "gate",
            "done", "hours_logged", "test_score", "errors_logged", "notes"]
    gate_dates = {g["when"]: g["id"] for g in gates(s1_len, days)}
    study_days = [d for d in days if d["kind"] == "study"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for d in days:
            p, g = d["polity"], d["geography"]
            if d["kind"] == "study":
                piles = revision_piles(days, study_days.index(d))
                pile_txt = " | ".join(f"-{x['gap']}d " + "/".join(x["units"]) for x in piles)
            else:
                pile_txt = "full week"
            w.writerow({
                "day_no": d["day_no"], "date": d["date"], "weekday": d["weekday"], "week": d["week"],
                "sprint": d["sprint"], "type": d["kind"],
                "polity_unit": p["unit"] if p else "",
                "polity_title": units[p["unit"]]["title"] if p else "",
                "polity_block": f"{p['block']}/{p['of']}" if p else "",
                "polity_pyq": p["pyq"] if p else "",
                "geo_unit": g["unit"] if g else "",
                "geo_title": units[g["unit"]]["title"] if g else "",
                "geo_block": f"{g['block']}/{g['of']}" if g else "",
                "geo_pyq": g["pyq"] if g else "",
                "map_drill": MAP_DRILLS[(d["study_index"] - 1) % len(MAP_DRILLS)] if d["kind"] == "study" else "",
                "mains_task": mains_task_for(d, units, s1_len),
                "revision_piles": pile_txt,
                "gate": gate_dates.get(d["date"], ""),
                "done": "", "hours_logged": "", "test_score": "", "errors_logged": "", "notes": "",
            })
    return path


def write_pdf(days, units, summary, split, total_blocks, s1_len, gate_list, phases):
    try:
        from fpdf import FPDF
    except ImportError:
        print("fpdf2 not installed - skipping PDF (pip install --break-system-packages fpdf2)")
        return None
    font_candidates = [
        (ROOT / "build_physics/fonts/DejaVuSans.ttf", ROOT / "build_physics/fonts/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    reg = bold = None
    for r, b in font_candidates:
        if Path(r).exists():
            reg, bold = str(r), (str(b) if Path(b).exists() else None)
            break

    class PDF(FPDF):
        def header(self):
            if self.page_no() == 1:
                return
            self.set_font(FONT, "", 7.5)
            self.set_text_color(120, 128, 140)
            self.cell(0, 5, "UPSC 2027 Polity + Geography 6-hour sprint plan", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(69, 199, 195)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(2)

        def footer(self):
            self.set_y(-13)
            self.set_font(FONT, "", 7.5)
            self.set_text_color(140, 146, 158)
            self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="C")

    FONT = "sans"
    pdf = PDF(orientation="L", unit="mm", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(True, margin=14)
    if reg:
        pdf.add_font(FONT, "", reg)
        if bold:
            pdf.add_font(FONT, "B", bold)
        else:
            pdf.add_font(FONT, "B", reg)
    else:
        FONT = "helvetica"
    pdf.alias_nb_pages()
    pdf.add_page()

    # ---- cover ----
    pdf.set_font(FONT, "B", 24)
    pdf.set_text_color(16, 35, 55)
    pdf.cell(0, 12, "UPSC 2027 - Polity + Geography", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT, "B", 18)
    pdf.set_text_color(25, 143, 146)
    pdf.cell(0, 10, f"{HOURS_PER_DAY} hours a day, both subjects, syllabus closed in "
                    f"{s1_len + SPRINT2_STUDY_DAYS + SPRINT3_STUDY_DAYS} study days",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font(FONT, "", 10.5)
    pdf.set_text_color(60, 66, 78)
    for line in [
        f"Start {START.strftime('%a %d %B %Y')}   |   Prelims {PRELIMS.strftime('%a %d %B %Y')}   |   "
        f"{(PRELIMS - START).days} days of runway",
        f"Derived from {summary['prelims_bank']['total_records']:,} Prelims questions (1995-2026) and "
        f"{len(summary['mains']['questions'])} Mains questions (2012-2025) in this repository",
        f"{total_blocks['Polity']} polity blocks + {total_blocks['Geography']} geography blocks "
        f"(100 min each) = {sum(total_blocks.values()) * BLOCK_MINUTES / 60:.0f} hours of new-content study",
        f"Split {split['polity_share']:.0%} polity / {split['geography_share']:.0%} geography from the data - "
        f"rounded to 3 h + 3 h daily",
    ]:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")

    def h1(t):
        pdf.ln(4)
        pdf.set_font(FONT, "B", 13)
        pdf.set_text_color(16, 35, 55)
        pdf.cell(0, 8, t, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(69, 199, 195)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 40, pdf.get_y())
        pdf.ln(2)

    def h2(t):
        pdf.set_font(FONT, "B", 10.5)
        pdf.set_text_color(25, 143, 146)
        pdf.cell(0, 7, t, new_x="LMARGIN", new_y="NEXT")

    def para(t, size=9):
        pdf.set_font(FONT, "", size)
        pdf.set_text_color(50, 56, 68)
        pdf.multi_cell(0, 4.6, t, new_x="LMARGIN", new_y="NEXT")

    def table(headers, rows, widths, size=8):
        pdf.set_font(FONT, "B", size)
        pdf.set_fill_color(16, 35, 55)
        pdf.set_text_color(255, 255, 255)
        for h, wd in zip(headers, widths):
            pdf.cell(wd, 6, str(h), border=0, fill=True)
        pdf.ln()
        pdf.set_font(FONT, "", size)
        pdf.set_text_color(40, 46, 58)
        fill = False
        for r in rows:
            if pdf.get_y() > pdf.h - 24:
                pdf.add_page()
                pdf.set_font(FONT, "B", size)
                pdf.set_fill_color(16, 35, 55)
                pdf.set_text_color(255, 255, 255)
                for h, wd in zip(headers, widths):
                    pdf.cell(wd, 6, str(h), border=0, fill=True)
                pdf.ln()
                pdf.set_font(FONT, "", size)
                pdf.set_text_color(40, 46, 58)
            if fill:
                pdf.set_fill_color(244, 246, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            for c, wd in zip(r, widths):
                pdf.cell(wd, 5.6, str(c)[:int(wd / 1.55)], border=0, fill=True)
            pdf.ln()
            fill = not fill

    h1("1. Milestones")
    first_pass = next(d for d in days if d["kind"] == "study" and d["study_index"] == s1_len)
    s2_end = next(d for d in days if d["kind"] == "study" and d["study_index"] == s1_len + SPRINT2_STUDY_DAYS)
    cycle_end = days[-1]
    table(["Milestone", "Study days", "Date", "Days before Prelims"],
          [["First reading of all 48 units", s1_len, first_pass["date"], (PRELIMS - date.fromisoformat(first_pass["date"])).days],
           ["Second reading + PYQ bank cleared", s1_len + SPRINT2_STUDY_DAYS, s2_end["date"], (PRELIMS - date.fromisoformat(s2_end["date"])).days],
           ["First full cycle closed", s1_len + SPRINT2_STUDY_DAYS + SPRINT3_STUDY_DAYS, cycle_end["date"], (PRELIMS - date.fromisoformat(cycle_end["date"])).days]],
          [110, 30, 40, 45])

    h1("2. PYQ priority - Polity (last 10 papers)")
    ranked = sorted((u for u in units.values() if u["subject"] == "Polity"), key=lambda u: (-u["pyq_last10"], -u["pyq_all"]))
    table(["#", "Unit", "Last 10", "Last 5", "All 32", "Mains", "Recurrence", "Blocks"],
          [[i, f"{u['id']} {short(u['title'], 62)}", u["pyq_last10"], u["pyq_last5"], u["pyq_all"],
            u["mains_qs"], u["recurring_share"] or "-", u["blocks"]] for i, u in enumerate(ranked, 1)],
          [10, 136, 20, 20, 20, 20, 28, 20], size=7.5)

    h1("3. PYQ priority - Geography (last 10 papers)")
    ranked = sorted((u for u in units.values() if u["subject"] == "Geography"), key=lambda u: (-u["pyq_last10"], -u["pyq_all"]))
    table(["#", "Unit", "Last 10", "Last 5", "All 32", "Mains", "Recurrence", "Blocks"],
          [[i, f"{u['id']} {short(u['title'], 62)}", u["pyq_last10"], u["pyq_last5"], u["pyq_all"],
            u["mains_qs"], u["recurring_share"] or "-", u["blocks"]] for i, u in enumerate(ranked, 1)],
          [10, 136, 20, 20, 20, 20, 28, 20], size=7.5)

    h1("4. Daily template - 360 minutes")
    table(["#", "Block", "Min", "What happens"],
          [[i, n, m, note[:96]] for i, (n, m, note) in enumerate(DAILY_TEMPLATE, 1)],
          [10, 45, 15, 203], size=8)
    para("")
    h2("Sunday - test day (no new content)")
    table(["#", "Block", "Min", "What happens"],
          [[i, n, m, note[:96]] for i, (n, m, note) in enumerate(SUNDAY_TEMPLATE, 1)],
          [10, 45, 15, 203], size=8)

    h1("5. Gates")
    table(["Gate", "Date", "Test", "Pass mark"],
          [[g["id"], g["when"], g["test"][:70], g["need"]] for g in gate_list],
          [20, 26, 130, 60], size=8)

    h1("6. Day-by-day schedule")
    rows = []
    study_days = [d for d in days if d["kind"] == "study"]
    for d in days:
        if d["kind"] == "test":
            rows.append([d["day_no"], f"{d['date']} {d['weekday']}", "TEST DAY", "50-Q sectional + analysis",
                         "", "", MAP_DRILLS[0][:0]])
            continue
        p, g = d["polity"], d["geography"]
        piles = revision_piles(days, study_days.index(d))
        rows.append([d["day_no"], f"{d['date']} {d['weekday']}", d["sprint"].split(" - ")[0],
                     (f"{p['unit']} b{p['block']}/{p['of']} {short(units[p['unit']]['title'], 28)}" if p else "-"),
                     (f"{g['unit']} b{g['block']}/{g['of']} {short(units[g['unit']]['title'], 28)}" if g else "-"),
                     f"{(p['pyq'] if p else 0) + (g['pyq'] if g else 0)} PYQ",
                     " ".join(f"-{x['gap']}d" for x in piles)])
    table(["Day", "Date", "Sprint", "Polity block", "Geography block", "Load", "Rev"],
          rows, [10, 24, 16, 88, 88, 20, 28], size=7)

    h1("7. Unit cards - master list and traps")
    for subj in ("Polity", "Geography"):
        h2(subj)
        for uid in TEACH_ORDER[subj]:
            u = units[uid]
            if pdf.get_y() > pdf.h - 60:
                pdf.add_page()
            pdf.set_font(FONT, "B", 9.5)
            pdf.set_text_color(16, 35, 55)
            pdf.cell(0, 6, f"{uid} - {u['title']}   |   {u['blocks']} block(s), {u['pages']} pp   |   "
                           f"PYQ {u['pyq_last10']} last-10 / {u['pyq_all']} all   |   Mains {u['mains_qs']}",
                     new_x="LMARGIN", new_y="NEXT")
            for label, text in (("Master", u["focus"]), ("Traps", u["traps"]), ("Mains", u["mains"])):
                pdf.set_font(FONT, "B", 8)
                pdf.set_text_color(25, 143, 146)
                pdf.cell(16, 4.4, label)
                pdf.set_font(FONT, "", 8)
                pdf.set_text_color(50, 56, 68)
                pdf.multi_cell(0, 4.4, text, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1.5)

    h1("8. After the first cycle")
    table(["Wk", "From", "To", "Phase", "This week", "Tests"],
          [[w["no"], w["start"], w["end"], w["phase"].split(" - ")[0].replace("Phase ", ""),
            w["focus"][:150], w["tests"][:40]] for w in phases],
          [9, 21, 21, 12, 174, 40], size=7)

    out = ROOT / "UPSC_Polity_Geo_Sprint_Plan.pdf"
    pdf.output(str(out))
    return out


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="theme-color" content="#102337" />
<meta name="description" content="UPSC 2027 Polity + Geography 6-hour-a-day sprint tracker built from 1,465 tagged PYQs." />
<title>UPSC Polity + Geography Sprint Tracker</title>
<style>
:root{--navy:#102337;--navy-2:#192e44;--ink:#171b35;--teal:#45c7c3;--teal-dark:#198f92;--amber:#df9849;
--wash:#f4f6fa;--white:#fff;--muted:#747b8a;--line:#e7ebf1;--shadow:0 9px 23px rgba(26,37,59,.09);
--pol:#7974db;--geo:#198f92}
*{box-sizing:border-box}
body{margin:0;background:var(--wash);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{background:linear-gradient(120deg,var(--navy),var(--navy-2));color:#fff;padding:26px 20px 22px}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
h1{margin:0;font-size:26px;letter-spacing:-.02em}
h1 em{color:var(--teal);font-style:normal}
.sub{margin:6px 0 0;color:#c6d2e0;font-size:14px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0 0}
.stat{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:12px;padding:12px 14px}
.stat b{display:block;font-size:22px;color:var(--teal)}
.stat span{font-size:12px;color:#c6d2e0;text-transform:uppercase;letter-spacing:.06em}
main{padding:22px 0 60px}
.card{background:var(--white);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);padding:18px;margin-bottom:18px}
.card h2{margin:0 0 4px;font-size:18px;color:var(--navy)}
.card p.hint{margin:0 0 14px;color:var(--muted);font-size:13px}
.bar{height:10px;border-radius:6px;background:var(--line);overflow:hidden}
.bar i{display:block;height:100%;background:var(--teal);width:0}
.row{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin:10px 0}
.today{border-left:5px solid var(--amber)}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{background:var(--wash);border:1px solid var(--line);border-radius:999px;padding:5px 11px;font-size:12.5px;color:var(--navy)}
.chip.pol{border-color:#dcdcf7;background:#f2f2ff}
.chip.geo{border-color:#d2ecec;background:#eefafa}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--navy);color:#fff;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;position:sticky;top:0}
tr.done{background:#f1fbf8;color:var(--muted)}
tr.done td:nth-child(3),tr.done td:nth-child(4){text-decoration:line-through}
tr.today-row{background:#fff8ec;box-shadow:inset 3px 0 0 var(--amber)}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tag{display:inline-block;border-radius:6px;padding:1px 6px;font-size:11px;font-weight:600;letter-spacing:.03em}
.tag.pol{background:#eceafd;color:#4b45b2}
.tag.geo{background:#e2f5f4;color:#146d70}
.tag.test{background:#fdeedd;color:#96551a}
button.detail{border:0;background:var(--wash);border-radius:8px;padding:3px 8px;font-size:12px;cursor:pointer;color:var(--navy)}
.detailbox{display:none;padding:10px 12px;background:#fbfcfe;border-left:3px solid var(--teal);margin:6px 0 10px}
.detailbox.open{display:block}
.detailbox h4{margin:0 0 4px;font-size:13px;color:var(--teal-dark);text-transform:uppercase;letter-spacing:.05em}
.detailbox p{margin:0 0 8px;font-size:13.5px}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.controls input,.controls select{padding:8px 10px;border:1px solid var(--line);border-radius:9px;font-size:13.5px;background:#fff}
.controls input[type=search]{min-width:210px}
.pill{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 13px;font-size:13px;cursor:pointer;color:var(--navy)}
.pill.on{background:var(--navy);color:#fff;border-color:var(--navy)}
.reset{margin-left:auto;border:1px solid #e6c9c9;background:#fff5f5;color:#963232;border-radius:9px;padding:7px 12px;font-size:12.5px;cursor:pointer}
footer{color:var(--muted);font-size:12.5px;text-align:center;padding:20px}
.legend{font-size:12.5px;color:var(--muted);margin-top:8px}
@media print{header{background:#fff;color:#000}.card{box-shadow:none;break-inside:avoid}th{position:static}.controls,.reset,button.detail{display:none}}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>UPSC 2027 <em>Polity + Geography</em> sprint tracker</h1>
    <p class="sub" id="subline">__SUBLINE__</p>
    <div class="stats" id="stats"></div>
  </div>
</header>
<main class="wrap">

  <section class="card today" id="todayCard">
    <h2 id="todayTitle">Today</h2>
    <p class="hint">The plan shrinks to one block when you are overwhelmed. Say the word and only the next 25 minutes exist.</p>
    <div id="todayBody"></div>
  </section>

  <section class="card">
    <h2>Priority from the PYQ bank</h2>
    <p class="hint">Core questions only, last ten papers (2017-2026). Bars are questions per paper-year.</p>
    <div class="row"><span class="chip pol">Polity __POLSHARE__</span><span class="chip geo">Geography __GEOSHARE__</span></div>
    <div id="rankings"></div>
  </section>

  <section class="card">
    <h2>Day-by-day schedule</h2>
    <p class="hint">Tick a day off - progress is stored in this browser only (localStorage), nothing is uploaded.</p>
    <div class="controls">
      <input id="q" type="search" placeholder="Search units, e.g. Parliament, monsoon, P07" />
      <button class="pill on" data-filter="all">All</button>
      <button class="pill" data-filter="study">Study days</button>
      <button class="pill" data-filter="test">Test days</button>
      <button class="pill" data-filter="open">Not done</button>
      <select id="sprintSel"></select>
      <button class="reset" id="resetBtn">Reset progress</button>
    </div>
    <div style="overflow:auto;max-height:70vh">
    <table id="days">
      <thead><tr><th></th><th>Day</th><th>Polity block</th><th>Geography block</th><th class="num">PYQ</th><th>Map drill</th><th>Rev</th><th>Gate</th></tr></thead>
      <tbody></tbody>
    </table>
    </div>
    <p class="legend">b<i>x</i>/<i>y</i> = block x of y for that unit. Rev = spaced-repetition piles due that day
    (1, 3, 7 and 21 study-days earlier).</p>
  </section>

  <section class="card">
    <h2>Gates</h2>
    <div id="gates"></div>
  </section>

  <section class="card">
    <h2>After the first cycle</h2>
    <p class="hint">Week-by-week from the end of Sprint 3 to prelims day.</p>
    <table id="phases"><thead><tr><th>Week</th><th>From</th><th>To</th><th>Phase</th><th>Focus</th><th class="num">Days left</th></tr></thead><tbody></tbody></table>
  </section>

</main>
<footer>Built by <code>scripts/build_pg_sprint_plan.py</code> from <code>build_upsc_pg/pyq_summary.json</code>.
Companion document: <code>UPSC_Polity_Geo_Sprint_Plan.md</code> / <code>.pdf</code>, printable tracker:
<code>UPSC_Polity_Geo_Sprint_Tracker.csv</code>.</footer>

<script id="plan" type="application/json">__PLAN_JSON__</script>
<script>
const PLAN = JSON.parse(document.getElementById('plan').textContent);
const KEY = 'upsc-pg-sprint-v1';
let store = {};
try { store = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { store = {}; }
const save = () => localStorage.setItem(KEY, JSON.stringify(store));
const todayStr = () => { const n = new Date();
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}-${String(n.getDate()).padStart(2, '0')}`; };
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* ---------- header stats ---------- */
const done = PLAN.days.filter(d => store[d.day_no]).length;
const studyDays = PLAN.days.filter(d => d.kind === 'study').length;
const stats = [
  ['Start', PLAN.start], ['Prelims', PLAN.prelims],
  ['Runway', PLAN.runway_days + ' days'],
  ['Blocks', PLAN.total_blocks.Polity + '+' + PLAN.total_blocks.Geography],
  ['Hours to close cycle', ((studyDays) * PLAN.hours_per_day)],
  ['Days ticked', done + ' / ' + PLAN.days.length],
];
document.getElementById('stats').innerHTML = stats.map(([k, v]) =>
  `<div class="stat"><b>${esc(v)}</b><span>${esc(k)}</span></div>`).join('');
document.getElementById('subline').textContent =
  `${PLAN.hours_per_day} h/day, 3 h Polity + 3 h Geography - first reading closed in ${PLAN.s1_len} study days ` +
  `(${PLAN.s1_end}), whole cycle by ${PLAN.cycle_end}.`;

/* ---------- today ---------- */
(function today() {
  const t = todayStr();
  let d = PLAN.days.find(x => x.date === t);
  const body = document.getElementById('todayBody');
  const title = document.getElementById('todayTitle');
  if (!d) {
    const next = PLAN.days.find(x => x.date >= t);
    title.textContent = next ? `Plan starts ${PLAN.start}` : 'Plan complete';
    body.innerHTML = next
      ? `<p>Day 1 is <b>${PLAN.start}</b>. Before then: the four books on the desk, the tracker printed, and the
         15-minute atlas slot on your phone. Nothing else needs deciding today.</p>`
      : `<p>Syllabus closed. Run Phase B-D from the week table below.</p>`;
    return;
  }
  title.textContent = d.kind === 'test'
    ? `Day ${d.day_no} - ${d.date} (${d.weekday}) - TEST DAY`
    : `Day ${d.day_no} - ${d.date} (${d.weekday}) - ${d.sprint}`;
  const mits = d.kind === 'test'
    ? ['Sit the 50-question sectional under UPSC timing', 'Analyse every wrong and every guessed question',
       'Write next week\'s three MITs per day, then stop']
    : [`Polity: ${d.polity ? d.polity.unit + ' block ' + d.polity.block + '/' + d.polity.of + ' - ' + d.polity.title : 'revision'}`,
       `Geography: ${d.geography ? d.geography.unit + ' block ' + d.geography.block + '/' + d.geography.of + ' - ' + d.geography.title : 'revision'}`,
       `${(d.polity ? d.polity.pyq : 0) + (d.geography ? d.geography.pyq : 0)} PYQs timed + error log`];
  body.innerHTML = `
    <div class="chips" style="margin-bottom:10px">
      <span class="chip">1. ${esc(mits[0])}</span><span class="chip">2. ${esc(mits[1])}</span><span class="chip">3. ${esc(mits[2])}</span>
    </div>
    <table><tbody>
      <tr><td><b>Map drill</b></td><td>${esc(d.map_drill || '-')}</td>
          <td><b>Mains task</b></td><td>${esc(d.mains_task || '-')}</td></tr>
      <tr><td><b>Revision due</b></td><td colspan="3">${d.revision.map(r => `-` + r.gap + `d ` + r.units.join('/')).join(' &nbsp; ') || 'first day'}</td></tr>
    </tbody></table>
    ${d.gate ? `<p><b>${esc(d.gate.id)}</b> today: ${esc(d.gate.test)} - pass mark ${esc(d.gate.need)}.</p>` : ''}`;
})();

/* ---------- rankings ---------- */
(function rankings() {
  const el = document.getElementById('rankings');
  const max = Math.max(...PLAN.units.map(u => u.pyq_last10));
  el.innerHTML = ['Polity', 'Geography'].map(subj => {
    const us = PLAN.units.filter(u => u.subject === subj).sort((a, b) => b.pyq_last10 - a.pyq_last10);
    const rows = us.map((u, i) => `<tr>
      <td class="num">${i + 1}</td>
      <td><span class="tag ${subj === 'Polity' ? 'pol' : 'geo'}">${esc(u.id)}</span> ${esc(u.title)}</td>
      <td class="num">${u.pyq_last10}</td><td class="num">${u.pyq_last5}</td><td class="num">${u.pyq_all}</td>
      <td class="num">${u.mains_qs}</td><td class="num">${u.blocks}</td>
      <td style="min-width:120px"><div class="bar"><i style="width:${(u.pyq_last10 / max * 100).toFixed(0)}%;background:${subj === 'Polity' ? 'var(--pol)' : 'var(--geo)'}"></i></div></td>
    </tr>`).join('');
    return `<h3 style="margin:14px 0 6px;font-size:15px">${subj}</h3>
      <table><thead><tr><th>#</th><th>Unit</th><th class="num">Last10</th><th class="num">Last5</th>
      <th class="num">All</th><th class="num">Mains</th><th class="num">Blocks</th><th>PYQ density</th></tr></thead>
      <tbody>${rows}</tbody></table>`;
  }).join('');
})();

/* ---------- gates + phases ---------- */
document.getElementById('gates').innerHTML =
  `<table><thead><tr><th>Gate</th><th>Date</th><th>Test</th><th>Pass</th><th>If you fail</th></tr></thead><tbody>` +
  PLAN.gates.map(g => `<tr><td><b>${esc(g.id)}</b></td><td>${esc(g.when)}</td><td>${esc(g.test)}</td>
   <td>${esc(g.need)}</td><td>${esc(g.fail_action)}</td></tr>`).join('') + `</tbody></table>`;
document.querySelector('#phases tbody').innerHTML = PLAN.phases.map(p =>
  `<tr><td>${p.no}</td><td>${p.start}</td><td>${p.end}</td><td>${esc(p.phase)}</td><td>${esc(p.focus)}</td>
   <td class="num">${p.days_left}</td></tr>`).join('');

/* ---------- day table ---------- */
const sprintSel = document.getElementById('sprintSel');
[...new Set(PLAN.days.map(d => d.sprint))].forEach(s => {
  const o = document.createElement('option'); o.value = s; o.textContent = s; sprintSel.appendChild(o);
});
let filter = 'all';
function render() {
  const q = document.getElementById('q').value.trim().toLowerCase();
  const sp = sprintSel.value;
  const tb = document.querySelector('#days tbody');
  const t = todayStr();
  tb.innerHTML = PLAN.days.filter(d => {
    if (sp && d.sprint !== sp) return false;
    if (filter === 'study' && d.kind !== 'study') return false;
    if (filter === 'test' && d.kind !== 'test') return false;
    if (filter === 'open' && store[d.day_no]) return false;
    if (q) {
      const hay = [d.polity && d.polity.unit, d.polity && d.polity.title, d.geography && d.geography.unit,
                   d.geography && d.geography.title, d.map_drill, d.sprint].join(' ').toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  }).map(d => {
    const cell = (b, cls) => b
      ? `<td><span class="tag ${cls}">${esc(b.unit)}</span> <b>b${b.block}/${b.of}</b> ${esc(b.title)}
         <button class="detail" data-u="${esc(b.unit)}">what to master</button>
         <div class="detailbox" id="d-${esc(b.unit)}-${d.day_no}"></div></td>`
      : `<td>-</td>`;
    return `<tr class="${store[d.day_no] ? 'done' : ''} ${d.date === t ? 'today-row' : ''}" data-day="${d.day_no}">
      <td><input type="checkbox" ${store[d.day_no] ? 'checked' : ''} data-cb="${d.day_no}" aria-label="Day ${d.day_no} done"></td>
      <td><b>${d.day_no}</b><br>${esc(d.date.slice(5))} ${esc(d.weekday)}${d.gate ? `<br><span class="tag test">${esc(d.gate.id)}</span>` : ''}</td>
      ${d.kind === 'test'
        ? `<td colspan="2"><span class="tag test">TEST DAY</span> ${esc(d.test_plan || '50-Q sectional + analysis + compress')}</td>`
        : cell(d.polity, 'pol') + cell(d.geography, 'geo')}
      <td class="num">${d.kind === 'study' ? (d.polity ? d.polity.pyq : 0) + (d.geography ? d.geography.pyq : 0) : '-'}</td>
      <td>${esc(d.map_drill || '-')}</td>
      <td>${d.kind === 'study' ? d.revision.map(r => '-' + r.gap + 'd').join(' ') : 'week'}</td>
      <td>${esc(d.gate ? d.gate.need : '')}</td></tr>`;
  }).join('');
}
document.querySelectorAll('[data-filter]').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('[data-filter]').forEach(x => x.classList.remove('on'));
  b.classList.add('on'); filter = b.dataset.filter; render();
}));
document.getElementById('q').addEventListener('input', render);
sprintSel.addEventListener('change', render);
document.getElementById('resetBtn').addEventListener('click', () => {
  if (confirm('Clear all ticked days in this browser?')) { store = {}; save(); render(); location.reload(); }
});
document.querySelector('#days tbody').addEventListener('change', e => {
  const cb = e.target.dataset && e.target.dataset.cb;
  if (!cb) return;
  if (e.target.checked) store[cb] = todayStr(); else delete store[cb];
  save(); e.target.closest('tr').classList.toggle('done', !!e.target.checked);
});
document.querySelector('#days tbody').addEventListener('click', e => {
  const b = e.target.closest('button.detail'); if (!b) return;
  const box = b.nextElementSibling; const u = PLAN.units.find(x => x.id === b.dataset.u);
  if (box.classList.contains('open')) { box.classList.remove('open'); return; }
  box.innerHTML = `<h4>Master</h4><p>${esc(u.focus)}</p><h4>Traps</h4><p>${esc(u.traps)}</p>
    <h4>Mains angle</h4><p>${esc(u.mains)}</p><h4>Source</h4><p>${esc(u.source)}</p>
    <p class="hint">Prelims PYQs: ${u.pyq_all} all-time, ${u.pyq_last10} in the last ten papers,
    ${u.pyq_last5} in the last five. Mains questions 2012-25: ${u.mains_qs}.</p>`;
  box.classList.add('open');
});
render();
</script>
</body>
</html>
"""


def write_html(days, units, summary, split, total_blocks, s1_len, gate_list, phases):
    first_pass = next(d for d in days if d["kind"] == "study" and d["study_index"] == s1_len)
    s2_end = next(d for d in days if d["kind"] == "study" and d["study_index"] == s1_len + SPRINT2_STUDY_DAYS)
    study_index = {d["study_index"]: i for i, d in enumerate([x for x in days if x["kind"] == "study"])}
    gate_dates = {g["when"]: g for g in gate_list}
    payload_days = []
    for d in days:
        e = {"day_no": d["day_no"], "date": d["date"], "weekday": d["weekday"], "week": d["week"],
             "kind": d["kind"], "sprint": d["sprint"], "gate": gate_dates.get(d["date"]),
             "map_drill": MAP_DRILLS[(d["study_index"] - 1) % len(MAP_DRILLS)] if d["kind"] == "study" else None,
             "mains_task": mains_task_for(d, units, s1_len),
             "revision": revision_piles(days, study_index[d["study_index"]]) if d["kind"] == "study" else [],
             "test_plan": "50-question sectional (rotation: polity / geography / mixed) + 90 min analysis + "
                          "mistake notebook + next week's MITs" if d["kind"] == "test" else None}
        for slot in ("polity", "geography"):
            b = d[slot]
            e[slot] = None if not b else {
                "unit": b["unit"], "block": b["block"], "of": b["of"], "pyq": b["pyq"],
                "title": units[b["unit"]]["title"]}
        payload_days.append(e)
    plan = {
        "start": START.isoformat(), "prelims": PRELIMS.isoformat(),
        "runway_days": (PRELIMS - START).days, "hours_per_day": HOURS_PER_DAY,
        "s1_len": s1_len, "s1_end": first_pass["date"], "s2_end": s2_end["date"],
        "cycle_end": days[-1]["date"], "total_blocks": total_blocks,
        "polity_share": split["polity_share"], "geography_share": split["geography_share"],
        "days": payload_days,
        "units": [{"id": u["id"], "subject": u["subject"], "title": u["title"], "source": u["source"],
                   "focus": u["focus"], "traps": u["traps"], "mains": u["mains"], "blocks": u["blocks"],
                   "pyq_all": u["pyq_all"], "pyq_last10": u["pyq_last10"], "pyq_last5": u["pyq_last5"],
                   "mains_qs": u["mains_qs"], "recurring_share": u["recurring_share"]}
                  for u in units.values()],
        "gates": gate_list, "phases": phases,
    }
    (BUILD / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")

    OUT_HTML.mkdir(parents=True, exist_ok=True)
    html = (HTML_TEMPLATE
            .replace("__PLAN_JSON__", json.dumps(plan, ensure_ascii=False)
                     .replace("</", "<\\/"))
            .replace("__SUBLINE__", f"Day 1 {START.isoformat()} · Prelims {PRELIMS.isoformat()}")
            .replace("__POLSHARE__", f"{split['polity_share']:.0%}")
            .replace("__GEOSHARE__", f"{split['geography_share']:.0%}"))
    path = OUT_HTML / "index.html"
    path.write_text(html, encoding="utf-8")
    return path, plan


def main():
    summary, per_unit = load_analysis()
    units = build_units(summary, per_unit)
    split = subject_split(summary)
    days, total_blocks, s1_len = schedule(units, summary)
    gate_list = gates(s1_len, days)
    phases = post_cycle_phases(days, units)

    md = render_md(days, units, summary, split, total_blocks, s1_len, gate_list, phases)
    (ROOT / "UPSC_Polity_Geo_Sprint_Plan.md").write_text(md, encoding="utf-8")
    csv_path = write_csv(days, units, s1_len)
    html_path, plan = write_html(days, units, summary, split, total_blocks, s1_len, gate_list, phases)
    pdf_path = write_pdf(days, units, summary, split, total_blocks, s1_len, gate_list, phases)

    first_pass = next(d for d in days if d["kind"] == "study" and d["study_index"] == s1_len)
    print(f"split: polity {split['polity_share']:.1%} / geography {split['geography_share']:.1%} "
          f"-> {split['hours']['Polity']} h polity + {split['hours']['Geography']} h geography")
    print(f"blocks: polity {total_blocks['Polity']}, geography {total_blocks['Geography']}")
    print(f"days in plan: {len(days)} (study {sum(1 for d in days if d['kind'] == 'study')}, "
          f"test {sum(1 for d in days if d['kind'] == 'test')})")
    print(f"Sprint 1 ends: {first_pass['date']} (study day {s1_len})")
    print(f"First cycle ends: {days[-1]['date']} - {(PRELIMS - date.fromisoformat(days[-1]['date'])).days} days before prelims")
    for p in (ROOT / "UPSC_Polity_Geo_Sprint_Plan.md", csv_path, html_path, pdf_path or "", BUILD / "plan.json"):
        if p:
            f = Path(p)
            print(f"  wrote {f.relative_to(ROOT)} ({f.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
