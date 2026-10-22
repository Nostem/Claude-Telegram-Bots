"""The 78-card deck: loading the card files and finding cards by what people type."""
import difflib
import random
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CARDS_DIR = ROOT / "content" / "tarot" / "cards"
IMAGES_DIR = ROOT / "content" / "tarot" / "images" / "cards"

SUITS = ["wands", "cups", "swords", "pentacles"]
SUIT_ALIASES = {
    "wand": "wands", "rods": "wands", "rod": "wands", "staves": "wands", "staff": "wands",
    "batons": "wands", "clubs": "wands",
    "cup": "cups", "chalices": "cups", "chalice": "cups", "hearts": "cups",
    "sword": "swords", "blades": "swords", "spades": "swords",
    "pentacle": "pentacles", "coins": "pentacles", "coin": "pentacles", "disks": "pentacles",
    "discs": "pentacles", "diamonds": "pentacles",
}
RANKS = {
    "ace": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10,
    "page": "page", "princess": "page", "knave": "page", "jack": "page",
    "knight": "knight", "prince": "knight",
    "queen": "queen", "king": "king",
}
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10,
         "xi": 11, "xii": 12, "xiii": 13, "xiv": 14, "xv": 15, "xvi": 16, "xvii": 17, "xviii": 18,
         "xix": 19, "xx": 20, "xxi": 21}
# Other names people use for some Major Arcana.
MAJOR_ALIASES = {"judgment": 20, "last judgment": 20, "fortitude": 8, "wheel": 10,
                 "fortune": 10, "hanged": 12, "priestess": 2, "pope": 5}
FILLER = {"the", "of", "card", "tarot", "reversed", "upright"}


@dataclass(frozen=True)
class Card:
    id: str
    name: str
    arcana: str
    data: dict

    @property
    def suit(self):
        return self.data.get("suit")

    @property
    def image_path(self):
        return IMAGES_DIR / self.data["image"]


def _words(text):
    return [w for w in re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split() if w not in FILLER]


class Deck:
    def __init__(self, cards_dir=CARDS_DIR):
        self.cards = {}
        for path in sorted(cards_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text())
            self.cards[data["id"]] = Card(data["id"], data["name"], data["arcana"], data)
        self._majors = {c.data["number"]: c for c in self.cards.values() if c.arcana == "major"}
        self._names = {" ".join(_words(c.name)): c for c in self.cards.values()}

    def __len__(self):
        return len(self.cards)

    def __getitem__(self, card_id):
        return self.cards[card_id]

    def in_group(self, group):
        """Cards in browsing order: 'major' or a suit name."""
        if group == "major":
            return [self._majors[n] for n in sorted(self._majors)]
        order = [f"{group}-{n:02d}" for n in range(1, 11)] + [
            f"{group}-{c}" for c in ("page", "knight", "queen", "king")]
        return [self.cards[i] for i in order]

    def find(self, query):
        """The card someone means, or None. Handles '3 cups', 'three of cups', 'III swords',
        'queen of coins', 'hanged man', 'XIII', 'death' and small typos."""
        words = _words(query)
        if not words:
            return None
        text = " ".join(words)
        if text in self._names:
            return self._names[text]
        if text in MAJOR_ALIASES:
            return self._majors[MAJOR_ALIASES[text]]

        suit = next((SUIT_ALIASES.get(w, w) for w in words if SUIT_ALIASES.get(w, w) in SUITS), None)
        rank, numeral = None, False
        for w in words:
            if w in RANKS:
                rank = RANKS[w]
            elif w.isdigit():
                rank, numeral = int(w), True
            elif w in ROMAN:
                rank, numeral = ROMAN[w], True
        if suit and rank is not None:
            card_id = f"{suit}-{rank:02d}" if isinstance(rank, int) else f"{suit}-{rank}"
            return self.cards.get(card_id)
        if not suit and numeral and len(words) == 1:
            return self._majors.get(rank)    # '13' or 'XIII' -> Death

        for alias, number in MAJOR_ALIASES.items():
            if alias in text:
                return self._majors[number]
        close = difflib.get_close_matches(text, self._names, n=1, cutoff=0.75)
        return self._names[close[0]] if close else None

    def draw(self, count, reversals, rng=None):
        """count distinct cards as (card_id, reversed) pairs."""
        rng = rng or random.SystemRandom()
        picks = rng.sample(sorted(self.cards), count)
        return [(card_id, reversals and rng.random() < REVERSAL_CHANCE) for card_id in picks]


REVERSAL_CHANCE = 0.5  # a well-shuffled physical deck turns up about half its cards reversed
