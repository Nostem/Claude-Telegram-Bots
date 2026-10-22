"""Whole conversations, run against a fake Telegram API."""
from datetime import timedelta

import pytest

from bots.engine import handlers as engine
from bots.engine.config import Settings
from bots.engine.db import Database, utcnow
from bots.tarot.bot import build_application, send_scheduled
from tests.fake_telegram import ADMIN_CHAT, USER_ID, FakeTelegram, Updates

ADMIN_USER = 222


@pytest.fixture
async def bot():
    fake = FakeTelegram()
    db = Database(":memory:")
    settings = Settings(token="123:abc", db_path=":memory:", admin_chat_id=ADMIN_CHAT,
                        admin_user_ids={ADMIN_USER}, lifetime_stars=750)
    app = build_application(settings, db=db, request=fake)
    await app.initialize()
    updates = Updates(app.bot)

    async def send(update):
        await app.process_update(update)

    yield app, fake, updates, send, db
    await app.shutdown()


async def onboard(send, updates, zone="Europe/London", reversals="1", daily="07:00"):
    await send(updates.message("/start"))
    await send(updates.callback(f"tz:{zone}"))
    await send(updates.callback(f"rev:{reversals}"))
    await send(updates.callback(f"dt:{daily}"))


async def test_onboarding_sets_everything_up_and_sends_first_card(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates)
    user = db.get_user(USER_ID)
    assert user["onboarded"] and user["timezone"] == "Europe/London" and user["reversals"] == 1
    assert app.bot_data["schedules"].for_user(USER_ID, "daily")[0]["time_local"] == "07:00"
    assert "Your card for today" in fake.last("sendPhoto")["caption"]
    assert db.count_draws(USER_ID) == 1


