#!/usr/bin/env python3
"""Prepare a lightweight build directory for GitHub Pages.

Copies index.html, static assets, and image files under a size threshold
to `pages_build/` and writes an adjusted `folderImages.json` there with
paths relative to the site root.
"""
import os
import shutil
import json
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art'
OUT = ROOT / 'pages_build'
SRC_JSON = ROOT / 'folderImages.json'
MAX_BYTES = 10 * 1024 * 1024  # 10 MB

def safe_mkdir(p):
    p.mkdir(parents=True, exist_ok=True)

def copy_if_safe(src, dst):
    try:
        size = src.stat().st_size
        if size > MAX_BYTES:
            return False
        shutil.copy2(src, dst)
        return True
    except Exception:
        return False

def main():
    if not SRC_JSON.exists():
        print('No folderImages.json, run update_artworks.py first')
        return 1
    # clear build dir
    if OUT.exists():
        shutil.rmtree(OUT)
    safe_mkdir(OUT)

    # copy root files
    for root_file in ['index.html', 'CNAME', 'Icon.svg', 'Logo.svg', 'favicon.ico', 'README.md']:
        p = ROOT / root_file
        if p.exists():
            shutil.copy2(p, OUT / p.name)

    # copy images but skip large files and videos
    with open(SRC_JSON, 'r', encoding='utf8') as f:
        fmap = json.load(f)

    out_map = {}
    for folder, qpaths in fmap.items():
        decoded = [urllib.parse.unquote(p) for p in qpaths]
        rel_out_folder = folder
        # create folder in build dir
        dest_folder = OUT / rel_out_folder
        safe_mkdir(dest_folder)
        copied = []
        for p in decoded:
            src = ROOT / p
            if not src.exists():
                continue
            # skip non-image extensions
            if not src.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                continue
            ok = copy_if_safe(src, dest_folder / src.name)
            if ok:
                copied.append(str((Path(rel_out_folder) / src.name).as_posix()))
        if copied:
            out_map[rel_out_folder] = copied

    # write adjusted folderImages.json
    with open(OUT / 'folderImages.json', 'w', encoding='utf8') as f:
        json.dump(out_map, f, ensure_ascii=False, indent=2)

    print('Prepared pages_build with', sum(len(v) for v in out_map.values()), 'images')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
