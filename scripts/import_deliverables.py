#!/usr/bin/env python3
"""
Import the 6 uploaded subjects (already extracted under deliverables/ and
deliverables_history/ on origin/main) into SIX separate books.

Run from repo root:  python3 scripts/import_deliverables.py
"""
import json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = ROOT / "books"
BOOKS_JSON = BOOKS_DIR / "books.json"

# (source subject file, book id, title, emoji, color)
SUBJECTS = [
    ("deliverables/subjects/physics.json",                           "physics",        "Physics",        "⚛️",  "#4ea3ff"),
    ("deliverables/subjects/chemistry.json",                         "chemistry",      "Chemistry",      "🧪", "#46d6a8"),
    ("deliverables/subjects/biology.json",                           "biology",        "Biology",        "🧬", "#7ed957"),
    ("deliverables_history/subjects/ancient_history_of_india.json",  "ancient_india",  "Ancient India",  "🏛️", "#c9a84c"),
    ("deliverables_history/subjects/medieval_history_of_india.json", "medieval_india", "Medieval India", "🏰", "#d4845a"),
    ("deliverables_history/subjects/modern_history_of_india.json",   "modern_india",   "Modern India",   "📜", "#b07cd9"),
]

# Keep every source field except obvious duplicates of the normalized keys.
DROP_Q_FIELDS = set()

def main():
    books = json.loads(BOOKS_JSON.read_text(encoding="utf-8")) if BOOKS_JSON.exists() else []
    by_id = {b["id"]: b for b in books}
    total_q = 0

    for src_rel, book_id, title, emoji, color in SUBJECTS:
        src = ROOT / src_rel
        if not src.exists():
            print(f"✗ missing {src_rel} — skipped"); continue
        data = json.loads(src.read_text(encoding="utf-8"))

        dest_dir = BOOKS_DIR / book_id / "data"
        if dest_dir.exists(): shutil.rmtree(dest_dir.parent)
        dest_dir.mkdir(parents=True)
        dest_assets = dest_dir.parent / "assets"
        dest_assets.mkdir(parents=True, exist_ok=True)
        src_asset_dirs = [src.parent.parent / "assets", ROOT / "deliverables" / "assets", ROOT / "deliverables_history" / "assets"]

        # Normalise: only fields the app consumes.
        clean_chapters = []
        q_count = 0
        for c in data.get("chapters", []):
            qs = []
            for q in c.get("questions", []) or []:
                kept = {
                    "q": q.get("q") or q.get("question") or "",
                    "options": q.get("options") or {},
                    "answer": q.get("answer") or q.get("correct_option") or "A",
                    "explanation": q.get("explanation") or "",
                    "exam": q.get("exam") or "",
                    "year": q.get("year") or "",
                    **{k: v for k, v in q.items() if k not in
                       {"q", "question", "options", "answer", "correct_option",
                        "explanation", "exam", "year", *DROP_Q_FIELDS}},
                }
                qs.append(kept)
                asset = kept.get("asset") or kept.get("image")
                if asset:
                    name = Path(asset).name
                    for folder in src_asset_dirs:
                        cand = folder / name
                        if cand.exists():
                            shutil.copy2(cand, dest_assets / name)
                            break
                q_count += 1
            clean_chapters.append({
                "chapter_name": c.get("chapter_name") or c.get("name") or "General",
                "questions": qs,
            })

        subject_file = f"{book_id}.json"
        (dest_dir / subject_file).write_text(
            json.dumps({"subject": title, "chapters": clean_chapters}, ensure_ascii=False, indent=2),
            encoding="utf-8")

        index = [{
            "key": book_id, "label": title, "emoji": emoji, "file": subject_file,
            "chapters": [{"name": c["chapter_name"], "count": len(c["questions"])} for c in clean_chapters],
        }]
        (dest_dir / "chapters.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        by_id[book_id] = {
            "id": book_id, "title": title,
            "subtitle": "Purvavalokan 2026 · English",
            "tag": title.split()[0].upper(), "emoji": emoji, "color": color,
            "dataDir": f"books/{book_id}/data", "chaptersFile": "chapters.json",
            "description": f"{len(clean_chapters)} chapters · {q_count:,} verified questions",
        }
        print(f"✓ {title:16s}  {len(clean_chapters):2d} chapters  {q_count:5,d} questions  → books/{book_id}/")
        total_q += q_count

    ordered = ([by_id.pop("bpsc_ghatna_chakra")] if "bpsc_ghatna_chakra" in by_id else [])
    ordered += [by_id[k] for k in by_id]
    BOOKS_JSON.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nRegistered 6 books with {total_q:,} total questions in books/books.json")

if __name__ == "__main__":
    main()