async def test_onboarding_with_typed_city_and_typed_time(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/start"))
    await send(updates.message("Toronto"))
    assert db.get_user(USER_ID)["timezone"] == "America/Toronto"
    await send(updates.callback("rev:0"))
    await send(updates.callback("dt:other"))
    await send(updates.message("7.30pm"))
    assert app.bot_data["schedules"].for_user(USER_ID, "daily")[0]["time_local"] == "19:30"
    assert db.get_user(USER_ID)["onboarded"]


async def test_unknown_city_asks_again(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/start"))
    await send(updates.message("Atlantis Underwater"))
    assert "couldn't find that place" in fake.texts()[-1]
    assert db.get_user(USER_ID)["timezone"] is None


async def test_daily_repeats_the_same_card(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates)
    first = fake.last("sendPhoto")
    await send(updates.message("/daily"))
    again = fake.last("sendPhoto")
    assert "already drawn" in again["caption"]
    assert first["caption"].split("\n")[1] == again["caption"].split("\n")[1]


async def test_card_lookup_caches_the_uploaded_image(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/card three of cups"))
    first = fake.last("sendPhoto")
    assert "Three of Cups" in first["caption"]
    assert "photo" not in first                          # uploaded as a file, not an id
    await send(updates.message("3 cups"))                # plain text works too
    assert isinstance(fake.last("sendPhoto")["photo"], str)  # reused Telegram's file_id


async def test_card_lookup_not_found(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/card the spaceship"))
    assert "couldn't find that card" in fake.texts()[-1]


async def test_more_and_waite_views(bot):
    app, fake, updates, send, db = bot
    await send(updates.callback("more:major-13-death:0"))
    text = fake.last("sendMessage")["text"]
    assert "almost never about physical death" in text and "Symbolism" in text
    assert "reply_markup" not in fake.last("sendMessage")   # no Report button for free users
    await send(updates.callback("waite:major-13-death"))
    assert "Waite's meanings (1910)" in fake.last("sendMessage")["text"]


async def test_browse_and_back(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/cards"))
    await send(updates.callback("browse:cups"))
    assert "Cups" in fake.last("editMessageText")["text"]
    await send(updates.callback("browse:back"))
    await send(updates.callback("show:cups-queen"))
    assert "Queen of Cups" in fake.last("sendPhoto")["caption"]


async def test_free_journal_shows_lock_for_older_draws(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates, zone="UTC")
    for days_ago in range(1, 10):
        day = (utcnow() - timedelta(days=days_ago)).date().isoformat()
        db.add_draw(USER_ID, day, "daily", [("major-00-the-fool", False)])
    await send(updates.message("/journal"))
    text = fake.last("sendMessage")["text"]
    assert "last 7 days" in text and "3 older draws are saved" in text


async def test_schedule_pause_resume_and_turn_off(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates)
    sid = app.bot_data["schedules"].for_user(USER_ID, "daily")[0]["id"]
    await send(updates.callback(f"sp:{sid}:1"))
    assert app.bot_data["schedules"].for_user(USER_ID, "daily")[0]["paused"] == 1
    await send(updates.callback(f"sp:{sid}:0"))
    assert app.bot_data["schedules"].for_user(USER_ID, "daily")[0]["paused"] == 0
    await send(updates.callback(f"sd:{sid}"))
    assert app.bot_data["schedules"].for_user(USER_ID, "daily") == []


async def test_cannot_touch_someone_elses_schedule(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates)
    sid = app.bot_data["schedules"].for_user(USER_ID, "daily")[0]["id"]
    await send(updates.callback(f"sd:{sid}", user_id=333))
    assert app.bot_data["schedules"].for_user(USER_ID, "daily")


async def test_settings_toggle_reversals(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates)
    await send(updates.message("/settings"))
    assert "Reversed cards: on" in fake.last("sendMessage")["text"]
    await send(updates.callback("rev:0"))
    assert db.get_user(USER_ID)["reversals"] == 0


async def test_scheduler_sends_due_daily_card(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates, zone="UTC")
    tomorrow = utcnow() + timedelta(days=1, hours=1)
    sent_before = fake.methods().count("sendPhoto")
    await engine.scheduler_tick(app, send_scheduled, tomorrow)
    assert fake.methods().count("sendPhoto") == sent_before + 1
    await engine.scheduler_tick(app, send_scheduled, tomorrow)      # not sent twice
    assert fake.methods().count("sendPhoto") == sent_before + 1


async def test_scheduler_pauses_when_user_blocked_the_bot(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates, zone="UTC")
    fake.fail_for.add(USER_ID)
    await engine.scheduler_tick(app, send_scheduled, utcnow() + timedelta(days=1, hours=1))
    assert app.bot_data["schedules"].for_user(USER_ID, "daily")[0]["paused"] == 1


async def test_free_feedback_is_bug_report_forwarded_without_identity(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/feedback"))
    assert "What went wrong" in fake.last("sendMessage")["text"]
    await send(updates.message("The daily card didn't arrive"))
    header = next(p["text"] for n, p in fake.calls if n == "sendMessage" and p["chat_id"] == ADMIN_CHAT)
    assert header.startswith("#bug") and "free user" in header and "Test" not in header
    copy = fake.last("copyMessage")
    assert copy["chat_id"] == ADMIN_CHAT and copy["from_chat_id"] == USER_ID
    assert "we read every one" in fake.last("sendMessage")["text"]


async def test_free_user_cannot_send_ideas(bot):
    app, fake, updates, send, db = bot
    await send(updates.callback("fb:idea"))
    assert "part of Lifetime" in fake.last("sendMessage")["text"]


async def test_owner_reply_and_done_reach_the_user(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/feedback"))
    await send(updates.message("Typo on the Moon card"))
    header_id = db.one("SELECT admin_message_id FROM feedback_messages ORDER BY admin_message_id")[0]
    await send(updates.message("Thanks, fixing it!", user_id=ADMIN_USER, chat_id=ADMIN_CHAT,
                               reply_to=header_id))
    relay = fake.last("copyMessage")
    assert relay["chat_id"] == USER_ID and relay["from_chat_id"] == ADMIN_CHAT
    await send(updates.message("/done", user_id=ADMIN_USER, chat_id=ADMIN_CHAT, reply_to=header_id))
    to_user = [p for n, p in fake.calls if n == "sendMessage" and p["chat_id"] == USER_ID]
    assert "It's done now" in to_user[-1]["text"]
    assert db.one("SELECT status FROM feedback")[0] == "done"


async def test_purchase_unlocks_lifetime_and_report_button(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/upgrade"))
    invoice = fake.last("sendInvoice")
    assert invoice["currency"] == "XTR" and invoice["prices"][0]["amount"] == 750
    await send(updates.pre_checkout())
    assert fake.last("answerPreCheckoutQuery")["ok"] is True
    await send(updates.payment())
    assert db.get_user(USER_ID)["lifetime_at"]
    await send(updates.callback("more:cups-queen:0"))
    assert "report:cups-queen" in str(fake.last("sendMessage")["reply_markup"])
    await send(updates.pre_checkout())                    # can't buy twice
    assert fake.last("answerPreCheckoutQuery")["ok"] is False


async def test_lifetime_feedback_menu_and_card_report(bot):
    app, fake, updates, send, db = bot
    await send(updates.payment())
    await send(updates.message("/feedback"))
    assert "fb:idea" in str(fake.last("sendMessage")["reply_markup"])
    await send(updates.callback("report:cups-queen"))
    await send(updates.message("The symbolism mentions the wrong cup"))
    row = db.one("SELECT kind, card_id FROM feedback")
    assert (row["kind"], row["card_id"]) == ("card", "cups-queen")


async def test_refund_by_owner_only(bot):
    app, fake, updates, send, db = bot
    await send(updates.payment(charge="ch-1"))
    await send(updates.message(f"/refund {USER_ID}", user_id=333))   # not an owner
    assert "refundStarPayment" not in fake.methods()
    await send(updates.message(f"/refund {USER_ID}", user_id=ADMIN_USER, chat_id=ADMIN_USER))
    assert fake.last("refundStarPayment") == {"user_id": USER_ID, "telegram_payment_charge_id": "ch-1"}
    assert db.get_user(USER_ID)["lifetime_at"] is None


async def test_delete_my_data_keeps_lifetime(bot):
    app, fake, updates, send, db = bot
    await onboard(send, updates)
    await send(updates.payment())
    await send(updates.message("/delete_my_data"))
    await send(updates.callback("del:yes"))
    user = db.get_user(USER_ID)
    assert not user["onboarded"] and user["timezone"] is None and user["lifetime_at"]
    assert db.count_draws(USER_ID) == 0
    assert app.bot_data["schedules"].for_user(USER_ID) == []


async def test_cancel_closes_an_open_question(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/feedback"))
    await send(updates.message("/cancel"))
    await send(updates.message("the tower"))
    assert "The Tower" in fake.last("sendPhoto")["caption"]
    assert db.one("SELECT COUNT(*) FROM feedback")[0] == 0


async def test_myid_shows_ids_for_setup(bot):
    app, fake, updates, send, db = bot
    await send(updates.message("/myid", user_id=ADMIN_USER, chat_id=ADMIN_CHAT))
    text = fake.last("sendMessage")["text"]
    assert str(ADMIN_USER) in text and str(ADMIN_CHAT) in text
