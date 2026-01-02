#!/usr/bin/env python3
"""Regenerate folderImages.json and update artworkSources in index.html.

Usage: run from project root (where `Art/` and `index.html` live):
  python3 scripts/update_artworks.py

This script:
- walks `Art/` and collects image files per folder
- writes `folderImages.json` (paths are URL-encoded to preserve spaces)
- selects a main thumbnail per folder (prefers files containing "_main" or "main")
- updates the `const artworkSources = [ ... ]` array in `index.html` to list those mains
"""
import os
import re
import json
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART_DIR = ROOT / 'Art'
OUT_JSON = ROOT / 'folderImages.json'
INDEX_HTML = ROOT / 'index.html'

def is_image(name):
    name = name.lower()
    return name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))

def collect_folders():
    d = {}
    for dirpath, dirs, files in os.walk(ART_DIR):
        imgs = [f for f in files if is_image(f)]
        if not imgs:
            continue
        imgs_sorted = sorted(imgs, key=lambda s: s.lower())
        rel_dir = os.path.relpath(dirpath, ROOT).replace('\\', '/')
        if not rel_dir.endswith('/'):
            rel_dir = rel_dir + '/'
        paths = [f"{rel_dir}{f}".replace('\\', '/') for f in imgs_sorted]
        # URL-encode paths for JSON to match existing format
        quoted = [urllib.parse.quote(p) for p in paths]
        d[rel_dir] = quoted
    return d

def pick_main(paths):
    # paths are unquoted strings like 'Art/Folder/file.jpg'
    lower = [p.lower() for p in paths]
    for i,p in enumerate(paths):
        if '_main' in lower[i] or lower[i].endswith('/main.jpg') or lower[i].endswith('main.jpg'):
            return p
    return paths[0]

def write_folder_json(fmap):
    OUT_JSON.write_text(json.dumps(fmap, ensure_ascii=False, indent=2), encoding='utf8')

def update_index_html(mains):
    txt = INDEX_HTML.read_text(encoding='utf8')
    pattern = re.compile(r"const\s+artworkSources\s*=\s*\[.*?\];", re.S)
    entries = ',\n        '.join([f"'{p}'" for p in mains])
    new_block = 'const artworkSources = [\n        ' + entries + '\n      ];'
    if pattern.search(txt):
        new_txt = pattern.sub(new_block, txt)
        backup = INDEX_HTML.with_suffix('.html.bak')
        backup.write_text(txt, encoding='utf8')
        INDEX_HTML.write_text(new_txt, encoding='utf8')
        return True
    else:
        return False

def main():
    if not ART_DIR.exists():
        print('Art/ directory not found in', ROOT)
        return 2
    fmap = collect_folders()
    # decode for main selection convenience
    mains = []
    for folder in sorted(fmap.keys(), key=lambda s: s.lower()):
        quoted_list = fmap[folder]
        decoded = [urllib.parse.unquote(p) for p in quoted_list]
        main = pick_main(decoded)
        mains.append(main)
    # write folderImages.json (keep quoted paths as in previous file)
    write_folder_json(fmap)
    ok = update_index_html(mains)
    print(f'Wrote {OUT_JSON} with {len(fmap)} folders')
    if ok:
        backup = INDEX_HTML.with_suffix('.html.bak')
        print(f'Updated {INDEX_HTML} with {len(mains)} main thumbnails (backup: {backup})')
    else:
        print('Failed to locate artworkSources block in index.html; no changes made to index.html')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
