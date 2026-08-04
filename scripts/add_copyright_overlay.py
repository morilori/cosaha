#!/usr/bin/env python3
"""Bake a small "© Cordula Saupe-Hartstang" text mark into the bottom-left
corner of every artwork image in Art/ — a visible copyright notice burned
into the actual pixels (unlike scripts/add_copyright_metadata.py, which
only edits EXIF and is invisible/strippable by a screenshot).

Run manually whenever new art is added (after scripts/update_artworks.py):
  python3 scripts/add_copyright_overlay.py

Safe to re-run: already-processed files are detected via a JPEG EXIF
marker and skipped, so it won't stack a second copyright line.

IMPORTANT — run this BEFORE scripts/add_copyright_metadata.py, not after.
This script recompresses the image (Pillow re-encode) and only carries
forward a fresh EXIF dict with its own marker tag; any other EXIF fields
present when it runs (Artist/Copyright from the metadata script, camera
info, etc.) are dropped. Running the metadata script second (it uses
piexif, which edits only the EXIF segment and preserves everything else)
restores those tags without touching the now-watermarked pixels.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art'
MARKER = 'cosaha-copyright-overlay-v1'
USER_COMMENT_TAG = 0x9286
TEXT = '© cosaha.com'
FONT_PATH = '/System/Library/Fonts/Supplemental/Arial.ttf'
BAR_COLOR = (195, 78, 78, 255)  # site's --accent color, #C34E4E


def is_image(name):
    return name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))


def already_marked(im):
    try:
        return im.getexif().get(USER_COMMENT_TAG) == MARKER
    except Exception:
        return False


def draw_copyright(overlay, w, h):
    short = min(w, h)
    font_size = max(14, int(short * 0.028))
    font = ImageFont.truetype(FONT_PATH, font_size)
    draw = ImageDraw.Draw(overlay)

    margin = max(10, int(short * 0.02))
    pad_x, pad_y = int(font_size * 0.55), int(font_size * 0.32)

    bbox = draw.textbbox((0, 0), TEXT, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    bar_x0, bar_y1 = margin, h - margin
    bar_x1 = bar_x0 + text_w + pad_x * 2
    bar_y0 = bar_y1 - (text_h + pad_y * 2)

    draw.rectangle([bar_x0, bar_y0, bar_x1, bar_y1], fill=BAR_COLOR)
    draw.text(
        (bar_x0 + pad_x - bbox[0], bar_y0 + pad_y - bbox[1]),
        TEXT, font=font, fill=(255, 255, 255, 255)
    )


def process(path):
    im = Image.open(path)
    if already_marked(im):
        im.close()
        return False

    # bake in EXIF-orientation rotation as real pixels first — a fresh
    # composited image below carries no orientation tag, and photos that
    # rely on it (most phone photos do) would otherwise render sideways
    im = ImageOps.exif_transpose(im)

    im = im.convert('RGBA')
    w, h = im.size
    overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    draw_copyright(overlay, w, h)

    out = Image.alpha_composite(im, overlay).convert('RGB')
    exif = out.getexif()
    exif[USER_COMMENT_TAG] = MARKER
    out.save(path, quality=90, exif=exif)
    return True


def main():
    if not ART.exists():
        print('Art/ directory not found')
        return 2
    done = skipped = 0
    for dirpath, dirs, files in os.walk(ART):
        for f in files:
            if not is_image(f):
                continue
            p = Path(dirpath) / f
            if process(p):
                done += 1
            else:
                skipped += 1
    print(f'Marked {done} images, skipped {skipped} already-marked')


if __name__ == '__main__':
    main()
