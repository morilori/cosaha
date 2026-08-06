#!/usr/bin/env python3
"""Append each artwork's dominant color (in German) to its folder name,
e.g. "1-Frühlingswogen" -> "1-Frühlingswogen-gelb".

Uses the exact same color-detection algorithm as index.html's client-side
"sort by color" feature (average RGB of a downscaled sample -> HSL hue ->
one of 12 named hue buckets), computed on the same file the site itself
would pick as the folder's thumbnail (pickMain), so the folder-name color
always matches what a visitor would see/sort by.

Safe to re-run: folders whose name already ends with a recognized German
color word are skipped, so running this after adding new art only
processes the new folders.

Run manually whenever new art is added (after scripts/update_artworks.py):
  python3 scripts/add_color_to_folder_names.py
"""
import os
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art'

# must match index.html's COLOR_NAMES array exactly (same order = same
# hue-bucket boundaries)
COLOR_NAMES_EN = ['red', 'orange', 'yellow', 'lime', 'green', 'teal',
                   'cyan', 'blue', 'indigo', 'violet', 'magenta', 'crimson']
# must match index.html's translations.de.colors
COLOR_DE = {
    'red': 'rot', 'orange': 'orange', 'yellow': 'gelb', 'lime': 'limette',
    'green': 'grün', 'teal': 'petrol', 'cyan': 'cyan', 'blue': 'blau',
    'indigo': 'indigo', 'violet': 'violett', 'magenta': 'magenta',
    'crimson': 'karmesinrot',
}
DE_COLOR_WORDS = set(COLOR_DE.values())


def is_image(name):
    return name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))


def pick_main(files):
    lower = [f.lower() for f in files]
    for i, l in enumerate(lower):
        if '_main' in l or l.endswith('/main.jpg') or l.endswith('main.jpg'):
            return files[i]
    return sorted(files, key=str.lower)[0]


def rgb_to_hue(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return 0.0
    d = mx - mn
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60


def hue_to_name_en(h):
    idx = round((h % 360) / 360 * len(COLOR_NAMES_EN)) % len(COLOR_NAMES_EN)
    return COLOR_NAMES_EN[idx]


def dominant_color_de(path):
    im = Image.open(path).convert('RGB')
    small = im.resize((80, 80))
    pixels = list(small.getdata())
    n = len(pixels)
    r = sum(p[0] for p in pixels) / n
    g = sum(p[1] for p in pixels) / n
    b = sum(p[2] for p in pixels) / n
    return COLOR_DE[hue_to_name_en(rgb_to_hue(r, g, b))]


def main():
    if not ART.exists():
        print('Art/ directory not found')
        return 2
    renamed = skipped = 0
    for entry in sorted(os.listdir(ART)):
        d = ART / entry
        if not d.is_dir():
            continue
        last_word = re.split(r'[-_ ]', entry)[-1].lower()
        if last_word in DE_COLOR_WORDS:
            skipped += 1
            continue
        files = [f for f in os.listdir(d) if is_image(f)]
        if not files:
            skipped += 1
            continue
        main_file = pick_main(files)
        color = dominant_color_de(d / main_file)
        new_name = f'{entry}-{color}'
        os.rename(d, ART / new_name)
        print(f'{entry} -> {new_name}')
        renamed += 1
    print(f'renamed {renamed}, skipped {skipped}')


if __name__ == '__main__':
    main()
