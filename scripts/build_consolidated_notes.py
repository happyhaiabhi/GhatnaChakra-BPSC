#!/usr/bin/env python3
"""Build the consolidated, de-duplicated A4 chemistry notes PDF from the DSL
content files in build_consolidated/content/*.txt."""
import os, re, glob
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Image as RLImage,
                                PageBreak, NextPageTemplate, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from PIL import Image as PILImage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "build_consolidated", "figures")
OUT = os.path.join(ROOT, "BPSC_Chemistry_Consolidated_Notes_A4.pdf")

pdfmetrics.registerFont(TTFont("DVS", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVS-B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVSerif", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("DVSerif-B", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"))
addMapping("DVS", 0, 0, "DVS"); addMapping("DVS", 1, 0, "DVS-B")
addMapping("DVS", 0, 1, "DVS"); addMapping("DVS", 1, 1, "DVS-B")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 40, 40, 46, 44
AVAIL = PAGE_W - ML - MR

ACCENTS = ["#1F5AA8", "#0E7C66", "#B34700", "#7A1F5C", "#245BCC", "#8C6D0F",
           "#A82828", "#0F6E8C", "#5B3E96", "#1D7A34", "#9A3B12", "#4A5A00"]
GREY = colors.HexColor("#5A6470")
LINE = colors.HexColor("#C9D2DC")

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def rich(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\^\{(.+?)\}", r"<super rise='3' size='6.4'>\1</super>", t)
    t = re.sub(r"_\{(.+?)\}", r"<sub fall='2' size='6.4'>\1</sub>", t)
    return t

def S(name, **kw):
    base = dict(fontName="DVS", fontSize=9.2, leading=12.6, textColor=colors.HexColor("#1B2430"),
                spaceBefore=0, spaceAfter=0)
    base.update(kw)
    return ParagraphStyle(name, **base)

ST = {
    "body": S("body", spaceAfter=3.2),
    "b0":   S("b0", leftIndent=14, bulletIndent=3, spaceAfter=2.4),
    "b1":   S("b1", leftIndent=27, bulletIndent=16, spaceAfter=2.0, fontSize=8.9, leading=12.0),
    "h2":   S("h2", fontName="DVS-B", fontSize=11.6, leading=14, spaceBefore=9, spaceAfter=3.5),
    "h3":   S("h3", fontName="DVS-B", fontSize=9.8, leading=12.5, spaceBefore=6, spaceAfter=2.5,
              textColor=colors.HexColor("#24303E")),
    "eq":   S("eq", fontName="DVS-B", fontSize=9.4, leading=13, alignment=TA_CENTER),
    "cap":  S("cap", fontSize=7.6, leading=9.6, textColor=GREY, alignment=TA_CENTER, spaceBefore=2.5),
    "note": S("note", fontSize=8.0, leading=10.8, textColor=colors.HexColor("#3E4A38")),
    "cell": S("cell", fontSize=8.3, leading=10.6),
    "cellh":S("cellh", fontName="DVS-B", fontSize=8.4, leading=10.6, textColor=colors.white),
    "boxh": S("boxh", fontName="DVS-B", fontSize=9.0, leading=11.5, textColor=colors.white),
}

UNIT_TITLES = []   # (num, title, accent)
FIGCTR = {}

def fig_path(fname):
    if not os.path.splitext(fname)[1]:
        fname += ".png"
    return os.path.join(FIG, fname)

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
        ("TOPPADDING", (0, 1), (0, 2), 2), ("BOTTOMPADDING", (0, 0), (0, 1), 2),
    ]))
    return t

