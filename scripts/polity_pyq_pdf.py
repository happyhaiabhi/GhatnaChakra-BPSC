#!/usr/bin/env python3
"""Render the single-sheet workbook as a readable, chapter-wise PDF."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from openpyxl import load_workbook
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

root = Path(__file__).resolve().parent.parent
pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuBold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
sheet = load_workbook(root / 'Polity_PYQ_Laxmikanth_Chapterwise.xlsx', read_only=True, data_only=True).active
rows = list(sheet.iter_rows(min_row=2, values_only=True))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCustom', fontName='DejaVuBold', fontSize=20, leading=27, textColor=colors.HexColor('#17365d'), alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name='ChapterCustom', fontName='DejaVuBold', fontSize=15, leading=20, textColor=colors.HexColor('#17365d'), spaceBefore=12, spaceAfter=12, keepWithNext=True))
styles.add(ParagraphStyle(name='QuestionCustom', fontName='DejaVuBold', fontSize=9.5, leading=14, spaceBefore=9, spaceAfter=4, keepWithNext=True))
styles.add(ParagraphStyle(name='OptionsCustom', fontName='DejaVu', fontSize=9, leading=14, leftIndent=10, spaceAfter=4))
styles.add(ParagraphStyle(name='MetaCustom', fontName='DejaVu', fontSize=7.6, leading=11, textColor=colors.HexColor('#465463'), spaceAfter=3))
styles.add(ParagraphStyle(name='IntroCustom', fontName='DejaVu', fontSize=10, leading=16, spaceAfter=10))

def safe(x):
    return escape(str(x or '')).replace('\n', '<br/>')

def footer(canvas, doc):
    canvas.setFont('DejaVu', 7)
    canvas.setFillColor(colors.HexColor('#65717d'))
    canvas.drawString(18*mm, 12*mm, 'Polity PYQ • Chapter-wise • Source answers, not independently verified')
    canvas.drawRightString(A4[0]-18*mm, 12*mm, str(doc.page))

doc = SimpleDocTemplate(str(root / 'Polity_PYQ_Laxmikanth_Chapterwise.pdf'), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=20*mm, title='Polity PYQ — Laxmikanth chapter-wise')
story = [Spacer(1, 30*mm), Paragraph('Polity PYQ<br/>Chapter-wise Compilation', styles['TitleCustom']),
         Paragraph(f'{len(rows)} questions and variants, grouped by best-fit Laxmikanth chapter.', styles['IntroCustom']),
         Paragraph('Includes the supplied KGS polity PDF and records labelled Polity in the supplied BPSC CSV and JSON. Full duplicates with matching normalized questions and options were merged; differently worded versions remain.', styles['IntroCustom']),
         Paragraph('Important: Chapter classifications are automated and require review. The review section includes potentially off-topic questions. Source answers have not been independently verified, and the PDF source contains extraction and translation defects. Asterisk or multiple answer letters are retained as printed. Refer to the source and the companion README before relying on an answer.', styles['IntroCustom']), PageBreak()]
previous = None
for number, (chapter, question, options, answer, answer_text, refs, notes) in enumerate(rows, 1):
    if chapter != previous:
        if previous is not None:
            story.append(PageBreak())
        story.append(Paragraph(safe(chapter), styles['ChapterCustom']))
        previous = chapter
    story.append(Paragraph(f'{number}. {safe(question)}', styles['QuestionCustom']))
    if options:
        formatted = safe(options)
        formatted = re.sub(r'\s+(?=\([b-eB-E]\)\s)', '<br/>', formatted)
        story.append(Paragraph(formatted, styles['OptionsCustom']))
    if answer or answer_text:
        story.append(Paragraph('<b>Source answer:</b> ' + safe(answer) + (' — ' + safe(answer_text) if answer_text else ''), styles['MetaCustom']))
    story.append(Paragraph('<b>Source:</b> ' + safe(refs), styles['MetaCustom']))
    if notes:
        story.append(Paragraph('<b>Note:</b> ' + safe(notes), styles['MetaCustom']))
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f'Rendered {len(rows)} rows')
