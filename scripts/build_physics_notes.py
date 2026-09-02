#!/usr/bin/env python3
"""Build the consolidated, de-duplicated A4 *physics* notes PDF
(BPSC_Physics_Consolidated_Notes_A4.pdf) from

  build_physics/content/*.txt      – topic-wise manuscript in the notes DSL
  build_physics/figures/*.png      – figures clipped from the 19 lecture PDFs
                                     (scripts/extract_physics_figures.py)
  build_physics/pyq_analysis.csv   – reviewed physics PYQs
  build_physics/pyq_summary.json   – topic ranking (scripts/analyse_physics_pyqs.py)

DSL (one directive per line):
  UNIT n | Title | Consolidated-from text
  H2 / H3 text                       headings (H2 goes to the TOC)
  P text                             paragraph      B text / BB text  bullets
  EQ text                            formula strip
  TBL h1~h2~…  (+ rows, blank line ends)   TBLW 30,70 sets column widths (%)
  IMG file|caption|width%            single figure (source lecture/page auto-added)
  IMGS f1|cap;;f2|cap                figures side by side
  BOX Title :: item; item            highlighted panel (source content)
  NOTE text                          green  "De-dup note"  – what was merged/moved
  CORR text                          coral  "Source correction" – error in the lecture fixed
  ADD Title :: item; item            blue   "Added by editor" – NOT in the source lectures
  PYQ text                           amber  "PYQ lens" – how BPSC has asked this
  PB / SP                            page break / small space
Inline: **bold**, ^{sup}, _{sub}.
"""
import csv
import glob
import json
import os
import re

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (BaseDocTemplate, Frame, Image as RLImage, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build_physics")
FIG = os.path.join(BUILD, "figures")
FIG_DPI = 150
OUT = os.path.join(ROOT, "BPSC_Physics_Consolidated_Notes_A4.pdf")

def _find_font(name):
    """Locate a DejaVu TTF: system dir first, then build_physics/fonts/, then matplotlib's bundle."""
    candidates = [os.path.join("/usr/share/fonts/truetype/dejavu", name),
                  os.path.join(BUILD, "fonts", name)]
    try:
        import matplotlib
        candidates.append(os.path.join(matplotlib.get_data_path(), "fonts", "ttf", name))
    except Exception:
        pass
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


pdfmetrics.registerFont(TTFont("DVS", _find_font("DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DVS-B", _find_font("DejaVuSans-Bold.ttf")))
_obl = _find_font("DejaVuSans-Oblique.ttf")
pdfmetrics.registerFont(TTFont("DVS-I", _obl if _obl else _find_font("DejaVuSans.ttf")))
addMapping("DVS", 0, 0, "DVS"); addMapping("DVS", 1, 0, "DVS-B")
addMapping("DVS", 0, 1, "DVS-I"); addMapping("DVS", 1, 1, "DVS-B")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 40, 40, 46, 44
AVAIL = PAGE_W - ML - MR

ACCENTS = ["#1F5AA8", "#0E7C66", "#B34700", "#7A1F5C", "#245BCC", "#8C6D0F",
           "#A82828", "#0F6E8C", "#5B3E96", "#1D7A34", "#9A3B12", "#4A5A00",
           "#0B5C8E", "#7A3E1F", "#2E4A7A", "#6B1F6B"]
NAVY = colors.HexColor("#10304F")
GREY = colors.HexColor("#5A6470")
LINE = colors.HexColor("#C9D2DC")
BLUE, BLUE_PALE = colors.HexColor("#2B6CB0"), colors.HexColor("#EAF2FB")
CORAL, CORAL_PALE = colors.HexColor("#C84B2F"), colors.HexColor("#FBEDE8")
GREEN, GREEN_PALE = colors.HexColor("#5E8C4A"), colors.HexColor("#EFF5EC")
AMBER, AMBER_PALE = colors.HexColor("#B8860B"), colors.HexColor("#FBF4E0")


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rich(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    # single *italic* (not touching another asterisk, not a bare multiplication sign like "6 * 2")
    t = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"\^\{(.+?)\}", r"<super rise='3' size='6.4'>\1</super>", t)
    t = re.sub(r"_\{(.+?)\}", r"<sub rise='1.5' size='6.4'>\1</sub>", t)
    return t


def S(name, **kw):
    base = dict(fontName="DVS", fontSize=9.2, leading=12.6, textColor=colors.HexColor("#1B2430"),
                spaceBefore=0, spaceAfter=0)
    base.update(kw)
    return ParagraphStyle(name, **base)


ST = {
    "body": S("body", spaceAfter=3.2),
    "b0": S("b0", leftIndent=14, bulletIndent=3, spaceAfter=2.4),
    "b1": S("b1", leftIndent=27, bulletIndent=16, spaceAfter=2.0, fontSize=8.9, leading=12.0),
    # keepWithNext: a heading is never left stranded at the foot of a page
    "h2": S("h2", fontName="DVS-B", fontSize=11.6, leading=14, spaceBefore=9, spaceAfter=3.5,
            keepWithNext=1),
    "h3": S("h3", fontName="DVS-B", fontSize=9.8, leading=12.5, spaceBefore=6, spaceAfter=2.5,
            textColor=colors.HexColor("#24303E"), keepWithNext=1),
    "eq": S("eq", fontName="DVS-B", fontSize=9.4, leading=13, alignment=TA_CENTER),
    "cap": S("cap", fontSize=7.6, leading=9.6, textColor=GREY, alignment=TA_CENTER, spaceBefore=2.5),
    "note": S("note", fontSize=8.0, leading=10.8, textColor=colors.HexColor("#3E4A38")),
    "cell": S("cell", fontSize=8.3, leading=10.6),
    "cellh": S("cellh", fontName="DVS-B", fontSize=8.4, leading=10.6, textColor=colors.white),
    "boxh": S("boxh", fontName="DVS-B", fontSize=9.0, leading=11.5, textColor=colors.white),
    "tag": S("tag", fontName="DVS-B", fontSize=7.2, leading=9, textColor=colors.white),
}

FIGCTR = {}
UNIT_LIST = []


def fig_path(fname):
    if not os.path.splitext(fname)[1]:
        fname += ".png"
    return os.path.join(FIG, fname)


def fig_source(fname):
    m = re.match(r"L(\d+)_p(\d+)", os.path.basename(fname))
    return f"Lecture {int(m.group(1))}, p. {m.group(2)}" if m else ""


class GlueSpacer(Spacer):
    """A spacer that does not break a heading's keepWithNext chain (used before figures)."""
    keepWithNext = 1

    def __init__(self, h):
        super().__init__(0, h)


class HRMini(Spacer):
    keepWithNext = 1        # the rule under an H2 stays glued to the heading AND to the next flowable

    def __init__(self, accent):
        super().__init__(0, 2.6)
        self._accent = accent

    def draw(self):
        self.canv.setStrokeColor(colors.HexColor(self._accent)); self.canv.setLineWidth(1.1)
        self.canv.line(0, 1, 46, 1)
        self.canv.setStrokeColor(LINE); self.canv.setLineWidth(0.5)
        self.canv.line(48, 1, AVAIL, 1)


def make_unit_band(num, title, source, accent):
    c = colors.HexColor(accent)
    t = Table([[Paragraph(f"UNIT {num}", ST["boxh"])],
               [Paragraph(f"<b>{esc(title)}</b>",
                          S("ut", fontName="DVS-B", fontSize=16, leading=19, textColor=colors.white))],
               [Paragraph(f"Consolidated from: {esc(source)}",
                          S("us", fontSize=8.2, leading=10.5, textColor=colors.HexColor("#EAF0F8")))]],
              colWidths=[AVAIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (0, 0), 10), ("BOTTOMPADDING", (0, -1), (0, -1), 10),
        ("TOPPADDING", (0, 1), (0, 2), 2), ("BOTTOMPADDING", (0, 0), (0, 1), 2)]))
    return t


