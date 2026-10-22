"""Check every tarot card file against the content plan's rules.

Usage: python3 tools/check_cards.py
Exits with an error and a list of problems if any card breaks a rule.
"""
import sys
from collections import Counter
from pathlib import Path

import yaml

CARDS_DIR = Path("content/tarot/cards")
IMAGES_DIR = Path("content/tarot/images/cards")

SHORT_MAX = 140  # characters
MEANING_WORDS = (80, 130)
CAPTION_MAX = 1024  # Telegram photo caption limit
YES_NO = {"Yes", "No", "Maybe"}
REQUIRED = ["id", "name", "arcana", "image", "keywords", "short", "meaning", "in_context",
            "symbolism", "reflection", "yes_no", "correspondences", "waite_1910"]


def check(path, card):
    problems = []
    for field in REQUIRED:
        if field not in card:
            problems.append(f"missing field: {field}")
    if problems:
        return problems

    if card["id"] != path.stem:
        problems.append(f"id {card['id']!r} doesn't match file name")
    if not (IMAGES_DIR / card["image"]).exists():
        problems.append(f"image not found: {IMAGES_DIR / card['image']}")

    for side in ("upright", "reversed"):
        if len(card["keywords"][side]) != 5:
            problems.append(f"keywords.{side}: need 5, found {len(card['keywords'][side])}")
        if len(card["short"][side]) > SHORT_MAX:
            problems.append(f"short.{side}: {len(card['short'][side])} characters (max {SHORT_MAX})")
        words = len(card["meaning"][side].split())
        if not MEANING_WORDS[0] <= words <= MEANING_WORDS[1]:
            problems.append(f"meaning.{side}: {words} words (want {MEANING_WORDS[0]}-{MEANING_WORDS[1]})")
        if not card["waite_1910"].get(side):
            problems.append(f"waite_1910.{side} is empty")

    for key in ("love", "work", "advice"):
        line = card["in_context"].get(key, "")
        if not line:
            problems.append(f"in_context.{key} is empty")
        elif len(line) > SHORT_MAX:
            problems.append(f"in_context.{key}: {len(line)} characters (max {SHORT_MAX})")

    if not 4 <= len(card["symbolism"]) <= 6:
        problems.append(f"symbolism: need 4-6 items, found {len(card['symbolism'])}")
    if len(card["reflection"]) != 3:
        problems.append(f"reflection: need 3 questions, found {len(card['reflection'])}")
    if card["yes_no"] not in YES_NO:
        problems.append(f"yes_no must be one of {sorted(YES_NO)}")
    if card["arcana"] == "major" and "hebrew_letter" not in card["correspondences"]:
        problems.append("Major Arcana cards need correspondences.hebrew_letter")

    caption = "\n".join([card["name"], ", ".join(card["keywords"]["upright"]), card["short"]["upright"]])
    if len(caption) > CAPTION_MAX:
        problems.append(f"caption is {len(caption)} characters (Telegram max {CAPTION_MAX})")
    return problems


def main():
    cards = {}
    failed = False
    for path in sorted(CARDS_DIR.glob("*.yaml")):
        card = yaml.safe_load(path.read_text())
        cards[path.stem] = card
        for problem in check(path, card):
            print(f"{path.name}: {problem}")
            failed = True

    # Keywords repeated across many cards make the deck feel samey.
    counts = Counter(k for c in cards.values() for side in ("upright", "reversed")
                     for k in c.get("keywords", {}).get(side, []))
    for keyword, n in counts.items():
        if n > 3:
            print(f"keyword {keyword!r} is used {n} times (max 3)")
            failed = True

    print(f"{len(cards)} cards checked: {'problems found' if failed else 'all OK'}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
