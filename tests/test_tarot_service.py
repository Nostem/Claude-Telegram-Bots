from datetime import timedelta

from bots.tarot.service import Tarot


def setup_user(db, tz="America/Los_Angeles"):
    db.get_user(1)
    db.update_user(1, timezone=tz)
    return db.get_user(1)


def test_daily_card_is_stable_within_a_local_day(db, deck, now):
    tarot = Tarot(db, deck)
    user = setup_user(db)
    first = tarot.daily(user, now)
    again = tarot.daily(user, now + timedelta(hours=3))
    assert first[3] and not again[3]
    assert (first[1], first[2]) == (again[1], again[2])


def test_daily_card_changes_on_the_next_local_day(db, deck, now):
    tarot = Tarot(db, deck)
    user = setup_user(db)
    tarot.daily(user, now)
    _, _, _, is_new = tarot.daily(user, now + timedelta(days=1))
    assert is_new


def test_no_reversals_when_turned_off(db, deck, now):
    tarot = Tarot(db, deck)
    user = setup_user(db)
    db.update_user(1, reversals=0)
    user = db.get_user(1)
    for day in range(30):
        _, _, rev, _ = tarot.daily(user, now + timedelta(days=day))
        assert not rev


def test_free_journal_shows_last_seven_days(db, deck, now):
    tarot = Tarot(db, deck)
    user = setup_user(db, "UTC")
    for day in range(10):
        tarot.daily(user, now - timedelta(days=day))
    entries, visible, hidden = tarot.journal_page(user, now, lifetime=False)
    assert visible == 7 and hidden == 3 and len(entries) == 7
    entries, visible, hidden = tarot.journal_page(user, now, lifetime=True)
    assert visible == 10 and hidden == 0
