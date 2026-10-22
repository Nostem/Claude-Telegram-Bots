"""Download the original 1909 card scans from Wikimedia Commons, after checking each
file's source details.

Every file comes from the "RWS1909" set (Category:Rider-Waite tarot deck (Roses &
Lilies)): scans of an original 1909 printing. A file is only saved if its Commons page
dates it to 1909 and marks it public domain. The results are recorded in
content/tarot/images/sources.json and content/tarot/images/CREDITS.md.

Wikimedia refuses bulk downloads of original files from shared servers and asks for
standard thumbnail sizes instead, so this downloads the 960px thumbnail of each scan
(rendered from the roughly 825px original), with a pause between requests.

Usage:
  python3 tools/fetch_card_images.py                   check sources, download missing scans
  python3 tools/fetch_card_images.py --no-download     check sources and update the records only
  python3 tools/fetch_card_images.py --fallback DIR    first fill missing scans from DIR, the
                                                       mariano-fu/arcana copies (see below)
"""
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "TarotBotContent/0.1 (https://github.com/Nostem/Claude-Telegram-Bots)"
RAW_DIR = Path("content/tarot/images/raw")
THUMB_WIDTH = 960  # one of Wikimedia's standard thumbnail sizes
FALLBACK_WIDTH = 600
FALLBACK_REPO = "https://github.com/mariano-fu/arcana"
PAUSE = 60  # seconds between downloads, to stay under Wikimedia's rate limit
SOURCES = Path("content/tarot/images/sources.json")
CREDITS = Path("content/tarot/images/CREDITS.md")

MAJORS = ["the-fool", "the-magician", "the-high-priestess", "the-empress", "the-emperor",
          "the-hierophant", "the-lovers", "the-chariot", "strength", "the-hermit",
          "wheel-of-fortune", "justice", "the-hanged-man", "death", "temperance", "the-devil",
          "the-tower", "the-star", "the-moon", "the-sun", "judgement", "the-world"]
SUITS = ["Cups", "Pentacles", "Swords", "Wands"]
COURTS = {11: "page", 12: "knight", 13: "queen", 14: "king"}
COURT_NAMES = {11: "Page", 12: "Knight", 13: "Queen", 14: "King"}
NUMBER_NAMES = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]


def cards():
    """(card id, display name, Commons file title) for all 78 cards."""
    out = []
    for n, slug in enumerate(MAJORS):
        title = slug.replace("the-", "").replace("-", " ").title().replace(" Of ", " of ")
        if n == 0:
            title = "Fool"
        commons = f"File:RWS1909 - {n:02d} {title}.jpeg"
        name = slug.replace("-", " ").title().replace(" Of ", " of ")
        out.append((f"major-{n:02d}-{slug}", name, commons))
    for suit in SUITS:
        for n in range(1, 15):
            card_id = f"{suit.lower()}-{COURTS.get(n, f'{n:02d}')}"
            rank = COURT_NAMES.get(n) or NUMBER_NAMES[n - 1]
            out.append((card_id, f"{rank} of {suit}", f"File:RWS1909 - {suit} {n:02d}.jpeg"))
    return out


def get(url, binary=False):
    """GET with Wikimedia's required User-Agent, backing off when rate-limited."""
    for attempt in range(10):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
                return data if binary else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise
            # Wikimedia's Retry-After is often too short for a shared server, so grow the
            # wait on each attempt (up to 10 minutes).
            wait = max(int(e.headers.get("Retry-After") or 0), min(15 * 2 ** attempt, 600))
            print(f"  HTTP {e.code}, waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"gave up on {url}")


def plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(html or ""))).strip()


def file_info(titles):
    params = {"action": "query", "titles": "|".join(titles), "prop": "imageinfo",
              "iiprop": "url|size|sha1|mime|extmetadata", "format": "json"}
    data = get(f"{API}?{urllib.parse.urlencode(params)}")
    info = {}
    for page in data["query"]["pages"].values():
        if "imageinfo" not in page:
            raise RuntimeError(f"missing on Commons: {page['title']}")
        ii = page["imageinfo"][0]
        meta = {k: plain(v.get("value")) for k, v in ii["extmetadata"].items()}
        info[page["title"]] = {
            "url": ii["url"], "page": ii["descriptionurl"], "sha1": ii["sha1"],
            "width": ii["width"], "height": ii["height"], "mime": ii["mime"],
            "date": meta.get("DateTimeOriginal", ""), "license": meta.get("LicenseShortName", ""),
            "artist": meta.get("Artist", ""), "credit": meta.get("Credit", ""),
            "description": meta.get("ImageDescription", ""),
        }
    return info


def thumb_url(original):
    """URL of the standard-size thumbnail for an original upload.wikimedia.org file."""
    base, name = original.split("?")[0].rsplit("/", 1)
    return f"{base.replace('/commons/', '/commons/thumb/', 1)}/{name}/{THUMB_WIDTH}px-{name}"


