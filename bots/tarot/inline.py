"""Public, read-only inline card discovery and Telegram photo results."""
import re

from .cards import Card, Deck, RANKS, ROMAN, SUIT_ALIASES, SUITS, _words

PAGE_SIZE = 20


def _canonical(word: str) -> str:
    return str(SUIT_ALIASES.get(word, RANKS.get(word, ROMAN.get(word, word))))


def search_cards(deck: Deck, query: str) -> list[Card]:
    """Find every matching card in stable deck order; fuzzy lookup is a fallback."""
    ordered = [card for group in ('major', *SUITS) for card in deck.in_group(group)]
    if not query.strip():
        return ordered
    words = _words(query)
    if not words:
        return []
    if words in (["major"], ["major", "arcana"], ["arcana"]):
        return deck.in_group('major')

    matches = []
    for card in ordered:
        name = _words(card.name)
        if all(any(w.startswith(q) or _canonical(w) == _canonical(q) for w in name)
               for q in words):
            matches.append(card)
    if matches:
        return matches
    closest = deck.find(query)
    return [closest] if closest else []


def card_page(deck: Deck, query: str, offset: str) -> tuple[list[Card], str]:
    """Telegram offsets are untrusted strings; invalid pages terminate pagination."""
    if offset and not re.fullmatch(r"[0-9]{1,3}", offset):
        return [], ""
    start = int(offset or '0')
    cards = search_cards(deck, query)
    page = cards[start:start + PAGE_SIZE]
    end = start + len(page)
    return page, str(end) if page and end < len(cards) else ""
