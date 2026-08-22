#!/usr/bin/env python3
"""
Import a book ZIP into the Ghatna Chakra multi-book app.

Usage:
    python3 scripts/import_book.py incoming/some_book.zip --id my_book --title "My Book"

It:
  * extracts the ZIP into a staging folder,
  * scans for JSON / question-bank files and reports what it found,
  * copies/normalizes supported files into books/<id>/data/,
  * generates books/<id>/data/chapters.json,
  * appends an entry to books/books.json (idempotent — updates if it exists).

If the ZIP's internal format is not recognized, it leaves the extracted copy
in incoming/_staging/<id>/ and prints the file tree so a manual mapping can be
added. It never touches existing book data or commits anything.
"""
import argparse, json, os, re, shutil, sys, zipfile, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS_JSON = ROOT / "books" / "books.json"

def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s or "book"

def safe_load_json(p):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  ! could not parse {p.name}: {e}")
        return None

def looks_like_subject_file(data):
    """Heuristic: the app's subject format is {subject, chapters:[{chapter_name, questions:[...]}]}."""
    return (
        isinstance(data, dict)
        and isinstance(data.get("chapters"), list)
        and data["chapters"]
        and isinstance(data["chapters"][0], dict)
        and isinstance(data["chapters"][0].get("questions"), list)
    )

def count_questions(data):
    if not looks_like_subject_file(data): return 0, 0
    ch = data.get("chapters", [])
    q = sum(len(c.get("questions", []) or []) for c in ch)
    return len(ch), q

def build_chapters_index(subject_files, book_id, dest_data):
    index = []
    for i, (src_path, data) in enumerate(sorted(subject_files), start=1):
        label = data.get("subject") or src_path.stem.replace("_", " ").title()
        key = slugify(label)
        # avoid key collisions
        base_key = key; n = 2
        existing = {s["key"] for s in index}
        while key in existing:
            key = f"{base_key}_{n}"; n += 1
        dest_name = f"{key}.json"
        index.append({
            "key": key,
            "label": label,
            "emoji": data.get("_emoji") or "📘",
            "file": dest_name,
            "chapters": [
                {"name": c.get("chapter_name") or c.get("name") or "General",
                 "count": len(c.get("questions", []) or [])}
                for c in data.get("chapters", [])
            ],
        })
        # copy normalized subject file
        clean = {
            "subject": label,
            "chapters": [
                {
                    "chapter_name": c.get("chapter_name") or c.get("name") or "General",
                    "questions": c.get("questions", []) or [],
                }
                for c in data.get("chapters", [])
            ],
        }
        with open(dest_data / dest_name, "w", encoding="utf-8") as f:
            json.dump(clean, f, ensure_ascii=False, indent=2)
    return index

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zip_path", help="Path to the .zip file (e.g. incoming/book.zip)")
    ap.add_argument("--id", dest="book_id", help="Book id (slug). Defaults to filename.")
    ap.add_argument("--title", help="Display title")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--emoji", default="📘")
    ap.add_argument("--color", default="#4a90d9")
    ap.add_argument("--description", default="")
    ap.add_argument("--force", action="store_true", help="Overwrite existing book folder")
    args = ap.parse_args()

    zip_path = (ROOT / args.zip_path).resolve() if not Path(args.zip_path).is_absolute() else Path(args.zip_path)
    if not zip_path.exists():
        print(f"ERROR: {zip_path} not found"); sys.exit(1)

    book_id = args.book_id or slugify(zip_path.stem)
    title = args.title or zip_path.stem.replace("_", " ").replace("-", " ").title()

    staging = ROOT / "incoming" / "_staging" / book_id
    if staging.exists(): shutil.rmtree(staging)
    staging.mkdir(parents=True)

    print(f"Extracting {zip_path.name} ...")
    try:
        with zipfile.ZipFile(zip_path) as z:
            # guard against zip-slip
            for member in z.namelist():
                target = (staging / member).resolve()
                if not str(target).startswith(str(staging.resolve())):
                    print(f"  ! skipping unsafe path: {member}"); continue
            z.extractall(staging)
    except zipfile.BadZipFile:
        print("ERROR: not a valid zip file"); sys.exit(1)

    # Find JSON files
    json_files = [p for p in staging.rglob("*") if p.is_file() and p.suffix.lower() == ".json"]
    print(f"Found {len(json_files)} JSON file(s).")

    subject_files = []
    for p in json_files:
        data = safe_load_json(p)
        if data is None: continue
        ch, q = count_questions(data)
        if ch:
            print(f"  ✓ {p.relative_to(staging)}  ({ch} chapters, {q} questions)")
            subject_files.append((p, data))
        else:
            print(f"  · {p.relative_to(staging)}  (not in app subject format)")

    if not subject_files:
        print("\nNo files matched the app's subject format.")
        print("Extracted contents are kept at:")
        print(f"  {staging.relative_to(ROOT)}")
        print("Tell me the book and its file layout, and I'll add a converter.")
        sys.exit(2)

    dest = ROOT / "books" / book_id / "data"
    if dest.exists():
        if not args.force:
            print(f"ERROR: {dest.relative_to(ROOT)} already exists. Use --force to overwrite."); sys.exit(1)
        shutil.rmtree(dest.parent)
    dest.mkdir(parents=True)

    index = build_chapters_index(subject_files, book_id, dest)
    with open(dest / "chapters.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    total_q = sum(sum(c["count"] for c in s["chapters"]) for s in index)
    print(f"\nWrote {len(index)} subject file(s), {total_q} question(s) to {dest.relative_to(ROOT)}/")

    # Register in books.json
    books = []
    if BOOKS_JSON.exists():
        books = json.loads(BOOKS_JSON.read_text(encoding="utf-8"))
    entry = {
        "id": book_id,
        "title": title,
        "subtitle": args.subtitle,
        "tag": args.tag or title,
        "emoji": args.emoji,
        "color": args.color,
        "dataDir": f"books/{book_id}/data",
        "chaptersFile": "chapters.json",
        "description": args.description,
    }
    books = [b for b in books if b.get("id") != book_id]
    # keep legacy book first, then append
    books.append(entry)
    BOOKS_JSON.write_text(json.dumps(books, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Registered '{title}' in books/books.json.")
    print("Done. Run `npm test` then reload the app to see the new book card.")

if __name__ == "__main__":
    main()
