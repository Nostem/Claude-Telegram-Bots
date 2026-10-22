import random

import pytest

from bots.tarot import render


def test_deck_has_78_cards_with_images(deck):
    assert len(deck) == 78
    for card in deck.cards.values():
        assert card.image_path.exists(), card.id


@pytest.mark.parametrize("query, expected", [
    ("the fool", "major-00-the-fool"),
    ("Fool", "major-00-the-fool"),
    ("hanged man", "major-12-the-hanged-man"),
    ("XIII", "major-13-death"),
    ("13", "major-13-death"),
    ("death", "major-13-death"),
    ("judgment", "major-20-judgement"),
    ("wheel", "major-10-wheel-of-fortune"),
    ("3 cups", "cups-03"),
    ("three of cups", "cups-03"),
    ("III swords", "swords-03"),
    ("ace of wands", "wands-01"),
    ("10 of pentacles", "pentacles-10"),
    ("queen of coins", "pentacles-queen"),
    ("Knight Cups", "cups-knight"),
    ("page of rods", "wands-page"),
    ("the empres", "major-03-the-empress"),   # typo
    ("high priestess", "major-02-the-high-priestess"),
])
def test_find(deck, query, expected):
    assert deck.find(query).id == expected


@pytest.mark.parametrize("query", ["", "hello there", "ace", "queen"])
def test_find_nothing(deck, query):
    assert deck.find(query) is None


def test_every_card_finds_itself_by_name(deck):
    for card in deck.cards.values():
        assert deck.find(card.name) is card


def test_draw_is_distinct_and_respects_reversal_setting(deck):
    rng = random.Random(1)
    cards = deck.draw(5, reversals=False, rng=rng)
    assert len({c for c, _ in cards}) == 5
    assert not any(r for _, r in cards)


def test_captions_fit_telegram_limits(deck):
    for card in deck.cards.values():
        for rev in (False, True):
            assert len(render.caption(card, rev, heading="Your card for today")) <= 1024
            assert len(render.full_text(card, rev)) <= 4096
        assert len(render.waite_text(card)) <= 4096
