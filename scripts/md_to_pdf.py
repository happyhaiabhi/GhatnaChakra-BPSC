#!/usr/bin/env python3
"""Render the Phase 2 markdown report to a print-ready A4 PDF."""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

ROOT = Path(__file__).resolve().parents[1]
FONT = "/usr/share/fonts/truetype/dejavu"
NAVY = (16, 35, 55)
TEAL = (26, 95, 180)
TEAL2 = (41, 156, 158)
INK = (26, 26, 26)
MUTED = (90, 98, 110)
RULE = (210, 216, 222)
TH_BG = (26, 95, 180)
TH_FG = (255, 255, 255)
ROW_ALT = (245, 248, 251)
QUOTE_BG = (255, 248, 225)
QUOTE_BD = (240, 180, 41)

REPLACEMENTS = {
    "\u27fa": "<->",  # ⟺
    "\u2208": "in",   # ∈
    "\xa0": " ",
}


def sanitize(s: str) -> str:
    for a, b in REPLACEMENTS.items():
        s = s.replace(a, b)
    return s.replace("\t", " ")


def strip_md(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    return s


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__(format="A4", unit="mm")
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(14, 16, 14)
        self.add_font("DejaVu", "", f"{FONT}/DejaVuSans.ttf")
        self.add_font("DejaVu", "B", f"{FONT}/DejaVuSans-Bold.ttf")
        self.add_font("DejaVuMono", "", f"{FONT}/DejaVuSansMono.ttf")
        self.add_font("DejaVuMono", "B", f"{FONT}/DejaVuSansMono-Bold.ttf")
        self.set_title("UPSC Prelims PYQ Conceptual-Linkage Analysis (Phase 2)")
        self.set_author("GhatnaChakra / Phase 2 expert calibration")
        self.set_creator("scripts/md_to_pdf.py")
        self._cover = True

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "UPSC Prelims PYQ Conceptual-Linkage Analysis  ·  Phase 2", align="L")
        self.cell(0, 6, "GS Paper I  ·  2015–2026", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*TEAL)
        self.set_line_width(0.45)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_draw_color(*RULE)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1.5)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "Honest, traceable-to-real-questions numbers  ·  20-year lookback, no future leakage", align="L")
        self.cell(0, 6, str(self.page_no()), align="R")

    # ----- drawing helpers -----
    def usable(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def write_inline(self, text: str, size: float = 10, leading: float = 5.4, color=INK):
        text = sanitize(text)
        parts = re.split(r"(\*\*.+?\*\*|`[^`]+`)", text)
        for p in parts:
            if not p:
                continue
            if p.startswith("**") and p.endswith("**") and len(p) >= 4:
                self.set_font("DejaVu", "B", size)
                self.set_text_color(*color)
                self.write(leading, p[2:-2])
            elif p.startswith("`") and p.endswith("`") and len(p) >= 2:
                self.set_font("DejaVuMono", "", max(size - 0.6, 7.5))
                self.set_text_color(40, 70, 110)
                self.write(leading, p[1:-1])
            else:
                self.set_font("DejaVu", "", size)
                self.set_text_color(*color)
                self.write(leading, p)
        self.ln(leading + 0.6)

    def h1(self, text: str):
        self.set_font("DejaVu", "B", 16)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 8, sanitize(strip_md(text)))
        self.set_draw_color(*TEAL)
        self.set_line_width(0.8)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)

    def h2(self, text: str):
        if self.get_y() > 250:
            self.add_page()
        self.ln(2.5)
        self.set_fill_color(*TEAL)
        x, y = self.l_margin, self.get_y()
        self.rect(x, y, 2.2, 8.2, style="F")
        self.set_xy(x + 4.2, y)
        self.set_font("DejaVu", "B", 12.5)
        self.set_text_color(*TEAL)
        self.multi_cell(self.usable() - 4.2, 8.2, sanitize(strip_md(text)))
        self.ln(1.5)

    def h3(self, text: str):
        self.ln(1.5)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 6, sanitize(strip_md(text)))
        self.ln(0.5)

    def para(self, text: str):
        self.write_inline(text, size=10, leading=5.3)

    def quote(self, text: str):
        x = self.l_margin
        self.set_x(x)
        start = self.get_y()
        self.set_fill_color(*QUOTE_BG)
        # measure via a dummy-ish wrap
        self.set_font("DejaVu", "", 9.5)
        w = self.usable()
        self.set_xy(x + 4, start + 1.5)
        self.write_inline(text, size=9.5, leading=5.0, color=(90, 70, 20))
        end = self.get_y()
        self.set_fill_color(*QUOTE_BG)
        # background behind would require two-pass; draw left bar only
        self.set_fill_color(*QUOTE_BD)
        self.rect(x, start, 1.6, max(end - start, 6), style="F")
        self.ln(2)

    def hr(self):
        self.ln(1)
        self.set_draw_color(*RULE)
        self.set_line_width(0.3)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(3)

    def bullet_block(self, items: list[str], ordered: bool = False):
        for i, item in enumerate(items, 1):
            mark = f"{i}." if ordered else "•"
            x = self.l_margin
            y = self.get_y()
            if y > 270:
                self.add_page()
                y = self.get_y()
            self.set_xy(x, y)
            self.set_font("DejaVu", "B", 10)
            self.set_text_color(*TEAL)
            self.cell(7, 5.3, mark)
            self.set_xy(x + 7, y)
            self.write_inline(item, size=10, leading=5.3)

    def render_table(self, header: list[str], rows: list[list[str]]):
        n = len(header)
        # pad/trim rows
        clean_rows = []
        for r in rows:
            r = (r + [""] * n)[:n]
            clean_rows.append([sanitize(strip_md(c)) for c in r])
        header = [sanitize(strip_md(c)) for c in header]

        # heuristic column weights from max content length
        lens = [max(len(header[j]), *(len(r[j]) for r in clean_rows)) for j in range(n)]
        total = sum(max(l, 4) for l in lens) or 1
        usable = self.usable()
        weights = [max(l, 4) / total for l in lens]
        # clamp so no column is tiny or huge
        weights = [min(max(w, 0.07), 0.45) for w in weights]
        s = sum(weights)
        col_w = [usable * w / s for w in weights]

        headings = FontFace(emphasis="BOLD", color=TH_FG, fill_color=TH_BG, size_pt=8)
        even = FontFace(fill_color=ROW_ALT, size_pt=8)
        odd = FontFace(fill_color=(255, 255, 255), size_pt=8)

        # numeric-ish columns right-aligned
        aligns = []
        for j, h in enumerate(header):
            sample = header[j] + "".join(r[j] for r in clean_rows[:8])
            if re.search(r"[A-Za-z]{4,}", header[j]) and j == 0:
                aligns.append("LEFT")
            elif re.fullmatch(r"[\d.%+\-\[\] ,≈~]+", sample.replace(" ", "")) or header[j] in {
                "n", "W", "pop", "ALT", "Share", "Year", "lag80",
            }:
                aligns.append("CENTER")
            else:
                aligns.append("LEFT")

        self.set_font("DejaVu", "", 8)
        self.set_text_color(*INK)
        if self.get_y() > 250:
            self.add_page()
        with self.table(
            col_widths=col_w,
            text_align=aligns,
            headings_style=headings,
            first_row_as_headings=True,
            line_height=4.4,
            padding=1.15,
            v_align="T",
            borders_layout="SINGLE_TOP_LINE",
        ) as table:
            row = table.row()
            for c in header:
                row.cell(c)
            for i, r in enumerate(clean_rows):
                row = table.row(style=even if i % 2 == 0 else odd)
                for c in r:
                    row.cell(c)
        self.ln(2.5)