def make_table(rows, widths, accent, zebra=True):
    c = colors.HexColor(accent)
    data = []
    for i, row in enumerate(rows):
        st = ST["cellh"] if i == 0 else ST["cell"]
        data.append([Paragraph(rich(cell), st) for cell in row])
    n = len(rows[0])
    for r in range(len(rows)):
        while len(rows[r]) < n:
            rows[r].append("—")
        rows[r] = rows[r][:n]
    if widths and len(widths) == n:
        colw = [AVAIL * w / 100.0 for w in widths]
    else:
        lens = [max(len(rows[r][c_]) + 2 for r in range(len(rows))) for c_ in range(n)]
        tot = sum(lens)
        colw = [max(AVAIL * 0.09, AVAIL * l / tot) for l in lens]
        sc = AVAIL / sum(colw); colw = [w * sc for w in colw]
    t = Table(data, colWidths=colw, repeatRows=1)
    style = [("GRID", (0, 0), (-1, -1), 0.5, LINE),
             ("BACKGROUND", (0, 0), (-1, 0), c),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2)]
    if zebra:
        for r in range(1, len(rows)):
            if r % 2 == 0:
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
    w = min(maxw, pw * 0.36)
    h = w * ph / pw
    maxh = 560
    if h > maxh:
        h = maxh; w = h * pw / ph
    img = RLImage(p, width=w, height=h)
    cap = Paragraph(f"<b>Fig. {unit_no}-{FIGCTR[unit_no]}</b> · {esc(caption)}" if caption else
                    f"<b>Fig. {unit_no}-{FIGCTR[unit_no]}</b>", ST["cap"])
    FIGCTR[unit_no] += 1
    inner = Table([[img], [cap]], colWidths=[w + 8])
    inner.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                               ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                               ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                               ("LEFTPADDING", (0, 0), (-1, -1), 3),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                               ("TOPPADDING", (0, 0), (-1, 0), 4),
                               ("BOTTOMPADDING", (0, -1), (0, -1), 4)]))
    return inner

def make_imgs(items, unit_no):
    n = len(items)
    cw = (AVAIL - 6 * (n - 1)) / n
    cells, caps = [], []
    for fname, caption in items:
        p = fig_path(fname)
        with PILImage.open(p) as im:
            pw, ph = im.size
        w = cw - 8
        h = w * ph / pw
        if h > 300:
            h = 300; w = h * pw / ph
        cells.append(RLImage(p, width=w, height=h))
        caps.append(Paragraph(f"<b>Fig. {unit_no}-{FIGCTR[unit_no]}</b> · {esc(caption)}", ST["cap"]))
        FIGCTR[unit_no] += 1
    t = Table([cells, caps], colWidths=[cw] * n)
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                           ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                           ("BOX", (0, 0), (0, -1), 0.5, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                           ("TOPPADDING", (0, 0), (-1, 0), 3), ("BOTTOMPADDING", (0, -1), (0, -1), 3)]))
    return t

def make_eq(text, accent):
    p = Paragraph(rich(text), ST["eq"])
    t = Table([[p]], colWidths=[AVAIL])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF6E8")),
                           ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E3D6AC")),
                           ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
    return t

def make_note(text):
    p = Paragraph(f"<b>↻ De-dup note:</b> {rich(text)}", ST["note"])
    t = Table([[p]], colWidths=[AVAIL])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF5EC")),
                           ("LINEBEFORE", (0, 0), (0, -1), 2.2, colors.HexColor("#5E8C4A")),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    return t

def make_box(title, body, accent):
    c = colors.HexColor(accent)
    rows = [[Paragraph(f"<b>{esc(title)}</b>", ST["boxh"])]]
    styles = [("BACKGROUND", (0, 0), (0, 0), c),
              ("SPAN", (0, 0), (0, 0)),
              ("BOX", (0, 0), (-1, -1), 0.7, c),
              ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (0, 0), 5)]
    for i, b in enumerate(body):
        rows.append([Paragraph(rich(b), ST["body"])])
        styles.append(("TOPPADDING", (0, i + 1), (0, i + 1), 3))
        if i == len(body) - 1:
            styles.append(("BOTTOMPADDING", (0, i + 1), (0, i + 1), 6))
        if i % 2 == 0:
            styles.append(("BACKGROUND", (0, i + 1), (0, i + 1), colors.HexColor("#F7FAFC")))
    t = Table(rows, colWidths=[AVAIL])
    t.setStyle(TableStyle(styles))
    return t

