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

A **Sync now** button is available for a manual check. Local progress continues to work while offline and merges after reconnection. On first sign-in, local and cloud records are merged before anything is written, so signing in on a new or empty device does not erase existing cloud progress. Archive entries act as deletion tombstones, preventing an older device from restoring removed/mastered items.

## Run locally

The app loads JSON with `fetch`, so use a local web server rather than a `file://` URL:

```bash
cd Ghatna_Chakra_BPSC_Quiz
python -m http.server 8000 --bind 0.0.0.0
```

Then open `http://localhost:8000/`. No build step is required.

Google sign-in is intended for the authorized GitHub Pages/custom domain. If local sign-in is needed, ensure `localhost` remains in Firebase Authentication’s authorized domains.

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
