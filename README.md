# Cosaha — minimal art site

This repository contains a single-file static site (index.html) and helper scripts to run and auto-update a local preview.

Quick start (local):

```bash
# create venv and install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run the watcher + static server (will regenerate folderImages.json on Art/ changes)
./start.sh

# open browser at the port shown in /tmp/cosaha_start.log (or check the console output)
tail -n 40 /tmp/cosaha_start.log
```

Deploying to cosaha.com (GitHub Pages)

This repository is configured to deploy to GitHub Pages via GitHub Actions. The workflow runs on pushes to `main` and will publish the repository contents to GitHub Pages. A `CNAME` file is included to configure the custom domain `cosaha.com`.

DNS setup for `cosaha.com` (apex/root domain):

- Add A records for the following IP addresses (GitHub Pages):

  - 185.199.108.153
  - 185.199.109.153
  - 185.199.110.153
  - 185.199.111.153

- Add a CNAME record for `www` pointing to `morilori.github.io` (or create an ALIAS/ANAME if your DNS provider supports it), then configure the domain on GitHub to enable HTTPS.

Notes

- Large media files were pushed to the repo. Consider enabling Git LFS for large videos and heavy image files.
- `folderImages.json` is generated automatically and is ignored by `.gitignore`.
