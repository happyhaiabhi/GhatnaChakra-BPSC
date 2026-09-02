# Book Covers

Cover images live in this folder and are referenced from `../books.json` with the
`cover` field. The book selection page shows each cover inside a fixed 3:4 frame
on the left of its card, with the tag pill, title and subtitle stacked in a
flexible column beside it — so nothing overlaps at any browser zoom level or
viewport width. The book `emoji` is shown inside that same frame only as a
fallback when no cover is registered or the image fails to load.

## Covers registered in `books/books.json` (all 13 books)

| Book (id) | File |
| --- | --- |
| `bpsc_ghatna_chakra` | `bpsc_ghatna_chakra.jpg` |
| `crown` | `crown.jpg` |
| `tarkas` | `tarkas.jpg` |
| `tarkash_annual` | `tarkash_annual.jpg` |
| `physics` | `physics.jpg` |
| `chemistry` | `chemistry.jpg` |
| `biology` | `biology.jpg` |
| `ancient_india` | `ancient_india.jpg` |
| `medieval_india` | `medieval_india.jpg` |
| `modern_india` | `modern_india.svg` |
| `kgs_test_series` | `kgs_test_series.svg` |
| `bihar_current_affairs` | `bihar_current_affairs.svg` |
| `eduteria_bihar_tathya_sangrah` | `eduteria_bihar_tathya_sangrah.jpg` |

JPG/PNG and SVG files both work (`<img>` handles them natively).

## Replacing or adding a cover

1. Drop your image into this folder, e.g. `crown.jpg` (portrait ≈ 3:4 looks best,
   e.g. 600×800).
2. In `bpsc/books/books.json` set the book's `cover` field:

   ```json
   { "id": "crown", "cover": "books/covers/crown.jpg" }
   ```

3. Done — no code changes needed. A broken/missing cover silently falls back to
   the book emoji.

Tip: the current AI-generated covers are placeholders only. Send real book
photos and overwrite these files (keep the same file names) to publish them
instantly.
