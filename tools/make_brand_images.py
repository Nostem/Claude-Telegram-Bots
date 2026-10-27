"""Make the bot's profile photo and description picture from the cleaned card images.

Usage: python3 tools/make_brand_images.py
Writes content/brand/profile.jpg (square; Telegram shows it as a circle) and
content/brand/description.jpg (640 x 360, shown above "What can this bot do?").
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CARDS = Path("content/tarot/images/cards")
OUT = Path("content/brand")
FONT = OUT / "fonts" / "CormorantGaramond.ttf"

NIGHT = (16, 20, 46)        # deep navy
NIGHT_EDGE = (6, 8, 22)
GOLD = (222, 186, 110)
CREAM = (238, 228, 204)
SUN_FACE = (422, 320, 330)   # centre x, centre y, half-width of the crop on the Sun card


def font(size, weight=b"SemiBold"):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_name(weight)
    return f


def night_sky(size, seed=7, stars=90):
    """Radial navy gradient with scattered stars."""
    w, h = size
    img = Image.new("RGB", size, NIGHT_EDGE)
    glow = Image.new("L", size, 0)
    ImageDraw.Draw(glow).ellipse((-w * 0.2, -h * 0.2, w * 1.2, h * 1.2), fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(min(w, h) * 0.25))
    img = Image.composite(Image.new("RGB", size, NIGHT), img, glow)
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for _ in range(stars):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice([0.6, 0.8, 1.0, 1.4])
        a = rng.randint(120, 255)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(a, a, min(255, a + 10)))
    return img


def card(card_id, height):
    img = Image.open(CARDS / f"{card_id}.jpg").convert("RGB")
    return img.resize((round(img.width * height / img.height), height), Image.LANCZOS)


def paste_with_shadow(base, img, xy, angle=0):
    """Paste a card, optionally rotated, with a soft shadow beneath it."""
    img = img.convert("RGBA")
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(img.getchannel("A").point(lambda a: int(a * 0.6)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    base.paste(shadow, (xy[0] + 6, xy[1] + 10), shadow)
    base.paste(img, xy, img)


def profile():
    """The face of the Sun card (XIX), cropped close and framed by a thin gold ring.
    Telegram shows profile photos as small circles, so a bold detail reads better than
    a whole card."""
    size = 1024
    sun = Image.open(CARDS / "major-19-the-sun.jpg").convert("RGB")
    cx, cy, half = SUN_FACE
    face = sun.crop((cx - half, cy - half, cx + half, cy + half)).resize((size, size), Image.LANCZOS)
    img = night_sky((size, size), stars=0)
    mask = Image.new("L", (size, size), 0)
    inset = 40
    ImageDraw.Draw(mask).ellipse((inset, inset, size - inset, size - inset), fill=255)
    img.paste(face, (0, 0), mask)
    ImageDraw.Draw(img).ellipse((inset, inset, size - inset, size - inset), outline=GOLD, width=10)
    return img


def description():
    """Three fanned cards beside the bot's name, 640 x 360 (shown at 2x for sharpness)."""
    w, h = 1280, 720
    img = night_sky((w, h), seed=3, stars=160)
    # Cards without nudity, since this picture is the first thing new users see.
    for card_id, x, y, angle in (("major-00-the-fool", 40, 175, 9),
                                 ("major-01-the-magician", 300, 175, -9),
                                 ("major-18-the-moon", 165, 125, 0)):
        paste_with_shadow(img, card(card_id, 430), (x, y), angle)
    draw = ImageDraw.Draw(img)
    x = 660
    draw.text((x, 210), "Tarot", font=font(108, b"Bold"), fill=GOLD)
    draw.text((x, 320), "Companion", font=font(108, b"Bold"), fill=GOLD)
    draw.line((x + 6, 468, x + 560, 468), fill=GOLD, width=3)
    draw.text((x + 4, 488), "78 cards · a card each day · your journal",
              font=font(34, b"Medium"), fill=CREAM)
    draw.text((x + 4, 538), "Original 1909 art · no subscriptions",
              font=font(34, b"Medium"), fill=CREAM)
    return img.resize((640, 360), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    profile().save(OUT / "profile.jpg", quality=92)
    description().save(OUT / "description.jpg", quality=92)
    print(f"wrote {OUT / 'profile.jpg'} and {OUT / 'description.jpg'}")


if __name__ == "__main__":
    main()
