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
FRAME_TARGET = 1.735  # usual height / width of the printed frame
FAINT_LINE_MIN = 0.6  # frame lines are faded on some scans, especially under the title
EDGE_ZONE = 10  # pixels from the scan edge where a line can be the frame cropped tight
FRAME_RATIO = (1.68, 1.80)  # height / width of the printed frame on real cards
MAX_TRIM = 0.08  # more than this cut from one edge suggests a wrong frame line
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
        """Outermost frame line, trying the most reliable kind of line first."""
        indices = list(indices)

        def paper_outside(i):
            paper = warmth[outside(i)]
            return paper.size and paper.mean() > PAPER_WARMTH

        # 1. A strong line with card paper outside it.
        for i in indices:
            if profile[i] >= LINE_MIN and paper_outside(i):
                return i
        # 2. A strong line at the very edge: the scan was cropped right at the frame.
        for i in indices[:EDGE_ZONE]:
            if profile[i] >= LINE_MIN:
                return i
        # 3. A faded line with card paper outside it.
        for i in indices:
            if profile[i] >= FAINT_LINE_MIN and paper_outside(i):
                return i
        raise ValueError("frame line not found")

    ys, xs = slice(int(h * 0.1), int(h * 0.9)), slice(int(w * 0.1), int(w * 0.9))
    e = EDGE_SKIP
    left = first(cols, range(e, int(w * 0.15)), lambda i: (ys, slice(max(i - 10, 0), i - 3)))
    right = first(cols, range(w - 1 - e, int(w * 0.85), -1), lambda i: (ys, slice(i + 4, i + 11)))
    top = first(rows, range(e, int(h * 0.15)), lambda i: (slice(max(i - 10, 0), i - 3), xs))
    bottom = closest_bottom(rows, warmth, xs, left, top, right, h)
    return left, top, right + 1, bottom + 1


def closest_bottom(rows, warmth, xs, left, top, right, h):
    """Bottom frame line: of the dark lines with card paper below them, the one that gives
    the frame its usual proportions. On some cards (Strength, Wheel of Fortune) the line
    under the title is faded, and the strongest line is the one above the title instead.
    """
    target = top + FRAME_TARGET * (right - left)
    candidates = []
    for i in range(h - 1 - EDGE_SKIP, int(h * 0.75), -1):
        paper = warmth[slice(i + 4, i + 11), xs]
        if rows[i] >= FAINT_LINE_MIN and paper.size and paper.mean() > PAPER_WARMTH:
            candidates.append(i)
    if not candidates:
        raise ValueError("frame line not found")
    # Use the outer edge of the chosen line: the lowest row of its run.
    best = min(candidates, key=lambda i: abs(i - target))
    while best + 1 in candidates:
        best += 1
    return best


def tone(img):
    # Brighten so the lightest paper reaches near-white. Scaling every channel by the
    # same factor keeps the colors' balance, so the vintage palette stays as printed.
    lum = np.asarray(img.convert("L"))
    hi = np.percentile(lum, 99.5)
    a = np.asarray(img).astype(float) * (WHITE / max(hi, 1))
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img = ImageEnhance.Contrast(img).enhance(CONTRAST)
    return img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=2))


def crop_warnings(size, box):
    """Signs that the frame was found in the wrong place."""
    w, h = size
    left, top, right, bottom = box
    warnings = []
    ratio = (bottom - top) / (right - left)
    if not FRAME_RATIO[0] <= ratio <= FRAME_RATIO[1]:
        warnings.append(f"frame proportions {ratio:.3f} (expected {FRAME_RATIO[0]}-{FRAME_RATIO[1]})")
    for side, cut, total in (("left", left, w), ("top", top, h), ("right", w - right, w),
                             ("bottom", h - bottom, h)):
        if cut / total > MAX_TRIM:
            warnings.append(f"{side} edge trimmed {cut / total:.0%}")
    return warnings


def clean(path):
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img = straighten(img)
    box = frame_box(img)
    for warning in crop_warnings(img.size, box):
        print(f"  CHECK {path.name}: {warning}")
    img = img.crop(box)
    img = img.resize(INNER_SIZE, Image.LANCZOS)
    img = tone(img)
    return ImageOps.expand(img, border=BORDER, fill=BORDER_COLOR)


def main():
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW_DIR
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    failed = []
    for path in sorted(raw.glob("*.jpg")):
        try:
            clean(path).save(out / path.name, quality=JPEG_QUALITY, optimize=True)
        except ValueError as e:
            print(f"  FAILED {path.name}: {e}")
            failed.append(path.name)
            continue
        print(f"{path.name} -> {out / path.name}")
    if failed:
        sys.exit(f"{len(failed)} card(s) failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