def make_table(rows, widths, accent, zebra=True, font=None):
    c = colors.HexColor(accent) if isinstance(accent, str) else accent
    n = max(len(r) for r in rows)
    for r in rows:
        while len(r) < n:
            r.append("—")
    cell = ST["cell"] if font is None else S("cellx", fontSize=font, leading=font + 2.3)
    data = [[Paragraph(rich(x), ST["cellh"] if i == 0 else cell) for x in row] for i, row in enumerate(rows)]
    if widths and len(widths) == n:
        colw = [AVAIL * w / 100.0 for w in widths]
    else:
        lens = [max(len(rows[r][k]) + 2 for r in range(len(rows))) for k in range(n)]
        tot = sum(lens)
        colw = [max(AVAIL * 0.08, AVAIL * l / tot) for l in lens]
        sc = AVAIL / sum(colw); colw = [w * sc for w in colw]
    t = Table(data, colWidths=colw, repeatRows=1)
    style = [("GRID", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, 0), c),
             ("NOSPLIT", (0, 0), (-1, min(1, len(rows) - 1))),   # header row never orphaned
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("TOPPADDING", (0, 0), (-1, -1), 3.0), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.0)]
    if zebra:
        for r in range(2, len(rows), 2):
            style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F2F6FA")))
    t.setStyle(TableStyle(style))
    return t


def make_img(fname, caption, width_pct, unit_no):
    p = fig_path(fname)
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    with PILImage.open(p) as im:
        pw, ph = im.size
    maxw = AVAIL * (width_pct / 100.0)
    w = min(maxw, pw * 72.0 / FIG_DPI)
    h = w * ph / pw
    if h > 520:
        h = 520; w = h * pw / ph
    img = RLImage(p, width=w, height=h)
    src = fig_source(fname)
    txt = f"<b>Fig. {unit_no}-{FIGCTR[unit_no]}</b>"
    if caption:
        txt += f" · {esc(caption)}"
    if src:
        txt += f"  <font color='#8A94A0'>[{src}]</font>"
    FIGCTR[unit_no] += 1
    inner = Table([[img], [Paragraph(txt, ST["cap"])]], colWidths=[w + 8])
    inner.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                               ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                               ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                               ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, -1), (0, -1), 4),
                               ("NOSPLIT", (0, 0), (-1, -1))]))   # caption never drifts to the next page
    # (a NOSPLIT Table instead of KeepTogether so that a preceding heading's
    #  keepWithNext can pull the figure along with it — KeepTogether containers
    #  are excluded from keepWithNext chains by reportlab)
    return inner


def make_imgs(items, unit_no):
    n = len(items)
    cw = (AVAIL - 6 * (n - 1)) / n
    cells, caps = [], []
    for fname, caption in items:
        p = fig_path(fname)
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        with PILImage.open(p) as im:
            pw, ph = im.size
        w = min(cw - 8, pw * 72.0 / FIG_DPI * 1.15)
        h = w * ph / pw
        if h > 300:
            h = 300; w = h * pw / ph
        cells.append(RLImage(p, width=w, height=h))
        src = fig_source(fname)
        txt = f"<b>Fig. {unit_no}-{FIGCTR[unit_no]}</b> · {esc(caption)}"
        if src:
            txt += f"  <font color='#8A94A0'>[{src}]</font>"
        caps.append(Paragraph(txt, ST["cap"]))
        FIGCTR[unit_no] += 1
    t = Table([cells, caps], colWidths=[cw] * n)
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                           ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                           ("TOPPADDING", (0, 0), (-1, 0), 3), ("BOTTOMPADDING", (0, -1), (0, -1), 3),
                           ("NOSPLIT", (0, 0), (-1, -1))]))
    return t


def make_eq(text):
    t = Table([[Paragraph(rich(text), ST["eq"])]], colWidths=[AVAIL])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF6E8")),
                           ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E3D6AC")),
                           ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
    return t


def make_strip(label, text, fg, bg):
    p = Paragraph(f"<font color='{fg.hexval()}'><b>{label}:</b></font> {rich(text)}", ST["note"])
    t = Table([[p]], colWidths=[AVAIL])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 2.2, fg),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    return t


