#!/usr/bin/env python3
"""Build an AI-optimized, fast-searchable, single-column A4 PDF of all
BPSC Preliminary Examination questions from 60th–62nd (Combined) to 71st BPSC,
complete with verified inline answers, full conceptual explanations,
deterministic [BPSC-XX-QYYY] search anchors, PDF bookmarks, and a Subject Index.

Usage:
    .venv/bin/python scripts/build_bpsc_pyq_60_to_71_pdf.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

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

OUT_PDF = ROOT / "BPSC_Prelims_PYQ_60th_to_71st.pdf"

# Register embedded UTF-8 TrueType fonts (full ToUnicode CMap, zero ligature PUA issues)
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
OBLIQUE_PATH = str(ROOT / "build_physics" / "fonts" / "DejaVuSans-Oblique.ttf")
if not os.path.exists(OBLIQUE_PATH):
    OBLIQUE_PATH = f"{FONT_DIR}/DejaVuSans.ttf"
pdfmetrics.registerFont(TTFont("DVS", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVS-B", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVS-O", OBLIQUE_PATH))
pdfmetrics.registerFont(TTFont("DVSM", f"{FONT_DIR}/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("DVSM-B", f"{FONT_DIR}/DejaVuSansMono-Bold.ttf"))
addMapping("DVS", 0, 0, "DVS")
addMapping("DVS", 1, 0, "DVS-B")
addMapping("DVS", 0, 1, "DVS-O")
addMapping("DVS", 1, 1, "DVS-B")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 15 * mm, 15 * mm, 17 * mm, 15 * mm
AVAIL_W = PAGE_W - ML - MR

# Palette — clean, high-contrast academic navy, royal blue, emerald, slate
NAVY = colors.HexColor("#0F2942")
NAVY_SOFT = colors.HexColor("#1B3B5A")
BLUE_ID = colors.HexColor("#1E40AF")
INK = colors.HexColor("#111827")
OPT_INK = colors.HexColor("#1F2937")
EMERALD = colors.HexColor("#0B6E4F")
AMBER = colors.HexColor("#9A3412")
SLATE = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748B")
RULE_LIGHT = colors.HexColor("#CBD5E1")
BG_TINT = colors.HexColor("#F8FAFC")
BG_HEADER_ROW = colors.HexColor("#E2E8F0")

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


def strip_injected_meta(text: str) -> str:
    s = str(text or "")
    s = re.sub(r"\s*\*?Correct Answer\s*:[\s\S]*$", "", s, flags=re.I)
    s = re.sub(r"\s*\*?Verified Answer\s*:[\s\S]*$", "", s, flags=re.I)
    return s.strip()


def clean_unicode(text: str) -> str:
    s = strip_injected_meta(text)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?[a-z][^>]*>", "", s, flags=re.I)
    # Replace private-use ligatures or odd control chars
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
    # Collapse excessive blank lines while preserving intentional single newlines
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in s.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


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
    # Remove redundant leading 'Correct Answer: (X)' prefix while keeping full explanation prose
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
    """When a bank explanation came from a different booklet set (e.g. Set A vs Set E)
    where the same answer text had a different option letter, align explicit concluding
    option-letter mentions so the explanation never contradicts our paper's Answer key."""
    ba = str(bank_ans or "").strip().upper()
    oa = str(our_ans or "").strip().upper()
    if not ba or not oa or ba == oa or len(ba) != 1 or len(oa) != 1:
        return expl
    b_txt = norm_key(bank_opts.get(ba, ""))
    o_txt = norm_key(our_opts.get(oa, ""))
    if not b_txt or not o_txt:
        return expl
    # Only rewrite if the answer texts represent the same option content
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


