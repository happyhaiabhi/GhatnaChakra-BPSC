#!/usr/bin/env python3
"""Render the single-sheet workbook as a readable, chapter-wise PDF.

The workbook is the source of truth: scripts/apply_polity_verification.py puts
the web-verification status on every row, and this renderer simply shows what
that column says, so the PDF can never drift ahead of the evidence ledger.
"""
from pathlib import Path
import json
import re
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from openpyxl import load_workbook
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

root = Path(__file__).resolve().parent.parent
pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuBold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

sheet = load_workbook(root / 'Polity_PYQ_Laxmikanth_Chapterwise.xlsx', read_only=True, data_only=True).active
rows = [r for r in sheet.iter_rows(min_row=2, values_only=True) if r[0] is not None]
ledger = json.loads((root / 'data' / 'polity_answer_verification.json').read_text(encoding='utf-8'))
entries = {e['row']: e for e in ledger['entries']}

TOTAL = len(rows)
CHECKED = len(entries)
CORRECTED = sum(1 for e in entries.values() if e['status'] == 'corrected')
CONFIRMED = sum(1 for e in entries.values() if e['status'] == 'confirmed')
RESOLVED = sum(1 for e in entries.values() if e['status'] == 'resolved')
DEFECTS = sum(1 for e in entries.values() if e['status'] in ('defect', 'deleted'))
UNCHECKED = TOTAL - CHECKED

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCustom', fontName='DejaVuBold', fontSize=20, leading=27,
                          textColor=colors.HexColor('#17365d'), alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name='ChapterCustom', fontName='DejaVuBold', fontSize=15, leading=20,
                          textColor=colors.HexColor('#17365d'), spaceBefore=12, spaceAfter=12, keepWithNext=True))
styles.add(ParagraphStyle(name='QuestionCustom', fontName='DejaVuBold', fontSize=9.5, leading=14,
                          spaceBefore=9, spaceAfter=4, keepWithNext=True))
styles.add(ParagraphStyle(name='OptionsCustom', fontName='DejaVu', fontSize=9, leading=14, leftIndent=10, spaceAfter=4))
styles.add(ParagraphStyle(name='MetaCustom', fontName='DejaVu', fontSize=7.6, leading=11,
                          textColor=colors.HexColor('#465463'), spaceAfter=3))
styles.add(ParagraphStyle(name='AnswerCustom', fontName='DejaVuBold', fontSize=8.4, leading=12,
                          textColor=colors.HexColor('#1e6b2f'), spaceAfter=3))
styles.add(ParagraphStyle(name='IntroCustom', fontName='DejaVu', fontSize=10, leading=16, spaceAfter=10))
styles.add(ParagraphStyle(name='CellCustom', fontName='DejaVu', fontSize=8, leading=10.5))
styles.add(ParagraphStyle(name='CellHead', fontName='DejaVuBold', fontSize=8, leading=10.5,
                          textColor=colors.white))


def safe(x):
    return escape(str(x or '')).replace('\n', '<br/>')


OPT_RE = re.compile(r'\(([a-e])\)\s*', re.I)


def option_text(options: str, letter: str) -> str:
    """Return the text this sheet's own option list carries for a letter."""
    if not options or not letter:
        return ''
    marks = list(OPT_RE.finditer(options))
    for i, m in enumerate(marks):
        if m.group(1).lower() != letter.lower():
            continue
        end = marks[i + 1].start() if i + 1 < len(marks) else len(options)
        text = options[m.end():end].strip(' ;,')
        if len(marks) > 5 and len(text) < 4:      # OCR answer-table fragments, not an option
            return ''
        return text
    return ''


def domain(url: str) -> str:
    host = urlparse(url).netloc
    return host[4:] if host.startswith('www.') else host


