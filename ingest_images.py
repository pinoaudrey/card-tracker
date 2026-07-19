#!/usr/bin/env python3
"""Convert card photos into site images.

Usage: python ingest_images.py <img> [<img> ...]

Each source (HEIC / JPG / PNG) becomes docs/images/<basename>.jpg at 760px, quality 72,
and the resulting name is printed so you can drop it into cards.json as `front`/`back`.
HEIC is converted via `sips` (built in on macOS); JPG/PNG go straight through Pillow.
"""
import os, sys, subprocess, tempfile
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(ROOT, "docs", "images")

def load(path):
    try:
        return Image.open(path)
    except Exception:
        tmp = tempfile.mktemp(suffix=".jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", path, "--out", tmp],
                       check=True, capture_output=True)
        return Image.open(tmp)

def main(paths):
    os.makedirs(DST, exist_ok=True)
    for src in paths:
        name = os.path.splitext(os.path.basename(src))[0]
        im = load(src).convert("RGB")
        im.thumbnail((760, 760))
        im.save(os.path.join(DST, name + ".jpg"), format="JPEG", quality=72)
        print(f"  {name}  ->  docs/images/{name}.jpg")
    print("Use these names as `front`/`back` in cards.json, then run: python build.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1:])
