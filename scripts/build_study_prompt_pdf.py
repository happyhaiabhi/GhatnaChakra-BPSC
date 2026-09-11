"""Build UPSC_Polity_Geography_Study_Prompt.pdf from upsc-polity-geography-study-prompt.md.

Usage: python3 scripts/build_study_prompt_pdf.py
Requires: fpdf2 (pip install fpdf2). Uses system DejaVu fonts.
"""
import re
import os

from fpdf import FPDF
from fpdf.fonts import FontFace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_PATH = os.path.join(ROOT, "upsc-polity-geography-study-prompt.md")
PDF_PATH = os.path.join(ROOT, "UPSC_Polity_Geography_Study_Prompt.pdf")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"

ACCENT = (30, 58, 138)      # deep blue
SUBTLE = (100, 100, 100)
CODE_BG = (243, 244, 246)
TABLE_HEAD_BG = (30, 58, 138)


def sanitize(text: str) -> str:
    """Drop glyphs DejaVu can't render (emoji etc.), tidy whitespace."""
    replacements = {
        "📋": "", "👇": "", "☝️": "", "☝": "", "📊": "",
        "📚": "", "🗓️": "", "🗓": "", "✅": "[OK]",
        "❓": "?", "⚖️": "", "⚖": "", "🧠": "", "🗺️": "",
        "🗺": "", "🎯": "»", "⭐": "*", "🔥": "",
        "\u200d": "", "\ufe0f": "",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = "".join(c for c in text if ord(c) < 0x2500 or c in ("\u2500", "\u2501"))
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def inline_md_to_html(text: str) -> str:
    """Convert **bold** and `code` to fpdf write_html subset; escape rest."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font face='mono'>\1</font>", text)
    return text


class PDF(FPDF):
    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("sans", "", 8)
        self.set_text_color(*SUBTLE)
        self.cell(0, 10, f"UPSC 2027 Polity + Geography Zero-to-Pro  |  Page {self.page_no() - 1}",
                  align="C")


def parse_table(block_lines):
    rows = []
    for ln in block_lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows


def main():
    with open(MD_PATH) as f:
        raw_lines = f.read().splitlines()

    pdf = PDF("P", "mm", "A4")
    pdf.set_margins(18, 16, 18)
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_font("sans", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
    pdf.add_font("sans", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
    pdf.add_font("sans", "I", os.path.join(FONT_DIR, "DejaVuSans.ttf"))  # no oblique file; reuse regular
    pdf.add_font("mono", "", os.path.join(FONT_DIR, "DejaVuSansMono.ttf"))
    pdf.add_font("mono", "B", os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf"))
    pdf.alias_nb_pages("{nb}")

    # ---------- Cover ----------
    pdf.add_page()
    pdf.ln(28)
    pdf.set_text_color(*ACCENT)
    pdf.set_font("sans", "B", 26)
    pdf.multi_cell(0, 12, "UPSC 2027\nPolity + Geography", align="C")
    pdf.set_font("sans", "", 20)
    pdf.set_text_color(60, 60, 60)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 12, "ZERO-TO-PRO Master Prompt", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.8)
    x = 60
    pdf.line(x, pdf.get_y(), 210 - x, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("sans", "", 11)
    pdf.set_text_color(40, 40, 40)
    for line in [
        "Prelims: 26 May 2027  |  Start: 11 Sept 2026  |  Runway: ~257 days (~37 weeks)",
        "Profile: 25 y/o, English medium, 6-8 hrs/day, basics done,",
        "self-study + paid test series, optional to be locked by 31 Oct 2026.",
    ]:
        pdf.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("sans", "I", 10)
    pdf.set_text_color(*SUBTLE)
    pdf.multi_cell(
        0, 6,
        "How to use: copy the MASTER PROMPT section (the grey box) and paste it as your "
        "first message into ChatGPT / Claude / Gemini / Grok. That AI becomes your daily coach. "
        "Appendices A-C are your quick-reference sheets.",
        align="C",
    )

    pdf.add_page()

    # ---------- Body ----------
    lines = [sanitize(l) for l in raw_lines]
    in_code = False
    para_buf = []
    i = 0

    def flush_para():
        if not para_buf:
            return
        text = " ".join(s.strip() for s in para_buf).strip()
        para_buf.clear()
        if not text or text == "---":
            if text == "---":
                pdf.ln(2)
                pdf.set_draw_color(180, 180, 180)
                pdf.set_line_width(0.3)
                pdf.line(18, pdf.get_y(), 192, pdf.get_y())
                pdf.ln(4)
            return
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("sans", "", 10)
        pdf.write_html(inline_md_to_html(text))
        pdf.ln(5)

    def code_line(text):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("mono", "", 8)
        pdf.set_text_color(25, 25, 25)
        pdf.set_fill_color(*CODE_BG)
        if text.strip() == "":
            pdf.cell(0, 3.2, "", new_x="LMARGIN", new_y="NEXT", fill=True)
        else:
            # bold-ish section headers inside prompt (ALL-CAPS single words at line start)
            pdf.multi_cell(0, 4.4, text, fill=True)

    n = len(lines)
    while i < n:
        ln = lines[i]
        stripped = ln.strip()

        # code fence
        if stripped.startswith("```"):
            flush_para()
            in_code = not in_code
            if in_code:
                pdf.set_font("sans", "B", 11)
                pdf.set_text_color(*ACCENT)
                pdf.cell(0, 7, "THE MASTER PROMPT  (copy everything in the grey box)",
                         new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1)
            else:
                pdf.ln(3)
            i += 1
            continue

        if in_code:
            code_line(ln)
            i += 1
            continue

        # headings
        if stripped.startswith("### "):
            flush_para()
            pdf.set_font("sans", "B", 11)
            pdf.set_text_color(*ACCENT)
            pdf.cell(0, 7, stripped[4:], new_x="LMARGIN", new_y="NEXT")
            i += 1
            continue
        if stripped.startswith("## "):
            flush_para()
            # keep appendices starting on fresh page
            if "Appendix" in stripped:
                pdf.add_page()
            pdf.set_font("sans", "B", 14)
            pdf.set_text_color(*ACCENT)
            pdf.cell(0, 9, stripped[3:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(*ACCENT)
            pdf.set_line_width(0.5)
            pdf.line(18, pdf.get_y(), 120, pdf.get_y())
            pdf.ln(3)
            i += 1
            continue
        if stripped.startswith("# "):
            flush_para()  # title already on cover; skip
            i += 1
            continue

        # table block
        if stripped.startswith("|"):
            flush_para()
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            rows = parse_table(block)
            if rows:
                pdf.set_font("sans", "", 9)
                pdf.set_text_color(30, 30, 30)
                ncols = max(len(r) for r in rows)
                rows = [r + [""] * (ncols - len(r)) for r in rows]
                # first column narrow for "#" tables
                if rows[0][0].strip() == "#":
                    widths = [10] + [(174 - 10) / (ncols - 1)] * (ncols - 1)
                else:
                    widths = [174 / ncols] * ncols
                with pdf.table(
                    width=174,
                    col_widths=tuple(int(w) for w in widths),
                    text_align="LEFT",
                    headings_style=FontFace(emphasis="BOLD", color=(255, 255, 255),
                                                  fill_color=TABLE_HEAD_BG),
                    line_height=5,
                ) as table:
                    for r_idx, row in enumerate(rows):
                        tr = table.row()
                        for cell in row:
                            c = sanitize(re.sub(r"\*\*(.+?)\*\*", r"\1", cell))
                            if r_idx == 0:
                                tr.cell(c)
                            else:
                                tr.cell(c)
                pdf.ln(3)
            continue

        # blockquote
        if stripped.startswith(">"):
            flush_para()
            pdf.set_font("sans", "I", 10)
            pdf.set_text_color(70, 70, 70)
            pdf.set_x(24)
            pdf.multi_cell(168, 5.5, stripped.lstrip("> ").strip())
            pdf.ln(2)
            i += 1
            continue

        # list items
        m = re.match(r"^(\s*)([-*]|\d+[.)])\s+(.*)$", ln)
        if m and stripped:
            flush_para()
            indent, marker, content = m.group(1), m.group(2), m.group(3)
            bullet = marker if marker not in ("-", "*") else "\u2022"
            left = 18 + (4 if indent else 0)
            pdf.set_text_color(30, 30, 30)
            pdf.set_font("sans", "", 10)
            pdf.set_x(left)
            pdf.write_html(f"<b>{bullet}</b>  " + inline_md_to_html(content.strip()))
            pdf.ln(5)
            i += 1
            continue

        # blank line
        if stripped == "":
            flush_para()
            i += 1
            continue

        # horizontal rule
        if stripped == "---":
            flush_para()
            i += 1
            continue

        # normal paragraph line
        para_buf.append(ln)
        i += 1

    flush_para()

    pdf.output(PDF_PATH)
    print(f"Wrote {PDF_PATH} ({os.path.getsize(PDF_PATH) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
