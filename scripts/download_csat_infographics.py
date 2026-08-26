#!/usr/bin/env python3
"""Download the locally bundled CSAT solution infographics.

data/csat.json references 1,211 solution infographics. Every question carries
an absolute `infographic_url` (Google Cloud Storage) and a `infographic_local`
path relative to the repository root, e.g. `infographics/2011/UPSCCSAT2011GS02001.webp`.

The UPSC app prefers the local file and automatically falls back to the
remote URL if the local image is missing, so the site works before this
script has been run. Run it once on a machine with internet access to make
the infographics fully local:

    python scripts/download_csat_infographics.py

Options:
    --workers N    parallel downloads (default 8)
    --force        re-download even if the local file exists
    --only-id ID   download a single question's infographic

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
CSAT_JSON = ROOT / "data" / "csat.json"
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
                    raise urllib.error.URLError(f"HTTP {response.status}")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--only-id", default="")
    args = parser.parse_args()

    data = json.loads(CSAT_JSON.read_text(encoding="utf-8"))
    questions = [
        q for q in data.get("questions", [])
        if q.get("infographic_url") and q.get("infographic_local")
        and (not args.only_id or q.get("id") == args.only_id)
    ]
    if not questions:
        print("error: no CSAT questions with infographic references found", file=sys.stderr)
        return 1

    todo = []
    skipped = 0
    for question in questions:
        target = ROOT / question["infographic_local"]
        if not args.force and webp_ok(target):
            skipped += 1
            continue
        todo.append((question["infographic_url"], target, question["id"]))

    print(f"CSAT infographics: {len(questions)} total, {skipped} already present, {len(todo)} to download")
    if not todo:
        print("nothing to do.")
        return 0

    failures = []
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {
            pool.submit(fetch, url, target): qid for url, target, qid in todo
        }
        for future in concurrent.futures.as_completed(futures):
            qid = futures[future]
            done += 1
            error = future.result()
            if error:
                failures.append((qid, error))
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