def make_box(title, body, accent, tag=None, tag_color=None, pale=None):
    c = colors.HexColor(accent) if isinstance(accent, str) else accent
    head = f"<b>{esc(title)}</b>"
    if tag:
        head = f"<font size='7.2'>▌{tag}▐</font>&nbsp;&nbsp;" + head
    rows = [[Paragraph(head, ST["boxh"])]]
    styles = [("BACKGROUND", (0, 0), (0, 0), c), ("BOX", (0, 0), (-1, -1), 0.8, c),
              ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (0, 0), 5)]
    for i, b in enumerate(body):
        if b.startswith("- "):
            rows.append([Paragraph(rich(b[2:]), S("bxb", leftIndent=12, bulletIndent=2), bulletText="•")])
        else:
            rows.append([Paragraph(rich(b), ST["body"])])
        styles.append(("TOPPADDING", (0, i + 1), (0, i + 1), 2.5))
        if i == len(body) - 1:
            styles.append(("BOTTOMPADDING", (0, i + 1), (0, i + 1), 6))
        if pale is not None:
            styles.append(("BACKGROUND", (0, i + 1), (0, i + 1), pale))
        elif i % 2 == 0:
            styles.append(("BACKGROUND", (0, i + 1), (0, i + 1), colors.HexColor("#F7FAFC")))
    if len(rows) > 1:
        # the coloured title bar must never be left alone at the foot of a page:
        # header + first body row are one unsplittable block
        styles.append(("NOSPLIT", (0, 0), (-1, 1)))
    t = Table(rows, colWidths=[AVAIL])
    t.setStyle(TableStyle(styles))
    return t


# ---------------------------------------------------------------- parsing
PREFIXES = ("UNIT ", "H2 ", "H3 ", "P ", "B ", "BB ", "EQ ", "NOTE ", "CORR ", "PYQ ", "ADD ",
            "BOX ", "IMG ", "IMGS ", "TBL ", "TBLW ", "TBLF ")


def is_directive(line):
    return line.startswith(PREFIXES) or line.strip() in ("PB", "SP") or line.lstrip().startswith("#")


def split_items(body):
    """Split a BOX/ADD body into rows on ';' — but only at bracket depth 0, and a
    fragment that starts in lower case is a continuation of the previous row,
    not a new one (so "…; the rocket accelerates…" stays in its sentence)."""
    if not body.strip():
        return []
    parts, buf, depth = [], [], 0
    for ch in body:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            parts.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    if depth != 0:                     # unbalanced brackets → plain split
        parts = body.split(";")
    items = []
    for frag in parts:
        frag = frag.strip()
        if not frag:
            continue
        lead = frag.lstrip("*_^")
        cont = bool(items) and lead[:1].islower()
        if cont:
            items[-1] = items[-1] + "; " + frag
        else:
            items.append(frag)
    return items


def page_break(story):
    """Append a PageBreak, first dropping any trailing Spacers: a spacer that no
    longer fits at the foot of a full page would otherwise open a new page on
    its own and the PageBreak that follows would leave that page blank."""
    while story and type(story[-1]) in (Spacer, GlueSpacer):
        story.pop()
    story.append(PageBreak())


def parse_file(path, story, unit_state):
    accent = unit_state["accent"]
    unit_no = unit_state["no"]
    pending_widths = None
    pending_font = None
    tbl_rows = None
    lines = open(path, encoding="utf-8").read().splitlines()

    def flush_table():
        nonlocal tbl_rows, pending_widths, pending_font
        if tbl_rows:
            story.append(Spacer(1, 3))
            story.append(make_table(tbl_rows, pending_widths, accent, font=pending_font))
            story.append(Spacer(1, 6))
        tbl_rows = None; pending_widths = None; pending_font = None

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n"); i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            if tbl_rows:
                flush_table()
            continue
        if tbl_rows is not None and not is_directive(line):
            tbl_rows.append(line.split("~")); continue
        if line.startswith("TBLW "):
            if tbl_rows:
                flush_table()
            pending_widths = [float(x) for x in line[5:].split(",")]; continue
        if line.startswith("TBLF "):
            if tbl_rows:
                flush_table()
            pending_font = float(line[5:].strip()); continue
        if line.startswith("TBL "):
            if tbl_rows:
                flush_table()
            tbl_rows = [line[4:].strip().split("~")]; continue
        if tbl_rows:
            flush_table()
        if line.startswith("UNIT "):
            parts = line.split("|")
            num = parts[0][5:].strip(); title = parts[1].strip()
            source = parts[2].strip() if len(parts) > 2 else ""
            unit_state["no"] = num; unit_state["title"] = title
            accent = ACCENTS[(int(num) - 1) % len(ACCENTS)]
            unit_state["accent"] = accent
            unit_no = num; FIGCTR[unit_no] = 1
            if story:
                page_break(story)
            band = make_unit_band(num, title, source, accent)
            band._toc = (0, f"Unit {num} — {title}")
            story.append(band); story.append(Spacer(1, 6)); continue
        if line.startswith("H2 "):
            txt = line[3:].strip()
            p = Paragraph(rich(txt), ParagraphStyle("h2x", parent=ST["h2"], textColor=colors.HexColor(accent)))
            p._toc = (1, txt)
            story.append(p); story.append(HRMini(accent)); continue
        if line.startswith("H3 "):
            story.append(Paragraph(rich(line[3:].strip()), ST["h3"])); continue
        if line.startswith("P "):
            story.append(Paragraph(rich(line[2:].strip()), ST["body"])); continue
        if line.startswith("BB "):
            story.append(Paragraph(rich(line[3:].strip()), ST["b1"], bulletText="–")); continue
        if line.startswith("B "):
            story.append(Paragraph(rich(line[2:].strip()), ST["b0"], bulletText="•")); continue
        if line.startswith("EQ "):
            story.append(make_eq(line[3:].strip())); story.append(Spacer(1, 4)); continue
        if line.startswith("NOTE "):
            story.append(Spacer(1, 2)); story.append(make_strip("↻ De-dup note", line[5:].strip(), GREEN, GREEN_PALE))
            story.append(Spacer(1, 4)); continue
        if line.startswith("CORR "):
            story.append(Spacer(1, 2)); story.append(make_strip("✎ Source correction", line[5:].strip(), CORAL, CORAL_PALE))
            story.append(Spacer(1, 4)); continue
        if line.startswith("PYQ "):
            story.append(Spacer(1, 2)); story.append(make_strip("★ PYQ lens", line[4:].strip(), AMBER, AMBER_PALE))
            story.append(Spacer(1, 4)); continue
        if line.startswith("BOX ") or line.startswith("ADD "):
            kind = line[:3]
            title, _, body = line[4:].partition("::")
            items = split_items(body)
            while i < len(lines) and lines[i].strip() and not is_directive(lines[i]):
                items.append(lines[i].strip()); i += 1
            if kind == "ADD":
                story.append(make_box(title.strip(), items, BLUE, tag="ADDED BY EDITOR — not in source lectures",
                                      pale=BLUE_PALE))
            else:
                story.append(make_box(title.strip(), items, accent))
            story.append(Spacer(1, 5)); continue
        if line.startswith("IMG "):
            parts = line[4:].split("|")
            fname = parts[0].strip()
            cap = parts[1].strip() if len(parts) > 1 else ""
            pct = float(parts[2]) if len(parts) > 2 and parts[2].strip() else 60
            story.append(GlueSpacer(3)); story.append(make_img(fname, cap, pct, unit_no)); story.append(Spacer(1, 5))
            continue
        if line.startswith("IMGS "):
            items = []
            for it in line[5:].split(";;"):
                f, _, c = it.partition("|")
                if f.strip():
                    items.append((f.strip(), c.strip()))
            story.append(GlueSpacer(3)); story.append(make_imgs(items, unit_no)); story.append(Spacer(1, 5))
            continue
        if line.strip() == "PB":
            page_break(story); continue
        if line.strip() == "SP":
            story.append(Spacer(1, 6)); continue
        raise ValueError(f"Unknown line in {path}: {line[:70]!r}")
    flush_table()


