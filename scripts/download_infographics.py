#!/usr/bin/env python3
"""Download the locally bundled solution infographics.

data/csat.json (CSAT Paper II) and data/prelims.json (Prelims GS Paper I)
reference one solution infographic per question. Every question carries an
absolute `infographic_url` (Google Cloud Storage) and an `infographic_local`
path relative to the repository root, e.g.
`infographics/2011/UPSCCSAT2011GS02001.webp` or
`infographics/1995/UPSCPRELI1995GS01001.webp`.

The UPSC app prefers the local file and automatically falls back to the
remote URL if the local image is missing, so the site works before this
script has been run. Run it once on a machine with internet access to make
the infographics fully local:

    python scripts/download_infographics.py

Options:
    --workers N    parallel downloads (default 8)
    --force        re-download even if the local file exists
    --only-id ID   download a single question's infographic
    --dataset NAME only process this dataset: csat or prelims

Already-downloaded files are verified by their WebP magic bytes and skipped,
so the script is safe to re-run after partial failures.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "GhatnaChakra-BPSC-infographic-sync/1.0"
RETRIES = 3
TIMEOUT = 30


def webp_ok(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 32:
        return False
    with path.open("rb") as handle:
        head = handle.read(12)
    return head[:4] == b"RIFF" and head[8:12] == b"WEBP"


def fetch(url: str, target: Path) -> str:
    """Download url into target with retries. Returns '' or an error string."""
    for attempt in range(1, RETRIES + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                if response.status != 200:
                    raise urllib.request.URLError(f"HTTP {response.status}")
                target.parent.mkdir(parents=True, exist_ok=True)
                tmp = target.with_suffix(target.suffix + ".part")
                with tmp.open("wb") as handle:
                    while True:
                        chunk = response.read(1 << 16)
                        if not chunk:
                            break
                        handle.write(chunk)
                if not webp_ok(tmp):
                    tmp.unlink(missing_ok=True)
                    raise ValueError("downloaded file is not a valid WebP image")
                tmp.replace(target)
                return ""
        except Exception as exc:  # noqa: BLE001 — report and retry on any failure
            if attempt == RETRIES:
                return f"{type(exc).__name__}: {exc}"
            time.sleep(1.5 * attempt)
    return "unreachable"


def load_questions(dataset: str):
    """Yield (id, infographic_url, infographic_local) for one dataset."""
    if dataset == "csat":
        data = json.loads((ROOT / "data" / "csat.json").read_text(encoding="utf-8"))
        questions = data.get("questions", [])
    else:
        data = json.loads((ROOT / "data" / "prelims.json").read_text(encoding="utf-8"))
        questions = [
            question
            for year_questions in data.get("records_by_year", {}).values()
            for question in year_questions
        ]
    for question in questions:
        if question.get("infographic_url") and question.get("infographic_local"):
            yield (question.get("id", "?"),
                   question["infographic_url"],
                   question["infographic_local"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--only-id", default="")
    parser.add_argument("--dataset", choices=("csat", "prelims"), default="")
    args = parser.parse_args()

    datasets = (args.dataset,) if args.dataset else ("csat", "prelims")

    todo = []  # (dataset, id, url, target)
    failures = []
    total_referenced = 0
    for dataset in datasets:
        referenced = skipped = 0
        for qid, url, local in load_questions(dataset):
            if args.only_id and qid != args.only_id:
                continue
            referenced += 1
            target = ROOT / local
            if not args.force and webp_ok(target):
                skipped += 1
                continue
            todo.append((dataset, qid, url, target))
        total_referenced += referenced
        print(f"{dataset} infographics: {referenced} referenced, "
              f"{skipped} already present, {len(todo)} queued so far")

    if not total_referenced:
        print("error: no questions with infographic references found "
              "(check --dataset / --only-id)", file=sys.stderr)
        return 1
    if not todo:
        print("nothing to do.")
        return 0

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {
            pool.submit(fetch, url, target): (dataset, qid)
            for dataset, qid, url, target in todo
        }
        for future in concurrent.futures.as_completed(futures):
            dataset, qid = futures[future]
            done += 1
            error = future.result()
            if error:
                failures.append((f"{dataset}/{qid}", error))
            if done % 100 == 0 or done == len(todo):
                print(f"  progress: {done}/{len(todo)} (failures so far: {len(failures)})")

    if failures:
        print(f"\n{len(failures)} downloads failed:", file=sys.stderr)
        for qid, error in failures[:25]:
            print(f"  {qid}: {error}", file=sys.stderr)
        if len(failures) > 25:
            print(f"  ... and {len(failures) - 25} more", file=sys.stderr)
        print("\nRe-run the script to retry the failed downloads.", file=sys.stderr)
        return 1

    print("all infographics are now available locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
