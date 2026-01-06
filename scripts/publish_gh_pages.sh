#!/usr/bin/env bash
set -euo pipefail

# Build a lightweight publish tree and push to gh-pages branch
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
echo "Building publish tree in $TMP"

# Copy site files but exclude large media and development files
rsync -a --exclude='.git' --exclude='.venv' --exclude='.github' --exclude='scripts' \
  --exclude='node_modules' --exclude='*.mp4' --exclude='*.mov' --exclude='*.tmp' \
  --exclude='*.log' --exclude='*.bak' "$ROOT/" "$TMP/"

cd "$TMP"
git init
git remote add origin "$(git -C "$ROOT" remote get-url origin)"
git checkout -b gh-pages
git add -A
git commit -m "Publish site to gh-pages (auto)" || true
echo "Pushing to origin gh-pages (force)"
git push -f origin gh-pages

echo "Published to gh-pages"
rm -rf "$TMP"