# ---------------------------------------------------------------- parsing
def parse_file(path, story, unit_state):
    accent = unit_state["accent"]
    unit_no = unit_state["no"]
    pending_widths = None
    tbl_rows = None
    DIRECTIVES = ("UNIT ", "H2 ", "H3 ", "P ", "B ", "BB ", "EQ ", "NOTE ", "BOX ",
                  "IMG ", "IMGS ", "TBL ", "TBLW ", "PB", "SP", "#")
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n"); i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            if tbl_rows:
                story.append(Spacer(1, 3))
                story.append(make_table(tbl_rows, pending_widths, accent))
                story.append(Spacer(1, 6))
                tbl_rows = None; pending_widths = None
            continue
        if tbl_rows and not line.startswith(DIRECTIVES):
            tbl_rows.append(line.split("~"))
            continue
        if line.startswith("TBLW "):
            if tbl_rows:
                story.append(Spacer(1, 3))
                story.append(make_table(tbl_rows, pending_widths, accent))
                story.append(Spacer(1, 6))
                tbl_rows = None
            pending_widths = [float(x) for x in line[5:].split(",")]
            continue
        if line.startswith("TBLW "):
            pending_widths = [float(x) for x in line[5:].split(",")]
            continue
        if line.startswith("UNIT "):
            parts = line.split("|")
            num = parts[0][5:].strip(); title = parts[1].strip()
            source = parts[2].strip() if len(parts) > 2 else ""
            unit_state["no"] = num; unit_state["title"] = title
            accent = ACCENTS[(int(num) - 1) % len(ACCENTS)]
            unit_state["accent"] = accent
            unit_no = num; FIGCTR[unit_no] = 1
            if story:
                story.append(PageBreak())
            band = make_unit_band(num, title, source, accent)
            band._toc = (0, f"Unit {num} — {title}")
            story.append(band)
            story.append(Spacer(1, 6))
            continue
        if line.startswith("H2 "):
            txt = line[3:].strip()
            p = Paragraph(rich(txt), ParagraphStyle("h2x", parent=ST["h2"], textColor=colors.HexColor(accent),
                                                    borderPadding=(0, 0, 1, 0)))
            p._toc = (1, txt)
            story.append(p)
            story.append(HRFlowableMini(accent))
            continue
        if line.startswith("H3 "):
            story.append(Paragraph(rich(line[3:].strip()), ST["h3"]))
            continue
        if line.startswith("P "):
            story.append(Paragraph(rich(line[2:].strip()), ST["body"]))
            continue
        if line.startswith("BB "):
            story.append(Paragraph(rich(line[3:].strip()), ST["b1"], bulletText="–"))
            continue
        if line.startswith("B "):
            story.append(Paragraph(rich(line[2:].strip()), ST["b0"], bulletText="•"))
            continue
        if line.startswith("EQ "):
            story.append(make_eq(line[3:].strip(), accent))
            story.append(Spacer(1, 4))
            continue
        if line.startswith("NOTE "):
            story.append(Spacer(1, 2))
            story.append(make_note(line[5:].strip()))
            story.append(Spacer(1, 4))
            continue
        if line.startswith("BOX "):
            title, _, body = line[4:].partition("::")
            body_items = [b.strip() for b in body.split(";") if b.strip()] if body.strip() else []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(DIRECTIVES):
                body_items.append(lines[i].strip()); i += 1
            story.append(make_box(title.strip(), body_items, accent))
            story.append(Spacer(1, 5))
            continue
        if line.startswith("IMG "):
            parts = line[4:].split("|")
            fname = parts[0].strip()
            cap = parts[1].strip() if len(parts) > 1 else ""
            pct = float(parts[2]) if len(parts) > 2 and parts[2].strip() else 96
            story.append(Spacer(1, 3))
            story.append(make_img(fname, cap, pct, unit_no))
            story.append(Spacer(1, 5))
            continue
        if line.startswith("IMGS "):
            items = []
            for it in line[5:].split(";;"):
                f, _, c = it.partition("|")
                if f.strip():
                    items.append((f.strip(), c.strip()))
            story.append(Spacer(1, 3))
            story.append(make_imgs(items, unit_no))
            story.append(Spacer(1, 5))
            continue
        if line.startswith("TBL "):
            tbl_rows = [line[4:].strip().split("~")]
            continue
        if line.strip() == "PB":
            story.append(PageBreak())
            continue
        if line.strip() == "SP":
            story.append(Spacer(1, 6))
            continue
        raise ValueError(f"Unknown line in {path}: {line[:60]!r}")
    if tbl_rows:
        story.append(Spacer(1, 3))
        story.append(make_table(tbl_rows, pending_widths, accent))

