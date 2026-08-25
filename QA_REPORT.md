# Final QA Report

**Project:** Ghatna Chakra BPSC Quiz  
**Validation date:** 18 August 2026  
**Status:** **PASS**

## Bank validation

| Check | Result |
|---|---:|
| Subjects | 12 |
| Chapters | 391 |
| Questions | 4,441 |
| Verified/nonblank answers | 4,441 |
| Retained warning notes | 81 |
| Bihar Special questions | 590 |
| Subject JSON files | 12 |
| Aggregate index | `chapters.json` |

All 13 files in the project’s `data/` directory were compared with the authoritative finalized bank and are byte-identical.

## Application validation

- Generated inline JavaScript passed `node --check`.
- All 12 configured subject files fetched and loaded successfully in the automated DOM test.
- Dashboard aggregates displayed 12 subjects, 391 chapters, and 4,441 questions.
- Chapter and question counts matched `chapters.json` for every subject.
- Standard question text, options, explanations, and notes are HTML-escaped before rendering.
- Quiz selection, palette navigation, previous/next navigation, scoring, results, and review passed.
- Mistakes, bookmarks, skips, archive, session dashboard, theme, and timer flows passed.
- Match rendering passed in both the quiz and post-result review.

## Cross-device sync validation

The Firebase layer uses Google Authentication and the same public Firebase project already supplied with the app.

Validated behaviors:

- local and cloud state are merged **before** the first cloud write;
- signing in on an empty/new device cannot replace populated cloud state with empty objects;
- local-only and cloud-only bookmarks converge into one bank;
- quiz histories merge by session date and deduplicate;
- mistake/skip attempt and mastery counters retain the higher known value during a conflict;
- archive entries act as tombstones and remove stale active-bank copies;
- manual **Sync now** control is available after sign-in;
- local save functions continue working offline and queue cloud updates only when authenticated;
- a per-payload size guard stays below Firestore’s document limit;
- sign-out preserves all local progress;
- owner-only Firestore rules are included in `firestore.rules`;
- cloud reads use per-document `get()` (not a collection list) so extra id constraints on live rules cannot fail the whole merge;
- writes are per-key, so a denied sibling such as `gc_attempts` does not block mistakes/bookmarks/history;
- permission-denied errors tell the user to publish `firestore.rules`.

Live Google authentication still requires the deployment domain to be listed in Firebase Authentication’s **Authorized domains**, as documented in `README.md`.

## GitHub validation/deployment

`.github/workflows/deploy-pages.yml`:

1. installs the locked test dependency;
2. runs the automated DOM/application test;
3. validates inline JavaScript with `node --check`;
4. creates a clean static Pages artifact;
5. deploys only after tests pass.

The workflow uses GitHub’s built-in Pages permissions and requires no repository secret.

## Match-question parser

| Check | Result |
|---|---:|
| Broad match/list candidates | 50 |
| Specialized book-style rendering | 49 |
| Safe standard fallback | 1 |

Confirmed specialized cases include the Stone Age reference question, A–D versus 1–4 rows, markers without whitespace, and Roman I–IV versus A–D labels. The sole fallback is the structurally malformed Environment & Ecology source object whose list rows are embedded inside option values; it remains unchanged and uses the standard renderer.

## Automated flow coverage

- Dashboard and all subject/chapter loading
- Standard and specialized question rendering
- Match variants and safe fallback
- Answer selection and navigation
- Scoring and result review
- Bookmarks, mistakes, skips, and archive
- Theme and timer
- HTML escaping
- Cross-device merge
- Archive tombstones
- Manual sync interface

## Regeneration

Generated application assets can be recreated without deleting project documentation, GitHub configuration, Firebase rules, or tests:

```bash
python /home/user/build_quiz_webapp.py
```