def build_dataset() -> list[dict]:
    with open(ROOT / "BPSC PYQ" / "bpsc_parsed.json", encoding="utf-8") as f:
        parsed_exams = json.load(f)
    with open(ROOT / "BPSC PYQ" / "bpsc_verified_answers.json", encoding="utf-8") as f:
        verified_map = json.load(f)["answers"]
    with open(ROOT / "pyq categorised" / "all_questions_tagged.json", encoding="utf-8") as f:
        tagged_map = {(q["exam"], int(q["q_no"])): q for q in json.load(f)}

    parsed_by_name = {e["exam"]: e["questions"] for e in parsed_exams}
    bank_items, exact_map, inv, opt_inv = load_explanation_bank()

    exams_out: list[dict] = []
    for meta in EXAM_META:
        exam_name = meta["exam"]
        exam_code = meta["code"]
        hints = EXAM_YEAR_HINTS[exam_name]
        raw_qs = parsed_by_name[exam_name]
        questions_out: list[dict] = []

        for q in sorted(raw_qs, key=lambda x: int(x["q_no"])):
            qno = int(q["q_no"])
            qid = f"{exam_code}-Q{qno:03d}"

            # 1. Clean & repair stem
            if (exam_name, qno) in STEM_REPAIRS:
                stem = clean_unicode(STEM_REPAIRS[(exam_name, qno)])
            else:
                stem = clean_unicode(q.get("stem", ""))

            # 2. Clean & repair options
            if (exam_name, qno) in OPTION_REPAIRS:
                options = dict(OPTION_REPAIRS[(exam_name, qno)])
            else:
                options = {}
                for k, v in (q.get("options") or {}).items():
                    ku = str(k).strip().upper()
                    cv = clean_unicode(v)
                    if cv:
                        options[ku] = cv

            # 3. Subject & subtopic tags
            tag_info = tagged_map.get((exam_name, qno), {})
            subject = clean_unicode(tag_info.get("category") or "General Studies")
            subtopic = clean_unicode(tag_info.get("subtopic") or subject)

            # 4. Verified answer key & text
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

            # 5. Explanation resolution (strict bank match -> verified editorial fallback)
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

            questions_out.append(
                {
                    "id": qid,
                    "exam": exam_name,
                    "exam_code": exam_code,
                    "exam_year": meta["year"],
                    "q_no": qno,
                    "subject": subject,
                    "subtopic": subtopic,
                    "stem": stem,
                    "options": options,
                    "answer_key": answer_key,
                    "answer_text": answer_text,
                    "is_deleted": is_deleted,
                    "explanation": explanation,
                    "expl_source": expl_source,
                }
            )

        exams_out.append({**meta, "questions": questions_out})

    validate_dataset(exams_out)
    return exams_out


def validate_dataset(exams_out: list[dict]) -> None:
    total = sum(len(e["questions"]) for e in exams_out)
    assert total == 1481, f"Expected 1481 questions across 60th–71st BPSC, got {total}"
    missing_expl = []
    bad_dt = []
    bad_meta = []
    keyed_cnt = 0
    deleted_cnt = 0
    for e in exams_out:
        for q in e["questions"]:
            if not q["explanation"]:
                missing_expl.append((q["exam"], q["q_no"]))
            if q["is_deleted"]:
                deleted_cnt += 1
            else:
                assert q["answer_key"] in ("A", "B", "C", "D", "E"), f"Invalid key on {q['id']}: {q['answer_key']}"
                assert q["answer_text"], f"Empty answer_text on {q['id']}"
                keyed_cnt += 1
            blob = " | ".join([q["stem"], *q["options"].values(), q["answer_text"], q["explanation"]])
            if "00:00:00" in blob:
                bad_dt.append(q["id"])
            if "*Correct Answer" in blob or "Verified Answer:" in blob:
                bad_meta.append(q["id"])
    assert not missing_expl, f"Missing explanations for {len(missing_expl)} items: {missing_expl[:10]}"
    assert not bad_dt, f"Datetime artifacts remain in: {bad_dt}"
    assert not bad_meta, f"Injected markdown metadata remains in: {bad_meta}"
    assert keyed_cnt == 1476 and deleted_cnt == 5, f"Unexpected keyed={keyed_cnt}, deleted={deleted_cnt}"


# ---------------------------------------------------------------------------
# ReportLab Flowables & Document Builder
# ---------------------------------------------------------------------------


def esc_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_stem_xml(s: str) -> str:
    return esc_xml(s).replace("\n", "<br/>")


