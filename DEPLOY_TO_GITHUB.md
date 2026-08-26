# Deploying the Combined Portal to the Existing GitHub Pages Site

Target repository:

```text
https://github.com/happyhaiabhi/GhatnaChakra-BPSC
```

Target website (unchanged):

```text
https://happyhaiabhi.github.io/GhatnaChakra-BPSC/
```

`main` now contains the combined portal at the repository root. Its routes are:

```text
/GhatnaChakra-BPSC/                 Exam portal
/GhatnaChakra-BPSC/upsc.html        UPSC application
/GhatnaChakra-BPSC/bpsc/            BPSC application
```

All project URLs are relative, so the GitHub Pages repository prefix works
without editing paths.

## Important: preserve the original BPSC source

The previous `main` was the standalone BPSC project. Before it is replaced by
the combined portal, the original source (tests, source documents and
extraction tools) must be preserved in a permanent branch:

```bash
git clone https://github.com/happyhaiabhi/GhatnaChakra-BPSC.git
cd GhatnaChakra-BPSC

# create the backup branch from the old BPSC main and publish it first
git switch main
git pull
git switch -c bpsc-source
git push -u origin bpsc-source
git switch main
```

After this:

- `main` contains the combined portal.
- `bpsc-source` retains the full editable BPSC project, tests, extraction
  scripts and source material.
- `scripts/sync_bpsc_runtime.py` reads BPSC updates from `bpsc-source`.

Do not skip this branch step. Once `main` becomes the portal, it is no longer
a valid standalone BPSC source branch, and `bpsc-source` must never be
deleted or overwritten by portal deployments.

## GitHub Pages configuration

The repository includes:

```text
.github/workflows/deploy-pages.yml
.nojekyll
```

The workflow:

- validates JavaScript (`node --check`), Python scripts (`py_compile`) and the
  100 MB single-file limit;
- uploads the repository root as the Pages artifact;
- deploys with `actions/deploy-pages@v4`.

In the repository:

1. Open **Settings → Pages**.
2. Set **Source** to **GitHub Actions**.
3. Open the **Actions** tab.
4. Wait for the **Deploy to GitHub Pages** run to finish green.
5. Open `https://happyhaiabhi.github.io/GhatnaChakra-BPSC/`.
6. Perform a hard refresh if the old BPSC page is cached.

The same workflow runs automatically after every push to `main`. No file
exceeds GitHub's 100 MB single-file limit (the largest bundled file is
approximately 5.6 MB).

## Firebase / Google sign-in

The hostname remains `happyhaiabhi.github.io`, so existing Firebase
authorization for that hostname should remain valid. Firebase authorizes
hostnames, not repository URL paths, so moving BPSC from
`/GhatnaChakra-BPSC/` to `/GhatnaChakra-BPSC/bpsc/` normally does not require
another authorized-domain entry.

After deployment, explicitly test:

- Google sign-in;
- cloud sync and **Sync now**;
- sign-out;
- progress restoration on a second device.

The Firebase browser configuration embedded in the BPSC page is public client
configuration; keep service-account credentials out of the repository and
keep Firestore protected by Authentication and the published rules
(`firestore.rules` documents the current rule set).

## Future BPSC updates

Make standalone BPSC source changes on `bpsc-source`, not on the generated
`main/bpsc/` runtime:

```bash
git switch bpsc-source
# edit/test BPSC source
git add -A
git commit -m "Update BPSC application"
git push origin bpsc-source
```

Then refresh the combined portal runtime:

```bash
git switch main
git pull
python scripts/sync_bpsc_runtime.py
git add bpsc
git commit -m "Sync latest BPSC runtime"
git push origin main
```

The sync script imports only browser-runtime files, injects portal navigation
and shared theme hooks, validates every data path, and excludes Git history,
PDFs, reports, tests and extraction artifacts.

## Recommended final verification

After deployment, verify:

1. Portal opens at the repository URL; both cards open correctly.
2. Night Mode defaults on and persists in both systems; light mode stays readable.
3. UPSC: P/resting/M selector, Prelims GS, CSAT and Mains flows, search
   drawer, filters, CSAT solutions and infographics.
4. BPSC: all book cards, core book totals (12 subjects / 391 chapters /
   4,441 questions), subject/chapter quiz, results, review banks, search,
   export, Google sign-in and cloud sync.
5. Mobile layout is usable on both systems.
