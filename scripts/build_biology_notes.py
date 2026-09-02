#!/usr/bin/env python3
"""Render the source-audited, topic-first BPSC biology notes as a polished A4 PDF.

Run after scripts/analyse_biology_pyqs.py.  The build is deterministic apart
from PDF metadata timestamps inserted by ReportLab.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, HRFlowable, Image, KeepTogether,
    LongTable, NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer,
    Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build_biology"
CONTENT = BUILD / "content.txt"
PYQ_CSV = BUILD / "pyq_analysis.csv"
SUMMARY = BUILD / "pyq_summary.json"
MANIFEST = BUILD / "assets_manifest.json"
ASSETS = BUILD / "assets"
OUT = ROOT / "BPSC_Biology_Consolidated_Notes.pdf"

PAGE_W, PAGE_H = A4
MARGIN_L = 17 * mm
MARGIN_R = 15 * mm
MARGIN_T = 20 * mm
MARGIN_B = 16 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

NAVY = HexColor("#102A43")
INK = HexColor("#243B53")
MUTED = HexColor("#627D98")
TEAL = HexColor("#0E7490")
TEAL_DARK = HexColor("#155E75")
TEAL_PALE = HexColor("#E6F6FA")
GREEN = HexColor("#2F855A")
GREEN_PALE = HexColor("#EDF9F2")
CORAL = HexColor("#D95D39")
CORAL_PALE = HexColor("#FFF0EA")
GOLD = HexColor("#D69E2E")
GOLD_PALE = HexColor("#FFF8DC")
BLUE = HexColor("#2B6CB0")
BLUE_PALE = HexColor("#EBF4FF")
SLATE_PALE = HexColor("#F2F6F8")
WHITE = colors.white
LINE = HexColor("#CBD5E0")

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("DVSans", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DVSans-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DVSerif", str(FONT_DIR / "DejaVuSerif.ttf")))
pdfmetrics.registerFont(TTFont("DVSerif-Bold", str(FONT_DIR / "DejaVuSerif-Bold.ttf")))
pdfmetrics.registerFontFamily("DVSans", normal="DVSans", bold="DVSans-Bold")
pdfmetrics.registerFontFamily("DVSerif", normal="DVSerif", bold="DVSerif-Bold")


def styles():
    ss = getSampleStyleSheet()
    def p(name, parent="Normal", **kw):
        ss.add(ParagraphStyle(name=name, parent=ss[parent], **kw))
    p("Body", fontName="DVSans", fontSize=8.45, leading=11.55, textColor=INK,
      alignment=TA_JUSTIFY, spaceAfter=3.8)
    p("BodySmall", parent="Body", fontSize=7.4, leading=9.6, spaceAfter=2)
    p("BulletBio", parent="Body", leftIndent=10, firstLineIndent=-7, bulletIndent=2,
      alignment=TA_LEFT, spaceAfter=2.8)
    p("BulletBio2", parent="Body", leftIndent=19, firstLineIndent=-6, bulletIndent=12,
      alignment=TA_LEFT, spaceAfter=2)
    p("UnitTitle", fontName="DVSerif-Bold", fontSize=22, leading=25, textColor=NAVY,
      spaceBefore=2, spaceAfter=5, keepWithNext=True)
    p("UnitDeck", fontName="DVSans", fontSize=8, leading=10.5, textColor=MUTED,
      spaceAfter=9, keepWithNext=True)
    p("H2", fontName="DVSerif-Bold", fontSize=13.2, leading=16, textColor=NAVY,
      spaceBefore=9, spaceAfter=4, keepWithNext=True)
    p("H3", fontName="DVSans-Bold", fontSize=10.2, leading=12.5, textColor=TEAL_DARK,
      spaceBefore=6, spaceAfter=3, keepWithNext=True)
    p("BoxTitle", fontName="DVSans-Bold", fontSize=7.6, leading=9.4, textColor=NAVY,
      spaceAfter=2)
    p("BoxBody", fontName="DVSans", fontSize=7.75, leading=10.2, textColor=INK,
      alignment=TA_LEFT)
    p("Caption", fontName="DVSans", fontSize=6.5, leading=8.2, textColor=MUTED,
      alignment=TA_CENTER, spaceBefore=2)
    p("TableHead", fontName="DVSans-Bold", fontSize=7.2, leading=8.7, textColor=WHITE,
      alignment=TA_LEFT)
    p("TableBody", fontName="DVSans", fontSize=6.9, leading=8.65, textColor=INK,
      alignment=TA_LEFT)
    p("TOCHeading", fontName="DVSerif-Bold", fontSize=22, leading=26, textColor=NAVY,
      spaceAfter=8)
    p("FrontH2", fontName="DVSerif-Bold", fontSize=14, leading=17, textColor=NAVY,
      spaceBefore=8, spaceAfter=5)
    p("CoverKicker", fontName="DVSans-Bold", fontSize=10, leading=12, textColor=TEAL,
      alignment=TA_CENTER, spaceAfter=7)
    p("CoverTitle", fontName="DVSerif-Bold", fontSize=30, leading=34, textColor=NAVY,
      alignment=TA_CENTER, spaceAfter=8)
    p("CoverSub", fontName="DVSans", fontSize=12, leading=16, textColor=INK,
      alignment=TA_CENTER, spaceAfter=9)
    p("CoverMeta", fontName="DVSans", fontSize=8.4, leading=12, textColor=MUTED,
      alignment=TA_CENTER)
    p("AppendixExam", fontName="DVSerif-Bold", fontSize=16, leading=19, textColor=NAVY,
      spaceBefore=5, spaceAfter=7, keepWithNext=True)
    p("Question", fontName="DVSans-Bold", fontSize=7.8, leading=10.1, textColor=INK,
      spaceAfter=2)
    p("Option", fontName="DVSans", fontSize=6.9, leading=8.4, textColor=MUTED,
      spaceAfter=1)
    p("Answer", fontName="DVSans", fontSize=7.25, leading=9, textColor=INK)
    p("Index", fontName="DVSans", fontSize=7.1, leading=9.2, textColor=INK)
    p("Footer", fontName="DVSans", fontSize=6.6, leading=8, textColor=MUTED)
    return ss

SS = styles()


def rich(text: str) -> str:
    """Escape text, then translate lightweight **bold** and *italic* markup."""
    text = html.escape(text.strip())
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = text.replace("→", "&#8594;").replace("←", "&#8592;")
    text = text.replace("↔", "&#8596;").replace("≥", "&#8805;").replace("≤", "&#8804;")
    return text


class TopicBarChart(Flowable):
    def __init__(self, rows, width=CONTENT_W, height=80*mm):
        super().__init__(); self.rows = rows; self.width = width; self.height = height
    def draw(self):
        c = self.canv; label_w = 73*mm; right = self.width - label_w - 8*mm
        row_h = (self.height - 4*mm) / max(len(self.rows), 1)
        maxv = max(r["all_questions"] for r in self.rows)
        for i, r in enumerate(self.rows):
            y = self.height - (i+1)*row_h + 1.8*mm
            c.setFont("DVSans", 6.5); c.setFillColor(INK)
            label = r["topic"] if len(r["topic"]) < 41 else r["topic"][:39] + "…"
            c.drawString(0, y + 1, label)
            w = right * r["all_questions"] / maxv
            c.setFillColor(TEAL_PALE); c.roundRect(label_w, y, right, 3.1*mm, 1.3*mm, fill=1, stroke=0)
            c.setFillColor(TEAL); c.roundRect(label_w, y, w, 3.1*mm, 1.3*mm, fill=1, stroke=0)
            c.setFillColor(NAVY); c.setFont("DVSans-Bold", 6.4)
            c.drawRightString(self.width, y+1, str(r["all_questions"]))


class BiologyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W, PAGE_H-MARGIN_T-MARGIN_B,
                      id="normal", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        cover_frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W, PAGE_H-MARGIN_T-MARGIN_B,
                            id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="Cover", frames=[cover_frame], onPage=self.draw_cover),
            PageTemplate(id="Body", frames=[frame], onPage=self.draw_page),
        ])
        self.running = "BPSC Biology · Consolidated Notes"
        self._bookmark_id = 0

    def beforeDocument(self):
        # multiBuild performs several passes to resolve the TOC; bookmark keys
        # must be identical on every pass or the TOC never converges.
        self._bookmark_id = 0
        self.running = "BPSC Biology · Consolidated Notes"

    def draw_cover(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(SLATE_PALE); canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.setFillColor(NAVY); canvas.rect(0, PAGE_H-48*mm, PAGE_W, 48*mm, fill=1, stroke=0)
        canvas.setFillColor(TEAL); canvas.rect(0, 0, PAGE_W, 9*mm, fill=1, stroke=0)
        # DNA-like motif: clean, restrained editorial decoration.
        canvas.setStrokeColor(HexColor("#3C6687")); canvas.setLineWidth(1)
        for i in range(12):
            y = PAGE_H - 8*mm - i*3.2*mm
            x1 = 13*mm + 4*mm*math.sin(i*.85)
            x2 = 31*mm - 4*mm*math.sin(i*.85)
            canvas.line(x1, y, x2, y)
        canvas.restoreState()

    def draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE); canvas.setLineWidth(.35)
        canvas.line(MARGIN_L, PAGE_H-12*mm, PAGE_W-MARGIN_R, PAGE_H-12*mm)
        canvas.setFont("DVSans-Bold", 6.5); canvas.setFillColor(TEAL_DARK)
        canvas.drawString(MARGIN_L, PAGE_H-9.2*mm, self.running[:80])
        canvas.setFont("DVSans", 6.4); canvas.setFillColor(MUTED)
        canvas.drawRightString(PAGE_W-MARGIN_R, PAGE_H-9.2*mm, "SOURCE-AUDITED · PYQ-INTEGRATED")
        canvas.line(MARGIN_L, 10.5*mm, PAGE_W-MARGIN_R, 10.5*mm)
        canvas.setFont("DVSans", 6.4); canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN_L, 7.2*mm, "Original visuals retain source PDF + page provenance")
        canvas.setFont("DVSans-Bold", 7); canvas.setFillColor(NAVY)
        canvas.drawRightString(PAGE_W-MARGIN_R, 7.2*mm, f"{doc.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("UnitTitle", "H2"):
            level = 0 if flowable.style.name == "UnitTitle" else 1
            text = flowable.getPlainText()
            self._bookmark_id += 1
            key = f"bk-{self._bookmark_id}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=(level == 0))
            self.notify("TOCEntry", (level, text, self.page, key))
            if level == 0:
                self.running = text


class UnitDivider(Flowable):
    def __init__(self, number: str, topics: str, priority_text: str):
        super().__init__(); self.number=number; self.topics=topics; self.priority=priority_text
        self.width=CONTENT_W; self.height=13*mm
    def draw(self):
        c=self.canv
        c.setFillColor(TEAL); c.roundRect(0, 2*mm, 24*mm, 9*mm, 2*mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("DVSans-Bold", 8.5); c.drawCentredString(12*mm, 5.1*mm, f"UNIT {self.number}")
        c.setFillColor(GOLD_PALE); c.roundRect(28*mm, 2*mm, 35*mm, 9*mm, 2*mm, fill=1, stroke=0)
        c.setFillColor(GOLD); c.setFont("DVSans-Bold", 7.2); c.drawCentredString(45.5*mm, 5.1*mm, self.priority)
        c.setFillColor(MUTED); c.setFont("DVSans", 6.5)
        c.drawRightString(self.width, 5.1*mm, "TOPIC-FIRST · DUPLICATES MERGED")


class VisualCard(Flowable):
    """Single image with its caption; scales at wrap time to avoid overflow."""
    def __init__(self, img_path: Path, caption: str, provenance: str, max_height_mm: float=65):
        super().__init__(); self.path=img_path; self.caption=caption; self.provenance=provenance
        self.max_h=max_height_mm*mm; self._img=None; self._cap=None
    def wrap(self, availWidth, availHeight):
        with PILImage.open(self.path) as im:
            iw, ih = im.size
        max_h=min(self.max_h, max(30*mm, availHeight-12*mm))
        scale=min(availWidth/iw, max_h/ih)
        w, h=iw*scale, ih*scale
        self._img=Image(str(self.path), width=w, height=h)
        self._cap=Paragraph(f"<b>{rich(self.caption)}</b><br/><font color='#627D98'>Original source visual · {rich(self.provenance)}</font>", SS["Caption"])
        cw,ch=self._cap.wrap(availWidth, 20*mm)
        self.width=availWidth; self.height=h+ch+3*mm; self._iw=w; self._ih=h; self._cap_h=ch
        return self.width,self.height
    def draw(self):
        c=self.canv; x=(self.width-self._iw)/2
        c.setFillColor(colors.white); c.setStrokeColor(LINE)
        c.roundRect(x-2*mm, self._cap_h+2*mm, self._iw+4*mm, self._ih+2*mm, 2*mm, fill=1, stroke=1)
        self._img.canv=c; self._img.drawOn(c,x,self._cap_h+3*mm)
        self._cap.canv=c; self._cap.drawOn(c,0,0)


ALIASES = {
    "photosynthesis_overview": "plant_physiology", "stomata": "leaf_anatomy",
    "tropisms": "plant_physiology", "plant_hormones": "photoperiodism",
    "muscle_tissue": "muscle_types", "human_skeleton": "long_bone",
    "intestinal_villus": "absorption_summary", "blood_cells": "blood_components",
    "cardiac_cycle": "cardiac_conduction", "ecg": "cardiac_conduction",
    "inhalation_exhalation": "breathing_mechanics",
    "male_reproductive_system": "reproductive_system", "female_reproductive_system": "reproductive_system",
    "human_brain": "brain", "hindbrain": "brain", "human_eye": "nerve_impulse", "human_ear": "nerve_impulse",
    "malaria_cycle": "dengue_vector", "disease_vectors": "dengue_vector",
    "population_growth": "energy_flow", "biogeochemical_cycles": "ecosystem_components",
    "biodiversity_conservation": "ecosystem_components", "food_chain": "food_chain_web",
    "joint_types": "vertebral_column",
}


def box(title, body, kind="key"):
    if kind == "added": palette=(BLUE_PALE, BLUE, "EDITOR ADDITION")
    elif kind == "corr": palette=(CORAL_PALE, CORAL, "EDITORIAL CORRECTION")
    elif kind == "pyq": palette=(GREEN_PALE, GREEN, "PYQ LENS")
    elif kind == "warn": palette=(GOLD_PALE, GOLD, "KEY-SENSITIVE")
    else: palette=(TEAL_PALE, TEAL, "EXAM KEY")
    bg, accent, label = palette
    title_txt = f"<font color='{accent.hexval()}'>{label}</font> · {rich(title)}" if title else f"<font color='{accent.hexval()}'>{label}</font>"
    t=Table([[Paragraph(title_txt, SS["BoxTitle"])], [Paragraph(rich(body), SS["BoxBody"])]], colWidths=[CONTENT_W-8*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),bg), ("BOX",(0,0),(-1,-1),.45,accent),
        ("LINEBEFORE",(0,0),(0,-1),3,accent), ("LEFTPADDING",(0,0),(-1,-1),4*mm),
        ("RIGHTPADDING",(0,0),(-1,-1),3*mm), ("TOPPADDING",(0,0),(-1,0),2.5*mm),
        ("BOTTOMPADDING",(0,-1),(-1,-1),2.7*mm),
    ]))
    return KeepTogether([Spacer(1,2*mm),t,Spacer(1,2*mm)])


def make_table(rows, widths=None, compact=False):
    if not rows: return Spacer(1,1)
    cols=len(rows[0]); widths = widths or [100/cols]*cols
    total=sum(widths); col_widths=[CONTENT_W*w/total for w in widths]
    pdata=[]
    for ri,row in enumerate(rows):
        sty=SS["TableHead"] if ri==0 else SS["TableBody"]
        pdata.append([Paragraph(rich(cell),sty) for cell in row])
    tab=LongTable(pdata,colWidths=col_widths,repeatRows=1,hAlign="LEFT")
    style=[
        ("BACKGROUND",(0,0),(-1,0),NAVY), ("TEXTCOLOR",(0,0),(-1,0),WHITE),
        ("VALIGN",(0,0),(-1,-1),"TOP"), ("GRID",(0,0),(-1,-1),.3,LINE),
        ("LEFTPADDING",(0,0),(-1,-1),2.2*mm), ("RIGHTPADDING",(0,0),(-1,-1),2.2*mm),
        ("TOPPADDING",(0,0),(-1,-1),1.5*mm if compact else 2*mm),
        ("BOTTOMPADDING",(0,0),(-1,-1),1.5*mm if compact else 2*mm),
    ]
    for i in range(1,len(rows)):
        if i%2==0: style.append(("BACKGROUND",(0,i),(-1,i),SLATE_PALE))
    tab.setStyle(TableStyle(style))
    return KeepTogether([Spacer(1,1.6*mm),tab,Spacer(1,2.5*mm)]) if len(rows)<10 else tab


def image_card(key, caption, max_h, manifest):
    original_key=key; key=ALIASES.get(key,key)
    if key not in manifest:
        print(f"WARNING: omitted missing visual: {original_key}"); return None
    m=manifest[key]; path=ASSETS/m["asset"]
    prov=f"{m['source']}, p. {m['page']}"
    return VisualCard(path, caption, prov, max_h)


def two_images(specs, manifest):
    cells=[]
    for key,cap in specs:
        card=image_card(key,cap,47,manifest)
        if card: cells.append(card)
    if not cells: return None
    if len(cells)==1: return cells[0]
    colw=(CONTENT_W-4*mm)/2
    # Each VisualCard wraps within table cell; provenance remains attached.
    t=Table([[cells[0],cells[1]]],colWidths=[colw,colw],hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),
                           ("RIGHTPADDING",(0,0),(0,0),2*mm),("LEFTPADDING",(1,0),(1,0),2*mm),
                           ("RIGHTPADDING",(0,0),(-1,-1),0)]))
    return KeepTogether([Spacer(1,2*mm),t,Spacer(1,3*mm)])


def priority_for(topics, ranking):
    names=[x.strip() for x in topics.split(";")]
    candidates=[r for r in ranking if r["topic"] in names]
    if not candidates: return "FOUNDATION"
    p=min((r["priority"] for r in candidates), key=lambda x:"ABC".index(x))
    if p=="A": return "PRIORITY A"
    if p=="B": return "PRIORITY B"
    return "FOUNDATION"


def parse_content(manifest, ranking):
    lines=CONTENT.read_text(encoding="utf-8").splitlines()
    story=[]; i=0; widths=None; first_unit=True
    while i<len(lines):
        raw=lines[i].strip(); i+=1
        if not raw or raw.startswith("#"): continue
        if raw.startswith("UNIT "):
            number,title,sources,topics=raw[5:].split("|",3)
            if not first_unit: story.append(PageBreak())
            first_unit=False
            story += [UnitDivider(number,topics,priority_for(topics,ranking)),
                      Paragraph(rich(title),SS["UnitTitle"]),
                      Paragraph(f"Consolidated from <b>{rich(sources)}</b> · PYQ theme: {rich(topics)}",SS["UnitDeck"]),
                      HRFlowable(width="100%",thickness=.6,color=LINE,spaceAfter=3*mm)]
        elif raw.startswith("H2 "): story.append(Paragraph(rich(raw[3:]),SS["H2"]))
        elif raw.startswith("H3 "): story.append(Paragraph(rich(raw[3:]),SS["H3"]))
        elif raw.startswith("P "): story.append(Paragraph(rich(raw[2:]),SS["Body"]))
        elif raw.startswith("B "): story.append(Paragraph("• "+rich(raw[2:]),SS["BulletBio"]))
        elif raw.startswith("BB "): story.append(Paragraph("– "+rich(raw[3:]),SS["BulletBio2"]))
        elif raw.startswith("ADDED "):
            title,body=raw[6:].split("|",1); story.append(box(title,body,"added"))
        elif raw.startswith("CORR "):
            title,body=raw[5:].split("|",1); story.append(box(title,body,"corr"))
        elif raw.startswith("PYQ "):
            q,a=raw[4:].split("~",1); story.append(box(q,a,"pyq"))
        elif raw.startswith("KEY "): story.append(box("",raw[4:],"key"))
        elif raw.startswith("TBLW "):
            widths=[float(x) for x in raw[5:].split(",")]
        elif raw=="TBL":
            rows=[]
            while i<len(lines):
                line=lines[i].strip()
                if not line: i+=1; break
                if line.startswith(("UNIT ","H2 ","H3 ","P ","B ","BB ","ADDED ","CORR ","PYQ ","KEY ","IMG ","IMGS ","TBLW ","TBL")):
                    break
                rows.append(line.split("~")); i+=1
            expected = len(rows[0]) if rows else 0
            bad = [(n+1, len(row)) for n, row in enumerate(rows) if len(row) != expected]
            if bad:
                raise ValueError(f"Table ending near content line {i} has {expected} columns but rows differ: {bad}")
            story.append(make_table(rows,widths)); widths=None
        elif raw.startswith("IMG "):
            rest=raw[4:]; namecap,*height=rest.split("|"); key,cap=namecap.split(":",1)
            card=image_card(key,cap,float(height[0]) if height else 62,manifest)
            if card: story += [Spacer(1,2*mm),card,Spacer(1,2*mm)]
        elif raw.startswith("IMGS "):
            specs=[]
            for spec in raw[5:].split("|"):
                key,cap=spec.split(":",1); specs.append((key,cap))
            card=two_images(specs,manifest)
            if card: story.append(card)
        else:
            raise ValueError(f"Unrecognised content line {i}: {raw}")
    return story


def load_pyqs():
    with PYQ_CSV.open(encoding="utf-8") as f: return list(csv.DictReader(f))


def front_matter(summary, pyqs):
    ranking=summary["topic_ranking"]
    recent_names={"66th BPSC","67th BPSC","68th BPSC","69th BPSC","70th BPSC","71st BPSC (2025)"}
    recent=Counter(r["topic"] for r in pyqs if r["exam"] in recent_names)
    all_core=Counter(r["topic"] for r in pyqs if r["scope"]=="core")

    story=[Spacer(1,38*mm),Paragraph("BPSC PRELIMS · BIOLOGY",SS["CoverKicker"]),
           Paragraph("Consolidated Biology Notes",SS["CoverTitle"]),
           Paragraph("Topic-first · duplicate-free · visual · PYQ-prioritised",SS["CoverSub"]),
           Spacer(1,9*mm)]
    metrics=Table([
        [Paragraph("<b>33</b><br/><font size='7'>source PDFs read</font>",SS["CoverMeta"]),
         Paragraph(f"<b>{summary['total_questions']}</b><br/><font size='7'>reviewed PYQs</font>",SS["CoverMeta"]),
         Paragraph("<b>20</b><br/><font size='7'>topic-first units</font>",SS["CoverMeta"])],
    ],colWidths=[45*mm]*3,rowHeights=[18*mm],hAlign="CENTER")
    metrics.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),WHITE),("BOX",(0,0),(-1,-1),.6,LINE),
                                 ("INNERGRID",(0,0),(-1,-1),.4,LINE),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    story += [metrics,Spacer(1,11*mm),Paragraph("Every original figure used is captioned with its lecture PDF and page. External/editorial additions are blue; corrections are coral. Supplied-key conflicts remain visible rather than being silently rewritten.",SS["CoverMeta"]),
              Spacer(1,20*mm),Paragraph("Edition 1.0 · September 2026",SS["CoverMeta"]),
              NextPageTemplate("Body"),PageBreak()]

    story += [Paragraph("How to use this book",SS["TOCHeading"]),
              Paragraph("This is a reconstruction—not a stack of lecture handouts. Repeated coverage was merged once, related material was brought together, and the notes were reordered around conceptual dependencies and BPSC recurrence.",SS["Body"])]
    legend=Table([
        [Paragraph("<b>PRIORITY A</b>",SS["BoxTitle"]),Paragraph("Highest recurrence across the reviewed corpus; revise first.",SS["BoxBody"])],
        [Paragraph("<font color='#2B6CB0'><b>EDITOR ADDITION</b></font>",SS["BoxTitle"]),Paragraph("Assistant-supplied context/data beyond the source lectures.",SS["BoxBody"])],
        [Paragraph("<font color='#D95D39'><b>EDITORIAL CORRECTION</b></font>",SS["BoxTitle"]),Paragraph("A source typo, outdated statement or scientific ambiguity corrected explicitly.",SS["BoxBody"])],
        [Paragraph("<font color='#2F855A'><b>PYQ LENS</b></font>",SS["BoxTitle"]),Paragraph("A prior-question hook placed next to the concept it tests.",SS["BoxBody"])],
    ],colWidths=[48*mm,CONTENT_W-48*mm])
    legend.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.35,LINE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                                ("ROWBACKGROUNDS",(0,0),(-1,-1),[SLATE_PALE,WHITE]),
                                ("LEFTPADDING",(0,0),(-1,-1),3*mm),("RIGHTPADDING",(0,0),(-1,-1),3*mm),
                                ("TOPPADDING",(0,0),(-1,-1),2.5*mm),("BOTTOMPADDING",(0,0),(-1,-1),2.5*mm)]))
    story += [Spacer(1,3*mm),legend,Spacer(1,4*mm),
              box("Coverage statement","All 33 supplied lesson PDFs were read end-to-end. The two L22 files are exact byte-identical duplicates, so they were counted once for content. Administrative slide furniture, repeated promotional text and exact duplicate facts were omitted; unique educational content was retained and re-organised.","key"),
              Paragraph("Three-pass revision",SS["FrontH2"])]
    story += [Paragraph("<b>Pass 1 · Priority A:</b> plants, disease/immunity, nutrition, and ecology (when extended ecology is in scope).",SS["BulletBio"]),
              Paragraph("<b>Pass 2 · Systems:</b> genetics, endocrine/reproduction, circulation, nerves, digestion and excretion.",SS["BulletBio"]),
              Paragraph("<b>Pass 3 · Retrieval:</b> Rapid Revision Atlas → key-sensitive table → complete PYQ audit appendix.",SS["BulletBio"]),
              PageBreak()]

    story += [Paragraph("Contents",SS["TOCHeading"])]
    toc=TableOfContents(); toc.levelStyles=[
        ParagraphStyle("TOC0",fontName="DVSans-Bold",fontSize=8.4,leading=11.5,textColor=NAVY,leftIndent=0,firstLineIndent=0,spaceBefore=3),
        ParagraphStyle("TOC1",fontName="DVSans",fontSize=7.1,leading=9,textColor=MUTED,leftIndent=7*mm,firstLineIndent=0),
    ]
    story += [toc,PageBreak(),Paragraph("PYQ-derived priority map",SS["TOCHeading"]),
              Paragraph(f"The two supplied workbooks yielded <b>{summary['total_questions']} manually reviewed biology-linked questions</b>: {summary['scope_counts']['core']} core and {summary['scope_counts']['extended']} extended (ecology, conservation, agri-biology and public-health boundary). Keyword-only selection was not used.",SS["Body"]),
              TopicBarChart(ranking,height=77*mm),Spacer(1,3*mm)]
    rows=[["Topic","All","Core","Latest 6","Papers","Tier"]]
    for r in ranking:
        rows.append([r["topic"],str(r["all_questions"]),str(all_core[r["topic"]]),str(recent[r["topic"]]),str(r["papers_present"]),r["priority"]])
    story += [make_table(rows,[45,9,9,12,12,9],compact=True),
              box("How to read the ranking","Counting extended ecology makes Ecology/Environment rank first; in core biology alone, Plant Form/Function, Microbes/Disease and Nutrition lead. “Latest 6” means the 66th through 71st supplied examination groups. Frequency informs order but does not justify dropping foundational systems.","warn"),
              Paragraph("Latest-six signal",SS["FrontH2"])]
    latest_sorted=sorted(recent.items(),key=lambda x:(-x[1],x[0]))
    story.append(Paragraph(" · ".join(f"<b>{rich(k)}</b> {v}" for k,v in latest_sorted),SS["BodySmall"]))
    story += [PageBreak()]
    return story


def question_card(r):
    status=r["status"]
    accent = CORAL if status in {"corrected","ambiguous","key-sensitive","restored"} else (BLUE if status=="added-answer" else GREEN)
    badge=status.upper().replace("-"," ")
    q=Paragraph(f"<font color='{accent.hexval()}'><b>Q{r['q_no']} · {rich(r['scope'].upper())} · {rich(badge)}</b></font><br/>{rich(r['question'])}",SS["Question"])
    opts=Paragraph(rich(r["options"].replace(" | ","  ·  ")),SS["Option"]) if r["options"] else Spacer(1,1)
    answer=Paragraph(f"<b>Study answer:</b> {rich(r['study_answer'])}",SS["Answer"])
    bottom=[]
    if status!="source-key":
        supplied=r["source_answer"] or "not supplied"
        bottom.append(Paragraph(f"<b>Supplied answer:</b> {rich(supplied)}  ·  <b>Editorial note:</b> {rich(r['editor_note'])}",SS["Option"]))
    data=[[q],[opts],[answer]]+[[x] for x in bottom]
    t=Table(data,colWidths=[CONTENT_W-8*mm],hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),WHITE),("BOX",(0,0),(-1,-1),.45,LINE),
                           ("LINEBEFORE",(0,0),(0,-1),2.2,accent),("LEFTPADDING",(0,0),(-1,-1),3*mm),
                           ("RIGHTPADDING",(0,0),(-1,-1),3*mm),("TOPPADDING",(0,0),(-1,0),2.3*mm),
                           ("BOTTOMPADDING",(0,-1),(-1,-1),2.3*mm)]))
    return KeepTogether([t,Spacer(1,2.2*mm)])


def appendix(pyqs, manifest):
    story=[PageBreak(),Paragraph("Appendix A · Complete reviewed PYQ audit",SS["UnitTitle"]),
           Paragraph("Every biology-linked question selected from the two supplied workbooks appears below. “Supplied answer” preserves the workbook field; “study answer” is what to learn. Any restoration, correction, ambiguity, key sensitivity or assistant-added answer is visibly badged.",SS["Body"]),
           box("Scope rule","CORE = direct biological concept/application. EXTENDED = ecology, wildlife, conservation, agri-biology, nutrition programmes or public-health boundary. This distinction prevents environmental-current-affairs questions from inflating the apparent core-biology trend.","key")]
    grouped=defaultdict(list)
    for r in pyqs: grouped[r["exam"]].append(r)
    for exam, rows in grouped.items():
        story += [PageBreak(),Paragraph(rich(exam),SS["AppendixExam"]),
                  Paragraph(f"{len(rows)} reviewed question(s) · workbook order retained",SS["UnitDeck"])]
        for r in rows: story.append(question_card(r))

    story += [PageBreak(),Paragraph("Appendix B · Original visual provenance",SS["UnitTitle"]),
              Paragraph("The notes use only reviewed figures extracted from the supplied lecture PDFs. No web image was inserted. When one original figure was reused for a closely related concept, its original source remains stated in the caption.",SS["Body"])]
    rows=[["Asset","Source lecture","Page"]]
    for key,m in sorted(manifest.items(),key=lambda kv:(kv[1]["source"],kv[1]["page"],kv[0])):
        rows.append([key.replace("_"," ").title(),m["source"],str(m["page"])])
    story.append(make_table(rows,[28,62,10],compact=True))

    story += [PageBreak(),Paragraph("Appendix C · Sources, method & limitations",SS["UnitTitle"]),
              Paragraph("<b>Primary source corpus.</b> All 33 PDFs in <i>EDUTERIA BIO NOTES</i>, from L1 through L32, plus the supplied 56th–59th and 60th–71st BPSC question workbooks. Two L22 PDFs are byte-identical; both were inventoried but their content was not duplicated.",SS["Body"]),
              Paragraph("<b>Consolidation method.</b> Page-delimited text and embedded figures were extracted, every lecture was read, recurring concepts were grouped, duplicate statements were merged, unique details were retained, and selected visuals were linked to a page-level manifest. Questions were reviewed individually rather than selected solely by keyword.",SS["Body"]),
              Paragraph("<b>Editorial additions/corrections.</b> Blue and coral boxes visibly identify externally supplied context and scientific corrections. For standard verification the editor used mainstream textbook/agency-level biology, including NCERT Class XI–XII Biology, WHO public-health terminology, IUCN conservation categories, and official programme descriptions. The 71st U-WIN item was checked against the official BPSC final-key context and Government of India programme features.",SS["Body"]),
              Paragraph("<b>Limitations.</b> A supplied answer key can contain errors; several are explicitly badged. Protected-area counts, IUCN status, government schemes and health guidance can change after this September 2026 edition. Verify dynamic facts and the exact official key for the examination you are preparing for.",SS["Body"]),
              box("Health disclaimer","This is an examination study aid, not medical advice. Disease descriptions and treatments are deliberately concise; diagnosis, vaccination and medicines require current professional guidance.","warn"),
              Spacer(1,8*mm),HRFlowable(width="100%",thickness=.6,color=LINE),Spacer(1,4*mm),
              Paragraph("END · Revise Unit 20, then revisit every coral key-sensitive card.",SS["CoverMeta"])]
    return story


def validate_inputs():
    required=[CONTENT,PYQ_CSV,SUMMARY,MANIFEST]
    missing=[str(p) for p in required if not p.exists()]
    if missing: raise SystemExit("Missing build inputs: "+", ".join(missing))


def build():
    validate_inputs()
    summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    pyqs=load_pyqs()
    story=front_matter(summary,pyqs)
    story += parse_content(manifest,summary["topic_ranking"])
    story += appendix(pyqs,manifest)
    doc=BiologyDocTemplate(str(OUT),pagesize=A4,
        leftMargin=MARGIN_L,rightMargin=MARGIN_R,topMargin=MARGIN_T,bottomMargin=MARGIN_B,
        title="BPSC Biology Consolidated Notes",author="Arena.ai editorial build",
        subject="Topic-first, visual and PYQ-integrated BPSC biology notes",
        keywords="BPSC biology PYQ notes ecology genetics physiology")
    doc.multiBuild(story)
    sha=hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"Built {OUT.name} · {OUT.stat().st_size/1024/1024:.2f} MiB · sha256 {sha}")


if __name__=="__main__":
    build()