def parse_blocks(md: str):
    lines = md.split("\n")
    i, n = 0, len(lines)
    blocks = []

    def is_table_sep(s: str) -> bool:
        return bool(re.match(r"^\|[\s:\-|]+\|$", s.strip() if s.strip().endswith("|") else s.strip() + "|"))

    def is_list(s: str) -> bool:
        return s.startswith("- ") or bool(re.match(r"^\d+\. ", s))

    while i < n:
        raw = lines[i]
        ln = raw.rstrip()
        if ln.startswith("|") and i + 1 < n and re.match(r"^\|[\s:\-|]+", lines[i + 1].strip()):
            hdr = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            blocks.append(("table", hdr, rows))
            continue
        if ln.startswith("### "):
            blocks.append(("h3", ln[4:])); i += 1; continue
        if ln.startswith("## "):
            blocks.append(("h2", ln[3:])); i += 1; continue
        if ln.startswith("# "):
            blocks.append(("h1", ln[2:])); i += 1; continue
        if ln.startswith("> "):
            parts = [ln[2:]]
            i += 1
            while i < n and lines[i].startswith("> "):
                parts.append(lines[i][2:]); i += 1
            blocks.append(("quote", " ".join(parts)))
            continue
        if ln.strip() == "---":
            blocks.append(("hr",)); i += 1; continue
        if is_list(ln):
            ordered = bool(re.match(r"^\d+\. ", ln))
            items = []
            while i < n and (is_list(lines[i]) or (items and lines[i].startswith("   ") and lines[i].strip())):
                if is_list(lines[i]):
                    items.append(re.sub(r"^(\-|\d+\.) ", "", lines[i].rstrip()))
                else:
                    items[-1] = items[-1] + " " + lines[i].strip()
                i += 1
            blocks.append(("list", ordered, items))
            continue
        if ln.strip() == "":
            i += 1
            continue
        # paragraph: join wrapped lines
        parts = [ln]
        i += 1
        while i < n:
            nxt = lines[i].rstrip()
            if (
                nxt == ""
                or nxt.startswith("#")
                or nxt.startswith("|")
                or nxt.startswith("> ")
                or nxt.strip() == "---"
                or is_list(nxt)
            ):
                break
            parts.append(nxt)
            i += 1
        blocks.append(("p", " ".join(parts)))
    return blocks


