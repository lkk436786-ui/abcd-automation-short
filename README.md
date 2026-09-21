# Independent Kids Shorts Engine

This repository is intentionally separate from the long-video engine. It creates five original vertical Shorts per daily run from the copied PNGs, voices, backgrounds, and music library.

## Required GitHub secret

Add only this required secret in `Settings → Secrets and variables → Actions`:

`YOUTUBE_TOKEN_JSON` — the complete authorized-user JSON for the YouTube channel that should receive the Shorts. A YouTube access token expiring is normal; the refresh token is what lets the workflow obtain a fresh access token. It is not guaranteed to live forever if revoked or invalidated, so keep the OAuth client and reauthorize only if Google invalidates it.

No Pixabay or Pexels key is required by this Shorts engine because it uses the local asset library. Never commit a token, OAuth client JSON, or `.env` file.

## Connect and push from Windows PowerShell

Use a fine-grained PAT for the `lkk436786-ui` account when Git prompts for the password. Give that PAT access to this repository with `Contents: Read and write`; do not paste it into this chat or into a remote URL.

```powershell
Set-Location "C:\Users\prajyot\Documents\Youtube\kids-phonics-shorts"
git init
git branch -M main
git lfs install
git add .
git commit -m "Add isolated daily Shorts engine"
git remote add origin https://github.com/lkk436786-ui/abcd-automation-short.git
git push -u origin main
```

If the GitHub repo already has an initial README, first run `git pull --rebase origin main`, resolve any conflict, then push. The workflow needs Actions enabled and repository `Settings → Actions → General → Workflow permissions` set to `Read and write permissions`.

## Local checks

```powershell
python -m pip install -r requirements-short.txt
python -m pytest -q
python -m shorts_engine.main --count 5 --dry-run
```

The workflow checks twelve two-hour windows at minute :47 India time, chooses one stable pseudo-random window per day, and uploads five Shorts automatically. If a run fails or only uploads part of the batch, the next window resumes the same batch without re-uploading successful items. A push to the default branch can also start the eligible run for the current day, so daily manual workflow runs are not required.

The workflow caches Git LFS objects so the roughly 505 MB asset library is not downloaded from LFS on every run. GitHub’s cache can still be evicted, so this reduces bandwidth but cannot remove GitHub’s storage/bandwidth limits.
