# Ghatna Chakra BPSC Quiz

A chapter-wise BPSC Prelims practice application built from the supplied Ghatna Chakra interface and the finalized, corrected JSON bank.

## Question bank

- **12 subjects**
- **391 chapters**
- **4,441 questions with verified answers**
- **81 retained warning notes**
- **590 Bihar Special questions**

The subjects are Ancient History, Medieval History, Modern History, Polity & Governance, Geography & Environment, Economy & Development, Physics, Chemistry, Biology, General Mental Ability, Current Affairs, and Bihar Special.

## Recommended setup: GitHub Pages + Google sync

GitHub Pages hosts the static application. Firebase securely stores each signed-in user’s progress. GitHub is not used as a progress database, so no GitHub personal-access token or other powerful secret is stored in the browser.

### 1. Publish with GitHub Pages

1. Create a GitHub repository.
2. Put the **contents of this folder** at the repository root. In particular, `.github/workflows/deploy-pages.yml` must remain under `.github/workflows/`.
3. Push to the `main` branch.
4. In the repository, open **Settings → Pages** and choose **GitHub Actions** as the source if it is not already selected.
5. Open the **Actions** tab. The “Test and deploy to GitHub Pages” workflow tests the app and publishes it.

The resulting address normally looks like:

```text
https://YOUR_USERNAME.github.io/YOUR_REPOSITORY/
```

All application paths are relative, so project-site URLs work without editing the app.

### 2. Complete the one-time Firebase setup

The app is configured for the existing Firebase project:

```text
mcq-practise-ff181
```

