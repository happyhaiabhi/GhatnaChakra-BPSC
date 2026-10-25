#!/usr/bin/env python3
"""Build a clean, single-line-per-record UTF-8 CSV of all 1,481 BPSC Preliminary
Examination questions from 60th–62nd (Combined) to 71st BPSC (2017–2025),
synchronized row-for-row with BPSC_Prelims_PYQ_60th_to_71st.pdf.

Usage:
    python3 scripts/build_bpsc_pyq_60_to_71_csv.py
"""
from __future__ import annotations

import csv
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from pyq_60_to_71_curated_fixes import (  # noqa: E402
    DELETED_71ST_QUESTIONS,
    EDITORIAL_EXPLANATIONS,
    EXAM_META,
    OPTION_REPAIRS,
    STEM_REPAIRS,
)

OUT_CSV = ROOT / "BPSC_Prelims_PYQ_60th_to_71st.csv"

STOPWORDS = {
    "the", "of", "in", "and", "to", "is", "are", "was", "were", "for", "with",
    "on", "at", "by", "from", "as", "which", "following", "consider", "statements",
    "statement", "correct", "incorrect", "select", "answer", "using", "codes",
    "code", "given", "below", "above", "match", "list", "assertion", "reason",
    "true", "false", "explanation", "choose", "out", "these", "one", "not",
    "has", "have", "had", "been", "who", "what", "when", "where",
}

OCR_WORD_FIXES = [
    ("BabuKunwar Singh", "Babu Kunwar Singh"),
    ("KhudaiKhidmatgar", "Khudai Khidmatgar"),
    ("RaghuveerChaudhari", "Raghuveer Chaudhari"),
    ("VirendraSehwag", "Virendra Sehwag"),
    ("MariyappanThangavelu", "Mariyappan Thangavelu"),
    ("Jammu &Kashmir", "Jammu & Kashmir"),
    ("Srilanka", "Sri Lanka"),
    ("4 February , 1900", "4 February, 1900"),
]

EXAM_YEAR_HINTS = {
    "60-62nd BPSC (Combined)": ["60", "62"],
    "63rd BPSC": ["63"],
    "64th BPSC": ["64"],
    "65th BPSC": ["65"],
    "66th BPSC": ["66"],
    "67th BPSC": ["67"],
    "68th BPSC": ["68"],
    "69th BPSC": ["69"],
    "70th BPSC": ["70"],
    "71st BPSC (2025)": ["71"],
}

CSV_COLUMNS = [
    "id",
    "paper_no",
    "exam_code",
    "exam",
    "exam_year",
    "exam_date",
    "q_no",
    "subject",
    "subtopic",
    "status",
    "question",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
    "answer_key",
    "answer_text",
    "explanation",
    "explanation_source",
]


def strip_injected_meta(text: str) -> str:
    s = str(text or "")
    s = re.sub(r"\s*\*?Correct Answer\s*:[\s\S]*$", "", s, flags=re.I)
    s = re.sub(r"\s*\*?Verified Answer\s*:[\s\S]*$", "", s, flags=re.I)
    return s.strip()


