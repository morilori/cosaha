#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .git ]; then
  git init
fi

# set a local user if none set (safer than touching global config)
if ! git config user.email >/dev/null 2>&1; then
  git config user.email "you@example.com"
fi
if ! git config user.name >/dev/null 2>&1; then
  git config user.name "Your Name"
fi

git add -A
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  git commit -m "Update project files" || true
else
  git commit -m "Initial commit" || true
fi

git branch -M main || true
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin https://github.com/morilori/cosaha.git
else
  git remote add origin https://github.com/morilori/cosaha.git
fi

if git push -u origin main; then
  echo "PUSH_OK"
else
  echo "PUSH_FAILED"
fi
