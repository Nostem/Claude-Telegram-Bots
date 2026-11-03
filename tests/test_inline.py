"""Inline card search/sharing contracts; network calls use the fake API transport."""
from html import unescape
import re
from urllib.parse import urlparse, parse_qs

import pytest

from bots.engine.config import Settings
from bots.engine.db import Database
from bots.tarot.bot import build_application
from tests.fake_telegram import FakeTelegram, Updates, USER_ID


@pytest.fixture
async def inline_bot():
    fake = FakeTelegram()
    db = Database(":memory:")
    app = build_application(Settings(token="123:abc", db_path=":memory:",
                            admin_chat_id=None, admin_user_ids=set(), lifetime_stars=1650),
                            db=db, request=fake)
    await app.initialize()
    yield app, fake, Updates(app.bot), db
    await app.shutdown()
    db.conn.close()



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
    ("prince of cups", "cups-knight"),
    ("princess of cups", "cups-page"),
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


@pytest.mark.parametrize("offset", ["-1", "abc", "1.0", "２０", "999", "9" * 5000, "1" * 65],
                         ids=["negative", "letters", "float", "unicode", "beyond-end", "huge", "too-long"])
def test_invalid_or_out_of_bounds_offset_ends_safely(deck, offset):
    from bots.tarot.inline import card_page
    assert card_page(deck, "", offset) == ([], "")


@pytest.mark.parametrize("query", ["3", "III"])
def test_exact_major_numeral_is_ranked_before_other_rank_matches(deck, query):
    from bots.tarot.inline import search_cards
    cards = search_cards(deck, query)
    assert cards[0].id == "major-03-the-empress"
    assert {c.id for c in cards[1:]} == {"wands-03", "cups-03", "swords-03", "pentacles-03"}


def test_single_match_has_no_next_page(deck):
    from bots.tarot.inline import card_page
    cards, offset = card_page(deck, "moon", "")
    assert [c.id for c in cards] == ["major-18-the-moon"]
    assert offset == ""


async def test_registered_inline_search_answers_without_user_records_or_messages(inline_bot):
    app, fake, updates, db = inline_bot
    await app.process_update(updates.inline("moon"))
    assert fake.methods().count("answerInlineQuery") == 1
    answer = fake.last("answerInlineQuery")
    assert answer["results"][0]["title"] == "The Moon"
    assert answer["next_offset"] == ""
    assert answer["cache_time"] == 60 and answer["is_personal"] is False
    assert set(fake.methods()) <= {"getMe", "answerInlineQuery"}
    assert db.one("SELECT COUNT(*) FROM users")[0] == 0
    assert db.one("SELECT COUNT(*) FROM draws")[0] == 0
    assert db.one("SELECT COUNT(*) FROM schedules")[0] == 0


async def test_uncached_inline_photo_is_sendable_with_caption_and_safe_private_link(inline_bot):
    app, fake, updates, db = inline_bot
    await app.process_update(updates.inline("moon"))
    result = fake.last("answerInlineQuery")["results"][0]
    assert result["type"] == "photo"
    assert result["photo_url"] == ("https://raw.githubusercontent.com/Nostem/Claude-Telegram-Bots/"
        "71c782a1ddee56ee8e60c756d09f9e45dc31444a/content/tarot/images/cards/major-18-the-moon.jpg")
    assert result["thumbnail_url"] == result["photo_url"]
    assert result["parse_mode"] == "HTML"
    assert "<b>The Moon</b>" in result["caption"]
    assert "<i>" in result["caption"] and len(result["caption"]) < 1024
    button = result["reply_markup"]["inline_keyboard"][0][0]
    assert button == {"text": "Open full interpretation", "url":
                      "https://t.me/tarot_test_bot?start=card_major-18-the-moon"}
    assert "callback_data" not in button


async def test_cached_inline_photo_uses_upright_art_not_reversed_art(inline_bot):
    app, fake, updates, db = inline_bot
    card = app.bot_data["deck"]["major-18-the-moon"]
    size = card.image_path.stat().st_size
    db.set_file_id(f"{card.data['image']}:{size}:upright", "saved-upright-photo")
    db.set_file_id(f"{card.data['image']}:{size}:reversed", "saved-reversed-photo")
    await app.process_update(updates.inline("moon"))
    result = fake.last("answerInlineQuery")["results"][0]
    assert result["photo_file_id"] == "saved-upright-photo"
    assert "photo_url" not in result
    assert result["reply_markup"]["inline_keyboard"][0][0]["url"].endswith("card_major-18-the-moon")
    assert "sendPhoto" not in fake.methods()


