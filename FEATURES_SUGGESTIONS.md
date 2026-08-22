# Feature suggestions for Ghatna Chakra BPSC

The visual refresh is already applied (soft “Botanical Bloom” light theme, a calm “Night Garden” dark theme that also follows your system preference, floral wallpaper, rounded petal-inspired cards, gentler colors and the new `Nunito` / `Cormorant Garamond` type pairing).

## ✅ Already implemented in this branch
- **Bloom Review** — spaced repetition for mistakes and skips (1 → 3 → 7 → 21 days), with a 🌷 Bloom button/badge and practice mode.
- **Dashboard insights** — soft accuracy ring + last-7-days weekly bar chart.
- **Pomodoro / focus timer** — 25 min focus, 15 min sprint, 5 min break from the navbar.
- **Search & filter** in Mistakes, Bookmarks, Skips and Archive.
- **Personal notes on bookmarks** with Search covering note text.
- **Night mode** — the “Night Garden” dark theme plus automatic first-visit detection of `prefers-color-scheme: dark`.

Below are the features I would prioritise next, roughly ordered by value-for-effort.

---

## 🌸 Quick wins (low effort, high visible value)

| # | Idea | Why it helps |
|---|------|--------------|
| 1 | **Daily Bloom greeting / date** | A soft “today” line on the landing page makes the app feel alive without adding friction. *(Already added as a small touch.)* |
| 2 | **Question of the Day** | Show one random verified question on the home screen with a “Practise it” shortcut — a 30-second daily habit. |
| 3 | **Progress ring on dashboard** | Replace numeric accuracy with a soft SVG ring + petal that fills up. Minimal change, much prettier. |
| 4 | **Streak counter** | “3-day streak 🌱” in the dashboard header. Motivates consistency. |
| 5 | **PWA / offline install** | Add a manifest + service worker so it can be installed and used offline. The app already stores progress locally, so this is mostly packaging. |

---

## 📚 Study-quality upgrades (medium effort)

| # | Idea | Why it helps |
|---|------|--------------|
| 6 | **Spaced repetition (“Bloom review”)** | Turn mastered/bank questions into a lightweight SRS queue — a question comes back at 1 / 3 / 7 / 21 days. Big retention win for exam prep. |
| 7 | **Focus / Pomodoro timer** | Add a soft 25/5 timer inside the quiz top bar that leans on the existing `totalSecs` timer logic. |
| 8 | **Daily planner** | “Today’s plan: 1 chapter + 20 questions + 5 mistakes.” Could be a card on the dashboard. |
| 9 | **Search & filter questions** | Search by keyword, exam year, or chapter from the subject list. The data is already structured, so this fits well. |
| 10 | **Custom tags / notes on bookmarks** | Let a user write a one-line note or a “why I got this wrong” memo on a bookmark. |

---

## 📊 Analytics & insights (medium effort)

| # | Idea | Why it helps |
|---|------|--------------|
| 11 | **Weekly / monthly chart** | Small bar chart (correct, wrong, skipped) per subject or week. Charts communicate progress better than raw numbers. |
| 12 | **Subject-wise heat map** | Soft heat grid of accuracy per chapter; users can instantly spot weak chapters. |
| 13 | **Weak-area recommendations** | “You’re weakest in Polity — try these 20 questions.” Derived from history data. |
| 14 | **Practice goal setting** | Let users set a weekly question target and show a petal/garden that grows as they hit it. |

---

## 🧪 Exam simulation & engagement (medium–high effort)

| # | Idea | Why it helps |
|---|------|--------------|
| 15 | **Full mock / exam mode** | Fixed question count, negative marking (optional), strict timer, and a percentile-style summary. |
| 16 | **Review flashcards from mistakes** | One-card-per-wrong-answer mode, flipping to the correct answer. |
| 17 | **Soft gamification** | Blooming flowers per mastered subject; gentle badges for streaks, 100-question milestones, etc. |
| 18 | **Leaderboard / study groups (optional)** | Fires a privacy discussion, so do this only if the user base wants it. |

---

## ♿ Accessibility & polish (low–medium effort)

| # | Idea | Why it helps |
|---|------|--------------|
| 19 | **Keyboard shortcuts help** | Add a small “?” popover listing Space / Enter / B / P shortcuts instead of the tiny hint text. |
| 20 | **Theme + size preferences** | “Comfort reading” toggle for slightly larger question text and line spacing. |
| 21 | **Export / import progress** | JSON export button so users can back up their banks and history outside Firebase. |
| 22 | **Reduced-motion mode** | Respect `prefers-reduced-motion` for the pulse, slide, and hover animations. |

---

## Suggested order to build

1. **PWA + offline install** — high value, low complexity.
2. **Daily Question of the Day + streak counter** — quick habit builders.
3. **Progress ring & weekly chart** — visual polish that reinforces the floral theme.
4. **Spaced-repetition “Bloom review”** — the single biggest study-quality feature.
5. **Focus timer + keyboard help** — small, focused UX wins.
6. **Export / import progress** — gives users control over their data.

If you want, I can implement any of these next — tell me which ones you’d like and I’ll build them on this branch.
