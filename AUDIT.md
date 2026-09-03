# Repository Audit — GhatnaChakra-BPSC

**Audited:** 2026-09-03 · `main` @ `433af3d` (re-audited after PRs #36–#40 landed)
**Branch of record for this audit:** `arena/01a065e6-ghatnachakra-bpsc`
**Live site:** https://happyhaiabhi.github.io/GhatnaChakra-BPSC/

> ### ⚠️ Read this before merging anything
> This branch was originally cut from a **disconnected root commit**, not from
> the real `main`. `main` has 151 commits and has moved several times since —
> PRs #36–#40 added the consolidated Physics/Biology notes, the **PYQ Lab**
> (`bpsc/pyq-lab.js`, 859 lines) and a deliberate change making **light mode
> the default with no persistence**.
>
> Merging an earlier version of this branch would have reverted all of it. The
> branch has since been **rebuilt on top of `main`** and the split re-run
> against the current `bpsc/index.html`, so the PYQ Lab is preserved — verified
> below. But the lesson generalises: **check what `main` has done before
> merging a long-lived branch here.**

A code + design audit of the combined UPSC/BPSC exam portal: how it is put
together today, what is costing you speed and maintainability, and the exact
add/subtract list — with the safe half already applied in this branch.

---

## 1. Scorecard

| Area | Grade | One-line verdict |
|---|---|---|
| Product idea & content depth | **A** | 6,486 UPSC questions + 19,050 BPSC questions across 12 books. The content is the moat. |
| Visual design | **B+** | Confident, coherent dark-first aesthetic. Four stylesheets and 102 KB of inline CSS keep it from being consistent. |
| Front-end architecture | **C−** | One 323 KB single-file app with 235 functions; no build, no modules, no tests. |
| Performance | **D** | UPSC page pulls ~14 MB before it renders. Pages publishes a 359 MB repo. |
| Repository hygiene | **D** | 76 % of the repo is unlinked source PDFs; `.gitignore` lies; 40 dead branches. |
| Deployment / CI | **F** | `DEPLOY_TO_GITHUB.md` documents a workflow that does not exist. Pages is on legacy branch-deploy. |
| Documentation | **B** | README is genuinely good — and is the source of two of the problems below, because it describes a repo that isn't there. |

**Headline:** the product is strong, the plumbing is not. Nothing here needs a
rewrite; it needs a *publishing boundary*, a *load budget*, and a *file-splitting
plan*. All three are cheap.

---

## 2. How the repository is organised today

```
main (359 MB · 448 files · zero build step)
│
├── index.html ────────────── exam gateway (UPSC card / BPSC card)   3.2 KB
├── upsc.html ─────────────── UPSC app shell                        11.3 KB
│   ├── styles.css            46 KB   UPSC design system
│   ├── app.js                36 KB   search, filters, browse flows
│   ├── data.js            6,438 KB   offline bundle (generated)
│   └── data/*.json        7,666 KB   the same data, fetched over HTTP
│
├── bpsc/index.html ───────── THE ENTIRE BPSC APPLICATION         323.6 KB
│   │                           235 functions · 102 KB inline CSS
│   │                           178 KB inline JS · 5 <style> blocks
│   ├── books/books.json       12 book manifests
│   ├── books/<id>/data/        ~90 subject JSON files (schema-consistent)
│   ├── data/                  13 legacy Ghatna Chakra subject files
│   └── css/floral-pattern.svg
│
├── bpsc-theme.css            24 KB   BPSC day/night palette
├── portal.css                10 KB   gateway page
├── theme.js                  2.8 KB  shared night-mode (the one genuinely
│                                     shared module in the project)
│
├── scripts/                  14 Python pipeline scripts (PDF → JSON,
│                                 PYQ analysis, notes typesetting, sync)
├── firestore.rules                 Firestore security rules
│
└── 310 MB of PDFs ─────────── 92 files
    ├── 4 linked from bpsc/index.html ("Study Notes" screen)    38.4 MB
    └── 88 linked from nothing                                271.7 MB  ← 76 %
```

**Two applications, one shared theme, zero shared code.** `theme.js` is the
only module both halves import. Everything else — colour tokens, button styles,
card patterns, empty states — is re-implemented in `styles.css`,
`bpsc-theme.css`, `portal.css`, and 102 KB of `<style>` blocks inside
`bpsc/index.html`.

**The content pipeline is the good part.** `scripts/` turns coaching PDFs into
validated JSON with PYQ-priority analysis. 130 JSON files parse cleanly and the
90 book subject files share one schema (`{subject, chapters[]}`). This is real,
disciplined work — and it is invisible to a contributor because none of it is
wired into CI.

---

## 3. Problems, ranked

### P0 — The site publishes the whole repository

```jsonc
// gh api repos/happyhaiabhi/GhatnaChakra-BPSC/pages
{ "build_type": "legacy", "source": { "branch": "main", "path": "/" } }
```

Pages is on **legacy branch-deploy from `/`**. Every byte in the repo is a
public URL. That includes `new kgs data/` (115 MB of KGS test PDFs),
`EDUTERIA BIO NOTES/` (81 MB), `physic notes eduteria/` (48 MB) — **271.7 MB
that no HTML file links to.**

Compounding it: `DEPLOY_TO_GITHUB.md` and `README.md` both say

> `.github/workflows/deploy-pages.yml` validates JavaScript, Python scripts and
> the 100 MB single-file limit…

**`.github/` does not exist in the repository.** Zero files. The documented CI
was never committed, so none of those safety checks have ever run.

> **Staged in this branch:** `docs/deploy-pages.workflow.yml` does exactly what
> the docs promise — `node --check`, `py_compile`, JSON validation, a 100 MB
> file-size gate, a data/reference integrity check, and a staged `_site/` that
> contains only the runtime plus the 4 PDFs actually linked (verified locally:
> **80 MB instead of 361 MB**).
>
> It is *staged* rather than active because the automation token that committed
> it is not granted GitHub's `workflows` permission, and GitHub rejects any
> push touching `.github/workflows/*` without it. **Two steps to turn it on:**
> ```bash
> mkdir -p .github/workflows
> git mv docs/deploy-pages.workflow.yml .github/workflows/deploy-pages.yml
> git commit -m "Activate Pages workflow" && git push
> ```
> then Settings → Pages → Source → **GitHub Actions**. Until both are done,
> nothing changes.

### P0 — `bpsc-source` was never created, so the sync script is a no-op

`git ls-remote --heads origin` → **41 branches: `main` + 40 stale `arena/*`
session branches. There is no `bpsc-source`.**

`DEPLOY_TO_GITHUB.md` opens with “Do not skip this branch step.” It was
skipped. Consequences:

- `scripts/sync_bpsc_runtime.py` logs a warning and falls back to `main` —
  i.e. it copies `bpsc/` onto `bpsc/`. Self-copy, silently.
- The standalone BPSC project (tests, extraction tools, editable source) has no
  home. `main` is now the generated portal, so the thing the sync script is
  supposed to read from no longer exists anywhere.
- 40 dead `arena/*` branches are accumulating on the remote.

> **Not fixed here** — I cannot create branches outside this session branch.
> This is the single highest-value thing you can do in five minutes; the exact
> commands are in §6.

### P1 — The UPSC page downloads ~14 MB before it shows a question

`upsc.html` ends with:

```html
<script src="data.js"></script>   <!-- 6,438,685 bytes, parser-blocking -->
<script src="app.js"></script>
```

and then `app.js` fetches `data/prelims.json` + `csat.json` + `mains.json` —
**another 7,666,029 bytes**. So a first-time visitor downloads the same 6,486
questions twice: once as a blocking script, once as JSON. Gzipped that is still
~3 MB and roughly 10–14 s on a decent Indian 4G connection before the search box
is usable.

`data.js` exists for one reason: when the folder is opened from disk
(`file://`), `fetch()` cannot read `data/*.json`. That is 1 % of sessions
paying a 100 % tax on the other 99 %.

> **Fixed in this branch:** `data.js` is now injected **only** when
> `location.protocol === 'file:'`. Over HTTP the page loads 11 KB of HTML +
> 46 KB CSS + 36 KB JS and streams the JSON it needs. **−6.4 MB per visit.**
>
> Verified both ways with jsdom: over HTTP the page renders 20 result cards and
> the full `6,486 questions · 3,196 Prelims · 1,211 CSAT · 2,079 Mains` header
> with `data.js` never requested; opened from `file://` the bundle is injected
> and `window.UPSC_QUESTION_BANK_DATA` is populated before `app.js` runs.
> (`tools/upsc-smoke.js` guards the HTTP path.)

### P1 — `bpsc/index.html` is a 323 KB single-file application

| | |
|---|---|
| File size | **342,449 bytes** |
| Inline CSS (3 `<style>` blocks) | **104,986 bytes** |
| Inline JS (2 `<script>` blocks) | **190,583 bytes** |
| Functions in one scope | **251** |
| Global `let`/`const` bindings | ~120 |
| External CSS/JS files | **0** |

Everything lives in one global scope: quiz engine, 12-book loader, chapter
tree, Bloom spaced-repetition scheduler, five review banks, attempt history,
dashboard, print/PDF exporter, focus timer, search, and the Firebase sync
layer. It works, and the escaping discipline is genuinely careful
(`bookText()` → `escapeHtml()` is applied consistently to question text —
235 functions and I could not find an unescaped data sink). But:

- **It cannot be reviewed.** A 323 KB diff is unreadable; every change to the
  quiz engine is a change to the same file as the print stylesheet.
- **It cannot be cached.** Every deploy invalidates 323 KB, including 102 KB of
  CSS that never changes.
- **It cannot be reused.** The UPSC half re-implements cards, filters, pills
  and empty states from scratch because none of it is importable.
- **It cannot be tested.** No module boundary means no unit test entry point.

**Resolution — done in this branch**

| | before | after |
|---|---|---|
| `bpsc/index.html` | **342,449 B** | **43,840 B** |
| inline CSS | 104,986 B (3 blocks) | 0 — `bpsc/css/{base,screens,portal-notes}.css` |
| inline JS | 190,583 B (2 blocks) | 0 — 16 ordered scripts in `bpsc/js/` |
| external assets | `theme.js?v=2`, `pyq-lab.js?v=6` | + 5 stylesheets, all still in order |
| cacheable | nothing | 105 KB CSS + 191 KB JS |

> **Done in this branch.** `tools/split-bpsc.js` lifted the 3 `<style>` blocks
> into `bpsc/css/` and sliced the 190 KB inline script into 15 ordered,
> single-purpose files (`00-data.js` … `14-boot.js`) plus `date-banner.js`.
> Slice 1 of §7, executed. The **PYQ Lab** that PRs #38/#40 added is preserved:
> its cross-book global search became `13-global-search.js`, and
> `pyq-lab.js?v=6` / `pyq-lab.css?v=5` keep their exact load order and their
> version query strings.

**Why it was safe, and how it was proven.** The file contains **zero `var`
declarations** (23 `let`, 28 `const`), and classic scripts share one global
lexical environment — so slicing at top-level *statement* boundaries with the
tags in original document order is semantically identical. The script asserts
this before writing anything: every extracted byte is checked back against the
original, every slice is re-parsed with acorn, and no top-level binding may be
duplicated.

Then it was verified at runtime, not just on paper. `tools/bpsc-smoke.js`
loads the app in jsdom and records errors, DOM state, 22 pure-function probes
and a SHA-1 of the body text; `tools/compare-smoke.js` diffs a before/after
pair. Result:

```text
15 identical · 5 structural change(s) · 0 regression(s)
PASS — behaviour is identical, only the file layout changed.
```

Identical down to 13 book cards, 12 subject cards, 942 CSS rules, 298 global
functions, the same SHA-1 body text, and an end-to-end run that opens the core
book, expands Ancient History (15 chapters, 208 questions), starts a quiz and
renders the same first question and the same 5 option buttons. The PYQ Lab's
`runGlobalBookSearch`, `ensureGlobalBookSearchIndex` and
`setupGlobalBookSearch` are all still defined after the split.

Two things the harness caught that a human reviewer would have missed:

- Moving the script tags to the end of `<body>` (tidier) changed the rendered
  body text by **one character** — the space in `"...explanations), or
  re-attempt"` was being swallowed by the extraction regex. Reverted to a pure
  tag removal; the difference disappeared.
- A first attempt dropped `js/00-data.js` and `js/date-banner.js` entirely,
  because byte offsets were computed before two tags were lifted out of the
  body. The smoke test showed 0 book cards where there should have been 13.

### P1 — 1,211 of 1,211 CSAT infographics are missing

`data/csat.json` gives every one of its 1,211 questions an
`infographic_local` path like `infographics/2011/UPSCCSAT2011GS02001.webp`
(4,407 references across all three datasets).

```
infographics/
└── .gitkeep        ← that's it.
```

Every single one silently falls back to `infographic_url` on Google Cloud
Storage. The site works, so this has never surfaced — but it means the
"locally bundled infographics" feature described in the README is not actually
on, every page view leaks a referrer to a third party, and the offline story is
broken. `scripts/download_infographics.py` exists and is resumable; it has
simply never been run (or the result was never committed).

> **Partly fixed:** the staged deploy workflow warns on every build when
> referenced infographics are missing, so this cannot stay invisible. Run
> `python scripts/download_infographics.py` to close it.

### P2 — Dead code and stale contracts

| File | Size | Why it's dead |
|---|---|---|
| `bpsc/css/style.css` | 20 KB | Never linked. `bpsc/index.html` only uses `url('css/floral-pattern.svg')` inline. |
| `bpsc/js/app.js` | 3.9 KB | Loads `data/chapters.json`, calls `goToQuiz()` → `quiz.html`. **There is no `bpsc/quiz.html`.** Orphan from the standalone app. |
| `bpsc/js/quiz.js` | 10.5 KB | Same. Never loaded by any HTML file. |

> **Fixed in this branch:** all three deleted. `scripts/sync_bpsc_runtime.py`
> updated so `js/` is no longer in `RUNTIME_DIRS` and won't resurrect them.

### P2 — `.gitignore` lies

It contains a blanket `*.pdf` rule. **92 PDFs are tracked.** `gitignore` never
un-tracks a file, so the rule has exactly one effect: it convinces the next
contributor that the 21 MB PDF they just added is being ignored.

> **Fixed in this branch:** rewritten with an explicit, honest policy and a
> comment explaining why the `*.pdf` rule was removed.

### P2 — Accessibility and mobile

- `bpsc/index.html` shipped `maximum-scale=1.0`, **disabling pinch-zoom**
  (WCAG 1.4.4 failure — and on a site students read dense question text on, a
  real usability problem). **Fixed.**
- 8 buttons in `upsc.html` have no accessible name.
- No `<html lang>` issue (all three set `lang="en"`) — good.
- No skip link on the BPSC app.

### P3 — No offline story

Everything was network-dependent: no service worker, no caching policy. On a
train, in a coaching-library basement, or anywhere Indian mobile data drops
out, the app simply didn't load — for the exact audience that most needs to
revise in those gaps.

> **Fixed in this branch:** `sw.js` (root-scoped, so one worker covers `/` and
> `/bpsc/`) plus a guarded `register-sw.js` on all four pages. Deliberately
> conservative: **HTML and JSON are network-first**, so an online visitor never
> sees stale questions — the cache is only a fallback when the network fails.
> CSS/JS are cache-first with background revalidation. Cross-origin traffic
> (Firebase, Google Fonts) and the large study PDFs are left alone.
>
> The deploy workflow now fails if `sw.js` precaches a path that doesn't exist,
> so a typo can't quietly disable half the offline shell.

### P3 — Missing the cheap polish

- **No favicon.** All three pages render a blank document icon in the tab and
  in "Add to Home Screen". The portal has a `theme-color` and a strong mark
  (`▰`, chakra motif) that was never turned into an icon. **Fixed** — added
  `favicon.svg` (an eight-spoke chakra in the portal's navy/gold) and
  `site.webmanifest`, so the site is installable as a standalone app.
- **No 404 page.** GitHub serves its own. **Fixed** — `404.html`, styled with
  `portal.css`, respecting night mode, with routes back to all three apps.

### P3 — Duplicated data

- `data.js` (6.4 MB) is a byte-for-byte repackaging of `data/*.json`
  (7.7 MB). Necessary for `file://`, but it must never be hand-edited — it is
  generated, and it is now loaded only when needed.
- `bpsc/books/tarkash_annual/Tarkash_Annual_PYQ_Plus_Book.html` (1.16 MB) is a
  self-contained study copy whose questions are **also** in
  `books/tarkash_annual/data/*.json`. Two copies, one of them hand-shaped. It
  will drift. Generate it from the JSON instead.

### P3 — Firebase config

`bpsc/index.html:3847` hardcodes the Firebase API key, and Firestore rules
require `request.auth.uid == userId` with a `< 900000` byte payload cap. That
is the correct pattern — a Firebase web key is a public identifier, not a
secret — but it is only safe *because* the rules are right. Add **App Check**
and restrict the key's HTTP referrer to `happyhaiabhi.github.io` so a copy of
this repo on someone else's origin cannot burn your quota.

### P3 — Filenames that fight the tooling

129 tracked paths contain spaces, apostrophes or Devanagari, e.g.
`new kgs data/Test_22_Full_Length_Paper_Solution_English_72nd_BPSC_Prelims_‘प्रहार’.pdf`.
Every script that walks these needs careful `-print0`/`quote()` handling. Rename
to `source/kgs/test-22-...pdf` style at the next convenient moment.

---

## 4. What I added (applied in this branch)

| # | Change | File | Payoff |
|---|---|---|---|
| 1 | **Real Pages workflow** with validate → stage → deploy | `docs/deploy-pages.workflow.yml` (staged — needs moving to `.github/workflows/`) | Publishes 80 MB instead of 361 MB; every push syntax-checked |
| 2 | **`data.js` loaded only on `file://`** | `upsc.html` | **−6.4 MB** and −6 s TTI per UPSC visit |
| 3 | **Favicon + web manifest** | `favicon.svg`, `site.webmanifest`, 3× `<link>` | Installable PWA; branded tabs |
| 4 | **404 page** | `404.html` | No more GitHub-branded dead ends |
| 5 | **Honest `.gitignore`** | `.gitignore` | Contributors stop trusting a rule that doesn't apply |
| 6 | **`requirements.txt`** | `requirements.txt` | One command to rebuild any deliverable PDF |
| 7 | **Removed `maximum-scale=1.0`** | `bpsc/index.html` | Pinch-zoom restored (WCAG 1.4.4) |
| 8 | **Missing-infographic guard** | workflow `validate` job | Silent 1,211-file gap becomes a build warning |
| 9 | **Sync script de-staled** | `scripts/sync_bpsc_runtime.py` | `js/` dropped from `RUNTIME_DIRS` with a comment saying why |
| 10 | **Dev-speak removed from the portal UI** | `index.html`, `portal.css` | “Connected” → real question counts; the internal integration note replaced with copy a student can use; redundant “Exam gateway” pill (and its 3 dead CSS rules) deleted |
| 11 | **`theme-color` + manifest on the BPSC app** | `bpsc/index.html` | Consistent browser chrome on mobile across all three pages |
| 12 | **Split the 342 KB monolith** | `bpsc/index.html` → `bpsc/css/*.css` + `bpsc/js/*.js` | 44 KB shell + 296 KB of cacheable, reviewable modules; PYQ Lab preserved |
| 13 | **A regression harness** | `tools/{bpsc-smoke,compare-smoke,split-bpsc,upsc-smoke}.js`, `package.json` | Any future refactor can be proven behaviour-neutral |
| 14 | **Offline support** | `sw.js`, `register-sw.js` | The portal, both apps and every question bank work with no signal; instant repeat loads |
| 15 | **Precache integrity gate** | workflow `build` job | A typo in `sw.js` fails the deploy instead of silently skipping a file |

## 5. What I subtracted (applied in this branch)

| Removed | Size | Reason |
|---|---|---|
| `bpsc/css/style.css` | 20 KB | Zero references |
| `bpsc/js/app.js` | 3.9 KB | Orphan; targets a `quiz.html` that doesn't exist |
| `bpsc/js/quiz.js` | 10.5 KB | Orphan; never loaded |
| **`data.js` from the HTTP path** | **6.4 MB / request** | Downloaded twice, needed once |
| **`*.pdf` ignore rule** | — | Un-tracks nothing, misleads everyone |
| `maximum-scale=1.0` | — | Accessibility regression |
| **“Exam gateway” pill** | 3 CSS rules | Duplicated the brand mark; hidden on mobile anyway |
| **“Connected” status pills** | 2 labels | Told the reader about your integration, not about the content |

**Net: −34 KB committed, −6.4 MB per page view, −279 MB published (once you
activate the staged workflow), and one 342 KB file turned into 21 files you can
actually review.**

---

## 6. What must happen next (needs you)

### 6.1 Create `bpsc-source` — five minutes, unblocks everything

```bash
git switch main && git pull
git switch -c bpsc-source
git push -u origin bpsc-source
git switch main
```

Then `scripts/sync_bpsc_runtime.py` stops being a self-copy. And prune the 40
dead session branches:

```bash
git ls-remote --heads origin 'refs/heads/arena/*' | \
  awk '{print $2}' | sed 's|refs/heads/||' | \
  xargs -n1 -I{} git push origin --delete {}
```

### 6.2 Flip Pages to GitHub Actions

Settings → Pages → Source → **GitHub Actions**. The workflow in this branch is
waiting for it. Until then the site keeps publishing 359 MB.

### 6.3 Run the infographic downloader once

```bash
pip install -r requirements.txt
python scripts/download_infographics.py     # resumable, ~4,400 WebP files
```

Budget ~150–400 MB of repo for these; consider `--dataset csat` first, since
CSAT is where the explanations matter most.

---

## 7. The architecture I'd move toward

Not a rewrite. A **reorganisation into three layers**, done one safe slice at a
time.

```
┌─ LAYER 1 · shared foundation ─────────────────────────────────────┐
│  tokens.css        one set of colour/space/type/radius variables   │
│  theme.js          (already exists — extend, don't replace)        │
│  ui.js             card, pill, chip, empty-state, sheet primitives │
│  data-loader.js    fetch + cache + progress, one implementation    │
└───────────────────────────────────────────────────────────────────┘
        ▲                                    ▲
┌───────┴──────────────┐        ┌────────────┴───────────────┐
│ LAYER 2 · UPSC app   │        │ LAYER 2 · BPSC app         │
│ upsc.html            │        │ bpsc/index.html  (shell)   │
│ js/{search,browse,   │        │ js/{books,quiz,review,     │
│    results}.js       │        │    bloom,history,export,   │
│ styles/upsc.css      │        │    sync}.js  ← ES modules  │
└──────────────────────┘        └────────────────────────────┘
                    ▲
┌───────────────────┴──────────────────────────────────────────┐
│ LAYER 3 · content pipeline (scripts/, unchanged in spirit)    │
│   PDFs → JSON → validated by CI → consumed by both apps       │
└──────────────────────────────────────────────────────────────┘
```

**Slice 1 — Split BPSC by concern ✅ DONE (see §3).** The 3 `<style>` blocks
are now `bpsc/css/{base,screens,portal-notes}.css` and the inline script is 15
ordered classic scripts in `bpsc/js/`, plus `date-banner.js`. Nothing was
rewritten, only moved, and `tools/compare-smoke.js` proves it: 15 behavioural
fields identical, 0 regressions.

*Next refinement (optional, ~1 hour):* the extracted files are still organised
by where the code sat, not by what it does. `02-chapters.js`, `03-dashboard.js`
and `07-question.js` are each ~25 KB and could be broken up further now that
they are separate files. Do it with `tools/compare-smoke.js` running.

**Slice 2 — One design system (2–3 days).** Today: 413 hardcoded hex values in
`styles.css`, 95 in `portal.css`, 82 in `bpsc-theme.css`, 295 inside
`bpsc/index.html`. Promote them to ~30 tokens in `tokens.css`. Then UPSC and
BPSC stop drifting, and the 24 KB `bpsc-theme.css` shim mostly deletes itself.

**Slice 3 — Payload budget (2 days).**
Split `data/*.json` by year and paper (`data/prelims/2020.json`), load a paper
on demand, and keep a generated `data/index.json` (~20 KB) for the landing
stats. First paint drops from ~14 MB to well under 500 KB. Delete `data.js`
entirely once a `serve.py` one-liner is documented for `file://` users.

**Slice 4 — CI as a gate (1 day).** Extend the workflow this branch adds:
fail on dead internal links, fail if any `books.json` subject path 404s, fail
if question counts regress by >1 %, and run `download_infographics.py
--check`. This is the change that makes the repo *stay* clean.

---

## 8. The bottom line

You built something substantial: 25,000+ questions, a real extraction pipeline,
spaced repetition, cloud sync, and a design that looks considered rather than
assembled. The problems are all *plumbing* — and plumbing is cheap to fix.

Three changes buy 90 % of the benefit:

1. **Move `docs/deploy-pages.workflow.yml` into `.github/workflows/` and switch Pages to GitHub Actions** → −281 MB published, every push validated.
2. **Create `bpsc-source`** → the sync script starts working, 40 dead branches get pruned.
3. **Keep the `data.js` lazy-load** → −6.4 MB per visit, already done.

Do those and the repo goes from D-plumbing to B-plumbing in an afternoon.
Slice 1 of §7 is already done — the 323 KB monolith is now 19 files, proven
behaviour-neutral — so the thing left is the design-system work (Slice 2) and
the payload work (Slice 3).