def footer(canvas, doc):
    canvas.setFont('DejaVu', 7)
    canvas.setFillColor(colors.HexColor('#65717d'))
    canvas.drawString(18 * mm, 12 * mm,
                      f'Polity PYQ • Chapter-wise • {CHECKED}/{TOTAL} answers web-checked ({CORRECTED} corrected)')
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, str(doc.page))


doc = SimpleDocTemplate(str(root / 'Polity_PYQ_Laxmikanth_Chapterwise.pdf'), pagesize=A4,
                        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                        title='Polity PYQ — Laxmikanth chapter-wise')

story = [
    Spacer(1, 22 * mm),
    Paragraph('Polity PYQ<br/>Chapter-wise Compilation', styles['TitleCustom']),
    Paragraph(f'{TOTAL} questions and variants, grouped by best-fit Laxmikanth chapter.', styles['IntroCustom']),
    Paragraph('Includes the supplied KGS polity PDF and records labelled Polity in the supplied BPSC CSV and JSON. '
              'Full duplicates with matching normalized questions and options were merged; differently worded versions remain.',
              styles['IntroCustom']),
    Paragraph('<b>What the answer lines mean.</b> Every question carries a verification status. '
              f'<b>{CHECKED}</b> rows ({CHECKED / TOTAL:.0%}) were checked against a published source and say '
              f'<i>Answer (web-checked)</i>: {CORRECTED} printed keys were wrong and are corrected here, {CONFIRMED} were '
              f'confirmed, {RESOLVED} ambiguous keys (printed as * or A/C) were resolved, and {DEFECTS} questions have no '
              'defensible answer (corrupt option tables in the source, plus one question BPSC deleted). The remaining '
              f'<b>{UNCHECKED}</b> rows still print the key taken from the source book and are labelled '
              '<i>not web-checked</i> — read them as "the source book says so", not as verified fact. '
              'Answers are always expressed in the option order printed on the row, never in the booklet order of the '
              'original paper, because BPSC shuffles options between booklets.', styles['IntroCustom']),
    Paragraph('<b>The source keys are not equally reliable.</b> The answer letters that came from the supplied JSON are '
              'misaligned with the options printed here (they look like a different booklet\'s letters): 28 of the 38 JSON-derived '
              'keys judged were wrong, and even a random sample of untouched rows was wrong three times out of eight, so those rows '
              'are marked unreliable rather than silently kept. A twelve-question audit of the KGS book keys '
              'found one error (Q47, now corrected) and two corrupt option tables, so those keys are plausible but not verified either; the CSV keys matched on every spot-check. See POLITY_PYQ_VERIFICATION.md for the evidence.',
              styles['IntroCustom']),
    Paragraph('Chapter classifications remain automated and need review. The last section holds questions the classifier put '
              'outside Laxmikanth chapter scope (international affairs, current affairs, reasoning, history and science misfiled as '
              'polity). Check those before using the sheet as a polity-only list.', styles['IntroCustom']),
    PageBreak(),
]

# --- summary of the check -------------------------------------------------
story.append(Paragraph('Verification summary', styles['ChapterCustom']))
summary = [
    ['Status', 'Rows', 'Meaning'],
    ['Web-verified, printed key correct', CONFIRMED, 'A published key or a solved paper agrees with the printed letter.'],
    ['Web-verified, key corrected', CORRECTED, 'The printed letter pointed at a wrong option; the option text now keyed is the correct one.'],
    ['Web-verified, ambiguous key resolved', RESOLVED, 'The source printed *, A/C or left the letter blank; the answer was settled from a source.'],
    ['No answer available', DEFECTS, 'Three questions have corrupt option tables as printed; one was deleted by BPSC before evaluation.'],
    ['Not web-checked', UNCHECKED, 'Still carries the source key (KGS book, CSV, or the unreliable JSON letter).'],
]
data = [[Paragraph(safe(c), styles['CellHead'] if i == 0 else styles['CellCustom']) for c in row]
        for i, row in enumerate(summary)]
