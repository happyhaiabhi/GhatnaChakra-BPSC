# GS1 Fast Pack — all Prelims GS Paper 1 explanations

Neutral bulk store of **every GS1 explanation** so GitHub (and CDNs) can serve them quickly — no scraping.

## Stats
| | |
|-|-:|
| Questions | **3,873** |
| Explanations | **3,873** |
| Years | **1995–2026** |

## Choose a file

| Need | File |
|------|------|
| **Load all GS1 explanations at once** | [`gs1_explanations_all.min.json`](./gs1_explanations_all.min.json) (~5 MB) |
| **Fastest lookup by question id** | [`gs1_id_to_explanation.json`](./gs1_id_to_explanation.json) |
| **One year only (best for web apps)** | [`explanations_by_year/YYYY.json`](./explanations_by_year/) (~150–260 KB) |
| Answer key table | [`gs1_index.csv`](./gs1_index.csv) |
| Full GS1 **with options A–D** | [`../../gs1/upsc_gs1_all_years.json`](../../gs1/upsc_gs1_all_years.json) |

## After you push to GitHub — instant raw URLs

```text
# all explanations
https://raw.githubusercontent.com/<USER>/upsc-prelims-archive/main/data/fast/gs1/gs1_explanations_all.min.json

# one year (fastest page load)
https://raw.githubusercontent.com/<USER>/upsc-prelims-archive/main/data/fast/gs1/explanations_by_year/2025.json

# id → explanation map
https://raw.githubusercontent.com/<USER>/upsc-prelims-archive/main/data/fast/gs1/gs1_id_to_explanation.json

# jsDelivr CDN mirror
https://cdn.jsdelivr.net/gh/<USER>/upsc-prelims-archive@main/data/fast/gs1/explanations_by_year/2025.json
```

## Python

```python
import json

# O(1) by id
m = json.load(open("data/fast/gs1/gs1_id_to_explanation.json"))
print(m["UPSCPRELI2016GS01041"]["answer"])
print(m["UPSCPRELI2016GS01041"]["explanation"])

# all years
pack = json.load(open("data/fast/gs1/gs1_explanations_all.min.json"))
print(pack["question_count"])
```

## Record shape

```json
{
  "id": "UPSCPRELI2025GS01001",
  "year": 2025,
  "paper": "GS1",
  "position": 1,
  "subject": "economy",
  "answer": "B",
  "question": "…",
  "explanation": "… full solution …",
  "infographic_url": "https://storage.googleapis.com/…/UPSCPRELI2025GS01001.webp",
  "url": "https://www.dalvoy.com/upsc/prelims/2025/q/…"
}
```

Infographic **images** stay as URLs (binaries are large). Download with `python3 scripts/download_infographics.py --paper GS1` if needed.