class HRFlowableMini(Spacer):
    """Thin accent rule under H2 headings."""
    def __init__(self, accent):
        super().__init__(0, 2.6)
        self._accent = accent
    def draw(self):
        self.canv.setStrokeColor(colors.HexColor(self._accent))
        self.canv.setLineWidth(1.1)
        self.canv.line(0, 1, 46, 1)
        self.canv.setStrokeColor(LINE)
        self.canv.setLineWidth(0.5)
        self.canv.line(48, 1, AVAIL, 1)

# ---------------------------------------------------------------- doc
class NotesDoc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=ML, rightMargin=MR,
                         topMargin=MT, bottomMargin=MB,
                         title="72nd BPSC Chemistry — Consolidated Notes (A4 rearranged edition)",
                         author="Chemistry by Sakshi Ma'am (Eduteria) — consolidated & de-duplicated", **kw)
        self.unit_name = ""
        frame_cover = Frame(0, 0, PAGE_W, PAGE_H, id="cover")
        frame_body = Frame(ML, MB, PAGE_W - ML - MR, PAGE_H - MT - MB, id="body")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[frame_cover], onPage=draw_cover),
            PageTemplate(id="body", frames=[frame_body], onPage=draw_body),
        ])

    def afterFlowable(self, fl):
        if hasattr(fl, "_toc"):
            level, text = fl._toc
            self.notify("TOCEntry", (level, text, self.page))

