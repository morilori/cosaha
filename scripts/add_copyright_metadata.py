#!/usr/bin/env python3
"""Tag every JPEG in Art/ with copyright metadata (EXIF Artist/Copyright).

Uses piexif to edit only the EXIF segment — the compressed image data is
never touched/recompressed, so this is fully lossless and preserves all
existing tags (including Orientation, which the site's photos rely on).

Doesn't stop anyone from copying a screenshot or a re-saved image (both
strip EXIF), but gives a real, standard paper trail if the original file
itself gets reposted.

Run manually whenever new art is added:
  python3 scripts/add_copyright_metadata.py
"""
import os
from pathlib import Path
import piexif

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art'
ARTIST = 'Cordula Saupe-Hartstang'
# plain ASCII only — EXIF string fields are spec'd as ASCII, and a "©" byte
# sequence gets mangled by readers that don't guess UTF-8 (verified: it did)
COPYRIGHT = 'Copyright Cordula Saupe-Hartstang, cosaha.com. All rights reserved.'


def is_jpeg(name):
    return name.lower().endswith(('.jpg', '.jpeg'))


def tag_file(path):
    try:
        exif_dict = piexif.load(str(path))
    except Exception:
        exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'thumbnail': None}

    # some phone exports have a malformed UserComment (37500) that piexif
    # parses but can't re-serialize (raises "wrong type of exif value");
    # drop it rather than fail — we don't need to preserve it
    exif_ifd = exif_dict.get('Exif') or {}
    if not isinstance(exif_ifd.get(37500), (bytes, type(None))):
        del exif_ifd[37500]
        exif_dict['Exif'] = exif_ifd

    zeroth = exif_dict.get('0th') or {}
    already = (
        zeroth.get(piexif.ImageIFD.Artist) == ARTIST.encode('utf-8')
        and zeroth.get(piexif.ImageIFD.Copyright) == COPYRIGHT.encode('utf-8')
    )
    if already:
        return False

    zeroth[piexif.ImageIFD.Artist] = ARTIST.encode('utf-8')
    zeroth[piexif.ImageIFD.Copyright] = COPYRIGHT.encode('utf-8')
    exif_dict['0th'] = zeroth
    piexif.insert(piexif.dump(exif_dict), str(path))
    return True


def main():
    if not ART.exists():
        print('Art/ directory not found')
        return 2
    done = skipped = errors = 0
    for dirpath, dirs, files in os.walk(ART):
        for f in files:
            if not is_jpeg(f):
                continue
            p = Path(dirpath) / f
            try:
                if tag_file(p):
                    done += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f'Error tagging {p}: {e}')
                errors += 1
    print(f'Tagged {done} images, skipped {skipped} already-tagged, {errors} errors')


if __name__ == '__main__':
    main()
