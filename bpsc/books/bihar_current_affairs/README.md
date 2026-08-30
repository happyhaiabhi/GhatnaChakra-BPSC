# Bihar Current Affairs — Sets 1–11

The book is populated from `Bihar_Current_Affairs_Sets1-11_Categorised (2).xlsx`.

- 11 subjects, one per practice set (`Set 1` … `Set 11`)
- 50 questions per set (550 total)
- Four-option MCQ structure with answer letters normalized from the workbook
- Legacy PDF placeholder chapters were removed

`data/chapters.json` is the book index: one entry per set, each pointing at its own
`data/set_1.json` … `data/set_11.json` runtime file. `data/current_affairs_sets.json`
is the consolidated 550-question export kept for reference — it is no longer wired
into the UI.

## Subject `file` paths

Every `"file"` entry in `data/chapters.json` is resolved against the book's
`dataDir` from `books/books.json` (`books/bihar_current_affairs/data`), so it must
be a bare filename — `set_1.json`, not `data/set_1.json`. A `data/`-prefixed value
points outside the book folder and the subject renders "⚠ Could not load this
subject". `python scripts/sync_bpsc_runtime.py` validates this for every book.