In its [Firebase Console](https://console.firebase.google.com/):

1. Open **Build → Authentication → Sign-in method** and enable **Google**.
2. Open **Authentication → Settings → Authorized domains**.
3. Add `YOUR_USERNAME.github.io`. Add your custom domain too if you use one.
4. Open **Build → Firestore Database** and create the database if it does not already exist.
5. Open **Firestore Database → Rules**, paste the contents of `firestore.rules`, and click **Publish**.

Alternatively, an owner of the Firebase project can publish the included rules with Firebase CLI:

```bash
npm install -g firebase-tools
firebase login
firebase deploy --only firestore:rules
```

The Firebase web API key in `index.html` is a public project identifier, not a server secret. Access is protected by Firebase Authentication and the included per-user Firestore rules. Never commit a Firebase service-account key.

### 3. Use sync

1. Open the GitHub Pages site on a device.
2. Press **Sync** and choose **Sign in with Google**.
3. Sign in with the same Google account on every device.

The app automatically merges and synchronizes:

- mistakes;
- bookmarks;
- skipped questions;
- archive/mastery removals;
- quiz history and dashboard statistics.
- attempt history with full details: re-open any past attempt's result screen (score, correct/wrong/skip, time, and the complete solution review with explanations), or re-attempt **only the wrong** or **only the skipped** questions of that attempt.

A **Sync now** button is available for a manual check. Local progress continues to work while offline and merges after reconnection. On first sign-in, local and cloud records are merged before anything is written, so signing in on a new or empty device does not erase existing cloud progress. Archive entries act as deletion tombstones, preventing an older device from restoring removed/mastered items.

If the Cloud Sync dialog shows **Missing or insufficient permissions** with **Last successful sync: Not yet**, Google sign-in worked but Firestore blocked the progress documents. Publish the included `firestore.rules` (step 5 above) and tap **Sync now**. The app reads and writes each known key individually, so a live project whose rules omit a newer key such as `gc_attempts` still syncs the rest of your progress.

## Run locally

The app loads JSON with `fetch`, so use a local web server rather than a `file://` URL:

```bash
cd Ghatna_Chakra_BPSC_Quiz
node server.js
# or: python -m http.server 8000 --bind 0.0.0.0
```

Then open `http://localhost:8000/`. No build step is required. `server.js` sends `Cache-Control: no-store` so the preview never serves a stale build.

KGS test papers (Test 1–15) are tagged by topic. Open a test card and tap a topic chip to practice only that topic. After a mixed-topic attempt, the result screen (and History → Details) shows a Topic-wise Performance table. Mistakes and Skips have a **⬇ Export PDF** button that builds an A4 black-and-white print sheet (correct answer marked, your wrong answer flagged, full explanation) and opens the print dialog.

Google sign-in is intended for the authorized GitHub Pages/custom domain. If local sign-in is needed, ensure `localhost` remains in Firebase Authentication’s authorized domains.

## Multiple books

The app opens on a **book-selection landing page**. Each book uses the exact same quiz interface, engine, banks (mistakes/bookmarks/skips/archive), dashboard, and sync — but points at its own question data and keeps its progress completely separate.

The list of books lives in [`books/books.json`](books/books.json):

```json
{
  "id": "bpsc_ghatna_chakra",
  "title": "BPSC Ghatna Chakra",
  "subtitle": "Bihar Public Service Commission · Prelims PYQ",
  "tag": "BPSC Pre PYQ",
  "emoji": "📜",
  "color": "#c9a84c",
  "dataDir": ".",
  "chaptersFile": "data/chapters.json",
  "description": "..."
}
```

- `chaptersFile` is the repository-relative path to the book's chapter index.
- Each subject's `file` inside that index is also repository-relative.
- If `file` is a bare filename (no `/`), it is resolved relative to `dataDir`.
- The first book in the list is the **legacy book**: it keeps the original `gc_*` local/Firestore keys so existing users never lose progress. Every other book's progress is stored under per-book namespaced keys (e.g. `gc_history__book_<id>`), so books never mix.

### Add a new book

1. Create a folder for its data, e.g. `books/my_book/data/`.
2. Add a `chapters.json` in the same format as [`data/chapters.json`](data/chapters.json) (subjects with `key`, `label`, `emoji`, `file`, and `chapters`).
3. Add one JSON file per subject in the same format as the existing subject files.
4. Append an entry to `books/books.json`.

A working starter example lives in [`books/ssc_sample/`](books/ssc_sample/).

## Main features

- Subject and chapter selection
- Configurable question count
- Optional timer
- Question and option shuffling
- Question palette and keyboard navigation
- Scoring, results, filtered review, and retry-wrong flow
- Mistakes, bookmarks, skips, and archive banks
- Five-correct-answer mastery progression
- Dashboard/session history
- Dark/light themes
- Automatic Google-account cross-device sync
- Responsive desktop and mobile layouts

## Match-the-following questions

Confidently parsed matching questions use aligned List I/List II columns and a compact answer-code matrix. The parser supports A–E versus numeric/Roman labels, markers without trailing spaces, and Roman I–IV versus A–D lists. The same layout appears in quiz and result-review views. If a source object cannot be parsed confidently, the app safely uses the standard MCQ presentation without modifying the JSON.

## Development and validation

Install the test dependency and run the automated application test:

```bash
npm ci
npm test
```

The GitHub Pages workflow runs this test and checks the inline JavaScript syntax before every deployment.

## Important files

- `index.html` — active self-contained interface, styles, quiz logic, and sync client
- `data/chapters.json` — aggregate subject/chapter index
- `data/*.json` — 12 finalized subject files
- `.github/workflows/deploy-pages.yml` — GitHub Pages test/deployment workflow
- `firestore.rules` — per-user cloud security rules
- `firebase.json`, `.firebaserc` — Firebase Rules deployment configuration
- `tests/test_quiz_webapp.js` — automated application and sync-merge test
- `QA_REPORT.md` — integrity and behavior test summary
- `css/style.css`, `js/app.js`, `js/quiz.js` — preserved supplied legacy references; the active application uses inline CSS and JavaScript in `index.html`

## Data integrity

The files in `data/` are byte-identical copies of the authoritative finalized JSON bank. Questions, options, answers, explanations, exam/year metadata, and warning notes were not rewritten by the webpage generator.
