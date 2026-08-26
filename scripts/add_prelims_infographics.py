#!/usr/bin/env python3
"""Add solution-infographic references to every Prelims GS Paper I question.

The Dalvoy source sheet gives every Prelims question a solution infographic
served from Google Cloud Storage under the deterministic scheme

    https://storage.googleapis.com/dalvoy-lessons-images/prelims-infographics/<year>/<QUESTION_ID>.webp

where `<QUESTION_ID>` is the trailing slug of the question's existing
`reference_url` (e.g. `UPSCPRELI1995GS01001`). This script mirrors, for
Prelims GS Paper I, what `data/csat.json` already carries for CSAT Paper II:
an absolute `infographic_url` plus a repository-relative `infographic_local`
path such as `infographics/1995/UPSCPRELI1995GS01001.webp`.

The four legacy rows whose `reference_url` points at a CSAT GS02 page are
skipped — the app excludes them from the Prelims collection and the richer
CSAT dataset already references those exact infographics.

Usage:
    python scripts/add_prelims_infographics.py            # add missing refs
    python scripts/add_prelims_infographics.py --check    # verify only

Idempotent: records that already carry both fields are left untouched.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRELIMS_JSON = ROOT / "data" / "prelims.json"
GCS_BASE = "https://storage.googleapis.com/dalvoy-lessons-images/prelims-infographics"
LOCAL_BASE = "infographics"
REFERENCE = re.compile(
    r"^https://www\.dalvoy\.com/upsc/prelims/(\d{4})/q/(UPSCPRELI\1GS\d+)$"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="only report; do not write anything")
    args = parser.parse_args()

    data = json.loads(PRELIMS_JSON.read_text(encoding="utf-8"))
    records = data.get("records_by_year", {})

    added = kept = skipped = 0
    for questions in records.values():
        for question in questions:
            url = question.get("reference_url", "")
            if not REFERENCE.match(url):
                skipped += 1  # legacy CSAT-pointing row — covered by csat.json
                continue
            if question.get("infographic_url") and question.get("infographic_local"):
                kept += 1
                continue
            match = REFERENCE.match(url)
            year, question_id = match.group(1), match.group(2)
            question["infographic_url"] = f"{GCS_BASE}/{year}/{question_id}.webp"
            question["infographic_local"] = f"{LOCAL_BASE}/{year}/{question_id}.webp"
            # Keep reference_url as the last key for a stable, readable diff.
            ordered = {k: question[k] for k in question
                       if k not in ("reference_url", "infographic_url", "infographic_local")}
            ordered["infographic_url"] = question["infographic_url"]
            ordered["infographic_local"] = question["infographic_local"]
            ordered["reference_url"] = url
            question.clear()
            question.update(ordered)
            added += 1

    total = sum(len(v) for v in records.values())
    with_infographic = sum(
        1
        for questions in records.values()
        for q in questions
        if q.get("infographic_url") and q.get("infographic_local")
    )
    data["with_infographic_file"] = with_infographic

    print(f"prelims records: {total}  already referenced: {kept}  "
          f"newly referenced: {added}  skipped (CSAT rows): {skipped}")
    print(f"questions with infographic references: {with_infographic}/{total}")

    if args.check:
        return 0 if with_infographic + skipped == total else 1

    # Match the original file byte-for-byte (2-space indent, no trailing
    # newline) so the diff contains only the newly added lines.
    PRELIMS_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {PRELIMS_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
