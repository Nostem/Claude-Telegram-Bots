from datetime import datetime, timedelta, timezone

import pytest

from bots.engine.feedback import DAILY_LIMIT, Feedback
from bots.engine.payments import Payments
from bots.engine.schedules import Schedules, next_run, parse_time
from bots.engine.timezones import find_timezones


@pytest.mark.parametrize("text, expected", [
    ("7", "07:00"), ("07:30", "07:30"), ("7.30pm", "19:30"), ("12am", "00:00"),
    ("12 pm", "12:00"), ("23:59", "23:59"), ("24:00", None), ("13pm", None), ("soon", None),
])
def test_parse_time(text, expected):
    assert parse_time(text) == expected


def test_next_run_same_day_and_next_day():
    after = datetime(2026, 3, 10, 6, 0, tzinfo=timezone.utc)
    assert next_run("07:00", "0123456", "UTC", after) == after.replace(hour=7)
    assert next_run("05:00", "0123456", "UTC", after) == datetime(2026, 3, 11, 5, tzinfo=timezone.utc)


def test_next_run_follows_daylight_saving():
    # New York moves from UTC-5 to UTC-4 on 8 March 2026.
    before = next_run("07:00", "0123456", "America/New_York", datetime(2026, 3, 7, 0, tzinfo=timezone.utc))
    after = next_run("07:00", "0123456", "America/New_York", datetime(2026, 3, 9, 0, tzinfo=timezone.utc))
    assert before.hour == 12 and after.hour == 11


def test_next_run_skips_days_not_selected():
    monday = datetime(2026, 3, 9, 12, tzinfo=timezone.utc)   # a Monday
    assert next_run("09:00", "6", "UTC", monday).weekday() == 6   # Sunday only


def test_schedule_lifecycle(db, now):
    db.get_user(1)
    db.update_user(1, timezone="Europe/London")
    schedules = Schedules(db)
    schedules.set_daily(1, "07:00", "Europe/London", now)
    assert schedules.due(now) == []
    later = now + timedelta(days=1)
    [due] = schedules.due(later)
    schedules.mark_run(due, later)
    assert schedules.due(later) == []
    schedules.set_paused(due["id"], True, "Europe/London", later)
    assert schedules.due(later + timedelta(days=3)) == []


@pytest.mark.parametrize("query, expected", [
    ("London", "Europe/London"), ("new york", "America/New_York"), ("PST", "America/Los_Angeles"),
    ("Europe/Paris", "Europe/Paris"), ("tokyo", "Asia/Tokyo"), ("Sao Paulo", "America/Sao_Paulo"),
])
def test_find_timezones(query, expected):
    assert find_timezones(query)[0] == expected


def test_find_timezones_nothing():
    assert find_timezones("zzzz") == []


def test_feedback_limit_and_permissions(db, now):
    fb = Feedback(db)
    assert fb.allowed("bug", lifetime=False)
    assert not fb.allowed("idea", lifetime=False)
    assert fb.allowed("idea", lifetime=True)
    for _ in range(DAILY_LIMIT):
        assert fb.can_send(1, now)
        fb.record(1, "bug", "it broke", now)
    assert not fb.can_send(1, now)
    assert fb.can_send(1, now + timedelta(days=1, seconds=1))


def test_feedback_admin_message_link(db, now):
    fb = Feedback(db)
    fid = fb.record(1, "idea", "more spreads", now)
    fb.link_admin_message(555, fid)
    assert fb.for_admin_message(555)["text"] == "more spreads"
    fb.set_status(fid, "done")
    assert fb.for_admin_message(555)["status"] == "done"


def test_payments_and_refund_window(db, now):
    db.get_user(1)
    pay = Payments(db)
    pay.record("charge-1", 1, 750, now)
    assert pay.is_lifetime(db.get_user(1))
    payment = pay.find("1")
    assert payment["charge_id"] == "charge-1"
    assert pay.within_refund_window(payment, now + timedelta(days=7))
    assert not pay.within_refund_window(payment, now + timedelta(days=8))
    pay.mark_refunded(payment, now)
    assert not pay.is_lifetime(db.get_user(1))


def test_checkin_due_after_two_weeks(db, now):
    db.get_user(1)
    Payments(db).record("c", 1, 750, now)
    assert Payments(db).due_checkins(now + timedelta(days=13)) == []
    assert len(Payments(db).due_checkins(now + timedelta(days=14))) == 1


def test_delete_user_removes_everything(db, now):
    db.get_user(1)
    db.add_draw(1, "2026-03-10", "daily", [("major-00-the-fool", False)])
    Schedules(db).set_daily(1, "07:00", "UTC", now)
    Feedback(db).record(1, "bug", "x", now)
    db.delete_user(1)
    for table in ("users", "draws", "draw_cards", "schedules", "feedback"):
        assert db.one(f"SELECT COUNT(*) FROM {table}")[0] == 0