def cover(pdf: ReportPDF):
    pdf.add_page()
    # navy band
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 92, style="F")
    pdf.set_fill_color(*TEAL2)
    pdf.rect(0, 92, 210, 4, style="F")

    pdf.set_xy(16, 22)
    pdf.set_font("DejaVu", "", 11)
    pdf.set_text_color(180, 220, 222)
    pdf.cell(0, 7, "GHATNACHAKRA  ·  UPSC PRELIMS GS PAPER I")
    pdf.ln(12)
    pdf.set_x(16)
    pdf.set_font("DejaVu", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(178, 10, "PYQ Conceptual-Linkage Analysis")
    pdf.set_x(16)
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(*TEAL2)
    pdf.cell(0, 9, "Phase 2  —  Final Report")
    pdf.ln(12)
    pdf.set_x(16)
    pdf.set_font("DejaVu", "", 11)
    pdf.set_text_color(210, 225, 230)
    pdf.multi_cell(178, 6, "Targets 2015–2026  (N = 1,200)   ·   Priors 1995–2025\nStrict 20-year lookback  ·  No future-to-past leakage")

    # headline cards
    cards = [
        ("7%", "Conservative", "L4+  directly answerable\n~7 questions / paper"),
        ("20%", "Moderate", "L3+  mechanism-level help\n~20 questions / paper"),
        ("46%", "Broad", "L2+  framework familiarity\n~46 questions / paper"),
    ]
    y = 112
    w = 56
    gap = 6
    x0 = 16
    for i, (num, label, blurb) in enumerate(cards):
        x = x0 + i * (w + gap)
        pdf.set_fill_color(245, 248, 251)
        pdf.set_draw_color(*TEAL)
        pdf.set_line_width(0.4)
        pdf.rect(x, y, w, 42, style="FD", round_corners=True, corner_radius=2)
        pdf.set_xy(x + 4, y + 4)
        pdf.set_font("DejaVu", "B", 20)
        pdf.set_text_color(*TEAL)
        pdf.cell(w - 8, 10, num, align="C")
        pdf.set_xy(x + 4, y + 14)
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(w - 8, 6, label, align="C")
        pdf.set_xy(x + 4, y + 21)
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(w - 8, 4.4, blurb, align="C")

    pdf.set_xy(16, 164)
    pdf.set_font("DejaVu", "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 7, "What this report is")
    pdf.ln(8)
    pdf.set_x(16)
    bullets = [
        "Expert conceptual (not lexical) analysis of UPSC Prelims PYQs, 1995–2026.",
        "Level 0–5 relationship annotation + advantage types for target → prior links.",
        "Design-weighted census: 349 expert overrides on 353 labeled targets.",
        "Engine: run13 frozen. Standard: honest numbers, traceable to real questions.",
        "Full §1–§24 in the brief's deliverable order, plus Appendix B timelines.",
    ]
    for b in bullets:
        pdf.set_x(16)
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(*TEAL)
        pdf.cell(6, 6, "▸")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(*INK)
        pdf.multi_cell(172, 6, b)

    pdf.set_xy(16, 250)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(
        178,
        5,
        "Appendix A (1,200 question-level links) ships as CSV alongside this PDF.\n"
        "Machine-readable tables: data/pyq_phase2_calibrated_*.json",
    )


def render_md(pdf: ReportPDF, md: str):
    for blk in parse_blocks(md):
        kind = blk[0]
        if kind == "h1":
            pdf.h1(blk[1])
        elif kind == "h2":
            pdf.h2(blk[1])
        elif kind == "h3":
            pdf.h3(blk[1])
        elif kind == "p":
            pdf.para(blk[1])
        elif kind == "quote":
            pdf.quote(blk[1])
        elif kind == "hr":
            pdf.hr()
        elif kind == "list":
            pdf.bullet_block(blk[2], ordered=blk[1])
        elif kind == "table":
            pdf.render_table(blk[1], blk[2])


def main():
    report = (ROOT / "docs/PYQ_PHASE2_REPORT.md").read_text(encoding="utf-8")
    appb = (ROOT / "docs/PYQ_PHASE2_APPENDIX_B.md").read_text(encoding="utf-8")
    out = ROOT / "docs/PYQ_PHASE2_REPORT.pdf"

    pdf = ReportPDF()
    cover(pdf)
    pdf.add_page()
    render_md(pdf, report)
    pdf.add_page()
    pdf.h1("Appendix B — Concept timelines")
    pdf.para(
        "75 concept timelines from the calibrated knowledge graph. "
        "Full question-level links (Appendix A) are in `docs/PYQ_PHASE2_APPENDIX_A.csv`."
    )
    render_md(pdf, appb)
    pdf.output(out)
    print(f"wrote {out}  pages={pdf.page_no()}  bytes={out.stat().st_size}")


if __name__ == "__main__":
    main()