class SectionTracker(Flowable):
    """Zero-height flowable that updates running header state, registers PDF
    bookmarks/outline entries, and records exact page numbers during layout."""

    def __init__(
        self,
        bookmark_key: str,
        outline_title: str,
        running_header: str,
        level: int = 0,
        page_registry: dict[str, int] | None = None,
    ) -> None:
        super().__init__()
        self.bookmark_key = bookmark_key
        self.outline_title = outline_title
        self.running_header = running_header
        self.level = level
        self.page_registry = page_registry
        self.width = 0
        self.height = 0
        self.keepWithNext = True

    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        canv = self.canv
        canv._current_section_header = self.running_header
        if self.page_registry is not None and self.bookmark_key not in self.page_registry:
            self.page_registry[self.bookmark_key] = canv.getPageNumber()
        if self.bookmark_key:
            canv.bookmarkPage(self.bookmark_key)
            canv.addOutlineEntry(self.outline_title, self.bookmark_key, level=self.level, closed=(self.level > 0))


def make_chrome_canvas(known_total_pages: int | None, out_counter: list[int]):
    """Factory returning a direct (non-buffering) Canvas subclass so native PDF
    bookmarks/outlines and internal #anchor links resolve to exact page objects."""

    class DirectChromeCanvas(pdfcanvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._current_section_header: str = "Master Index & Corpus Schema"

        def showPage(self):
            out_counter[0] = max(out_counter[0], self._pageNumber)
            if known_total_pages is not None:
                self._draw_chrome(known_total_pages)
            super().showPage()

        def _draw_chrome(self, total_pages: int) -> None:
            page_no = self._pageNumber
            self.saveState()
            # Top running header
            self.setStrokeColor(RULE_LIGHT)
            self.setLineWidth(0.5)
            y_top = PAGE_H - 11.5 * mm
            self.line(ML, y_top, PAGE_W - MR, y_top)
            self.setFont("DVS-B", 7.6)
            self.setFillColor(NAVY)
            self.drawString(ML, y_top + 2.2 * mm, "BPSC Prelims PYQ Master Compendium (60th–71st)")
            self.setFont("DVS", 7.6)
            self.setFillColor(MUTED)
            self.drawRightString(PAGE_W - MR, y_top + 2.2 * mm, self._current_section_header)

            # Bottom running footer
            y_bot = 10.5 * mm
            self.line(ML, y_bot, PAGE_W - MR, y_bot)
            self.setFont("DVS", 7.4)
            self.setFillColor(MUTED)
            self.drawString(
                ML,
                y_bot - 3.6 * mm,
                "AI-Optimized Linear Single-Column Edition  •  Search by [BPSC-XX-QYYY], Subject:, or Subtopic:",
            )
            self.setFont("DVS-B", 7.6)
            self.setFillColor(NAVY)
            self.drawRightString(PAGE_W - MR, y_bot - 3.6 * mm, f"Page {page_no} of {total_pages}")
            self.restoreState()

    return DirectChromeCanvas


def build_styles() -> dict[str, ParagraphStyle]:
    def ps(name: str, **kw) -> ParagraphStyle:
        base = dict(
            fontName="DVS",
            fontSize=9.3,
            leading=13.0,
            textColor=INK,
            spaceBefore=0,
            spaceAfter=0,
            alignment=TA_LEFT,
        )
        base.update(kw)
        return ParagraphStyle(name, **base)

    return {
        "cover_kicker": ps(
            "cover_kicker",
            fontName="DVS-B",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#93C5FD"),
        ),
        "cover_title": ps(
            "cover_title",
            fontName="DVS-B",
            fontSize=17.5,
            leading=22,
            textColor=colors.white,
            spaceBefore=2,
            spaceAfter=4,
        ),
        "cover_sub": ps(
            "cover_sub",
            fontName="DVS",
            fontSize=9.2,
            leading=13.0,
            textColor=colors.HexColor("#E2E8F0"),
        ),
        "sec_h1": ps(
            "sec_h1",
            fontName="DVS-B",
            fontSize=12.0,
            leading=15.5,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "sec_h2": ps(
            "sec_h2",
            fontName="DVS-B",
            fontSize=10.2,
            leading=13.5,
            textColor=BLUE_ID,
            spaceBefore=8,
            spaceAfter=2.5,
            keepWithNext=True,
        ),
        "body_sm": ps(
            "body_sm",
            fontSize=8.6,
            leading=12.2,
            textColor=SLATE,
            spaceAfter=3,
        ),
        "tbl_h": ps(
            "tbl_h",
            fontName="DVS-B",
            fontSize=8.0,
            leading=10.5,
            textColor=colors.white,
        ),
        "tbl_c": ps(
            "tbl_c",
            fontSize=8.0,
            leading=10.6,
            textColor=INK,
        ),
        "tbl_c_right": ps(
            "tbl_c_right",
            fontSize=8.0,
            leading=10.6,
            textColor=INK,
            alignment=TA_RIGHT,
        ),
        "exam_banner_code": ps(
            "exam_banner_code",
            fontName="DVSM-B",
            fontSize=8.6,
            leading=11,
            textColor=colors.HexColor("#93C5FD"),
        ),
        "exam_banner_title": ps(
            "exam_banner_title",
            fontName="DVS-B",
            fontSize=14.0,
            leading=18.0,
            textColor=colors.white,
            spaceBefore=1.5,
            spaceAfter=2.5,
        ),
        "exam_banner_meta": ps(
            "exam_banner_meta",
            fontSize=8.3,
            leading=11.4,
            textColor=colors.HexColor("#E2E8F0"),
        ),
        "gap_note": ps(
            "gap_note",
            fontName="DVS-O",
            fontSize=8.2,
            leading=11.4,
            textColor=AMBER,
            leftIndent=8,
            spaceBefore=4,
            spaceAfter=5,
        ),
        # Question block styles — strictly linear, machine- & human-parseable
        "q_meta": ps(
            "q_meta",
            fontName="DVS-B",
            fontSize=8.2,
            leading=11.2,
            textColor=BLUE_ID,
            spaceBefore=5.5,
            spaceAfter=2.0,
            keepWithNext=True,
        ),
        "q_stem": ps(
            "q_stem",
            fontSize=9.5,
            leading=13.3,
            textColor=INK,
            spaceAfter=2.5,
            keepWithNext=True,
        ),
        "q_opt": ps(
            "q_opt",
            fontSize=9.0,
            leading=12.4,
            textColor=OPT_INK,
            leftIndent=10,
            spaceAfter=1.2,
            keepWithNext=True,
        ),
        "q_opt_correct": ps(
            "q_opt_correct",
            fontName="DVS-B",
            fontSize=9.0,
            leading=12.4,
            textColor=EMERALD,
            leftIndent=10,
            spaceAfter=1.2,
            keepWithNext=True,
        ),
        "q_ans": ps(
            "q_ans",
            fontName="DVS-B",
            fontSize=9.1,
            leading=12.6,
            textColor=EMERALD,
            spaceBefore=2.2,
            spaceAfter=1.8,
            keepWithNext=True,
        ),
        "q_ans_del": ps(
            "q_ans_del",
            fontName="DVS-B",
            fontSize=9.0,
            leading=12.5,
            textColor=AMBER,
            spaceBefore=2.2,
            spaceAfter=1.8,
            keepWithNext=True,
        ),
        "q_expl": ps(
            "q_expl",
            fontSize=8.65,
            leading=12.1,
            textColor=SLATE,
            leftIndent=10,
            spaceAfter=5.0,
        ),
        "idx_sub": ps(
            "idx_sub",
            fontSize=8.1,
            leading=11.4,
            textColor=INK,
            leftIndent=8,
            spaceAfter=2.8,
        ),
    }


def make_story(
    exams_data: list[dict],
    st: dict[str, ParagraphStyle],
    known_pages: dict[str, int] | None,
    record_pages: dict[str, int] | None,
) -> list:
    story: list = []

    # 1. Overview & Master Index
    story.append(
        SectionTracker(
            bookmark_key="OVERVIEW",
            outline_title="Overview, AI Search Schema & Master Exam Index",
            running_header="Master Index & Corpus Schema",
            level=0,
            page_registry=record_pages,
        )
    )

    total_qs = sum(len(e["questions"]) for e in exams_data)
    keyed_qs = sum(1 for e in exams_data for q in e["questions"] if not q["is_deleted"])
    deleted_qs = total_qs - keyed_qs

    banner_tbl = Table(
        [
            [Paragraph("BIHAR PUBLIC SERVICE COMMISSION  •  PRELIMINARY EXAMINATION ARCHIVE (2017–2025)", st["cover_kicker"])],
            [Paragraph("BPSC Prelims Question Bank (60th to 71st)", st["cover_title"])],
            [
                Paragraph(
                    f"Complete Exam-wise Corpus of 10 Official Papers  •  {total_qs:,} Questions  •  "
                    "Verified Answer Keys &amp; Full Conceptual Explanations  •  AI-Optimized Single-Column Linear Edition",
                    st["cover_sub"],
                )
            ],
        ],
        colWidths=[AVAIL_W],
    )
    banner_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (0, 0), 11),
                ("BOTTOMPADDING", (0, -1), (0, -1), 11),
                ("TOPPADDING", (0, 1), (0, -1), 1),
                ("BOTTOMPADDING", (0, 0), (0, -2), 1),
            ]
        )
    )
    story.append(banner_tbl)
    story.append(Spacer(1, 6))

    # AI-Swift Reading & Fast-Search Specification Box
    story.append(Paragraph("1. Structured Schema for Fast AI Parsing &amp; Instant Keyword Search", st["sec_h1"]))
    schema_lines = [
        "• <b>Linear Single-Column Text Stream:</b> Every question is rendered in strict top-to-bottom single-column reading order using embedded UTF-8 TrueType fonts (zero multi-column interleaving, zero rasterized text, zero per-question nested tables).",
        "• <b>Globally Unique Anchor IDs:</b> Every question begins with a deterministic primary key <b>[BPSC-&lt;EXAM&gt;-Q&lt;NNN&gt;]</b> (for example, <b>[BPSC-60-62-Q001]</b> through <b>[BPSC-71-Q150]</b>), enabling exact single-match lookup.",
        "• <b>Self-Identifying Metadata Header:</b> Every question header carries <b>Exam:</b>, <b>Q.No</b>, <b>Subject:</b>, and <b>Subtopic:</b> inline so page chunks remain 100% self-contained for AI retrieval and RAG.",
        "• <b>Deterministic Field Prefixes:</b> Each entry uses consistent labels—<b>Question:</b>, <b>(A)–(E)</b> options on separate lines, <b>Answer:</b>, and <b>Explanation:</b>—plus a complete <b>Subject &amp; Subtopic Question-ID Cross-Reference Index</b> in the Appendix.",
    ]
    for line in schema_lines:
        story.append(Paragraph(line, st["body_sm"]))
    story.append(Spacer(1, 4))

    # Master Exam-wise Table
    story.append(Paragraph("2. Exam-wise Master Summary (60th–62nd Combined to 71st BPSC)", st["sec_h1"]))
    exam_rows = [
        [
            Paragraph("Code", st["tbl_h"]),
            Paragraph("Examination Paper", st["tbl_h"]),
            Paragraph("Exam Date", st["tbl_h"]),
            Paragraph("Qs", st["tbl_h"]),
            Paragraph("Keyed", st["tbl_h"]),
            Paragraph("Option Structure &amp; Notes", st["tbl_h"]),
            Paragraph("Page", st["tbl_h"]),
        ]
    ]
    for i, e in enumerate(exams_data):
        code = e["code"]
        q_cnt = len(e["questions"])
        k_cnt = sum(1 for q in e["questions"] if not q["is_deleted"])
        pg_num = known_pages.get(code) if known_pages else None
        pg_str = f'<a href="#{code}" color="#1E40AF"><b>p. {pg_num}</b></a>' if pg_num else "—"
        code_link = f'<a href="#{code}" color="#1E40AF"><b>{esc_xml(code)}</b></a>'
        exam_rows.append(
            [
                Paragraph(code_link, st["tbl_c"]),
                Paragraph(esc_xml(e["exam"]), st["tbl_c"]),
                Paragraph(esc_xml(e["date"]), st["tbl_c"]),
                Paragraph(str(q_cnt), st["tbl_c_right"]),
                Paragraph(str(k_cnt) if k_cnt == q_cnt else f"{k_cnt} (+{q_cnt - k_cnt} del)", st["tbl_c_right"]),
                Paragraph(esc_xml(e["options_note"]), st["tbl_c"]),
                Paragraph(pg_str, st["tbl_c_right"]),
            ]
        )
    # Appendix row
    app_pg = known_pages.get("APPENDIX_INDEX") if known_pages else None
    app_pg_str = f'<a href="#APPENDIX_INDEX" color="#1E40AF"><b>p. {app_pg}</b></a>' if app_pg else "—"
    exam_rows.append(
        [
            Paragraph('<a href="#APPENDIX_INDEX" color="#1E40AF"><b>INDEX</b></a>', st["tbl_c"]),
            Paragraph("<b>Appendix: Subject &amp; Subtopic ID Index</b>", st["tbl_c"]),
            Paragraph("2017–2025", st["tbl_c"]),
            Paragraph(f"<b>{total_qs}</b>", st["tbl_c_right"]),
            Paragraph(f"<b>{keyed_qs}</b>", st["tbl_c_right"]),
            Paragraph(f"All 13 subjects &amp; subtopics mapped to [BPSC-XX-QYYY] IDs ({deleted_qs} official 71st deletions noted)", st["tbl_c"]),
            Paragraph(app_pg_str, st["tbl_c_right"]),
        ]
    )

    col_w = [AVAIL_W * w for w in (0.135, 0.215, 0.13, 0.068, 0.087, 0.285, 0.08)]
    exam_tbl = Table(exam_rows, colWidths=col_w, repeatRows=1)
    tbl_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.45, RULE_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("BACKGROUND", (0, -1), (-1, -1), BG_HEADER_ROW),
    ]
    for r in range(1, len(exam_rows) - 1):
        if r % 2 == 0:
            tbl_style.append(("BACKGROUND", (0, r), (-1, r), BG_TINT))
    exam_tbl.setStyle(TableStyle(tbl_style))
    story.append(exam_tbl)
    story.append(Spacer(1, 8))

    # Subject Distribution Summary (60th–71st)
    story.append(Paragraph("3. Subject Distribution Across 60th–71st BPSC Prelims", st["sec_h1"]))
    subj_counts = Counter(q["subject"] for e in exams_data for q in e["questions"])
    subtopic_by_subj: dict[str, Counter] = defaultdict(Counter)
    for e in exams_data:
        for q in e["questions"]:
            subtopic_by_subj[q["subject"]][q["subtopic"]] += 1

    subj_rows = [
        [
            Paragraph("#", st["tbl_h"]),
            Paragraph("Subject", st["tbl_h"]),
            Paragraph("Questions", st["tbl_h"]),
            Paragraph("Share", st["tbl_h"]),
            Paragraph("Highest-Yield Subtopics (60th–71st)", st["tbl_h"]),
        ]
    ]
    for idx_s, (subj, cnt) in enumerate(sorted(subj_counts.items(), key=lambda x: (-x[1], x[0])), 1):
        pct = cnt * 100.0 / total_qs
        top_subs = ", ".join(
            f"{sub} ({n})" for sub, n in subtopic_by_subj[subj].most_common(3)
        )
        subj_key = "SUBJ_" + re.sub(r"[^A-Z0-9]+", "_", subj.upper()).strip("_")
        subj_link = f'<a href="#{subj_key}" color="#1E40AF"><b>{esc_xml(subj)}</b></a>'
        subj_rows.append(
            [
                Paragraph(str(idx_s), st["tbl_c_right"]),
                Paragraph(subj_link, st["tbl_c"]),
                Paragraph(str(cnt), st["tbl_c_right"]),
                Paragraph(f"{pct:.1f}%", st["tbl_c_right"]),
                Paragraph(esc_xml(top_subs), st["tbl_c"]),
            ]
        )
    subj_col_w = [AVAIL_W * w for w in (0.05, 0.20, 0.115, 0.08, 0.555)]
    subj_tbl = Table(subj_rows, colWidths=subj_col_w, repeatRows=1)
    st_subj = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_SOFT),
        ("GRID", (0, 0), (-1, -1), 0.45, RULE_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
    ]
    for r in range(1, len(subj_rows)):
        if r % 2 == 0:
            st_subj.append(("BACKGROUND", (0, r), (-1, r), BG_TINT))
    subj_tbl.setStyle(TableStyle(st_subj))
    story.append(subj_tbl)

    # 2. All 10 Exam Papers in Chronological Order
    for paper_idx, exam_obj in enumerate(exams_data, 1):
        story.append(PageBreak())
        code = exam_obj["code"]
        exam_name = exam_obj["exam"]
        qs = exam_obj["questions"]
        q_cnt = len(qs)
        k_cnt = sum(1 for q in qs if not q["is_deleted"])

        story.append(
            SectionTracker(
                bookmark_key=code,
                outline_title=f"{paper_idx}. {exam_name} ({q_cnt} Qs) [{code}]",
                running_header=f"{exam_name}  •  [{code}]",
                level=0,
                page_registry=record_pages,
            )
        )

        # Subject breakdown string for this paper
        paper_subjs = Counter(q["subject"] for q in qs)
        breakdown_str = "  •  ".join(
            f"{s}: {n}" for s, n in sorted(paper_subjs.items(), key=lambda x: (-x[1], x[0]))
        )

        eb_tbl = Table(
            [
                [
                    Paragraph(
                        f"PAPER {paper_idx} OF {len(exams_data)}  •  ANCHOR PREFIX: [{esc_xml(code)}-Q001 .. Q150]  •  EXAM DATE: {esc_xml(exam_obj['date'])}",
                        st["exam_banner_code"],
                    )
                ],
                [Paragraph(esc_xml(exam_obj["title"]), st["exam_banner_title"])],
                [
                    Paragraph(
                        f"<b>Questions:</b> {q_cnt}  |  <b>Verified Answers:</b> {k_cnt}  |  "
                        f"<b>Format:</b> {esc_xml(exam_obj['options_note'])}<br/>"
                        f"<b>Subject Split:</b> {esc_xml(breakdown_str)}",
                        st["exam_banner_meta"],
                    )
                ],
            ],
            colWidths=[AVAIL_W],
        )
        eb_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (0, 0), 9),
                    ("BOTTOMPADDING", (0, -1), (0, -1), 9),
                    ("TOPPADDING", (0, 1), (0, -1), 1.5),
                    ("BOTTOMPADDING", (0, 0), (0, -2), 1.5),
                ]
            )
        )
        story.append(eb_tbl)
        story.append(Spacer(1, 5))

        prev_qno = 0
        for q in qs:
            qno = q["q_no"]
            # Explicit gap annotation for 66th BPSC unrecorded source gaps
            if prev_qno and qno > prev_qno + 1:
                story.append(
                    HRFlowable(width="100%", thickness=0.45, color=RULE_LIGHT, spaceBefore=2, spaceAfter=2)
                )
                story.append(
                    Paragraph(
                        f"[Note: {esc_xml(exam_name)} Q.{prev_qno + 1} to Q.{qno - 1} are unrecorded in the source master workbook; "
                        f"numbering continues directly at Q.{qno} to preserve exact official paper alignment.]",
                        st["gap_note"],
                    )
                )
            prev_qno = qno

            story.append(
                HRFlowable(width="100%", thickness=0.4, color=RULE_LIGHT, spaceBefore=1.5, spaceAfter=1.5)
            )

            meta_line = (
                f"[{esc_xml(q['id'])}]  Exam: {esc_xml(exam_name)}  |  Q.{qno}  |  "
                f"Subject: {esc_xml(q['subject'])}  |  Subtopic: {esc_xml(q['subtopic'])}"
            )
            story.append(Paragraph(meta_line, st["q_meta"]))

            stem_para = Paragraph(f"<b>Question:</b> {format_stem_xml(q['stem'])}", st["q_stem"])
            story.append(stem_para)

            opt_items = list(q["options"].items())
            for idx_opt, (opt_k, opt_v) in enumerate(opt_items):
                is_corr = (not q["is_deleted"]) and (opt_k == q["answer_key"])
                opt_style = st["q_opt_correct"] if is_corr else st["q_opt"]
                story.append(Paragraph(f"({esc_xml(opt_k)}) {esc_xml(opt_v)}", opt_style))

            if q["is_deleted"]:
                story.append(
                    Paragraph(
                        "Answer: [Officially Deleted in BPSC Final Answer Key]",
                        st["q_ans_del"],
                    )
                )
            else:
                story.append(
                    Paragraph(
                        f"Answer: ({esc_xml(q['answer_key'])}) {esc_xml(q['answer_text'])}",
                        st["q_ans"],
                    )
                )

            story.append(
                Paragraph(
                    f"<b>Explanation:</b> {esc_xml(q['explanation'])}",
                    st["q_expl"],
                )
            )

    # 3. Appendix: Subject & Subtopic Question-ID Cross-Reference Index
    story.append(PageBreak())
    story.append(
        SectionTracker(
            bookmark_key="APPENDIX_INDEX",
            outline_title="Appendix: Subject & Subtopic Question-ID Index",
            running_header="Appendix: Subject & Subtopic Question-ID Index",
            level=0,
            page_registry=record_pages,
        )
    )
    story.append(
        Paragraph(
            "Appendix: Subject &amp; Subtopic Question-ID Cross-Reference Index (60th–71st BPSC)",
            st["sec_h1"],
        )
    )
    story.append(
        Paragraph(
            "Use this index (or AI text search) to retrieve every question across all 10 BPSC Prelims papers "
            "for any specific subject or subtopic via its unique <b>[BPSC-XX-QYYY]</b> identifier.",
            st["body_sm"],
        )
    )

    by_subj_subtopic: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for e in exams_data:
        for q in e["questions"]:
            by_subj_subtopic[q["subject"]][q["subtopic"]].append(q["id"])

    for subj, sub_map in sorted(
        by_subj_subtopic.items(),
        key=lambda item: (-sum(len(v) for v in item[1].values()), item[0]),
    ):
        subj_total = sum(len(v) for v in sub_map.values())
        subj_key = "SUBJ_" + re.sub(r"[^A-Z0-9]+", "_", subj.upper()).strip("_")
        story.append(
            SectionTracker(
                bookmark_key=subj_key,
                outline_title=f"{subj} ({subj_total} Qs)",
                running_header=f"Appendix Index  •  {subj}",
                level=1,
                page_registry=record_pages,
            )
        )
        story.append(Paragraph(f"{esc_xml(subj)} ({subj_total} Questions)", st["sec_h2"]))
        for subtopic, id_list in sorted(sub_map.items(), key=lambda x: (-len(x[1]), x[0])):
            ids_str = ", ".join(id_list)
            story.append(
                Paragraph(
                    f"<b>{esc_xml(subtopic)} ({len(id_list)}):</b> {esc_xml(ids_str)}",
                    st["idx_sub"],
                )
            )

    return story