def draw_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#123C6B"))
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#0E2F55"))
    canvas.rect(0, PAGE_H - 240, PAGE_W, 240, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#1E5FA8"))
    canvas.rect(0, PAGE_H - 252, PAGE_W, 12, stroke=0, fill=1)
    # decorative molecules
    canvas.setStrokeColor(colors.HexColor("#3E7BC0"))
    canvas.setLineWidth(1.2)
    import math, random
    random.seed(7)
    for i in range(14):
        x = random.uniform(30, PAGE_W - 30); y = random.uniform(60, PAGE_H - 300)
        r = random.uniform(3, 9)
        canvas.setFillColor(colors.HexColor("#2C6AA8"))
        canvas.circle(x, y, r, stroke=0, fill=1)
        if i % 3 == 0:
            canvas.line(x, y, x + random.uniform(20, 44), y + random.uniform(-24, 24))
    canvas.setFillColor(colors.white)
    canvas.setFont("DVS-B", 15)
    canvas.drawString(48, PAGE_H - 78, "EDUTERIA  ·  72nd BPSC PRELIMS  ·  CHEMISTRY")
    canvas.setFont("DVS-B", 34)
    canvas.drawString(46, PAGE_H - 140, "CHEMISTRY")
    canvas.setFont("DVS-B", 21)
    canvas.setFillColor(colors.HexColor("#FFD465"))
    canvas.drawString(48, PAGE_H - 172, "Consolidated Class Notes — A4 Edition")
    canvas.setFillColor(colors.HexColor("#C9DCEF"))
    canvas.setFont("DVS", 10.5)
    canvas.drawString(48, PAGE_H - 200, "The complete class-wise notes of Chemistry by Sakshi Ma'am — re-arranged topic-wise,")
    canvas.drawString(48, PAGE_H - 215, "duplicate lectures merged, every chart & visual explanation kept.")
    # unit chips
    canvas.setFont("DVS-B", 11)
    canvas.setFillColor(colors.white)
    canvas.drawString(48, PAGE_H - 292, "12 UNITS INSIDE")
    y = PAGE_H - 316
    col_x = [48, 232, 416]
    for i, (num, title) in enumerate(UNIT_LIST):
        x = col_x[i % 3]
        yy = y - (i // 3) * 26
        canvas.setFillColor(colors.HexColor("#173F6F"))
        canvas.roundRect(x, yy - 6, 176, 22, 5, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#FFD465"))
        canvas.setFont("DVS-B", 9.2)
        canvas.drawCentredString(x + 20, yy + 1, num)
        canvas.setFillColor(colors.white)
        canvas.setFont("DVS", 7.6)
        t = title if len(title) <= 24 else title[:23] + "…"
        canvas.drawString(x + 36, yy, t)
    # bottom info
    canvas.setFillColor(colors.white)
    canvas.setFont("DVS-B", 12)
    canvas.drawString(48, 118, "Re-arranged & de-duplicated edition")
    canvas.setFont("DVS", 9)
    canvas.setFillColor(colors.HexColor("#C9DCEF"))
    canvas.drawString(48, 100, "Source: Eduteria Chem Notes Class Wise.pdf (157 pages, 12 lecture files)")
    canvas.drawString(48, 86, "Chemistry by Sakshi Ma'am  ·  Contact: 8252405793, 9431216685")
    canvas.setFillColor(colors.HexColor("#FFD465"))
    canvas.setFont("DVS", 9)
    canvas.drawRightString(PAGE_W - 48, 86, "Print-ready A4 · 2026")
    canvas.restoreState()

def draw_body(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#123C6B"))
    canvas.rect(0, PAGE_H - 30, PAGE_W, 30, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("DVS-B", 8)
    canvas.drawString(ML, PAGE_H - 20, "72nd BPSC · CHEMISTRY · CONSOLIDATED NOTES")
    canvas.setFont("DVS", 7.6)
    canvas.setFillColor(colors.HexColor("#C9DCEF"))
    canvas.drawRightString(PAGE_W - MR, PAGE_H - 20, "Rearranged from “Eduteria Chem Notes Class Wise”")
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
    canvas.line(ML, MB - 12, PAGE_W - MR, MB - 12)
    canvas.setFont("DVS", 7.6)
    canvas.setFillColor(GREY)
    canvas.drawString(ML, MB - 24, "Chemistry by Sakshi Ma'am · Eduteria — de-duplicated & re-organised edition")
    canvas.setFont("DVS-B", 8.6)
    canvas.setFillColor(colors.HexColor("#123C6B"))
    canvas.drawRightString(PAGE_W - MR, MB - 24, f"Page {doc.page}")
    canvas.restoreState()

UNIT_LIST = []

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "build_consolidated", "content", "*.txt")))
    # first pass to collect unit list for the cover
    for f in files:
        for line in open(f, encoding="utf-8"):
            if line.startswith("UNIT "):
                parts = line.split("|")
                if len(parts) < 3:
                    continue
                num = parts[0][5:].strip(); title = parts[1].strip()
                UNIT_LIST.append((num, title))
    doc = NotesDoc(OUT)
    story = []
    # ---- page 1: cover (artwork drawn by the cover page template)
    story.append(Spacer(1, 1))
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())
    add_front_matter(story)
    story.append(PageBreak())
    story.append(Paragraph("Contents", S("toct", fontName="DVS-B", fontSize=17, leading=21,
                                         textColor=colors.HexColor("#123C6B"), spaceAfter=8)))
    toc = TableOfContents()
    toc.levelStyles = [
        S("t0", fontName="DVS-B", fontSize=10.2, leading=15.5, textColor=colors.HexColor("#123C6B"),
          leftIndent=2, spaceBefore=5),
        S("t1", fontSize=8.8, leading=12.6, leftIndent=16, textColor=colors.HexColor("#24303E")),
    ]
    toc.dotsMinLevel = 0
    story.append(toc)
    # ---- content
    unit_state = {"no": "0", "title": "", "accent": ACCENTS[0]}
    for f in files:
        parse_file(f, story, unit_state)
    doc.multiBuild(story)
    print("built:", OUT)

def add_front_matter(story):
    st_h = S("fmh", fontName="DVS-B", fontSize=15, leading=19, textColor=colors.HexColor("#123C6B"), spaceAfter=6)
    st_p = S("fmp", fontSize=9.0, leading=12.8, spaceAfter=4)
    story.append(Paragraph("About this edition", st_h))
    story.append(Paragraph(
        "These are the <b>complete class-wise chemistry notes of Sakshi Ma'am (Eduteria, 72nd BPSC batch)</b>, "
        "re-arranged into 12 clean topic-wise units for A4 printing. <b>Every fact, table, equation, mnemonic and "
        "visual explanation of the original notes is kept</b> — only the repetition is gone.", st_p))
    story.append(Paragraph(
        "The source PDF teaches the same topics several times across its 12 lecture files (the batch revised them). "
        "Where a topic appeared more than once, the most complete version is kept and the repeats are merged into it. "
        "Green <b>“De-dup note”</b> strips record exactly what was merged, so nothing is lost silently. Lecture cover "
        "pages, watermarks and page headers were removed.", st_p))
    story.append(Spacer(1, 4))
    rows = [["#", "Source lecture file (as in the original PDF)", "Pages", "Now in"]]
    mapping = [
        ("01 Basic Chemistry Part-I", "2–10", "Unit 1"),
        ("02 Basic Chemistry Part-II", "12–23", "Units 2, 1 & 8"),
        ("03 Atomic Structure", "25–40", "Unit 3 (+ history → Unit 4)"),
        ("04 Periodic Table & Classification", "42–46", "Unit 4"),
        ("05 Chemical Bonding & Molecular Structure", "48–56", "Unit 5"),
        ("06 Chemical Bond and Hydrogen Bond", "58–64", "Unit 5"),
        ("07 Chemical Reaction", "66–71", "Unit 6"),
        ("08 Acids, Bases and Salts", "73–81", "Unit 7 (+ carbon intro → Unit 10)"),
        ("09 “Acids, Bases…” (actual content: Periodic Table revision)", "83–85", "Unit 4"),
        ("10 Important S, P, D, F Elements", "87–110", "Unit 9"),
        ("11 Metal & Nonmetal", "112–124", "Unit 8"),
        ("12 Organic Chemistry Part-1 & 2 (+ Polymers, Everyday life, Fuels)", "126–157", "Units 10–12"),
    ]
    for i, (a, b, c) in enumerate(mapping, 1):
        rows.append([str(i), a, b, c])
    t = make_table(rows, [5, 56, 11, 28], "#123C6B")
    story.append(t)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Major duplicate topics resolved", st_h))
    merges = [
        "States of matter — taught in Part-I (pp. 4–10) and again in Part-II (p. 12): merged in Unit 1; "
        "Part-II's examples kept.",
        "Metals / Non-metals / Metalloids — Part-II (pp. 13–16) vs Metal & Nonmetal lecture (pp. 112–117): "
        "merged in Unit 8; alloy tables of p. 17 attached there.",
        "History of periodic table (Döbereiner, Newlands, Mendeleev) — Atomic Structure (pp. 25–27) and "
        "Periodic Table (pp. 42–43) lectures: kept once, in Unit 4.",
        "Atomic number, electron distribution (2n² rule, octet) and valency — repeated in both lectures: "
        "kept once, in Unit 3; shell-capacity table merged.",
        "Periodic trends — three versions (p. 31 table, p. 46 table, pp. 83–85 revision): merged into one master "
        "table + factor lists in Unit 4.",
        "Bond types & comparison tables — Bonding (p. 48) vs Chemical Bond & H-bond (pp. 58, 63): merged into "
        "one set in Unit 5.",
        "Bases (Arrhenius/Brønsted definitions and examples) printed twice on source p. 75 — kept once.",
        "Organic-compound definition & nature of carbon — p. 81 vs pp. 126: kept once, in Unit 10.",
        "Refining methods (distillation/liquation/electrolytic) repeated on pp. 123–124 — kept once in Unit 8.",
        "d-block alloy-formation block printed twice on p. 104; K₂Cr₂O₇ properties wrongly repeated under "
        "KMnO₄ on p. 107 — each kept once in Unit 9.",
        "Detergent/biodegradability blocks repeated on p. 153; octane & TEL blocks repeated on pp. 156–157 — "
        "merged in Units 12.",
        "Ionization-energy factor list appears under both IE and electron-gain-enthalpy on p. 85 — kept once.",
    ]
    for m in merges:
        story.append(Paragraph(rich(m), S("mrg", fontSize=8.6, leading=11.8, leftIndent=12,
                                          bulletIndent=2, spaceAfter=2.4), bulletText="✔"))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>How to read:</b> coloured bands open each unit, green strips tell you what was merged, boxed panels "
        "highlight exam points, and every original chart keeps its “Fig. U-x” caption with the source page.", st_p))

if __name__ == "__main__":
    main()
