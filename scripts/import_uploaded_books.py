#!/usr/bin/env python3
"""
Import the two uploaded multi-subject ZIPs into SIX separate books on the
Ghatna Chakra landing page.

Expected in dropbox/ (or given as paths):
  - general_science_part7_2026_json_bank.zip  -> Physics, Chemistry, Biology
  - indian_history_part2_2026_json_bank.zip    -> Ancient, Medieval, Modern India

Each subject becomes its own book under books/<id>/ with a chapters.json,
exactly like the existing BPSC book. books/books.json is updated.

The source ZIPs are deleted afterwards (they are never committed).
"""
import argparse, json, os, re, shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = ROOT / "books"
BOOKS_JSON = BOOKS_DIR / "books.json"
DROPBOX = ROOT / "dropbox"

# Each ZIP maps to (zip-filename, list of subject -> (book_id, title, emoji, color, filename_in_zip))
ZIP_MAP = {
    "general_science_part7_2026_json_bank.zip": [
        ("physics",          "Physics",                 "⚛️",  "#4ea3ff", "physics.json"),
        ("chemistry",        "Chemistry",               "🧪", "#46d6a8", "chemistry.json"),
        ("biology",          "Biology",                 "🧬", "#7ed957", "biology.json"),
    ],
    "indian_history_part2_2026_json_bank.zip": [
        ("ancient_india",    "Ancient India",           "🏛️", "#c9a84c", "ancient_history_of_india.json"),
        ("medieval_india",   "Medieval India",          "🏰", "#d4845a", "medieval_history_of_india.json"),
        ("modern_india",     "Modern India",            "📜", "#b07cd9", "modern_history_of_india.json"),
    ],
}

def slugify(s): return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

def find_zip(expected_name, explicit_paths):
    for p in explicit_paths:
        if p and Path(p).name == expected_name and Path(p).exists():
            return Path(p)
    for base in (DROPBOX, ROOT, ROOT/"incoming"):
        cand = base / expected_name
        if cand.exists(): return cand
    return None

def extract_member(zf, wanted_name):
    wanted = wanted_name.lower()
    for name in zf.namelist():
        if name.endswith("/"): continue
        if Path(name).name.lower() == wanted:
            return zf.read(name)
    return None

def build_chapters_index(subject_data, dest_name, emoji, label):
    chapters = subject_data.get("chapters", [])
    return {
        "key": slugify(label),
        "label": label,
        "emoji": emoji,
        "file": dest_name,
        "chapters": [
            {"name": c.get("chapter_name") or c.get("name") or "General",
             "count": len(c.get("questions", []) or [])}
            for c in chapters
        ],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="optional explicit paths to the two zips")
    ap.add_argument("--keep-zips", action="store_true")
    args = ap.parse_args()

    books = json.loads(BOOKS_JSON.read_text(encoding="utf-8")) if BOOKS_JSON.exists() else []
    by_id = {b["id"]: b for b in books}

    imported = []
    for zip_name, subjects in ZIP_MAP.items():
        zpath = find_zip(zip_name, args.paths)
        if not zpath:
            print(f"✗ {zip_name} not found in dropbox/ — skipped."); continue
        print(f"✓ {zpath.name}")
        with zipfile.ZipFile(zpath) as zf:
            for book_id, title, emoji, color, inner_name in subjects:
                raw = extract_member(zf, inner_name)
                if raw is None:
                    print(f"  ! {inner_name} not inside ZIP — skipped."); continue
                data = json.loads(raw.decode("utf-8"))
                dest_dir = BOOKS_DIR / book_id / "data"
                if dest_dir.exists(): shutil.rmtree(dest_dir.parent)
                dest_dir.mkdir(parents=True)
                # normalise subject file
                subject_file = f"{book_id}.json"
                clean = {
                    "subject": title,
                    "chapters": [
                        {"chapter_name": c.get("chapter_name") or c.get("name") or "General",
                         "questions": c.get("questions", []) or []}
                        for c in data.get("chapters", [])
                    ],
                }
                (dest_dir / subject_file).write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
                index = [build_chapters_index(data, subject_file, emoji, title)]
                (dest_dir / "chapters.json").write_text(json.dumps(index, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
                q_count = sum(len(c.get("questions",[]) or []) for c in clean["chapters"])
                ch_count = len(clean["chapters"])
                by_id[book_id] = {
                    "id": book_id,
                    "title": title,
                    "subtitle": "Purvavalokan 2026 · English",
                    "tag": title.split()[0].upper(),
                    "emoji": emoji,
                    "color": color,
                    "dataDir": f"books/{book_id}/data",
                    "chaptersFile": "chapters.json",
                    "description": f"{ch_count} chapters · {q_count:,} verified questions",
                }
                print(f"    → {title}: {ch_count} chapters, {q_count:,} questions")
                imported.append(book_id)
        if not args.keep_zips and zpath.parent in (DROPBOX, ROOT/"incoming"):
            try: zpath.unlink(); print(f"    removed {zpath.name}")
            except OSError: pass

    if not imported:
        print("Nothing imported."); sys.exit(1)

    # Write back, keeping BPSC first
    ordered = ([by_id.pop("bpsc_ghatna_chakra")] if "bpsc_ghatna_chakra" in by_id else [])
    ordered += [by_id[k] for k in by_id]
    BOOKS_JSON.write_text(json.dumps(ordered, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"\nRegistered {len(imported)} book(s): {', '.join(imported)}")

if __name__ == "__main__":
    main()