async def test_inline_browse_pages_all_78_sendable_cards(inline_bot):
    app, fake, updates, db = inline_bot
    offset, seen = "", []
    for expected_size in (20, 20, 20, 18):
        await app.process_update(updates.inline("", offset))
        answer = fake.last("answerInlineQuery")
        results = answer["results"]
        assert len(results) == expected_size
        seen.extend(r["id"] for r in results)
        for result in results:
            assert 1 <= len(result["id"].encode()) <= 64
            caption = unescape(re.sub(r"<[^>]+>", "", result["caption"]))
            assert len(caption) <= 1024
            assert result["photo_url"].endswith(".jpg")
            url = result["reply_markup"]["inline_keyboard"][0][0]["url"]
            payload = parse_qs(urlparse(url).query)["start"][0]
            assert len(payload) <= 64 and re.fullmatch(r"[A-Za-z0-9_-]+", payload)
            assert payload.removeprefix("card_") in app.bot_data["deck"].cards
        offset = answer["next_offset"]
    assert offset == "" and len(seen) == len(set(seen)) == 78
    assert set(fake.methods()) <= {"getMe", "answerInlineQuery"}


@pytest.mark.parametrize("query,offset", [("spaceship", ""), ("!!!", ""), ("", "bad"), ("moon", "20")])
async def test_inline_no_match_and_bad_offsets_always_answer_empty(inline_bot, query, offset):
    app, fake, updates, db = inline_bot
    await app.process_update(updates.inline(query, offset))
    assert fake.methods().count("answerInlineQuery") == 1
    answer = fake.last("answerInlineQuery")
    assert answer["results"] == [] and answer["next_offset"] == ""


@pytest.mark.parametrize("query,expected_ids", [
    ("queen of co", {"pentacles-queen"}),
    ("queen of coi", {"pentacles-queen"}),
    ("chal", {"cups-01", "cups-02", "cups-03", "cups-04", "cups-05", "cups-06", "cups-07",
              "cups-08", "cups-09", "cups-10", "cups-page", "cups-knight", "cups-queen", "cups-king"}),
    ("prin", {"wands-page", "cups-page", "swords-page", "pentacles-page",
              "wands-knight", "cups-knight", "swords-knight", "pentacles-knight"}),
    ("fort", {"major-08-strength", "major-10-wheel-of-fortune"}),
    ("last judg", {"major-20-judgement"}),
])
async def test_partial_aliases_return_all_relevant_inline_results_before_fuzzy_fallback(
        inline_bot, query, expected_ids):
    app, fake, updates, db = inline_bot
    await app.process_update(updates.inline(query))
    results = fake.last("answerInlineQuery")["results"]
    assert {r["id"] for r in results} == expected_ids
    assert len(results) == len(expected_ids)
    assert set(fake.methods()) <= {"getMe", "answerInlineQuery"}


async def test_repeated_inline_search_has_stable_ids_and_preserves_private_prompt(inline_bot):
    app, fake, updates, db = inline_bot
    app.user_data[USER_ID]["awaiting"] = {"type": "feedback", "kind": "payment"}
    await app.process_update(updates.inline("moon"))
    first_id = fake.last("answerInlineQuery")["results"][0]["id"]
    await app.process_update(updates.inline("THE MOON"))
    assert fake.last("answerInlineQuery")["results"][0]["id"] == first_id
    assert app.user_data[USER_ID]["awaiting"] == {"type": "feedback", "kind": "payment"}


@pytest.mark.parametrize("onboarded", [False, True])
async def test_card_deep_link_shows_full_meaning_without_onboarding_or_draw(inline_bot, onboarded):
    app, fake, updates, db = inline_bot
    if onboarded:
        db.get_user(USER_ID)
        db.update_user(USER_ID, onboarded=1, timezone="America/New_York", reversals=0)
    app.user_data[USER_ID]["awaiting"] = {"type": "time"}
    await app.process_update(updates.message("/start card_major-18-the-moon"))
    assert "The Moon" in fake.last("sendPhoto")["caption"]
    meaning = fake.last("sendMessage")["text"]
    assert "Symbolism" in meaning and "To reflect on" in meaning
    assert db.one("SELECT COUNT(*) FROM draws")[0] == 0
    assert db.one("SELECT COUNT(*) FROM schedules")[0] == 0
    user = db.one("SELECT * FROM users WHERE id=?", (USER_ID,))
    assert bool(user["onboarded"]) is onboarded
    assert user["timezone"] == ("America/New_York" if onboarded else None)
    assert app.user_data[USER_ID]["awaiting"] == {"type": "time"}
    assert "flow" not in app.user_data[USER_ID]


@pytest.mark.parametrize("payload", ["card_", "card_not-a-card", "card_major-18-the-moon extra",
                                     "card_../major-18-the-moon"])
async def test_invalid_card_deep_link_does_not_onboard_or_send_wrong_card(inline_bot, payload):
    app, fake, updates, db = inline_bot
    await app.process_update(updates.message("/start " + payload))
    assert "sendPhoto" not in fake.methods()
    assert "card" in fake.last("sendMessage")["text"].lower()
    assert "awaiting" not in app.user_data[USER_ID]
    assert "flow" not in app.user_data[USER_ID]


async def test_ordinary_start_still_runs_onboarding(inline_bot):
    app, fake, updates, db = inline_bot
    await app.process_update(updates.message("/start"))
    assert app.user_data[USER_ID]["flow"] == "onboard"
    assert app.user_data[USER_ID]["awaiting"]["type"] == "timezone"
