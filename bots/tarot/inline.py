"""Public, read-only inline card discovery and Telegram photo results."""
import re
from typing import Any
from urllib.parse import quote

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedPhoto,
                      InlineQueryResultPhoto, Update)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from . import render

from .cards import Card, Deck, RANKS, ROMAN, SUIT_ALIASES, SUITS, _words

PAGE_SIZE = 20
# Immutable public artwork: no bot-token URLs, live uploads or owner-chat prewarming.
ARTWORK_BASE = ("https://raw.githubusercontent.com/Nostem/Claude-Telegram-Bots/"
                "71c782a1ddee56ee8e60c756d09f9e45dc31444a/content/tarot/images/cards/")


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
    if len(words) == 1 and (words[0].isascii() and words[0].isdigit() or words[0] in ROMAN):
        numbered_major = deck.find(query)
        if numbered_major:
            matches = [numbered_major, *[card for card in matches if card != numbered_major]]
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


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answer even empty searches; selecting a result sends the photo, never a DM."""
    query = update.inline_query
    assert query is not None  # Only registered for InlineQuery updates.
    services = context.bot_data
    cards, next_offset = card_page(services["deck"], query.query, query.offset)
    results = []
    for card in cards:
        link = f"https://t.me/{context.bot.username}?start=card_{card.id}"
        common: dict[str, Any] = dict(
            id=card.id, title=card.name,
            description=", ".join(card.data["keywords"]["upright"]),
            caption=render.caption(card, False), parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                "Open full interpretation", url=link)]]),
        )
        key = f"{card.data['image']}:{card.image_path.stat().st_size}:upright"
        file_id = services["db"].get_file_id(key)
        if file_id:
            result = InlineQueryResultCachedPhoto(photo_file_id=file_id, **common)
        else:
            url = ARTWORK_BASE + quote(card.data["image"], safe="")
            result = InlineQueryResultPhoto(photo_url=url, thumbnail_url=url, **common)
        results.append(result)
    # Photo results give Telegram its gallery-style picker. Public card content is
    # identical for everyone; sharing this short cache never exposes user data.
    await query.answer(results, cache_time=60, is_personal=False, next_offset=next_offset)