def check_image(title, data, info):
    """The download must be a JPEG with the same proportions as the Commons original."""
    img = Image.open(io.BytesIO(data))
    expected = info["height"] / info["width"]
    if img.format != "JPEG" or abs(img.height / img.width - expected) > 0.01:
        raise RuntimeError(f"{title}: unexpected download ({img.format}, {img.size})")


def verify(title, info):
    problems = []
    if "1909" not in info["date"]:
        problems.append(f"date is {info['date']!r}, not 1909")
    if "public domain" not in info["license"].lower():
        problems.append(f"license is {info['license']!r}")
    if info["mime"] != "image/jpeg":
        problems.append(f"type is {info['mime']}")
    if problems:
        raise RuntimeError(f"{title}: " + "; ".join(problems))


def local_copy(card_id):
    """Which copy of the scan is in raw/: Wikimedia's full thumbnail, or the fallback."""
    path = RAW_DIR / f"{card_id}.jpg"
    if not path.exists():
        return "missing"
    return "commons" if Image.open(path).width == THUMB_WIDTH else "fallback"


def write_credits(entries):
    lines = [
        "# Card image credits",
        "",
        "<!-- Generated by tools/fetch_card_images.py. Do not edit by hand. -->",
        "",
        "**Artwork:** Pamela Colman Smith, for the Smith-Waite (RWS) tarot deck, published by",
        "Rider & Son, London, 1909. Public domain: published before 1931 (US), and the artist died",
        "in 1951 (life + 70 years).",
        "",
        "**Scans:** the \"RWS1909\" set on Wikimedia Commons, scans of an original 1909 \"Roses &",
        "Lilies\" printing. Every card's Commons page was checked for a 1909 date and a",
        "public-domain license before its image was used; see `sources.json` for the details.",
        "These are **not** the US Games 1971 recoloring, which carries a \"© 1971 U.S. Games\"",
        "line on the card edge and must not be used.",
        "",
        "**Copies used** (the *Copy* column below):",
        f"- *commons*: Wikimedia's {THUMB_WIDTH}px thumbnail of the scan.",
        f"- *fallback*: a {FALLBACK_WIDTH}px copy of the same Commons file, from the",
        f"  [mariano-fu/arcana]({FALLBACK_REPO}) project, used while Wikimedia rate-limits",
        "  downloads. Running `python3 tools/fetch_card_images.py` again replaces these with",
        "  the full Commons thumbnails.",
        "",
        "- `raw/`: the downloaded scans (not stored in git).",
        "- `cards/`: the cleaned-up images the bot uses, made by `tools/clean_card_images.py`.",
        "",
        "| Card | File | Commons source | Date | License | Copy |",
        "|---|---|---|---|---|---|",
    ]
    for e in entries:
        lines.append(f"| {e['name']} | `{e['id']}.jpg` | [{e['commons']}]({e['page']}) "
                     f"| {e['date']} | {e['license']} | {local_copy(e['id'])} |")
    CREDITS.write_text("\n".join(lines) + "\n")


def write_records(entries):
    for e in entries:
        e["copy"] = local_copy(e["id"])
    SOURCES.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")
    write_credits(entries)


def fill_from_fallback(all_cards, folder):
    """Fill missing raw scans from mariano-fu/arcana's resized copies of the same files
    (web/src/seed/images/cards/full/), named like major-00.webp and cups-13.webp."""
    for n, (card_id, _, title) in enumerate(all_cards):
        path = RAW_DIR / f"{card_id}.jpg"
        if path.exists():
            continue
        if n < 22:
            key = f"major-{n:02d}"
        else:
            suit = title.split(" - ")[1].split(" ")[0].lower()
            key = f"{suit}-{title.split(' ')[-1].split('.')[0]}"
        Image.open(Path(folder) / f"{key}.webp").convert("RGB").save(path, quality=92)
        print(f"{card_id}: filled from fallback {key}.webp")


def main():
    args = sys.argv[1:]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    all_cards = cards()
    info = {}
    for i in range(0, len(all_cards), 40):
        info.update(file_info([c[2] for c in all_cards[i:i + 40]]))
        time.sleep(2)

    # Check every card's source details before using any image.
    entries = []
    for card_id, name, title in all_cards:
        meta = info[title]
        verify(title, meta)
        meta["downloaded"] = thumb_url(meta["url"])
        entries.append({"id": card_id, "name": name, "commons": title.removeprefix("File:"), **meta})
    print(f"{len(entries)} cards verified on Commons")

    if "--fallback" in args:
        fill_from_fallback(all_cards, args[args.index("--fallback") + 1])
    if "--no-download" not in args:
        for e in entries:
            if local_copy(e["id"]) == "commons":
                continue
            data = get(e["downloaded"], binary=True)
            check_image(e["commons"], data, e)
            (RAW_DIR / f"{e['id']}.jpg").write_bytes(data)
            print(f"{e['id']}: downloaded", flush=True)
            write_records(entries)
            time.sleep(PAUSE)

    write_records(entries)
    counts = {k: sum(local_copy(e["id"]) == k for e in entries) for k in ("commons", "fallback", "missing")}
    print(f"wrote {SOURCES} and {CREDITS}: {counts}")


if __name__ == "__main__":
    main()
