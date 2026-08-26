# Replace the Existing BPSC GitHub Pages Site with This Combined Portal

Target repository:

```text
https://github.com/happyhaiabhi/GhatnaChakra-BPSC
```

Target website (unchanged):

```text
https://happyhaiabhi.github.io/GhatnaChakra-BPSC/
```

After deployment, that URL will open the new UPSC/BPSC portal. Its routes will be:

```text
/GhatnaChakra-BPSC/                 Exam portal
/GhatnaChakra-BPSC/upsc.html        UPSC application
/GhatnaChakra-BPSC/bpsc/            BPSC application
```

All project URLs are relative, so the GitHub Pages repository prefix works without editing paths.

## Important: preserve the original BPSC source

The current repository is also the upstream source used by `scripts/sync_bpsc_runtime.py`. Before replacing `main`, preserve the current BPSC project in a permanent source branch:

```bash
git clone https://github.com/happyhaiabhi/GhatnaChakra-BPSC.git combined-exam-portal
cd combined-exam-portal

git switch -c bpsc-source
git push -u origin bpsc-source

git switch main
```

After this:

- `main` will contain the combined portal.
- `bpsc-source` will retain the full editable BPSC project, tests, extraction scripts and source material.
- `scripts/sync_bpsc_runtime.py` will automatically read from `bpsc-source`.

Do not skip this branch step. Once `main` becomes the portal, it is no longer a valid standalone BPSC source branch.

## Replace `main` with the combined project

Copy the **contents** of the prepared `upsc-question-bank` directory into the cloned repository root. Preserve only the repository's hidden `.git` directory from the clone.

On macOS/Linux, from inside the clone:

```bash
rsync -a --delete --exclude='.git/' /FULL/PATH/TO/upsc-question-bank/ ./
```

On Windows with GitHub Desktop:

1. Clone `happyhaiabhi/GhatnaChakra-BPSC`.
2. Create and publish the `bpsc-source` branch.
3. Switch back to `main`.
4. Delete the old working-tree files, but **do not delete `.git`**.
5. Copy everything from `upsc-question-bank` into the cloned folder.
6. GitHub Desktop will show the replacement changes.

Commit and push:

```bash
git status
git add -A
git commit -m "Deploy unified UPSC and BPSC exam portal"
git push origin main
```

No project file is near GitHub's 100 MB single-file limit; the largest bundled file is approximately 5.6 MB.

## GitHub Pages configuration

The prepared project includes:

```text
.github/workflows/deploy-pages.yml
.nojekyll
```

In the repository:

1. Open **Settings → Pages**.
2. Set **Source** to **GitHub Actions**.
3. Open the **Actions** tab.
4. Wait for **Deploy combined UPSC + BPSC portal** to finish.
5. Open `https://happyhaiabhi.github.io/GhatnaChakra-BPSC/`.
6. Perform a hard refresh if the old BPSC page is cached.

The same workflow runs automatically after every push to `main`.

## Firebase / Google sign-in

The hostname remains `happyhaiabhi.github.io`, so an existing Firebase authorization for that hostname should remain valid. Still test:

- Google sign-in;
- Sync now;
- sign-out;
- progress restoration on a second device.

Firebase authorizes hostnames, not repository URL paths, so moving BPSC from `/GhatnaChakra-BPSC/` to `/GhatnaChakra-BPSC/bpsc/` normally does not require another authorized-domain entry.

## Future BPSC updates

Make standalone BPSC source changes on `bpsc-source`, not on the generated `main/bpsc/` runtime:

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

The sync script imports only browser-runtime files, injects portal navigation and shared theme hooks, validates every data path, and excludes Git history, PDFs, reports, tests and extraction artifacts.

## Recommended final verification

After deployment, verify:

1. Portal opens at the repository URL.
2. UPSC card opens `upsc.html`.
3. BPSC card opens `bpsc/`.
4. Night Mode persists in both systems.
5. UPSC search, filters, CSAT solutions and infographics work.
6. BPSC books, subjects, quiz, review, PDF export and cloud sync work.
7. Both systems return to the exam portal.
