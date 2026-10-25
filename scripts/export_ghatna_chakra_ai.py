#!/usr/bin/env python3
"""Export the Ghatna Chakra Ancient / Medieval / Modern India question banks to
AI-readable datasets (JSONL, JSON, CSV, Markdown) under exports/ghatna_chakra/.

Source of truth is the runtime book data used by the BPSC app:

    bpsc/books/ancient_india/data/ancient_india.json
    bpsc/books/medieval_india/data/medieval_india.json
    bpsc/books/modern_india/data/modern_india.json

Each source file looks like {"subject": str, "chapters": [{"chapter_name": str,
"questions": [ {q, options, answer, explanation, exam, year, [note], [asset]} ]}]}

The exporter normalises the PDF-extracted text (ligatures such as "ﬁ rst",
wrapped lines, exam names accidentally pasted into option text), turns every
question into one flat, self-describing record, and tags machine-detectable
problems with quality flags instead of silently dropping or "fixing" content.

Run:
    python scripts/export_ghatna_chakra_ai.py            # rebuild all exports
    python scripts/export_ghatna_chakra_ai.py --check    # verify only, no writes
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOKS = OrderedDict(
    [
        ("ancient_india", {"period": "Ancient India", "code": "anc", "emoji": "🏛️"}),
        ("medieval_india", {"period": "Medieval India", "code": "med", "emoji": "🏰"}),
        ("modern_india", {"period": "Modern India", "code": "mod", "emoji": "📜"}),
    ]
)
OUT_DIR = ROOT / "exports" / "ghatna_chakra"

# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

LIGATURES = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}

# Word frequencies of the whole corpus, filled in by build_records(); used to
# repair ligatures that the PDF extraction split into "fi rst" / "diff erent".
VOCAB: Counter | None = None

# The PDF extraction often emits "ﬁ rst" (ligature + spurious space). Merge the
# ligature with the following fragment so the word is whole again.
_LIG_THEN_SPACE = re.compile("[%s][ \t]+(?=[A-Za-z])" % "".join(LIGATURES))

_WHITESPACE = re.compile(r"[ \t\u00a0]+")
_CID_GLYPH = re.compile(r"(?:\(cid:\d+\))+")
_SINGLE_NEWLINE = re.compile(r"[ \t]*\n[ \t]*")
_BLANK_LINES = re.compile(r"\n{2,}")

# A leftover exam+year tail inside option text, e.g. "Sikandar Lodi 44 B.P.S.C.
# (Pre) 2000 th" or "Aurangzeb U.P.P.C.S. (Pre) 2012".
_EXAM_CODE = re.compile(
    # optional leading paper number, possibly a range: "44", "45th", "53 to 55"
    r"(?:\d{1,2}\s*(?:st|nd|rd|th)?(?:\s*(?:to|-|–)\s*\d{1,2}\s*(?:st|nd|rd|th)?)?\s*)?"
    r"(?:"
    r"B\.?\s?P\.?\s?S\.?\s?C|U\.?\s?P\.?\s?P?\.?\s?C\.?\s?S|C\.?\s?S\.?\s?S|"
    r"I\.?\s?A\.?\s?S|M\.?\s?P\.?\s?P?\.?\s?C\.?\s?S|U\.?\s?P\.?\s?S\.?\s?C|"
    r"R\.?\s?A\.?\s?S|J\.?\s?P\.?\s?S\.?\s?C"
    r")\.?",
    re.I,
)
_TAIL_YEAR = re.compile(r"(?:19|20)\d{2}")


def fix_ligatures(text: str) -> str:
    text = _LIG_THEN_SPACE.sub(lambda m: LIGATURES[m.group(0)[0]], text)
    for lig, repl in LIGATURES.items():
        text = text.replace(lig, repl)
    return text


def normalize_text(text: str, keep_paragraphs: bool = False) -> str:
    """Collapse PDF line wrapping; optionally keep blank-line paragraph breaks."""
    if text is None:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    text = fix_ligatures(text)
    if VOCAB:
        text = repair_split_ligatures(text, VOCAB)
        text = repair_line_hyphens(text, VOCAB)
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u00ad", "")
    text = _CID_GLYPH.sub("", text)
    if keep_paragraphs:
        paragraphs = [normalize_text(p) for p in _BLANK_LINES.split(text)]
        return "\n\n".join(p for p in paragraphs if p)
    text = _SINGLE_NEWLINE.sub(" ", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()


_ORPHAN_ORDINALS = re.compile(r"^(?:(?:st|nd|rd|th|to|and|&)\b[\s,;]*)+|(?:[\s,]+(?:st|nd|rd|th))+\s*$", re.I)


def clean_exam(exam: str) -> str:
    """Drop the ordinal fragments the PDF extraction leaves behind ("rd th")."""
    parts = []
    for part in re.split(r"[;]", exam or ""):
        part = part.strip(" ,;.-")
        if not part:
            continue
        if re.fullmatch(r"[\W_]+", part):
            continue
        if re.fullmatch(r"(?:st|nd|rd|th|to|and|&|-)+", part, re.I):
            continue
        part = _ORPHAN_ORDINALS.sub("", part).strip(" ,;-")
        if part:
            parts.append(part)
    return "; ".join(parts)


# Many ligatures were split by the original extraction: "first" arrived as
# "fi rst", "different" as "diff erent", "official" as "offi cial".  We repair
# these only when the glued word actually exists elsewhere in the corpus, so
# genuine word pairs ("most of", "west Bengal") are left untouched.
_SPLIT_LIGATURE = re.compile(
    r"\b(?P<head>[A-Za-z]{0,8}?)(?P<lig>ffi|ffl|ff|fi|fl|ft|st)\s+(?P<rest>[a-z]{2,10})\b"
)
_TOKEN = re.compile(r"[A-Za-z]+")


def build_vocabulary(texts) -> Counter:
    vocab: Counter = Counter()
    for text in texts:
        vocab.update(t.lower() for t in _TOKEN.findall(fix_ligatures(text)))
    return vocab


# Common English words that still occasionally arrive split in this corpus.
# Seeded with a high count so the repair never depends on luck.
SEED_WORDS = """
first field fields five fifteen fifteenth fifty fifth fiftytwo
fixed fixing fix file filed files film films filmmaker final finally
financial financed fine fined fines finish finished finishing fire firing
firearms firm firms fiscal fiction fictional fierce fiery fight fighter
fighters fights figurine figurines fillip flag flags flagrant flame flat
fled fledged fleet fleeting flocked flood floods floor floors floral
flourish flourished flourishing flow flower flowers fluctuate fluctuations
fluke fulfil fulfilled fulfilling fulfilment fulfillment fief fiefs
official officials office officer officers different difficult difficulties
difficulty sufficient efficiently efficiency deficiency beneficial sacrifice
sacrifice crucifixion affluent affiliated affiliates afflictions confident
confirmed configuration confined confiscated conflicting conflicts confluence
identified identifies notified ratified rectified modified modification
modifications purification qualification qualified superficial proficient
significance significant significantly signifies significance
""".split()


def repo_corpus_vocabulary() -> Counter:
    """Word frequencies from every question bank in the repo, for text repair."""
    texts: list[str] = []

    def walk(node) -> None:
        if isinstance(node, str):
            texts.append(node)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for path in sorted((ROOT / "bpsc" / "books").glob("*/data/*.json")):
        try:
            walk(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue

    vocab = build_vocabulary(texts)
    for word in SEED_WORDS:
        vocab[word] = max(vocab[word], 50)
    return vocab


def repair_split_ligatures(text: str, vocab: Counter) -> str:
    def repl(match: re.Match) -> str:
        joined = (match.group("head") + match.group("lig") + match.group("rest"))
        if len(joined) < 3:
            return match.group(0)
        if vocab.get(joined.lower(), 0) >= 2:
            return joined
        return match.group(0)

    return _SPLIT_LIGATURE.sub(repl, text)


# Words that keep their hyphen when a PDF line break split them:
# "Non- cooperation" is "Non-cooperation", "in- law" is "in-law".
_HYPHEN_PREFIXES = {
    "non", "self", "well", "ill", "pre", "post", "sub", "super", "anti", "co",
    "re", "mid", "over", "under", "semi", "multi", "inter", "intra", "counter",
    "pro", "quasi", "ultra", "half", "all", "cross", "vice", "ex", "by", "off",
    "in", "on", "out", "up", "ever", "never", "twice", "three", "one", "two",
}
_LINE_HYPHEN = re.compile(r"\b(?P<left>[A-Za-z]+)-(?P<space>\s+)(?P<right>[a-z]{2,})\b")


def repair_line_hyphens(text: str, vocab: Counter) -> str:
    """Undo hyphenation introduced by a PDF line break ("headquar- ters")."""

    def repl(match: re.Match) -> str:
        left, right = match.group("left"), match.group("right")
        joined = (left + right)
        if vocab.get(joined.lower(), 0) >= 2:
            return joined
        if left.lower() in _HYPHEN_PREFIXES:
            return f"{left}-{right}"
        return match.group(0)

    return _LINE_HYPHEN.sub(repl, text)


def strip_exam_tail(option_text: str) -> tuple[str, str | None]:
    """Remove an exam name + year pasted onto the end of an option.

    Returns (clean_option, removed_text_or_None).
    """
    text = option_text.rstrip()
    matches = list(_EXAM_CODE.finditer(text))
    for match in reversed(matches):
        tail = text[match.start():]
        if len(tail) > 70:  # a real option, not a pasted exam label
            continue
        if not _TAIL_YEAR.search(tail):
            continue
        cleaned = text[: match.start()].rstrip(" ,;.-–")
        if len(cleaned) < 2:
            continue  # never strip an option down to nothing
        return cleaned, tail.strip()
    return text, None


# ---------------------------------------------------------------------------
# Record building
# ---------------------------------------------------------------------------

LETTERS = ("A", "B", "C", "D", "E", "F")
BLOCKING_FLAGS = {
    "answer_missing",
    "answer_key_invalid",
    "malformed_question",
    "duplicate_question",
    "image_dependent",
    "option_missing",
}


def normalize_answer_key(raw, options: dict) -> tuple[list[str], list[str]]:
    """Return (letters, flags)."""
    flags: list[str] = []
    letters: list[str] = []
    if isinstance(raw, str):
        candidate = raw.strip().upper()
        if candidate in ("", "*", "?", "-"):
            return [], ["answer_missing"]
        if re.fullmatch(r"[A-F](?:\s*[,/&]\s*[A-F])+", candidate):
            letters = [c for c in re.findall(r"[A-F]", candidate)]
            flags.append("multi_answer")
        elif candidate in LETTERS:
            letters = [candidate]
        else:
            flags.append("answer_key_invalid")
            return [], flags
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            token = str(item).strip().upper()
            if token in LETTERS:
                letters.append(token)
        if not letters:
            flags.append("answer_missing")
            return [], flags
        if len(letters) > 1:
            flags.append("multi_answer")
    else:
        flags.append("answer_missing")
        return [], flags

    letters = list(dict.fromkeys(letters))
    missing = [l for l in letters if l not in options]
    if missing:
        flags.append("answer_key_invalid")
        return letters, flags
    return letters, flags


def parse_years(raw) -> list[int]:
    if raw is None:
        return []
    found = re.findall(r"(?:19|20)\d{2}", str(raw))
    return [int(y) for y in dict.fromkeys(found)]


def load_books() -> "OrderedDict[str, dict]":
    loaded = OrderedDict()
    for book_id in BOOKS:
        path = ROOT / "bpsc" / "books" / book_id / "data" / f"{book_id}.json"
        loaded[book_id] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def build_records() -> tuple[list[dict], list[dict]]:
    records: list[dict] = []
    subjects_meta: list[dict] = []

    global VOCAB
    books = load_books()
    VOCAB = repo_corpus_vocabulary()

    for book_id, meta in BOOKS.items():
        data = books[book_id]
        subject = data.get("subject") or book_id
        chapters = data.get("chapters") or []
        counter = 0
        chapter_meta = []
        seen_questions: dict[str, str] = {}

        for chapter_index, chapter in enumerate(chapters, start=1):
            chapter_name = normalize_text(chapter.get("chapter_name", ""))
            questions = chapter.get("questions") or []
            chapter_meta.append(
                {"chapter_no": chapter_index, "chapter_name": chapter_name, "count": len(questions)}
            )

            for q_index, raw in enumerate(questions, start=1):
                counter += 1
                flags: list[str] = []

                question = normalize_text(raw.get("q", ""))
                explanation = normalize_text(raw.get("explanation", ""), keep_paragraphs=True)
                note = normalize_text(raw.get("note", "")) if raw.get("note") else ""
                asset = normalize_text(raw.get("asset", "")) if raw.get("asset") else ""

                options: dict[str, str] = OrderedDict()
                stripped_tails: list[str] = []
                for key, value in (raw.get("options") or {}).items():
                    cleaned = normalize_text(value)
                    cleaned, removed = strip_exam_tail(cleaned)
                    if removed:
                        stripped_tails.append(removed)
                    options[str(key).strip().upper()] = cleaned

                if any(not v for v in options.values()):
                    flags.append("option_missing")
                if stripped_tails:
                    flags.append("option_exam_text_removed")
                if len(options) >= 5:
                    flags.append("five_options")

                answer_letters, answer_flags = normalize_answer_key(raw.get("answer"), options)
                flags.extend(answer_flags)

                exam = clean_exam(normalize_text(raw.get("exam", "")))
                if exam in (".", "-", "—"):
                    exam = ""
                if not exam and stripped_tails:
                    exam = clean_exam(stripped_tails[0])
                    if exam:
                        flags.append("exam_recovered_from_option")
                if not exam:
                    flags.append("exam_missing")
                years = parse_years(raw.get("year"))
                if not years:
                    years = parse_years(exam)
                if not years:
                    flags.append("year_missing")

                # The source PDF occasionally glues a whole note block onto the
                # front of a question (multi-thousand-character "questions").
                if len(question) > 1100:
                    flags.append("malformed_question")
                if len(options) < 2:
                    flags.append("option_missing")

                if asset:
                    flags.append("image_dependent")

                if not explanation:
                    flags.append("explanation_missing")

                # Two different questions can share a generic stem ("Which of the
                # following is not correctly matched?"), so dedupe on stem+options.
                dedupe_key = re.sub(
                    r"[^a-z0-9]+",
                    " ",
                    (question + " " + " ".join(options.values())).lower(),
                ).strip()
                if dedupe_key and dedupe_key in seen_questions:
                    flags.append("duplicate_question")
                elif dedupe_key:
                    seen_questions[dedupe_key] = f"{meta['code']}-{counter:04d}"

                flags = list(dict.fromkeys(flags))
                answer_text = [options[l] for l in answer_letters if l in options]

                record = OrderedDict(
                    [
                        ("id", f"{meta['code']}-{counter:04d}"),
                        ("subject", subject),
                        ("period", meta["period"]),
                        ("chapter_no", chapter_index),
                        ("chapter", chapter_name),
                        ("question_no", q_index),
                        ("question", question),
                        ("options", options),
                        ("num_options", len(options)),
                        ("answer_key", answer_letters),
                        ("answer_text", answer_text),
                        ("answer_raw", raw.get("answer")),
                        ("multi_correct", len(answer_letters) > 1),
                        ("explanation", explanation),
                        ("exam", exam),
                        ("year", years[0] if years else None),
                        ("years", years),
                        ("note", note or None),
                        ("asset", asset or None),
                        (
                            "quality",
                            OrderedDict(
                                [
                                    ("clean", not any(f in BLOCKING_FLAGS for f in flags)),
                                    ("flags", flags),
                                    (
                                        "removed_option_text",
                                        stripped_tails or None,
                                    ),
                                ]
                            ),
                        ),
                    ]
                )
                records.append(record)

        subjects_meta.append(
            {
                "book_id": book_id,
                "subject": subject,
                "period": meta["period"],
                "emoji": meta["emoji"],
                "id_prefix": meta["code"],
                "chapters": chapter_meta,
                "question_count": counter,
            }
        )

    return records, subjects_meta


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(path: Path, records: list[dict]) -> None:
    columns = [
        "id",
        "period",
        "subject",
        "chapter_no",
        "chapter",
        "question_no",
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "option_e",
        "num_options",
        "answer_key",
        "answer_text",
        "multi_correct",
        "explanation",
        "exam",
        "year",
        "clean",
        "flags",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for r in records:
            opts = r["options"]
            writer.writerow(
                {
                    "id": r["id"],
                    "period": r["period"],
                    "subject": r["subject"],
                    "chapter_no": r["chapter_no"],
                    "chapter": r["chapter"],
                    "question_no": r["question_no"],
                    "question": r["question"],
                    "option_a": opts.get("A", ""),
                    "option_b": opts.get("B", ""),
                    "option_c": opts.get("C", ""),
                    "option_d": opts.get("D", ""),
                    "option_e": opts.get("E", ""),
                    "num_options": r["num_options"],
                    "answer_key": "|".join(r["answer_key"]),
                    "answer_text": " | ".join(r["answer_text"]),
                    "multi_correct": r["multi_correct"],
                    "explanation": r["explanation"],
                    "exam": r["exam"],
                    "year": r["year"] or "",
                    "clean": r["quality"]["clean"],
                    "flags": "|".join(r["quality"]["flags"]),
                }
            )


def write_markdown(path: Path, records: list[dict], subjects_meta: list[dict]) -> None:
    lines = [
        "# Ghatna Chakra — Ancient, Medieval and Modern India question bank",
        "",
        "One section per subject and chapter. Every question carries its four or five",
        "options, the correct answer key, the book's explanation and the exam it was",
        "asked in.",
        "",
        "| Subject | Chapters | Questions |",
        "|---|---|---|",
    ]
    for meta in subjects_meta:
        lines.append(f"| {meta['subject']} | {len(meta['chapters'])} | {meta['question_count']} |")
    lines.append(f"| **Total** | **{sum(len(m['chapters']) for m in subjects_meta)}** | **{len(records)}** |")
    lines.append("")

    current_subject = None
    current_chapter = None
    for record in records:
        if record["subject"] != current_subject:
            current_subject = record["subject"]
            lines += ["", f"# {current_subject}", ""]
            current_chapter = None
        if record["chapter"] != current_chapter:
            current_chapter = record["chapter"]
            lines += ["", f"## {current_chapter}", ""]

        lines.append(f"**Q{record['question_no']}.** {record['question']}")
        lines.append("")
        for letter, text in record["options"].items():
            lines.append(f"- **{letter}.** {text}")
        lines.append("")
        key = ", ".join(record["answer_key"]) if record["answer_key"] else "not given in source"
        if record["answer_key"]:
            lines.append(f"**Answer:** {key} — {'; '.join(record['answer_text'])}")
        else:
            lines.append(f"**Answer:** {key}")
        meta_bits = []
        if record["exam"]:
            meta_bits.append(record["exam"])
        if record["explanation"]:
            lines.append(f"**Explanation:** {record['explanation']}")
        if meta_bits:
            lines.append(f"*Asked in:* {' · '.join(meta_bits)}")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="build in memory and compare counts only")
    args = parser.parse_args()

    records, subjects_meta = build_records()
    clean_records = [r for r in records if r["quality"]["clean"]]

    flag_counts = Counter(f for r in records for f in r["quality"]["flags"])
    per_subject = Counter(r["subject"] for r in records)
    per_subject_clean = Counter(r["subject"] for r in clean_records)
    exams = Counter(r["exam"] for r in records if r["exam"])
    years = Counter(r["year"] for r in records if r["year"])

    print(f"records: {len(records)}  clean: {len(clean_records)}")
    for subject, count in per_subject.items():
        print(f"  {subject}: {count} ({per_subject_clean[subject]} clean)")
    print("flags:", dict(flag_counts))
    print("distinct exams:", len(exams), "| distinct years:", len(years))

    if args.check:
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    files = {}

    # Per-subject JSONL (all records, flagged) ------------------------------
    for book_id, meta in BOOKS.items():
        subject_records = [r for r in records if r["period"] == meta["period"]]
        name = f"ghatna_chakra_{book_id}.jsonl"
        write_jsonl(OUT_DIR / name, subject_records)
        files[name] = {
            "description": f"{meta['period']} — every question, one JSON object per line",
            "records": len(subject_records),
        }

    # Combined JSONL --------------------------------------------------------
    write_jsonl(OUT_DIR / "ghatna_chakra_all_india.jsonl", records)
    files["ghatna_chakra_all_india.jsonl"] = {
        "description": "Ancient + Medieval + Modern India — all questions, flagged, one JSON object per line",
        "records": len(records),
    }

    write_jsonl(OUT_DIR / "ghatna_chakra_all_india_clean.jsonl", clean_records)
    files["ghatna_chakra_all_india_clean.jsonl"] = {
        "description": "Same records with quality.clean = true only (no unknown answer keys, no malformed or duplicate rows, no image-only questions)",
        "records": len(clean_records),
    }

    # Single JSON document --------------------------------------------------
    document = OrderedDict(
        [
            ("dataset", "Ghatna Chakra — Ancient, Medieval and Modern India"),
            (
                "description",
                "Previous-year MCQs compiled in the Ghatna Chakra series for BPSC / UPSC / State PCS, "
                "extracted from the BPSC app's book data. Every question keeps its options, answer key, "
                "explanation, exam name and year.",
            ),
            ("source", "bpsc/books/{ancient_india,medieval_india,modern_india}/data/*.json"),
            ("generated_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
            ("license_note", "Compiled study material. Verify facts against the original book before reuse."),
            ("counts", {"total": len(records), "clean": len(clean_records)}),
            ("subjects", subjects_meta),
            ("questions", records),
        ]
    )
    (OUT_DIR / "ghatna_chakra_all_india.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    files["ghatna_chakra_all_india.json"] = {
        "description": "Single JSON document: dataset metadata, subject/chapter index and every question",
        "records": len(records),
    }

    # CSV -------------------------------------------------------------------
    write_csv(OUT_DIR / "ghatna_chakra_all_india.csv", records)
    files["ghatna_chakra_all_india.csv"] = {
        "description": "Flat spreadsheet export (option_a … option_e, answer_key, flags)",
        "records": len(records),
    }

    # Markdown --------------------------------------------------------------
    write_markdown(OUT_DIR / "ghatna_chakra_all_india.md", records, subjects_meta)
    files["ghatna_chakra_all_india.md"] = {
        "description": "Human- and LLM-friendly reading copy: question, options, answer, explanation",
        "records": len(records),
    }

    for name in files:
        path = OUT_DIR / name
        files[name]["bytes"] = path.stat().st_size
        files[name]["sha256"] = sha256(path)

    manifest = OrderedDict(
        [
            ("dataset", "Ghatna Chakra — Ancient, Medieval and Modern India"),
            ("generated_at", document["generated_at"]),
            ("generator", "scripts/export_ghatna_chakra_ai.py"),
            ("counts", {
                "total": len(records),
                "clean": len(clean_records),
                "by_subject": dict(per_subject),
                "by_subject_clean": dict(per_subject_clean),
                "chapters": sum(len(m["chapters"]) for m in subjects_meta),
            }),
            ("quality_flags", dict(flag_counts.most_common())),
            ("distinct_exams", len(exams)),
            ("year_range", [min(years), max(years)] if years else None),
            ("subjects", subjects_meta),
            ("files", files),
        ]
    )
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {len(files) + 1} files to {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
