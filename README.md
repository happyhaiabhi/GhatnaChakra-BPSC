# Ghatna Chakra BPSC PYQ Quiz 📚

A clean, chapter-wise MCQ quiz website built for BPSC Prelims preparation using the **Ghatna Chakra Book Series (BPSC General Studies 2026)** question bank — same engine as the Priyadarshani quiz, just re-pointed at Ghatna Chakra content.

## 🗂 Project Structure

```
ghatnachakra/
├── index.html                        ← Self-contained app (home + quiz + dashboard, all inline)
├── css/
│   └── style.css                     ← Legacy stylesheet (kept for reference; index.html has its own inline styles)
├── js/
│   ├── app.js                        ← Legacy home-page script (kept for reference; unused by index.html)
│   └── quiz.js                       ← Legacy quiz-engine script (kept for reference; unused by index.html)
└── data/
    ├── chapters.json                 ← Master index (auto-generated; do not edit manually)
    ├── history.json                  ← History MCQs
    ├── polity_governance.json        ← Polity & Governance MCQs
    ├── geography_environment.json    ← Geography & Environment MCQs
    ├── economy_development.json      ← Economy & Development MCQs
    ├── general_science.json          ← General Science MCQs
    ├── general_mental_ability.json   ← General Mental Ability MCQs
    ├── current_affairs.json          ← Current Affairs MCQs
    ├── society_demography.json       ← Society & Demography MCQs
    ├── art_culture_literature.json   ← Art, Culture & Literature MCQs
    ├── infrastructure_industry.json  ← Infrastructure & Industry MCQs
    └── miscellaneous.json            ← Miscellaneous MCQs
```

> **Note:** All actual app logic (subject grid, chapter picker, quiz engine, dashboard, mistakes/bookmarks/skips/archive banks, Firebase cloud sync) lives inline inside `index.html`, exactly like the original Priyadarshani app. The `css/` and `js/` folders are kept only for structural parity with the original project — `index.html` doesn't load them.

## ✏️ How to Update Questions

Each subject has its own JSON file in `data/`. The format is:

```json
{
  "subject": "History",
  "chapters": [
    {
      "chapter_name": "Mauryan Empire",
      "questions": [
        {
          "q": "Who was the founder of the Mauryan Empire?",
          "options": {
            "A": "Bindusara",
            "B": "Chandragupta Maurya",
            "C": "Ashoka",
            "D": "Chanakya",
            "E": "None of the above/More than one of the above"
          },
          "answer": "B",
          "explanation": "Chandragupta Maurya founded the Mauryan Empire around 321 BCE...",
          "exam": "BPSC",
          "year": "64th B.P.S.C. (Pre), 2018"
        }
      ]
    }
  ]
}
```

**To add/edit questions:** Open the relevant `data/<subject>.json` and edit the questions array. No other file needs to change.

**To add a new chapter/topic:** Add a new object to the `chapters` array inside the subject JSON.

**To add a new subject:** Create a new JSON file in `data/` following the format above, then add both an entry to `data/chapters.json` **and** to the `SUBJECTS_CONFIG` array near the top of the `<script>` block in `index.html`.

## 🚀 Hosting on GitHub Pages

### Step 1 — Create a GitHub Repository

1. Go to [github.com](https://github.com) → **New Repository**
2. Name it `ghatnachakra-quiz` (or anything you like)
3. Set it to **Public** (required for free GitHub Pages)
4. Click **Create Repository**

### Step 2 — Upload Files

**Option A: GitHub Web UI (easiest)**
1. Open your new repository
2. Click **Add file → Upload files**
3. Drag and drop the entire folder contents
4. Make sure the folder structure is preserved:
   - `index.html` at the root
   - `css/style.css`
   - `js/app.js`, `js/quiz.js`
   - `data/*.json`
5. Click **Commit changes**

**Option B: Git CLI**
```bash
cd ghatnachakra
git init
git add .
git commit -m "Initial quiz upload"
git remote add origin https://github.com/YOUR_USERNAME/ghatnachakra-quiz.git
git push -u origin main
```

### Step 3 — Enable GitHub Pages

1. In your repository, go to **Settings → Pages**
2. Under **Source**, select **Deploy from a branch**
3. Choose **main** branch, **/ (root)** folder
4. Click **Save**
5. Wait 1–2 minutes, then visit:
   ```
   https://YOUR_USERNAME.github.io/ghatnachakra-quiz/
   ```

## ☁️ Cloud Sync

The app has the same optional Firebase-based login + sync feature as Priyadarshani (mistakes, bookmarks, skips, history, archive), stored under separate local-storage keys (`gc_*`) and a separate Firestore app instance (`ghatnachakra`), so using this app won't overwrite or clash with your Priyadarshani data — you can safely run both side by side, even signed into the same account.

## 📊 Question Stats

| Subject | Chapters | Questions |
|---------|----------|-----------|
| History | 92 | 1,142 |
| General Science | 59 | 728 |
| Geography & Environment | 127 | 696 |
| Current Affairs | 15 | 550 |
| Polity & Governance | 37 | 420 |
| Economy & Development | 22 | 419 |
| General Mental Ability | 29 | 396 |
| Society & Demography | 1 | 49 |
| Infrastructure & Industry | 2 | 31 |
| Art, Culture & Literature | 2 | 29 |
| Miscellaneous | 1 | 23 |
| **Total** | **387** | **4,483** |

**A note on data quality:** 123 questions (≈2.7% of the bank) were flagged `(*)` in the source book, meaning the original answer key considers the question disputed/ambiguous. These were imported with the question text, options, and explanation intact, but no `answer` key is set for them — the app will default to marking option **A** as correct for these until you review and fix them by hand in the relevant `data/<subject>.json` file. A handful of "select two correct options" style questions were also collapsed to their first listed correct letter, for the same reason.

---

*Built for BPSC Prelims preparation. Questions sourced from the Ghatna Chakra Book Series (BPSC General Studies 2026 edition).*