tbl = Table(data, colWidths=[62 * mm, 14 * mm, 98 * mm], repeatRows=1)
tbl.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17365d')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f6fa')]),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#c9d3de')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
]))
story.append(tbl)

story.append(Paragraph('Corrections made in this edition', styles['ChapterCustom']))
story.append(Paragraph('Every row below had a wrong or missing printed key and now carries the verified option. '
                       'The full sentence of evidence and the URL are in the workbook\'s "Web evidence" column and in '
                       'data/polity_answer_verification.json.', styles['IntroCustom']))
corr = [[Paragraph(h, styles['CellHead']) for h in ('Q. No.', 'Printed', 'Verified', 'Correct option', 'Source')]]
for qno in sorted(entries):
    e = entries[qno]
    if e['status'] not in ('corrected', 'resolved'):
        continue
    corr.append([Paragraph(str(qno), styles['CellCustom']),
                 Paragraph(safe(e['printed']), styles['CellCustom']),
                 Paragraph(safe(e['verified_key']), styles['CellCustom']),
                 Paragraph(safe(e['verified_text']), styles['CellCustom']),
                 Paragraph(safe(domain(e['source'])), styles['CellCustom'])])
ct = Table(corr, colWidths=[13 * mm, 16 * mm, 16 * mm, 92 * mm, 37 * mm], repeatRows=1)
ct.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17365d')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fdf1e8')]),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#c9d3de')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
]))
story.append(ct)
story.append(PageBreak())

# --- the questions --------------------------------------------------------
previous = None
for qno, chapter, question, options, answer, answer_text, refs, notes, vkey, vstatus, vevidence in (
        (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10]) for r in rows):
    if chapter != previous:
        if previous is not None:
            story.append(PageBreak())
        story.append(Paragraph(safe(chapter), styles['ChapterCustom']))
        previous = chapter
    block = [Paragraph(f'{qno}. {safe(question)}', styles['QuestionCustom'])]
    if options:
        formatted = re.sub(r'\s+(?=[(]([b-eB-E])[)]\s)', '<br/>', safe(options))
        block.append(Paragraph(formatted, styles['OptionsCustom']))
    status = (vstatus or '')
    if vkey and vkey != 'DELETED':
        entry = entries.get(qno)
        shown = option_text(options, vkey) or (entry['verified_text'] if entry else '')
        line = f'<b>Answer (web-checked):</b> {safe(vkey)}' + (f' — {safe(shown)}' if shown else '')
        if entry and entry['status'] == 'corrected':
            line += f'  <font color="#a33">[printed key {safe(entry["printed"])} is wrong]</font>'
        if entry and entry['status'] == 'resolved':
            line += f'  <font color="#a33">[printed key {safe(entry["printed"])}]</font>'
        block.append(Paragraph(line, styles['AnswerCustom']))
    elif entry_q := entries.get(qno):
        if entry_q['status'] == 'deleted':
            block.append(Paragraph('<b>Answer:</b> none — BPSC deleted this question from the 71st final key; no marks were awarded for any option.',
                                   styles['AnswerCustom']))
        else:
            block.append(Paragraph(f'<b>Answer:</b> none — {safe(entry_q["evidence"])}', styles['AnswerCustom']))
    else:
        block.append(Paragraph('<b>Source answer:</b> ' + safe(answer) + (' — ' + safe(answer_text) if answer_text else ''),
                               styles['MetaCustom']))
    block.append(Paragraph('<b>Source:</b> ' + safe(refs), styles['MetaCustom']))
    block.append(Paragraph('<b>Verification:</b> ' + safe(status or 'not recorded'), styles['MetaCustom']))
    if notes:
        block.append(Paragraph('<b>Note:</b> ' + safe(notes), styles['MetaCustom']))
    story.append(KeepTogether(block))

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f'Rendered {len(rows)} rows ({CHECKED} web-checked, {CORRECTED} corrected)')
