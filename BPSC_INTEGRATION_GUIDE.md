# BPSC Integration — Implemented

The Ghatna Chakra BPSC website is integrated locally into the same exam
portal. The combined project **is** the repository — the portal files live at
the repository root and the BPSC runtime lives under `bpsc/`.

## Final routing

```text
repository root (main)
├── index.html              # Exam portal (only visible Night Mode control)
├── portal.css
├── theme.js                # Shared portal/UPSC/BPSC day-night preference
├── upsc.html               # UPSC application
├── app.js / styles.css
├── data.js                 # UPSC file:// fallback bundle
├── data/                   # UPSC JSON datasets (prelims, csat, mains)
├── infographics/           # Locally bundled CSAT + Prelims solution infographics
├── bpsc-theme.css          # UPSC-aligned BPSC day/night design
├── scripts/                # build_data_bundle.py, download_infographics.py, add_prelims_infographics.py, sync_bpsc_runtime.py
└── bpsc/
    ├── index.html          # Complete BPSC browser application
    ├── books/              # All registered BPSC books
    ├── data/               # Ghatna Chakra core question data
    ├── css/
    └── js/
```

Portal routes:

- **UPSC card → `upsc.html`**
- **BPSC card → `bpsc/index.html`**
- The UPSC brand/logo returns to `index.html`.
- **← Portal** pills (class `nav-portal-home`, styled by the shared
  `bpsc-theme.css`) were injected into the BPSC top navbar and the quiz
  topbar; both return to `../index.html`.

## What was copied

The public source repository is:

`https://github.com/happyhaiabhi/GhatnaChakra-BPSC`

Only files required by the running browser application were imported into
`bpsc/`:

- `index.html`
- `books/`
- `data/`
- `css/`
- `js/`

The imported runtime contains 10 registered books and 50 referenced subject
files. Every manifest, chapters index and subject-file path is validated by
the sync script (18,395 question objects in total; the core Ghatna Chakra
book keeps 4,441 verified questions across 12 subjects and 391 chapters).

The root `data/` folder is split deliberately: it holds the **UPSC** datasets
(`prelims.json`, `csat.json`, `mains.json`) while the BPSC subject data lives
under `bpsc/data/` and `bpsc/books/*/data/`.

Large non-runtime material is intentionally excluded from `bpsc/`:

- Git history;
- source PDFs under `New folder/`;
- tests and development dependencies;
- extraction scripts;
- reports;
- old deliverables and deliverable history.

All of that remains preserved in the **`bpsc-source`** branch, which is the
permanent home of the standalone BPSC source.

## Refreshing BPSC after upstream updates

Run from the repository root:

```bash
python scripts/sync_bpsc_runtime.py
```

The script:

1. resolves the upstream branch — it prefers the permanent **`bpsc-source`**
   branch and falls back to `main` only while the backup branch has not been
   created yet (it warns when it does);
2. shallow-clones that branch into a temporary directory;
3. copies only browser-runtime files;
4. injects the **Portal** return pills plus the shared `../theme.js` and
   `../bpsc-theme.css` hooks (idempotently, and it strips any Cloudflare
   scrape residue from the source HTML);
5. validates all book, chapter and subject data paths (full JSON parsing and
   question counts);
6. replaces the local BPSC runtime only after validation succeeds.

The design override remains in the repository root, so upstream BPSC updates
can be refreshed without losing the UPSC-aligned minimalist theme.

Do not manually copy `.git`, PDFs or `node_modules` into `bpsc/`.

## Night Mode

- The portal hosts the single visible Night Mode button.
- `theme.js` stores the preference as `exam_portal_theme` (night mode is the
  low-glare default) and mirrors it to BPSC's legacy `gc_theme` key, which the
  BPSC application reads on startup.
- `theme.js` also listens for `gc_theme` changes, so toggling from BPSC's own
  buttons stays consistent across open tabs.
- Both day and night palettes are designed to readable accessibility levels in
  `portal.css`, `styles.css` and `bpsc-theme.css`.

## Running locally

Use an HTTP server because BPSC loads JSON using `fetch()`:

```bash
python -m http.server 8000
```

Open:

```text
http://localhost:8000/
```

The root opens the exam portal. Select BPSC to enter the integrated
application.

## Deployment and Firebase

The BPSC application keeps its existing Firebase project and Google sign-in
implementation. The hostname remains `happyhaiabhi.github.io`, so existing
Firebase authorization should remain valid even though BPSC moves to
`/GhatnaChakra-BPSC/bpsc/` — Firebase authorizes hostnames, not paths.

Still, after deployment test on the live domain:

1. Google sign-in;
2. cloud sync and **Sync now**;
3. sign-out;
4. progress recovery on another device.

If sign-in ever fails, open **Authentication → Settings → Authorized domains**
in the Firebase Console and add the portal hostname.

## Why this method was chosen

A local runtime merge provides:

- one landing portal;
- same-domain navigation;
- no iframe restrictions;
- all BPSC books and quiz features;
- a repeatable update workflow;
- no duplicate repository history or source-document bulk on `main`.

It is more seamless than an external link and more reliable than embedding the
existing site in an iframe.
