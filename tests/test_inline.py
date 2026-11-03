"""Inline card search/sharing contracts; network calls use the fake API transport."""
import pytest


def test_empty_query_browses_all_cards_in_deck_order(deck):
    from bots.tarot.inline import search_cards
    cards = search_cards(deck, "  ")
    assert len(cards) == 78 and len({c.id for c in cards}) == 78
    assert cards[0].id == "major-00-the-fool"
    assert cards[22].id == "wands-01"
    assert cards[-1].id == "pentacles-king"


@pytest.mark.parametrize("query,card_id", [
    ("moon", "major-18-the-moon"),
    ("THE MOON", "major-18-the-moon"),
    ("3 cups", "cups-03"),
    ("queen of coins", "pentacles-queen"),
    ("III swords", "swords-03"),
    ("hanged", "major-12-the-hanged-man"),
    ("pope", "major-05-the-hierophant"),
    ("mooon", "major-18-the-moon"),
    ("XIII", "major-13-death"),
])
def test_card_names_aliases_and_typos_find_expected_card(deck, query, card_id):
    from bots.tarot.inline import search_cards
    assert search_cards(deck, query)[0].id == card_id


@pytest.mark.parametrize("query,prefix,count", [
    ("queen", "", 4), ("cups", "cups-", 14),
    ("chalices", "cups-", 14), ("major arcana", "major-", 22),
    ("major", "major-", 22), ("thr", "", 4),
])
def test_partial_rank_suit_or_group_query_returns_all_matches(deck, query, prefix, count):
    from bots.tarot.inline import search_cards
    cards = search_cards(deck, query)
    assert len(cards) == count
    assert all(c.id.startswith(prefix) for c in cards)
    if query == "queen":
        assert {c.id for c in cards} == {"wands-queen", "cups-queen", "swords-queen", "pentacles-queen"}


@pytest.mark.parametrize("query", ["spaceship", "💫", "!!!", "月", "the", "<script>"])
def test_unsupported_nonempty_query_is_not_an_unrelated_card_or_full_deck(deck, query):
    from bots.tarot.inline import search_cards
    assert search_cards(deck, query) == []


def test_pages_browse_every_card_once_without_truncating_at_telegram_limit(deck):
    from bots.tarot.inline import card_page
    offset, seen, sizes = "", [], []
    for want_offset in ["20", "40", "60", ""]:
        cards, offset = card_page(deck, "", offset)
        seen.extend(c.id for c in cards)
        sizes.append(len(cards))
        assert offset == want_offset
    assert sizes == [20, 20, 20, 18]
    assert len(seen) == len(set(seen)) == 78


@pytest.mark.parametrize("offset", ["-1", "abc", "1.0", "２０", "999", "9" * 5000, "1" * 65])
def test_invalid_or_out_of_bounds_offset_ends_safely(deck, offset):
    from bots.tarot.inline import card_page
    assert card_page(deck, "", offset) == ([], "")


def test_single_match_has_no_next_page(deck):
    from bots.tarot.inline import card_page
    cards, offset = card_page(deck, "moon", "")
    assert [c.id for c in cards] == ["major-18-the-moon"]
    assert offset == ""
