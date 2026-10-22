"""Clean up raw tarot card scans into consistent, polished card images.

For each scan in the input folder:
1. Straighten it, using the printed black frame line as the reference.
2. Crop to the outer edge of the frame, dropping the worn, uneven scan border.
3. Resize to a standard size and gently even out tone: cleaner whites, a touch more
   color, crisper line work. The vintage color stays.
4. Add a new, even cream border.

Usage: python3 tools/clean_card_images.py [raw_dir] [out_dir]
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

RAW_DIR = Path("content/tarot/images/raw")
OUT_DIR = Path("content/tarot/images/cards")

INNER_SIZE = (780, 1352)  # framed artwork, width x height
BORDER = 32  # cream border width in pixels
BORDER_COLOR = (238, 228, 204)
DARK = 110  # luminance below this counts as ink
FRAME_DARK = 160  # looser ink threshold for the frame line, which is faded on some scans
LINE_MIN = 0.8  # share of a row/column that must be ink to count as the frame line
EDGE_SKIP = 3  # ignore the outermost pixels
PAPER_WARMTH = 40  # card paper is warm cream (red minus blue); the scanner bed is neutral
JPEG_QUALITY = 90
WHITE = 248  # target for the lightest paper in the artwork
CONTRAST = 1.08


def ink(gray, threshold=DARK):
    return np.asarray(gray).astype(int) < threshold


def left_line_slope(gray):
    """Slope (dx per dy) of the frame's left line, from the first ink pixel per row."""
    d = ink(gray)
    h, w = d.shape
    ys, xs = [], []
    for y in range(int(h * 0.1), int(h * 0.9), 5):
        hits = np.where(d[y, : int(w * 0.1)])[0]
        if len(hits):
            ys.append(y)
            xs.append(hits[0])
    # Drop outliers (art touching the edge) before fitting.
    xs, ys = np.array(xs), np.array(ys)
    keep = np.abs(xs - np.median(xs)) <= 3
    return np.polyfit(ys[keep], xs[keep], 1)[0]


def straighten(img):
    angle = math.degrees(math.atan(left_line_slope(img.convert("L"))))
    # PIL rotates counterclockwise for positive angles.
    return img.rotate(-angle, resample=Image.BICUBIC, expand=False, fillcolor=BORDER_COLOR)


def frame_box(img):
    """Outer edges (left, top, right, bottom) of the printed frame line.

    Scans can also show a dark shadow line where the card edge meets the scanner bed.
    A real frame line has cream card paper outside it; a shadow has the neutral
    scanner bed, so lines without warm paper outside are skipped.
    """
    a = np.asarray(img).astype(int)
    warmth = a[..., 0] - a[..., 2]
    d = ink(img.convert("L"), FRAME_DARK)
    h, w = d.shape
    cols = d[int(h * 0.1) : int(h * 0.9)].mean(0)
    rows = d[:, int(w * 0.1) : int(w * 0.9)].mean(1)

    def first(profile, indices, outside):
        indices = list(indices)
        for i in indices:
            paper = warmth[outside(i)]
            if profile[i] >= LINE_MIN and paper.size and paper.mean() > PAPER_WARMTH:
                return i
        # Some scans are cropped right at the frame line, with no paper outside it.
        edge = indices[0]
        if profile[edge] >= LINE_MIN:
            return edge
        raise ValueError("frame line not found")

    ys, xs = slice(int(h * 0.1), int(h * 0.9)), slice(int(w * 0.1), int(w * 0.9))
    e = EDGE_SKIP
    left = first(cols, range(e, int(w * 0.15)), lambda i: (ys, slice(max(i - 10, 0), i - 3)))
    right = first(cols, range(w - 1 - e, int(w * 0.85), -1), lambda i: (ys, slice(i + 4, i + 11)))
    top = first(rows, range(e, int(h * 0.15)), lambda i: (slice(max(i - 10, 0), i - 3), xs))
    bottom = first(rows, range(h - 1 - e, int(h * 0.85), -1), lambda i: (slice(i + 4, i + 11), xs))
    return left, top, right + 1, bottom + 1


def tone(img):
    # Brighten so the lightest paper reaches near-white. Scaling every channel by the
    # same factor keeps the colors' balance, so the vintage palette stays as printed.
    lum = np.asarray(img.convert("L"))
    hi = np.percentile(lum, 99.5)
    a = np.asarray(img).astype(float) * (WHITE / max(hi, 1))
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img = ImageEnhance.Contrast(img).enhance(CONTRAST)
    return img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=2))


def clean(path):
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img = straighten(img)
    img = img.crop(frame_box(img))
    img = img.resize(INNER_SIZE, Image.LANCZOS)
    img = tone(img)
    return ImageOps.expand(img, border=BORDER, fill=BORDER_COLOR)


def main():
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW_DIR
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    for path in sorted(raw.glob("*.jpg")):
        clean(path).save(out / path.name, quality=JPEG_QUALITY, optimize=True)
        print(f"{path.name} -> {out / path.name}")


if __name__ == "__main__":
    main()
