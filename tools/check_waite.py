"""Check every card's waite_1910 quotes against Waite's text.

Project Gutenberg doesn't have Waite's own edition, so this uses #43548: L. W. De
Laurence's 1918 "Illustrated Key to the Tarot", which reprints Waite's meanings word for
word but with American spelling. The comparison ignores punctuation and spelling
differences such as honour/honor, shews/shows and defence/defense.

Usage: python3 tools/check_waite.py
"""
import re
import sys
import urllib.request
from pathlib import Path

import yaml

CARDS_DIR = Path("content/tarot/cards")
BOOK_URL = "https://www.gutenberg.org/cache/epub/43548/pg43548.txt"
BOOK_CACHE = Path(".cache/pg43548.txt")


def normalize(text):
    text = text.lower().replace("our", "or").replace("shews", "shows").replace("defence", "defense")
    text = text.replace("-", "")
    return re.sub(r"[^a-z]", "", text)


def main():
    if not BOOK_CACHE.exists():
        BOOK_CACHE.parent.mkdir(exist_ok=True)
        req = urllib.request.Request(BOOK_URL, headers={"User-Agent": "TarotBotContent/0.1"})
        BOOK_CACHE.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    book = normalize(BOOK_CACHE.read_text(encoding="utf-8"))

    problems = 0
    cards = sorted(CARDS_DIR.glob("*.yaml"))
    for path in cards:
        card = yaml.safe_load(path.read_text())
        for side in ("upright", "reversed"):
            if normalize(card["waite_1910"][side]) not in book:
                print(f"{path.name}: waite_1910.{side} not found in the book text")
                problems += 1
    print(f"{len(cards)} cards checked: {'problems found' if problems else 'all quotes match'}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