# ---------------------------------------------------------------- document
class NotesDoc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
                         title="72nd BPSC Physics — Consolidated Notes (A4 rearranged edition, PYQ-prioritised)",
                         author="Physics by Sakshi Ma'am (Eduteria) — consolidated, de-duplicated & PYQ-mapped",
                         subject="Topic-wise physics notes with BPSC PYQ topic priority (56–59th to 71st)",
                         **kw)
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[Frame(0, 0, PAGE_W, PAGE_H, id="cover")], onPage=draw_cover),
            PageTemplate(id="body", frames=[Frame(ML, MB, PAGE_W - ML - MR, PAGE_H - MT - MB, id="body")],
                         onPage=draw_body),
        ])

    def afterFlowable(self, fl):
        if hasattr(fl, "_toc"):
            level, text = fl._toc
            self.notify("TOCEntry", (level, text, self.page))
            # PDF outline (sidebar bookmarks) in addition to the printed contents page
            key = f"bm_{abs(hash((level, text, self.page)))}"
            self.canv.bookmarkPage(key)
            try:
                self.canv.addOutlineEntry(text, key, level=level, closed=(level == 0))
            except Exception:
                pass


def draw_cover(canvas, doc):
    import math
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#0F2A44")); canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#0A1F33")); canvas.rect(0, PAGE_H - 250, PAGE_W, 250, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#F2A900")); canvas.rect(0, PAGE_H - 262, PAGE_W, 12, stroke=0, fill=1)
    # decorative physics motifs: waves, orbit, rays
    canvas.setStrokeColor(colors.HexColor("#2C5B8A")); canvas.setLineWidth(1.4)
    for k in range(3):
        y0 = 330 - k * 34
        pts = [(x, y0 + 14 * math.sin(x / 26.0 + k)) for x in range(0, int(PAGE_W) + 1, 6)]
        p = canvas.beginPath(); p.moveTo(*pts[0])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        canvas.drawPath(p, stroke=1, fill=0)
    canvas.setStrokeColor(colors.HexColor("#3E7BC0"))
    canvas.ellipse(PAGE_W - 200, 420, PAGE_W - 40, 520, stroke=1, fill=0)
    canvas.ellipse(PAGE_W - 170, 400, PAGE_W - 70, 540, stroke=1, fill=0)
    canvas.setFillColor(colors.HexColor("#F2A900")); canvas.circle(PAGE_W - 120, 470, 9, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#9CC4EE")); canvas.circle(PAGE_W - 60, 500, 3.5, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("DVS-B", 15); canvas.drawString(48, PAGE_H - 78, "EDUTERIA  ·  72nd BPSC PRELIMS  ·  PHYSICS")
    canvas.setFont("DVS-B", 34); canvas.drawString(46, PAGE_H - 140, "PHYSICS")
    canvas.setFont("DVS-B", 21); canvas.setFillColor(colors.HexColor("#FFD465"))
    canvas.drawString(48, PAGE_H - 172, "Consolidated Class Notes — A4 Edition")
    canvas.setFillColor(colors.HexColor("#C9DCEF")); canvas.setFont("DVS", 10.5)
    canvas.drawString(48, PAGE_H - 200, "All 19 lectures of Physics by Sakshi Ma'am — re-arranged topic-wise, duplicates merged,")
    canvas.drawString(48, PAGE_H - 215, "every chart & diagram kept, and every BPSC physics PYQ (56–59th → 71st) mapped to its unit.")
    canvas.setFont("DVS-B", 11); canvas.setFillColor(colors.white)
    canvas.drawString(48, PAGE_H - 296, f"{len(UNIT_LIST)} UNITS  +  PYQ TOPIC-PRIORITY MAP  +  FULL PYQ APPENDIX")
    y = PAGE_H - 320
    col_x = [48, 232, 416]
    for i, (num, title) in enumerate(UNIT_LIST):
        x = col_x[i % 3]; yy = y - (i // 3) * 26
        canvas.setFillColor(colors.HexColor("#173F6F")); canvas.roundRect(x, yy - 6, 176, 22, 5, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#FFD465")); canvas.setFont("DVS-B", 9.2)
        canvas.drawCentredString(x + 20, yy + 1, num)
        canvas.setFillColor(colors.white); canvas.setFont("DVS", 7.4)
        t = title if len(title) <= 27 else title[:26] + "…"
        canvas.drawString(x + 36, yy, t)
    canvas.setFillColor(colors.white); canvas.setFont("DVS-B", 12)
    canvas.drawString(48, 132, "Re-arranged, de-duplicated & PYQ-prioritised edition")
    canvas.setFont("DVS", 9); canvas.setFillColor(colors.HexColor("#C9DCEF"))
    canvas.drawString(48, 114, "Source: 19 lecture PDFs in “physic notes eduteria/” (84 pages) · Physics by Sakshi Ma'am · Eduteria")
    canvas.drawString(48, 100, "PYQ data: 56–59th (2015) paper + BPSC master question bank 60–62nd … 71st (2025)")
    canvas.drawString(48, 86, "Blue boxes = added by the editor (not in the lectures) · coral strips = source corrections")
    canvas.setFillColor(colors.HexColor("#FFD465")); canvas.setFont("DVS", 9)
    canvas.drawRightString(PAGE_W - 48, 86, "Print-ready A4 · 2026")
    canvas.restoreState()


def draw_body(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#0F2A44")); canvas.rect(0, PAGE_H - 30, PAGE_W, 30, stroke=0, fill=1)
    canvas.setFillColor(colors.white); canvas.setFont("DVS-B", 8)
    canvas.drawString(ML, PAGE_H - 20, "72nd BPSC · PHYSICS · CONSOLIDATED NOTES")
    canvas.setFont("DVS", 7.6); canvas.setFillColor(colors.HexColor("#C9DCEF"))
    canvas.drawRightString(PAGE_W - MR, PAGE_H - 20, "Rearranged from the 19 Eduteria physics lectures · PYQ-prioritised")
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5); canvas.line(ML, MB - 12, PAGE_W - MR, MB - 12)
    canvas.setFont("DVS", 7.6); canvas.setFillColor(GREY)
    canvas.drawString(ML, MB - 24, "Physics by Sakshi Ma'am · Eduteria — de-duplicated & re-organised edition")
    canvas.setFont("DVS-B", 8.6); canvas.setFillColor(colors.HexColor("#0F2A44"))
    canvas.drawRightString(PAGE_W - MR, MB - 24, f"Page {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------- generated sections
def load_pyq():
    with open(os.path.join(BUILD, "pyq_analysis.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(os.path.join(BUILD, "pyq_summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    return rows, summary


def add_front_matter(story):
    st_h = S("fmh", fontName="DVS-B", fontSize=15, leading=19, textColor=NAVY, spaceAfter=6)
    st_p = S("fmp", fontSize=9.0, leading=12.8, spaceAfter=4)
    story.append(Paragraph("About this edition", st_h))
    story.append(Paragraph(
        "These are the <b>complete class-wise physics notes of Sakshi Ma'am (Eduteria, 72nd BPSC batch)</b> — all "
        "19 lecture PDFs — re-arranged into 16 topic-wise units for A4 printing. <b>Every fact, table, formula, "
        "example, chart and diagram of the original notes is kept</b>; only the repetition is gone. Lecture cover "
        "pages, watermarks, running headers/footers and the contact strip were removed.", st_p))
    story.append(Paragraph(
        "Where a topic appeared in more than one lecture, the most complete version is kept and the repeats are "
        "merged into it; a green <b>“De-dup note”</b> strip records exactly what was merged or moved, so nothing is "
        "lost silently. Formulas that came out garbled in the source typesetting were re-typed from the rendered "
        "pages. Obvious slips in the lectures are fixed <i>visibly</i> in coral <b>“Source correction”</b> strips — "
        "the original wording is always quoted.", st_p))
    story.append(Paragraph(
        "<b>What was added by the editor is always marked.</b> Anything that is <u>not</u> in the lecture PDFs — an "
        "extra data table, a derivation the notes skipped, a definition needed to make a PYQ answerable — sits in a "
        "<b>blue “ADDED BY EDITOR” box</b>. Amber <b>“PYQ lens”</b> strips show how BPSC has actually asked the "
        "concept, quoting the exam and question number.", st_p))
    story.append(Spacer(1, 4))
    rows = [["#", "Source lecture (PDF in “physic notes eduteria/”)", "Pages", "Now in"]]
    mapping = [
        ("01 Introduction to Physics (course plan + light intro + reflection)", "3", "Front matter, Units 2 & 4"),
        ("02 Light Part-01 (colour mixing, plane & spherical mirrors)", "3", "Units 2 & 4"),
        ("03 Light Part-02 (mirror formula, refraction, TIR)", "3", "Units 2 & 3"),
        ("04 Light Part-03 (lenses, power, human eye, defects)", "3", "Unit 3"),
        ("05 Light Part-04 (dispersion, scattering, wave optics, instruments)", "4", "Unit 4"),
        ("06 Wave (EM waves, EM spectrum table)", "2 (+1 blank)", "Unit 5"),
        ("07 Sound Wave", "4", "Units 5 & 6"),
        ("08 Heat-01 (heat, transfer modes, specific/latent heat)", "3", "Unit 7"),
        ("09 Temperature (state change, scales, thermometers)", "3", "Unit 7"),
        ("10 Heat Part-3 (expansion, radiation laws, thermodynamics)", "4", "Unit 8"),
        ("11 Kinematics", "3", "Unit 9"),
        ("12 Motion Part-02 (graphs, Newton's laws, Kepler, friction)", "5", "Units 9, 10 & 11"),
        ("13 Circular Motion & Gravitation", "3", "Unit 11"),
        ("14 Gravitation & Mechanical Properties of Fluids", "4", "Units 11 & 12"),
        ("15 Electricity Part-01 (charge, Coulomb, field, potential, current)", "2", "Unit 13"),
        ("16 Electricity Part-02 (Ohm's law, resistance, combinations)", "2", "Unit 13"),
        ("17 Electricity Part-03 (power, effects, instruments, devices, lamps, safety)", "4", "Unit 14"),
        ("18 Magnetism", "3", "Unit 15"),
        ("19 Unit & Dimension, Photoelectric, WPE, Nuclear, Measurement", "6", "Units 1, 10 & 16"),
    ]
    for i, (a, b, c) in enumerate(mapping, 1):
        rows.append([str(i), a, b, c])
    story.append(make_table(rows, [4, 58, 12, 26], "#0F2A44", font=7.9))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Lecture-1 course plan (as printed in the source — kept for reference)", st_h))
    plan = [["Block", "Topics announced in Lecture 1"],
            ["Light (1)", "Nature and properties of light, reflection of light and mirrors, types of mirrors and their uses."],
            ["Light (2)", "Refraction of light, total internal reflection, lenses and their types, uses of lenses and correction of eye defects."],
            ["Light (3)", "Scattering of light, dispersion of light, polarization, interference and their examples."],
            ["Waves", "Types of waves, mechanical waves and their properties, non-mechanical waves (electromagnetic waves), their properties and uses."],
            ["Sound waves", "Speed of sound waves, echo, Mach number, shock waves, Doppler effect."],
            ["Heat (1)", "Heat and temperature, thermometer and its scale, methods of heat conduction, thermal expansion and its examples."],
            ["Heat (2)", "Anomalous behaviour of water, specific heat, latent heat, evaporation and humidity (relative humidity), precipitation."],
            ["Motion", "Basic elements of motion – distance, displacement, speed, velocity, and acceleration, force and types of force, Newton's laws of motion."],
            ["Types of motion", "Linear motion, uniform circular motion, rotational motion, projectile motion, periodic motion, oscillatory motion, simple harmonic motion, etc."],
            ["Universal gravitation", "Gravitational force and gravity, Newton's law of gravitation, gravitational acceleration, changes in the value of g, orbital velocity, escape velocity, Kepler's planetary laws."],
            ["Mechanical properties of fluids", "Cohesive and cohesive forces, fluid pressure and Pascal's law, surface tension and capillarity, streamline flow and Bernoulli's theorem, buoyancy and Archimedes' principle."],
            ["Electricity (1)", "Charge, electric field, electric field intensity, electric potential, potential difference, electric capacitance and capacitors, electric current, Ohm's law and resistance."],
            ["Electricity (2)", "Electric power, commercial units (kilowatt-hour units), electromagnetic induction, electric motors and generators."],
            ["Magnetism", "Magnetic field, magnetic flux, magnetic permeability, magnetic susceptibility, types of magnetic materials, geomagnetism."]]
    story.append(make_table(plan, [18, 82], "#0F2A44", font=7.9))
    story.append(Spacer(1, 4))
    story.append(make_strip("↻ De-dup note",
                            "Several items of this printed plan (Mach number, shock waves, Doppler effect, anomalous "
                            "expansion of water, humidity, capacitors, electromagnetic induction, flux, permeability, "
                            "geomagnetism) never received their own lecture; the missing ones that BPSC has asked about "
                            "are supplied in clearly marked blue editor boxes inside the relevant unit.", GREEN, GREEN_PALE))
    page_break(story)
    story.append(Paragraph("Major duplicate topics resolved", st_h))
    merges = [
        "Scattering of light & Rayleigh's law (Lecture 1 p. 3 and Lecture 5 p. 2) → kept once in Unit 4; the Lecture-1 formula strip merged there.",
        "Reflection of light — Lecture 1 prints the laws on p. 3 and again on p. 4 (regular/diffused) and Lecture 2 repeats the plane-mirror image properties → one sequence in Unit 2.",
        "Periscope & kaleidoscope — Lecture 2 (uses of plane mirror) and Lecture 5 (optical instruments) → kept in Unit 4, cross-referenced from Unit 2.",
        "Mirror formula & magnification — Lecture 3 opens with them; moved next to spherical mirrors (Unit 2) so the mirror story reads in one place.",
        "Lens formula & magnification are printed in Lecture 4 for both convex and concave lenses → one formula block in Unit 3.",
        "Heat-transfer modes — Lecture 8 (detailed) and Lecture 9 (comparison table) → both kept together in Unit 7 (table + details).",
        "Temperature definition, SI unit and the temperature-scales table — printed in Lecture 8, Lecture 9 p. 2 and again in Lecture 9 p. 4 → one master table (5 scales) in Unit 7.",
        "Velocity of sound: Newton's formula and Laplace correction are each printed twice on Lecture 7 p. 3 → one derivation ladder in Unit 6.",
        "Kinematics: the distance/displacement and speed/velocity definitions are written twice on Lecture 11 p. 2 → once, plus the comparison table.",
        "Newton's first law is stated three times in Lecture 12 (statement, 'Galileo's law of inertia', inertia of rest example printed twice) → one statement + three inertia cases in Unit 10.",
        "Kepler's laws (Lecture 12 p. 5) sit between momentum and friction in the source; moved to gravitation (Unit 11).",
        "Escape velocity is introduced twice on Lecture 14 p. 2 (and a stray fragment repeats under Pascal's law on p. 3) → one section in Unit 11.",
        "Oersted's discovery is narrated twice on Lecture 18 pp. 2–3 → one numbered list in Unit 15.",
        "Fleming's rules: the paragraph and the two hand-rule lists on Lecture 18 p. 4 → one table in Unit 15.",
        "Lecture 19 prints the dimensional-formula introduction and the 'how to write a dimensional formula' question twice (pp. 3–4) → once in Unit 1; both dimension tables kept (they list different quantities).",
        "Lecture 17 lists 'Advantages of CFLs' under LEDs (a heading slip) and repeats the fuse under 'Safety devices' → merged in Unit 14 with a correction strip.",
    ]
    for m in merges:
        story.append(Paragraph(rich(m), S("mrg", fontSize=8.6, leading=11.8, leftIndent=12, bulletIndent=2, spaceAfter=2.4),
                               bulletText="✔"))
    story.append(Spacer(1, 8))
    story.append(Paragraph("How to read the colour code", st_h))
    legend = [
        ("De-dup note", GREEN, GREEN_PALE, "what was merged or moved, and from where (nothing is dropped silently)."),
        ("Source correction", CORAL, CORAL_PALE, "a typo or slip in the lecture text, fixed visibly with the original wording quoted."),
        ("ADDED BY EDITOR", BLUE, BLUE_PALE, "material that is NOT in the lecture PDFs (extra data, a missing derivation, a topic BPSC asks but the lectures skipped)."),
        ("PYQ lens", AMBER, AMBER_PALE, "how BPSC has asked this exact point — exam and question number quoted; full text in Appendix A."),
    ]
    rows = [[Paragraph(f"<font color='{fg.hexval()}'><b>{n}</b></font>", ST["cell"]), Paragraph(d, ST["cell"])] for n, fg, bg, d in legend]
    t = Table(rows, colWidths=[AVAIL * 0.24, AVAIL * 0.76])
    st = [("GRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for r, (_, fg, bg, _) in enumerate(legend):
        st.append(("BACKGROUND", (0, r), (0, r), bg))
    t.setStyle(TableStyle(st))
    story.append(t)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Suggested passes:</b> (1) read the PYQ Topic Priority pages first and mark the A-priority units; (2) study "
        "each unit — the amber strips tell you which lines have already been examined; (3) finish with Appendix A, "
        "which lists every reviewed physics question with its answer and a one-line reason.", st_p))


def add_priority_section(story, rows, summary):
    st_h = S("prh", fontName="DVS-B", fontSize=15, leading=19, textColor=NAVY, spaceAfter=6)
    st_p = S("prp", fontSize=9.0, leading=12.8, spaceAfter=4)
    band = make_unit_band("★", "PYQ Topic Priority — what BPSC actually asks in physics",
                          "all physics questions of 56–59th (2015), 60–62nd, 63rd … 71st (2025) BPSC Prelims — manually classified",
                          "#0F2A44")
    band._toc = (0, "PYQ Topic Priority (56–59th → 71st BPSC)")
    story.append(band); story.append(Spacer(1, 6))
    n_all, n_rec = summary["total_questions"], summary["recent_questions"]
    ex = summary["exam_counts"]
    story.append(Paragraph(
        f"All <b>1,623 questions</b> of the eleven papers were read one by one; <b>{n_all}</b> are physics or "
        f"physics-adjacent (<b>{n_rec}</b> of them in the last six papers, 66th–71st). Physics is a steady block: "
        f"<b>≈10–11 questions per paper</b> since the 64th BPSC (64th {ex['64th BPSC']}, 65th {ex['65th BPSC']}, "
        f"66th {ex['66th BPSC']}, 67th {ex['67th BPSC']}, 68th {ex['68th BPSC']}, 69th {ex['69th BPSC']}, "
        f"70th {ex['70th BPSC']}, 71st {ex['71st BPSC (2025)']}) against only 3–4 in the 56–59th, 60–62nd and 63rd papers. "
        "Questions are counted against the unit of this book that answers them; 'recent' = 66th–71st. "
        "Score = all + recent + 0.5 × papers in which the topic appeared, so a topic that keeps returning ranks above a one-off cluster.", st_p))
    story.append(Paragraph("Topic ranking (all papers, recent papers weighted)", st_h))
    trows = [["Rank", "Unit / topic", "All Qs", "Recent Qs (66–71st)", "Papers", "Priority"]]
    for r in summary["topic_ranking"]:
        trows.append([str(r["rank"]), r["topic"], str(r["all_questions"]), str(r["recent_questions"]),
                      f'{r["papers_present"]} ({r["recent_papers_present"]} recent)', r["priority"]])
    t = make_table(trows, [7, 49, 9, 14, 12, 9], "#0F2A44", font=8.0)
    story.append(t)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Priority A</b> = asked in ≥6 of the last-six-paper questions, or ≥9 questions overall with presence in ≥3 recent papers. "
        "<b>B</b> = ≥3 recent questions or ≥6 overall. <b>C</b> = occasional. Unit numbers refer to the units of this book.", st_p))
    story.append(Paragraph("What the pattern says — read this before the units", st_h))
    insights = [
        "**Modern & nuclear physics (Unit 16) is the single most examined block** — 19 questions across 10 of 11 papers: photoelectric effect (Einstein's Nobel 64th; photoelectric cell 69th; photodiode 68th), nucleus & nuclide arithmetic (65th, 66th, 67th), alpha/cosmic radiation, Higgs boson, fusion breakthrough, Manhattan Project, Thomson's atomic model (70th). Expect 1–2 questions every year.",
        "**Mechanics has become numerical since the 68th paper.** Laws of motion / friction / work-energy (Unit 10) drew 9 questions in the last four papers alone — the 71st paper set four short sums (F = ma, W = F·s, friction at constant velocity, energy conservation) plus a kinematics one (s = ½at²). Practise the one-line formulas in Units 9–10.",
        "**Current electricity & household electricity (Units 13–14)** are asked every year: units of power (watt, kWh → joule), ammeter/voltmeter, motor & dynamo energy conversions, Ohm's law forms, parallel-resistance sum (66th), semiconductor resistance vs temperature, short circuit & fuse (71st), Faraday constant, tesla (70th).",
        "**Units, dimensions & instruments (Unit 1)** gave a cluster of 9 questions in the 64th–65th papers (angstrom, hertz, pressure unit, strain, hygrometer, light-year, odometer). They are cheap marks — memorise the SI table, the 'no-unit' quantities and the instrument list.",
        "**Optics is asked in small, conceptual bites** — spectrum range (3900–7600 Å, 63rd), red vs violet wavelength (64th), speed of light in media (67th), frequency unchanged on refraction (66th), concave-mirror image at C (69th), colour mixing (69th), plane-mirror focal length (71st), black strips on a lens (68th). Wave optics/instruments (Unit 4) appears rarely — read once, keep the rainbow angles and scattering law.",
        "**Heat & sound**: Celsius→Fahrenheit conversion twice (64th, 65th), poorest heat conductor (66th), radiation needs no medium (70th), sound is longitudinal (65th), pitch ↔ frequency (68th), speed of sound in solids (71st). The thermodynamics laws, Stefan/Wien and thermal expansion (Unit 8) have appeared only through the solar constant (70th) and the Thomson effect (67th).",
        "**Gravitation (Unit 11)** keeps recurring in reasoning form: weight at the equator if the spin increases (67th), free fall on the Moon (69th), centripetal force (68th), centrifugation in a washing machine (67th), comets' orbits (70th).",
        "Physics-flavoured current affairs (LIGO-India, fusion ignition, space missions, pulsars) count as 'extended' — glance at them in Appendix A; they are not in the lectures and are marked as editor additions where mentioned.",
    ]
    for m in insights:
        story.append(Paragraph(rich(m), S("ins", fontSize=8.8, leading=12.2, leftIndent=12, bulletIndent=2, spaceAfter=3), bulletText="▶"))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Paper-by-paper physics load", st_h))
    prow = [["Paper"] + [e.replace(" BPSC", "").replace(" (Combined)", "").replace(" (2015)", "").replace(" (2025)", "") for e in summary["exam_counts"]],
            ["Physics Qs"] + [str(v) for v in summary["exam_counts"].values()]]
    story.append(make_table(prow, None, "#0F2A44", font=8.0))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Most-repeated question stems (learn these cold)", st_h))
    hot = [
        "Unit of electric power → watt (64th Q11, 65th Q120); device to measure current → ammeter (64th Q14, 65th Q119).",
        "°C → °F: 40 °C = 104 °F (64th Q10); 50 °C = 122 °F (65th Q116). Formula F = 9C/5 + 32.",
        "Frequency is measured in hertz (64th Q4, 65th Q117); angstrom = unit of wavelength (64th Q3); light-year = distance (66th Q5).",
        "Unit of pressure: N/m² (64th Q20), kg/cm² (65th Q111). Strain has no unit (65th Q114); pressure is a scalar (65th Q113); speed is not a vector (67th Q67).",
        "Photoelectric effect: Einstein's Nobel (64th Q16); photoelectric cell converts light → electrical energy (69th Q16); photodiode for digital use (68th Q113).",
        "Infrared radiation for muscle/body ache (66th Q1, 70th Q45) — the same fact twice in five papers.",
        "Electric motor: electrical → mechanical (64th Q12); dynamo produces AC (69th Q26); transformer works only on AC; fuse = protective device (71st Q130).",
        "Nucleus arithmetic: mass number = p + n (65th Q92); neutrons in ₉₄Pu²⁴² = 148 (66th Q9); nucleus = protons + neutrons (67th Q75).",
    ]
    for m in hot:
        story.append(Paragraph(rich(m), S("hot", fontSize=8.6, leading=11.8, leftIndent=12, bulletIndent=2, spaceAfter=2.4), bulletText="★"))


def add_appendix(story, rows):
    st_h = S("aph", fontName="DVS-B", fontSize=15, leading=19, textColor=NAVY, spaceAfter=6)
    band = make_unit_band("A", "Appendix A — every reviewed physics PYQ (56–59th → 71st BPSC)",
                          "verbatim question text from the supplied workbooks; study answer, status and one-line reason", "#0F2A44")
    band._toc = (0, "Appendix A — Complete reviewed PYQ list")
    page_break(story); story.append(band); story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Status codes: <b>source-key</b> = answer follows the verified key in the workbook; <b>added-answer</b> = the workbook "
        "has no key for that paper (71st BPSC), the answer was worked out by the editor and the working is shown; "
        "<b>editor-corrected</b> = the workbook key conflicts with standard references and both are shown. Scope "
        "<b>core</b> = taught in the lectures; <b>extended</b> = physics-adjacent context.", S("app", fontSize=8.8, leading=12, spaceAfter=6)))
    by_exam = {}
    for r in rows:
        by_exam.setdefault(r["exam"], []).append(r)
    qst = S("q", fontSize=8.6, leading=11.4)
    ost = S("o", fontSize=8.0, leading=10.6, textColor=colors.HexColor("#2C3A4A"))
    ast = S("a", fontSize=8.0, leading=10.6)
    for exam, lst in by_exam.items():
        story.append(Paragraph(f"{esc(exam)} — {len(lst)} physics questions", st_h))
        for r in lst:
            tag = {"source-key": ("#3E7A2A", "source-key"), "added-answer": ("#2B6CB0", "added-answer"),
                   "editor-corrected": ("#C84B2F", "editor-corrected")}[r["status"]]
            head = Paragraph(f"<b>Q{r['q_no']}</b> · <font color='#6A7480'>{esc(r['topic'])}</font> · "
                             f"<font color='{tag[0]}'><b>{tag[1]}</b></font> · <font color='#6A7480'>{r['scope']}</font>", ost)
            q = Paragraph(esc(r["question"]), qst)
            opts = " &nbsp;|&nbsp; ".join(f"({chr(65 + i)}) {esc(o.strip())}" for i, o in enumerate(r["options"].split(" | ")))
            o = Paragraph(opts, ost)
            ans = f"<b>Answer:</b> {esc(r['study_answer'])}"
            if r["status"] == "editor-corrected":
                ans += f" &nbsp;<font color='#C84B2F'>(workbook key: {esc(r['source_answer'])})</font>"
            a = Paragraph(ans + f" &nbsp;<font color='#5A6470'>— {esc(r['editor_note'])}</font>", ast)
            t = Table([[head], [q], [o], [a]], colWidths=[AVAIL])
            t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.4, LINE), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F7FA")),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                   ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            story.append(KeepTogether(t)); story.append(Spacer(1, 3))


def optimize(path):
    import pymupdf
    doc = pymupdf.open(path)
    n_pages, n_imgs = len(doc), sum(len(p.get_images()) for p in doc)
    doc.rewrite_images(dpi_threshold=10000, dpi_target=150, quality=88, lossless=True, color=True, gray=True)
    tmp = path + ".opt"
    doc.save(tmp, garbage=4, deflate=True); doc.close()
    os.replace(tmp, path)
    print(f"optimized: {n_pages} pages, {n_imgs} images -> {os.path.getsize(path) / 1e6:.1f} MB")


def main():
    files = sorted(glob.glob(os.path.join(BUILD, "content", "*.txt")))
    for f in files:
        for line in open(f, encoding="utf-8"):
            if line.startswith("UNIT "):
                parts = line.split("|")
                UNIT_LIST.append((parts[0][5:].strip(), parts[1].strip()))
    rows, summary = load_pyq()
    doc = NotesDoc(OUT)
    story = [Spacer(1, 1), NextPageTemplate("body"), PageBreak()]
    add_front_matter(story)
    page_break(story)
    story.append(Paragraph("Contents", S("toct", fontName="DVS-B", fontSize=17, leading=21, textColor=NAVY, spaceAfter=8)))
    toc = TableOfContents()
    toc.levelStyles = [
        S("t0", fontName="DVS-B", fontSize=10.0, leading=15, textColor=NAVY, leftIndent=2, spaceBefore=5),
        S("t1", fontSize=8.6, leading=12.2, leftIndent=16, textColor=colors.HexColor("#24303E")),
    ]
    toc.dotsMinLevel = 0
    story.append(toc)
    page_break(story)
    add_priority_section(story, rows, summary)
    unit_state = {"no": "0", "title": "", "accent": ACCENTS[0]}
    for f in files:
        parse_file(f, story, unit_state)
    add_appendix(story, rows)
    doc.multiBuild(story)
    print("built:", OUT)
    optimize(OUT)


if __name__ == "__main__":
    main()
