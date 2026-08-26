#!/usr/bin/env python3
"""Refresh the integrated BPSC runtime (bpsc/) from the public source repository.

The combined portal keeps the complete BPSC browser application under bpsc/
(index.html, books/, data/, css/, js/). When the upstream BPSC project ships
updates, run this script from the repository root:

    python scripts/sync_bpsc_runtime.py

How it works:
1. Resolves the upstream branch. It prefers the permanent ``bpsc-source``
   backup branch and falls back to ``main`` only while that backup branch has
   not been created yet (with a warning).
2. Shallow-clones that branch into a temporary directory.
3. Copies only the browser-runtime files — never .git, source PDFs, tests,
   node_modules or extraction artifacts.
4. Re-injects the portal hooks: the fixed "← Exam Portal" return link and the
   shared ../theme.js + ../bpsc-theme.css references (idempotent).
5. Validates every book manifest, chapters index and subject data file,
   including full JSON parsing and question counts.
6. Replaces the local bpsc/ runtime only after validation succeeds.

Usage:
    python scripts/sync_bpsc_runtime.py [--repo URL] [--branch NAME] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPO = "https://github.com/happyhaiabhi/GhatnaChakra-BPSC.git"
PREFERRED_BRANCH = "bpsc-source"
FALLBACK_BRANCH = "main"

# Files from the source tree that belong to the browser runtime.
RUNTIME_DIRS = ("books", "css", "js", "data")
# UPSC portal datasets live in data/ of the combined main branch; the
# standalone BPSC source never needs them.
UPSC_ONLY_DATA_FILES = {"prelims.json", "csat.json", "mains.json"}

THEME_HOOKS = ('<script src="../theme.js"></script>\n'
               '<link rel="stylesheet" href="../bpsc-theme.css">')
CF_MARKER = "<script>(function(){function c(){var b=a.contentDocument"

# Return-to-portal navigation, matching the canonical integrated page:
# a fixed "← Exam Portal" pill at the top of the body plus a compact Portal
# pill at the start of the book-switcher top navbar.
PORTAL_RETURN = ('<a class="exam-portal-return" href="../index.html" '
                 'aria-label="Back to exam selection">\u2190 Exam Portal</a>\n'
                 '<style>\n'
                 '.exam-portal-return{position:fixed;z-index:10000;top:12px;left:12px;display:inline-flex;align-items:center;border:1px solid color-mix(in srgb,var(--border) 80%,transparent);border-radius:999px;padding:8px 12px;background:color-mix(in srgb,var(--surface) 90%,transparent);box-shadow:0 6px 18px rgba(0,0,0,.13);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);color:var(--text2);font:700 12px/1 \'Nunito\',system-ui,sans-serif;text-decoration:none;transition:transform .18s ease,border-color .18s ease}\n'
                 '.exam-portal-return:hover{transform:translateY(-2px);border-color:var(--gold);color:var(--gold)}\n'
                 '@media(max-width:600px){.exam-portal-return{top:8px;left:8px;padding:7px 9px;font-size:10px}}\n'
                 '</style>')
NAV_PILL = ('<a class="nav-portal-home" href="../index.html" '
            'title="Back to exam portal">\u2302 <span>Portal</span></a>')
NAV_ANCHOR = '<div class="top-navbar">'


def log(message: str) -> None:
    print(message, flush=True)


def run_git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def remote_branches(repo: str) -> set[str]:
    output = run_git(["ls-remote", "--heads", repo])
    return {line.split()[-1].removeprefix("refs/heads/") for line in output.splitlines() if line.strip()}


def resolve_branch(repo: str, requested: str) -> str:
    if requested:
        log(f"syncing from branch: {requested}")
        return requested
    available = remote_branches(repo)
    if PREFERRED_BRANCH in available:
        log(f"syncing from branch: {PREFERRED_BRANCH}")
        return PREFERRED_BRANCH
    log(f"warning: branch '{PREFERRED_BRANCH}' does not exist on the remote yet; "
        f"falling back to '{FALLBACK_BRANCH}' temporarily. Create the backup branch before "
        f"'{FALLBACK_BRANCH}' is replaced with the combined portal.")
    return FALLBACK_BRANCH


def is_bpsc_app_html(html: str) -> bool:
    """The BPSC application references its book manifest; the portal does not."""
    return "books/books.json" in html and "Ghatna Chakra" in html


def find_app_html(source: Path) -> Path:
    """Locate the BPSC application HTML in the upstream tree.

    Standalone checkouts keep it at the root (index.html); combined-portal
    checkouts keep it under bpsc/index.html.
    """
    for candidate in (source / "index.html", source / "bpsc" / "index.html"):
        if candidate.is_file() and is_bpsc_app_html(candidate.read_text(encoding="utf-8")):
            return candidate
    raise RuntimeError(
        "the upstream branch does not contain the standalone BPSC application "
        "(no index.html with the book-library runtime was found at the root or under bpsc/). "
        "Point --branch at the branch that preserves the original BPSC source."
    )


def strip_cloudflare_artifact(html: str) -> str:
    """Drop the Cloudflare challenge residue that scrape tooling can leave behind."""
    start = html.find(CF_MARKER)
    if start == -1:
        return html
    end = html.find("</script>", start)
    if end == -1:
        return html
    return html[:start] + html[end + len("</script>"):]


def inject_portal_hooks(html: str) -> str:
    """Inject (idempotently) the shared theme hooks and the portal return links."""
    if CF_MARKER in html:
        html = strip_cloudflare_artifact(html)

    if 'src="../theme.js"' not in html:
        head_close = html.find("</head>")
        if head_close == -1:
            raise RuntimeError("source index.html has no </head> tag")
        html = html[:head_close] + THEME_HOOKS + "\n" + html[head_close:]

    if 'class="exam-portal-return"' not in html:
        body_open = html.find("<body>")
        if body_open == -1:
            raise RuntimeError("source index.html has no <body> tag")
        insert_at = body_open + len("<body>")
        html = html[:insert_at] + "\n" + PORTAL_RETURN + html[insert_at:]

    if 'class="nav-portal-home"' not in html:
        if NAV_ANCHOR in html:
            html = html.replace(NAV_ANCHOR, NAV_ANCHOR + "\n    " + NAV_PILL, 1)
        else:
            log("warning: top-navbar anchor not found; the nav Portal pill was not injected")

    return html


def copy_runtime(source: Path, staging: Path) -> None:
    app_html = find_app_html(source)
    log(f"using BPSC application HTML from: {app_html.relative_to(source)}")
    (staging / "index.html").write_text(
        inject_portal_hooks(strip_cloudflare_artifact(app_html.read_text(encoding="utf-8"))),
        encoding="utf-8",
    )
    for name in RUNTIME_DIRS:
        src_dir = source / name
        if not src_dir.is_dir():
            continue
        dst_dir = staging / name
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        dst_dir.mkdir(parents=True)
        for entry in sorted(src_dir.iterdir()):
            target = dst_dir / entry.name
            if entry.is_dir():
                shutil.copytree(entry, target)
            elif entry.is_file():
                if name == "data" and entry.name in UPSC_ONLY_DATA_FILES:
                    continue
                shutil.copy2(entry, target)


def resolve_subject_path(file_field: str, data_dir: str) -> str:
    """Mirror bookFilePath() from the BPSC application."""
    clean = file_field[2:] if file_field.startswith("./") else file_field
    if clean.startswith(("http://", "https://", "//")):
        return clean
    if data_dir and data_dir != "." and "/" not in clean:
        clean = data_dir.rstrip("/") + "/" + clean
    return clean


def validate_runtime(runtime: Path) -> dict:
    """Validate every book manifest, chapters file and subject file. Raises on failure."""
    manifest_path = runtime / "books" / "books.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list) or not manifest:
        raise RuntimeError("books/books.json must be a non-empty list")

    subject_files = set()
    total_questions = 0
    books_report = []
    for book in manifest:
        book_id = book.get("id", "<missing-id>")
        data_dir = (book.get("dataDir") or "data").strip()
        if data_dir == ".":
            chapters_path = Path(book["chaptersFile"])
        else:
            chapters_path = Path(data_dir.rstrip("/")) / book["chaptersFile"]
        chapters_file = runtime / chapters_path
        if not chapters_file.is_file():
            raise RuntimeError(f"book '{book_id}': missing chapters file {chapters_path}")
        index = json.loads(chapters_file.read_text(encoding="utf-8"))
        if not isinstance(index, list):
            raise RuntimeError(f"book '{book_id}': {chapters_path} must be a list of subjects")

        book_questions = 0
        for subject in index:
            file_field = subject.get("file") or f"{subject.get('key')}.json"
            rel = resolve_subject_path(file_field, data_dir)
            if rel.startswith(("http://", "https://")):
                continue
            subject_file = runtime / rel
            if not subject_file.is_file():
                raise RuntimeError(f"book '{book_id}': missing subject file {rel}")
            subject_files.add(rel)
            payload = json.loads(subject_file.read_text(encoding="utf-8"))
            for chapter in payload.get("chapters", []):
                book_questions += len(chapter.get("questions", []))
        total_questions += book_questions
        books_report.append((book_id, len(index), book_questions))

    core = next(
        (row for row in books_report if row[0] == "bpsc_ghatna_chakra"),
        None,
    )
    if core is None:
        log("warning: core book 'bpsc_ghatna_chakra' not found in books.json")
    if len(subject_files) < 50:
        log(f"warning: expected at least 50 subject files, found {len(subject_files)}")

    for book_id, subject_count, question_count in books_report:
        log(f"  book {book_id:<20} subjects={subject_count:<4} questions={question_count:,}")
    log(f"  total: {len(manifest)} books, {len(subject_files)} subject files, {total_questions:,} questions")
    if core:
        log(f"  core Ghatna Chakra book: {core[1]} subjects, {core[2]:,} questions")
    return {
        "books": len(manifest),
        "subject_files": len(subject_files),
        "total_questions": total_questions,
        "core": core,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default="", help="override the upstream branch")
    parser.add_argument("--dry-run", action="store_true", help="validate without replacing bpsc/")
    args = parser.parse_args()

    branch = resolve_branch(args.repo, args.branch)
    log(f"cloning {args.repo} (branch: {branch}, depth 1)…")

    tmp_dir = Path(tempfile.mkdtemp(prefix="bpsc-sync-"))
    try:
        run_git(["clone", "--depth", "1", "--single-branch", "--branch", branch, args.repo, str(tmp_dir / "src")])
        source = tmp_dir / "src"

        staging = tmp_dir / "staging"
        staging.mkdir()
        copy_runtime(source, staging)
        log("validating staged runtime…")
        stats = validate_runtime(staging)

        if args.dry_run:
            log(f"dry run complete — local bpsc/ left untouched ({stats['total_questions']:,} questions validated).")
            return 0

        local = ROOT / "bpsc"
        log("replacing local bpsc/ runtime…")
        for entry in sorted(local.iterdir()) if local.exists() else []:
            shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
        for entry in sorted(staging.iterdir()):
            target = local / entry.name
            if entry.is_dir():
                shutil.copytree(entry, target)
            else:
                shutil.copy2(entry, target)
        log(f"bpsc/ updated: {stats['books']} books, {stats['subject_files']} subject files, "
            f"{stats['total_questions']:,} questions.")
        return 0
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except subprocess.TimeoutExpired:
        print("error: git operation timed out", file=sys.stderr)
        raise SystemExit(1)
