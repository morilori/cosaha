#!/usr/bin/env python3
"""Build the published copy of the site into _site/ (used by the deploy workflow).

Copies every git-tracked file the website needs and shrinks the artwork
photos to web size. The originals in Art/ are never modified — only the
copies in _site/ are resized. Full-size phone photos (~2 MB each) pushed
the published site past what GitHub Pages can deploy in time.

It also writes small grid thumbnails to _site/thumbs/<same path>: the grid
shows ~100 tiles at once, and loading the 2000px photos (~1 MB each) for
them made the page slow. The lightbox still loads the full web size.

Usage: python3 scripts/build_site.py [--max-size 2000] [--thumb-size 800] [--out _site]
"""
import argparse
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

# tracked files/folders that are not part of the website
EXCLUDE_PREFIXES = ('.github/', 'scripts/')
EXCLUDE_NAMES = {'.gitignore', 'README.md', 'requirements.txt', 'start.sh',
                 'philosophy.txt', 'Kategorien.numbers', 'Kategorien.xlsx'}
RESIZE_EXT = {'.jpg', '.jpeg'}


def tracked_files():
    out = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, check=True,
                         capture_output=True).stdout.decode('utf-8')
    return [p for p in out.split('\0') if p]


def resize(src, dst, max_size, quality):
    with Image.open(src) as im:
        exif = im.info.get('exif')          # keeps copyright + orientation
        icc = im.info.get('icc_profile')
        if max(im.size) > max_size:
            im.thumbnail((max_size, max_size), Image.LANCZOS)
        kwargs = {'quality': quality, 'optimize': True, 'progressive': True}
        if exif:
            kwargs['exif'] = exif
        if icc:
            kwargs['icc_profile'] = icc
        im.convert('RGB').save(dst, 'JPEG', **kwargs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-size', type=int, default=2000,
                    help='longest side of artwork photos in pixels')
    ap.add_argument('--thumb-size', type=int, default=800,
                    help='longest side of grid thumbnails in pixels')
    ap.add_argument('--quality', type=int, default=85)
    ap.add_argument('--out', default='_site')
    args = ap.parse_args()

    out = ROOT / args.out
    if out.exists():
        shutil.rmtree(out)

    copied = resized = 0
    for rel in tracked_files():
        if rel.startswith(EXCLUDE_PREFIXES) or rel in EXCLUDE_NAMES:
            continue
        src = ROOT / rel
        if not src.is_file():
            continue
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel.startswith('Art/') and src.suffix.lower() in RESIZE_EXT:
            resize(src, dst, args.max_size, args.quality)
            thumb = out / 'thumbs' / rel
            thumb.parent.mkdir(parents=True, exist_ok=True)
            resize(src, thumb, args.thumb_size, 75)
            resized += 1
        else:
            shutil.copy2(src, dst)
            copied += 1

    total = sum(f.stat().st_size for f in out.rglob('*') if f.is_file())
    print(f'{resized} images resized, {copied} files copied, '
          f'{total / 1e6:.0f} MB in {out}')


if __name__ == '__main__':
    main()