def render_pdf(exams_data: list[dict], out_path: Path) -> dict[str, int]:
    st = build_styles()

    def run_pass(
        target_path: str,
        known_pages: dict[str, int] | None,
        known_total: int | None,
    ) -> tuple[dict[str, int], int]:
        recorded: dict[str, int] = {}
        page_counter = [0]
        doc = BaseDocTemplate(
            target_path,
            pagesize=A4,
            leftMargin=ML,
            rightMargin=MR,
            topMargin=MT,
            bottomMargin=MB,
            title="BPSC Prelims PYQ Master Compendium (60th to 71st)",
            author="GhatnaChakra-BPSC Portal",
            subject="BPSC Preliminary Examination Questions (60th–62nd to 71st) with Verified Answers & Explanations",
            keywords="BPSC, Prelims, PYQ, 60th, 62nd, 63rd, 64th, 65th, 66th, 67th, 68th, 69th, 70th, 71st, Bihar PCS",
        )
        frame = Frame(ML, MB, AVAIL_W, PAGE_H - MT - MB, id="single_col", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
        story = make_story(exams_data, st, known_pages=known_pages, record_pages=recorded)
        doc.build(story, canvasmaker=make_chrome_canvas(known_total, page_counter))
        return recorded, page_counter[0]

    # Pass 1 records exact page numbers & total page count
    tmp_path = str(out_path) + ".pass1.tmp"
    try:
        pages_pass1, total_pass1 = run_pass(tmp_path, known_pages=None, known_total=None)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Pass 2 writes final PDF with native bookmarks, exact page numbers, and 'Page X of N'
    pages_final, _ = run_pass(str(out_path), known_pages=pages_pass1, known_total=total_pass1)
    return pages_final


def main() -> None:
    print("Building curated 60th–71st BPSC Prelims dataset...")
    exams_data = build_dataset()
    src_counts = Counter(q["expl_source"] for e in exams_data for q in e["questions"])
    print("Explanation provenance breakdown:")
    for src, cnt in src_counts.most_common():
        print(f"  {src:<32s}: {cnt:4d}")
    print(f"Rendering two-pass AI-optimized PDF -> {OUT_PDF} ...")
    pages = render_pdf(exams_data, OUT_PDF)
    size_mb = OUT_PDF.stat().st_size / (1024 * 1024)
    print(f"Done! Wrote {OUT_PDF.name} ({size_mb:.2f} MB)")
    for k, v in pages.items():
        if not k.startswith("SUBJ_"):
            print(f"  {k:<18s} -> page {v}")


if __name__ == "__main__":
    main()
