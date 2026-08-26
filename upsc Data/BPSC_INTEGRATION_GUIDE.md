# BPSC Integration — Implemented

The Ghatna Chakra BPSC website is now integrated locally into the same exam portal.

## Final routing

```text
upsc-question-bank/
├── index.html              # Exam portal
├── portal.css
├── upsc.html               # UPSC application
├── app.js / styles.css
├── theme.js                # Shared portal/UPSC/BPSC day-night preference
├── bpsc-theme.css          # UPSC-aligned BPSC day/night design
├── data/ / infographics/
└── bpsc/
    ├── index.html          # Complete BPSC browser application
    ├── books/              # All registered BPSC books
    ├── data/               # Ghatna Chakra question data
    ├── css/
    └── js/
```

Portal routes:

- **UPSC card → `upsc.html`**
- **BPSC card → `bpsc/index.html`**
- The UPSC logo returns to `index.html`.
- A fixed **← Exam Portal** button was injected into BPSC and returns to `../index.html`.

## What was copied

The public source repository is:

`https://github.com/happyhaiabhi/GhatnaChakra-BPSC`

Only files required by the running browser application were imported:

- `index.html`
- `books/`
- `data/`
- `css/`
- `js/`

The imported runtime contains 10 registered books and 50 referenced subject files. Every manifest, chapters index and subject-file path is validated by the sync script.

Large non-runtime material was intentionally excluded:

- Git history;
- source PDFs under `New folder/`;
- tests and development dependencies;
- extraction scripts;
- reports;
- old deliverables and deliverable history.

This keeps the merged BPSC application around 19 MiB instead of copying roughly 150 MiB of repository and Git material. It does not remove any browser-facing quiz feature.

## Refreshing BPSC after upstream updates

Run from the portal project directory:

```bash
python scripts/sync_bpsc_runtime.py
```

The script:

1. shallow-clones the latest `main` branch into a temporary directory;
2. copies only browser-runtime files;
3. injects the **Exam Portal** return links plus shared `../theme.js` and `../bpsc-theme.css` hooks;
4. validates all book, chapter and subject data paths;
5. replaces the old local BPSC runtime only after validation succeeds.

The design override remains in the portal root, so upstream BPSC updates can be refreshed without losing the UPSC-aligned minimalist theme.

Do not manually copy `.git`, PDFs or `node_modules` into `bpsc/`.

## Running locally

Use an HTTP server because BPSC loads JSON using `fetch()`:

```bash
cd upsc-question-bank
python -m http.server 8000
```

Open:

```text
http://localhost:8000/
```

The root opens the exam portal. Select BPSC to enter the integrated application.

## Deployment and Firebase

The BPSC application keeps its existing Firebase project and Google sign-in implementation. When deploying the combined portal on a new hostname:

1. Open Firebase Console for the BPSC Firebase project.
2. Go to **Authentication → Settings → Authorized domains**.
3. Add the new portal hostname.
4. Confirm the existing Firestore rules are published.
5. Test Google sign-in, cloud sync and sign-out on the deployed domain.

Without the authorized-domain step, the quiz still works locally, but Google sign-in/cloud sync can fail on the new host.

## Why this method was chosen

A local runtime merge provides:

- one landing portal;
- same-domain navigation;
- no iframe restrictions;
- all BPSC books and quiz features;
- a repeatable update workflow;
- no duplicate repository history or source-document bulk.

It is more seamless than an external link and more reliable than embedding the existing site in an iframe.