def clean_unicode(text: str) -> str:
    s = strip_injected_meta(text)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?[a-z][^>]*>", "", s, flags=re.I)
    s = (
        s.replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\u00a0", " ")
        .replace("\u200b", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    for bad, good in OCR_WORD_FIXES:
        s = s.replace(bad, good)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in s.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def single_line(text: str) -> str:
    """Flatten any remaining internal line breaks into ' | ' so 1 CSV line = 1 record."""
    parts = [re.sub(r"\s+", " ", p).strip() for p in str(text or "").splitlines()]
    parts = [p for p in parts if p]
    return " | ".join(parts)


def clean_explanation_text(text: str) -> str:
    s = str(text or "")
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"</?[a-z][^>]*>", "", s, flags=re.I)
    s = (
        s.replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\u00a0", " ")
        .replace("\u200b", "")
        .replace("\r\n", " ")
        .replace("\r", " ")
    )
    s = re.sub(r"^\s*\*?Correct\s+Answer\s*:\s*\(?[A-Ea-e]\)?[\.\:\-\s\*]*", "", s, flags=re.I)
    for bad, good in OCR_WORD_FIXES:
        s = s.replace(bad, good)
    s = re.sub(r"\s*\n+\s*", " ", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def is_stub_explanation(raw_expl: str, cleaned_expl: str) -> bool:
    if len(cleaned_expl) < 22:
        return True
    if re.match(r"^\s*correct\s+answer\s*:", cleaned_expl, flags=re.I) and len(cleaned_expl) < 60:
        return True
    if re.search(
        r"\b(refer\s+to\s+(the\s+)?(above|previous|chapter|q\.?\s*no|que\b)|see\s+(the\s+)?explai?nation\s+(of|above))",
        cleaned_expl,
        flags=re.I,
    ):
        return True
    return False


def norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_injected_meta(s).lower()).strip()


def extract_nums(s: str) -> set[str]:
    return set(re.findall(r"\d+", strip_injected_meta(s)))


def content_tokens(s: str) -> set[str]:
    return {w for w in norm_key(s).split() if len(w) > 2 and w not in STOPWORDS}


def is_generic_option(on: str) -> bool:
    if not on or "above" in on or "00 00 00" in on:
        return True
    if re.search(r"\b(both a and r|assertion|reason|statement i|only [1-4])\b", on):
        return True
    toks = on.split()
    allowed = {
        "a", "b", "c", "d", "e", "1", "2", "3", "4", "5",
        "i", "ii", "iii", "iv", "and", "only", "are", "correct",
    }
    return all(t in allowed for t in toks)


def align_explanation_option_letter(
    expl: str,
    bank_ans: str,
    bank_opts: dict[str, str],
    our_ans: str,
    our_opts: dict[str, str],
) -> str:
    ba = str(bank_ans or "").strip().upper()
    oa = str(our_ans or "").strip().upper()
    if not ba or not oa or ba == oa or len(ba) != 1 or len(oa) != 1:
        return expl
    b_txt = norm_key(bank_opts.get(ba, ""))
    o_txt = norm_key(our_opts.get(oa, ""))
    if not b_txt or not o_txt:
        return expl
    if b_txt == o_txt or SequenceMatcher(None, b_txt, o_txt).ratio() >= 0.80:
        expl = re.sub(
            rf"\b(option|choice)\s*\(\s*{ba}\s*\)",
            rf"\1 ({oa})",
            expl,
            flags=re.I,
        )
        expl = re.sub(
            rf"\b(option|choice)\s+{ba}\b",
            rf"\1 ({oa})",
            expl,
            flags=re.I,
        )
    return expl


def load_explanation_bank() -> tuple[list[dict], dict, dict, dict]:
    patterns = [
        ("Ghatna Chakra BPSC Bank", "bpsc/data/*.json"),
        ("Tarkash Annual PYQ Plus", "bpsc/books/tarkash_annual/data/*.json"),
        ("Tarkash BPSC PYQ", "bpsc/books/tarkas/data/*.json"),
        ("Ghatna Chakra Purvavlokan", "bpsc/books/modern_india/data/*.json"),
        ("Ghatna Chakra Purvavlokan", "bpsc/books/ancient_india/data/*.json"),
        ("Ghatna Chakra Purvavlokan", "bpsc/books/medieval_india/data/*.json"),
        ("Ghatna Chakra Purvavlokan", "bpsc/books/biology/data/*.json"),
        ("Ghatna Chakra Purvavlokan", "bpsc/books/chemistry/data/*.json"),
        ("Ghatna Chakra Purvavlokan", "bpsc/books/physics/data/*.json"),
        ("Crown Bihar GK", "bpsc/books/crown/data/*.json"),
        ("Eduteria Bihar Tathya Sangrah", "bpsc/books/eduteria_bihar_tathya_sangrah/data/*.json"),
    ]
    bank_items: list[dict] = []
    for rank, (label, pat) in enumerate(patterns):
        for p in sorted(glob.glob(str(ROOT / pat))):
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            qs = []
            if isinstance(d, dict) and "chapters" in d:
                for ch in d["chapters"]:
                    if isinstance(ch, dict):
                        qs.extend(ch.get("questions", []))
            elif isinstance(d, list):
                qs = d
            for q in qs:
                if not isinstance(q, dict):
                    continue
                qtext = q.get("q") or q.get("question") or q.get("stem") or ""
                raw_ex = q.get("explanation") or ""
                expl = clean_explanation_text(raw_ex)
                if not qtext or is_stub_explanation(raw_ex, expl):
                    continue
                opts = {
                    str(k).strip().upper(): str(v)
                    for k, v in (q.get("options") or {}).items()
                    if v is not None
                }
                opt_norms = {
                    norm_key(v)
                    for k, v in opts.items()
                    if k in ("A", "B", "C", "D") and not is_generic_option(norm_key(v))
                }
                bank_items.append(
                    {
                        "rank": rank,
                        "label": label,
                        "q": qtext,
                        "nq": norm_key(qtext),
                        "nums": extract_nums(qtext),
                        "ctoks": content_tokens(qtext),
                        "opt_norms": opt_norms,
                        "options": opts,
                        "answer": str(q.get("answer") or "").strip().upper(),
                        "year": str(q.get("year") or q.get("exam_year") or ""),
                        "expl": expl,
                    }
                )

    inv = defaultdict(list)
    opt_inv = defaultdict(list)
    exact_map = defaultdict(list)
    for idx, it in enumerate(bank_items):
        exact_map[it["nq"]].append(idx)
        for t in it["ctoks"]:
            inv[t].append(idx)
        for on in it["opt_norms"]:
            opt_inv[on].append(idx)
    return bank_items, exact_map, inv, opt_inv


def build_rows() -> list[dict]:
    with open(ROOT / "BPSC PYQ" / "bpsc_parsed.json", encoding="utf-8") as f:
        parsed_exams = json.load(f)
    with open(ROOT / "BPSC PYQ" / "bpsc_verified_answers.json", encoding="utf-8") as f:
        verified_map = json.load(f)["answers"]
    with open(ROOT / "pyq categorised" / "all_questions_tagged.json", encoding="utf-8") as f:
        tagged_map = {(q["exam"], int(q["q_no"])): q for q in json.load(f)}

    parsed_by_name = {e["exam"]: e["questions"] for e in parsed_exams}
    bank_items, exact_map, inv, opt_inv = load_explanation_bank()

    rows: list[dict] = []
    for paper_no, meta in enumerate(EXAM_META, start=1):
        exam_name = meta["exam"]
        exam_code = meta["code"]
        hints = EXAM_YEAR_HINTS[exam_name]
        raw_qs = parsed_by_name[exam_name]

        for q in sorted(raw_qs, key=lambda x: int(x["q_no"])):
            qno = int(q["q_no"])
            qid = f"{exam_code}-Q{qno:03d}"

            if (exam_name, qno) in STEM_REPAIRS:
                stem = clean_unicode(STEM_REPAIRS[(exam_name, qno)])
            else:
                stem = clean_unicode(q.get("stem", ""))

            if (exam_name, qno) in OPTION_REPAIRS:
                options = dict(OPTION_REPAIRS[(exam_name, qno)])
            else:
                options = {}
                for k, v in (q.get("options") or {}).items():
                    ku = str(k).strip().upper()
                    cv = clean_unicode(v)
                    if cv:
                        options[ku] = cv

            tag_info = tagged_map.get((exam_name, qno), {})
            subject = single_line(clean_unicode(tag_info.get("category") or "General Studies"))
            subtopic = single_line(clean_unicode(tag_info.get("subtopic") or subject))

            va = verified_map.get(f"{exam_name}::{qno}", {})
            raw_key = str(va.get("answerKey") or q.get("answer") or "").strip().upper()
            is_deleted = exam_name == "71st BPSC (2025)" and qno in DELETED_71ST_QUESTIONS
            if is_deleted:
                answer_key = "DELETED"
                answer_text = "Officially Deleted in BPSC Final Answer Key"
            else:
                m = re.search(r"\b([A-E])\b", raw_key)
                answer_key = m.group(1) if m else raw_key
                answer_text = options.get(answer_key) or clean_unicode(va.get("answerText") or "")

            explanation = ""
            expl_source = ""
            if (exam_name, qno) == ("60-62nd BPSC (Combined)", 2):
                explanation = (
                    "Birsa Munda was captured while asleep in the Jamkopai forest of Chakradharpur in early 1900 "
                    "(standard Jharkhand/tribal histories record 3 March 1900, while some secondary sources cite 3 February 1900); "
                    "per BPSC's official 60th–62nd Final Answer Key, Option (E) ('None of the above / More than one of the above') is the verified answer."
                )
                expl_source = "Official BPSC Key Note"
            elif is_deleted and (exam_name, qno) in EDITORIAL_EXPLANATIONS:
                explanation = clean_explanation_text(EDITORIAL_EXPLANATIONS[(exam_name, qno)])
                expl_source = "Official BPSC Key Note"
            else:
                nq = norm_key(stem)
                qnums = extract_nums(stem)
                qct = content_tokens(stem)
                qopt_norms = {
                    norm_key(v)
                    for k, v in options.items()
                    if k in ("A", "B", "C", "D") and not is_generic_option(norm_key(v))
                }

                matched_item = None
                if nq in exact_map:
                    cands = [bank_items[i] for i in exact_map[nq]]
                    cands.sort(key=lambda it: (0 if any(h in it["year"] for h in hints) else 1, it["rank"]))
                    matched_item = cands[0]
                else:
                    cand_scores: dict[int, float] = defaultdict(float)
                    for t in qct:
                        freq = len(inv.get(t, ()))
                        if 0 < freq < 3500:
                            w = 3.0 if freq < 200 else (2.0 if freq < 800 else 1.0)
                            for idx in inv[t]:
                                cand_scores[idx] += w
                    for on in qopt_norms:
                        for idx in opt_inv.get(on, ()):
                            cand_scores[idx] += 4.0

                    best = (0.0, None)
                    for idx, _ in sorted(cand_scores.items(), key=lambda x: -x[1])[:60]:
                        it = bank_items[idx]
                        cjacc = len(qct & it["ctoks"]) / (len(qct | it["ctoks"]) or 1)
                        if cjacc < 0.35:
                            continue
                        q_years = {x for x in qnums if len(x) == 4}
                        it_years = {x for x in it["nums"] if len(x) == 4}
                        opt_match = len(qopt_norms & it["opt_norms"])
                        yr_match = any(h in it["year"] for h in hints)
                        if (
                            q_years
                            and it_years
                            and q_years != it_years
                            and not (opt_match >= 3 and cjacc >= 0.65)
                            and not (yr_match and cjacc >= 0.60)
                        ):
                            continue
                        if (
                            qnums
                            and it["nums"]
                            and qnums != it["nums"]
                            and opt_match < 2
                            and not (yr_match and cjacc >= 0.65)
                        ):
                            if cjacc < 0.78:
                                continue
                        seq = SequenceMatcher(None, nq[:240], it["nq"][:240]).ratio()
                        score = max(cjacc, seq)
                        if opt_match >= 3 and cjacc >= 0.40:
                            score = max(score, 0.88)
                        elif opt_match >= 2 and yr_match and cjacc >= 0.40:
                            score = max(score, 0.85)
                        elif yr_match and cjacc >= 0.58:
                            score = max(score, 0.83)
                        elif yr_match and opt_match >= 1 and cjacc >= 0.50:
                            score = max(score, 0.81)
                        if score > best[0]:
                            best = (score, it)
                    if best[0] >= 0.78:
                        matched_item = best[1]

                if matched_item is not None:
                    raw_expl = clean_explanation_text(matched_item["expl"])
                    explanation = align_explanation_option_letter(
                        raw_expl,
                        matched_item["answer"],
                        matched_item["options"],
                        answer_key,
                        options,
                    )
                    expl_source = matched_item["label"]
                elif (exam_name, qno) in EDITORIAL_EXPLANATIONS:
                    explanation = clean_explanation_text(EDITORIAL_EXPLANATIONS[(exam_name, qno)])
                    expl_source = "Editorial Verified Solution"

            rows.append(
                {
                    "id": qid,
                    "paper_no": paper_no,
                    "exam_code": exam_code,
                    "exam": exam_name,
                    "exam_year": meta["year"],
                    "exam_date": meta["date"],
                    "q_no": qno,
                    "subject": subject,
                    "subtopic": subtopic,
                    "status": "Deleted" if is_deleted else "Keyed",
                    "question": single_line(stem),
                    "option_a": single_line(options.get("A", "")),
                    "option_b": single_line(options.get("B", "")),
                    "option_c": single_line(options.get("C", "")),
                    "option_d": single_line(options.get("D", "")),
                    "option_e": single_line(options.get("E", "")),
                    "answer_key": answer_key,
                    "answer_text": single_line(answer_text),
                    "explanation": single_line(explanation),
                    "explanation_source": expl_source,
                }
            )

    return rows


def validate_and_write_csv(rows: list[dict], out_path: Path) -> None:
    assert len(rows) == 1481, f"Expected 1481 rows, got {len(rows)}"
    seen_ids: set[str] = set()
    for r in rows:
        assert r["id"] not in seen_ids, f"Duplicate id: {r['id']}"
        seen_ids.add(r["id"])
        assert r["question"], f"Empty question on {r['id']}"
        assert r["explanation"], f"Empty explanation on {r['id']}"
        assert r["explanation_source"], f"Empty explanation_source on {r['id']}"
        for col in ("option_a", "option_b", "option_c", "option_d"):
            assert r[col], f"Missing {col} on {r['id']}"
        if r["status"] == "Deleted":
            assert r["answer_key"] == "DELETED"
        else:
            assert r["answer_key"] in ("A", "B", "C", "D", "E")
            assert r["answer_text"], f"Empty answer_text on {r['id']}"
        for v in r.values():
            sv = str(v)
            assert "\n" not in sv and "\r" not in sv, f"Newline leaked in {r['id']}"
            assert "00:00:00" not in sv, f"Datetime artifact in {r['id']}"

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows()
    validate_and_write_csv(rows, OUT_CSV)
    src_counts = Counter(r["explanation_source"] for r in rows)
    size_kb = OUT_CSV.stat().st_size / 1024
    print(f"Wrote {OUT_CSV.name}: {len(rows)} questions ({size_kb:.1f} KB)")
    for src, cnt in src_counts.most_common():
        print(f"  {src:<32s}: {cnt:4d}")


if __name__ == "__main__":
    main()
