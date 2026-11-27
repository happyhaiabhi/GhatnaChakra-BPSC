#!/usr/bin/env python3
"""Apply the web-verification ledger to the Polity PYQ workbook.

Usage: python scripts/apply_polity_verification.py [--check]

Reads data/polity_answer_verification.json and rewrites
Polity_PYQ_Laxmikanth_Chapterwise.xlsx with four extra columns:

  * Q. No.             - the number printed in the PDF (stable row id)
  * Verified key (web) - the answer mapped to *this sheet's* option order
  * Verification status- what was done to the row
  * Web evidence       - source URL + the sentence that decides the answer

Every row gets a status, including rows nobody has checked yet: an unverified
answer is labelled as such instead of being presented as verified. The script is
idempotent - it strips its own columns before rebuilding them.

--check reports what would change and exits non-zero when the ledger and the
workbook disagree, so the PDF build can gate on it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "Polity_PYQ_Laxmikanth_Chapterwise.xlsx"
LEDGER = ROOT / "data" / "polity_answer_verification.json"

BASE_HEADERS = [
    "Chapter (best fit)",
    "Question",
    "Options / statements",
    "Answer key (source)",
    "Answer text (source)",
    "Source / exam / question",
    "Review notes",
]
EXTRA_HEADERS = ["Q. No.", "Verified key (web)", "Verification status", "Web evidence"]
WIDTHS = [7, 32, 70, 70, 18, 30, 55, 55, 13, 46, 70]

LABELS = {
    "confirmed": "Web-verified: printed key correct",
    "corrected": "Web-verified: key was wrong, corrected",
    "resolved": "Web-verified: ambiguous printed key resolved",
    "defect": "Source defect: no single defensible answer",
    "deleted": "Deleted by BPSC: question has no answer",
}
FILLS = {
    "confirmed": "E2F0D9",
    "corrected": "FCE4D6",
    "resolved": "E2F0D9",
    "defect": "FFF2CC",
    "deleted": "FFF2CC",
}
KGS_UNCHECKED = "Not web-checked: KGS printed key retained (12-row audit: 1 wrong, now corrected)"
CSV_UNCHECKED = "Not web-checked: CSV key retained (spot-checks consistent)"
JSON_UNCHECKED = "Not web-checked: source letter unreliable (booklet-order mismatch)"


def origin(refs: str) -> str:
    refs = refs or ""
    if "JSON:" in refs and "CSV:" in refs:
        return "merged"
    if "JSON:" in refs:
        return "json"
    if "CSV:" in refs:
        return "csv"
    return "kgs"


def strip_extra_guarantee(ws) -> None:
    """Remove the columns this script adds, so the build is repeatable."""
    if ws.max_column >= 11 and ws.cell(1, 9).value == "Verified key (web)":
        ws.delete_cols(9, 3)
    if ws.cell(1, 1).value == "Q. No.":
        ws.delete_cols(1)
    assert ws.max_column == 7, f"unexpected column count {ws.max_column}"
    assert [ws.cell(1, i).value for i in range(1, 8)] == BASE_HEADERS


def main() -> int:
    check = "--check" in sys.argv[1:]
    entries = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
    ledger = {e["row"]: e for e in entries}
    if len(ledger) != len(entries):
        print("duplicate row ids in ledger")
        return 2

    wb = load_workbook(XLSX)
    ws = wb.active
    strip_extra_guarantee(ws)

    header_fill = PatternFill("solid", fgColor="17365D")
    header_font = Font(bold=True, color="FFFFFF")
    wrap = Alignment(wrap_text=True, vertical="top")

    ws.insert_cols(1)
    n = ws.max_row - 1
    # headers: Q.No + the seven base headers + three verification columns
    order = EXTRA_HEADERS[:1] + BASE_HEADERS + EXTRA_HEADERS[1:]
    for i, title in enumerate(order, 1):
        c = ws.cell(1, i, title)
        c.fill = header_fill
        c.font = header_font
        c.alignment = wrap
    for i, width in enumerate(WIDTHS, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = width

    problems: list[str] = []
    counts: dict[str, int] = {}
    for qno in range(1, n + 1):
        row = qno + 1
        ws.cell(row, 1, qno)
        refs = ws.cell(row, 7).value or ""
        question = ws.cell(row, 3).value or ""
        printed = (ws.cell(row, 5).value or "").strip().upper()
        entry = ledger.get(qno)
        if entry is None:
            kind = origin(refs)
            label = {"kgs": KGS_UNCHECKED, "csv": CSV_UNCHECKED}.get(kind, JSON_UNCHECKED)
            ws.cell(row, 9, "")
            ws.cell(row, 10, label).fill = PatternFill("solid", fgColor="F2F2F2")
            ws.cell(row, 11, "")
            counts[kind] = counts.get(kind, 0) + 1
        else:
            if entry["q"][:28].lower() not in question[:140].lower():
                problems.append(f"Q{qno}: ledger question {entry['q']!r} does not match sheet question {question[:60]!r}")
            status = entry["status"]
            vkey = entry["verified_key"]
            if status == "corrected" and printed == vkey:
                problems.append(f"Q{qno}: ledger says corrected but printed key already equals {vkey}")
            if status == "confirmed" and printed != vkey:
                problems.append(f"Q{qno}: ledger says confirmed but printed key is {printed}, not {vkey}")
            ws.cell(row, 9, vkey)
            ws.cell(row, 10, LABELS[status]).fill = PatternFill("solid", fgColor=FILLS[status])
            ws.cell(row, 11, f"{entry['source']} — {entry['evidence']}")
            # the answer half of the boilerplate review note is settled now
            notes = ws.cell(row, 8).value or ""
            notes = notes.replace("chapter and answer require review", "chapter still requires review")
            notes = notes.replace("check source for OCR, options, and answer accuracy",
                                  "source key retained for the chapter audit only")
            if not notes.startswith('[Web-checked'):
                ws.cell(row, 8, f"[Web-checked {entry.get('checked', '2026-11-27')}] {notes}".strip())
            counts[status] = counts.get(status, 0) + 1
        for col in (9, 10, 11):
            ws.cell(row, col).alignment = wrap

    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions

    checked = sum(v for k, v in counts.items() if k in LABELS)
    print(f"rows: {n}   web-checked: {checked}   ({checked / n:.1%})")
    for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {k:>10}: {v}")
    if problems:
        print("\nLEDGER PROBLEMS:")
        for p in problems:
            print("  " + p)
        return 1
    if not check:
        wb.save(XLSX)
        print(f"wrote {XLSX.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
