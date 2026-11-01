"""Donation rules and additive SQLite upgrades; no Telegram network calls."""
from datetime import timedelta

import pytest

from bots.engine.db import Database
from bots.engine.payments import Payments


@pytest.mark.parametrize("text,want", [
    ("1", 1), ("25", 25), ("10000", 10000), (" 75 ", 75),
    ("0", None), ("10001", None), ("-5", None), ("2.5", None),
    ("", None), ("ten", None), ("+10", None), ("1e3", None),
    ("9" * 5000, None),
])
def test_amount_rejects_non_whole_or_out_of_range_input(text, want):
    from bots.engine.donations import Donations
    assert Donations.amount(text) == want


@pytest.mark.parametrize("payload,want", [
    ("donation:25", 25), ("donation:1", 1), ("donation:10000", 10000),
    ("donation:0", None), ("donation:10001", None), ("donation:025", None),
    ("donation:25 ", None), ("donation:-25", None), ("donation:25:extra", None),
    ("lifetime", None), ("other:25", None), ("donation:" + "9" * 5000, None),
])
def test_payload_requires_canonical_bounded_donation_amount(payload, want):
    from bots.engine.donations import Donations
    assert Donations.expected_stars(payload) == want


def test_donation_receipt_is_idempotent_and_refund_does_not_change_lifetime(db, now):
    from bots.engine.donations import Donations
    pay = Payments(db)
    pay.record("lifetime", 1, 990, now, founder=True)
    before = dict(db.get_user(1))
    donations = Donations(db)
    assert donations.record("tip-1", 1, 50, now) is True
    assert donations.record("tip-1", 1, 50, now + timedelta(days=1)) is False
    row = donations.find("tip-1")
    assert row["stars"] == 50 and row["user_id"] == 1
    assert donations.find("1")["charge_id"] == "tip-1"
    assert donations.within_refund_window(row, now + timedelta(days=7))
    assert not donations.within_refund_window(row, now + timedelta(days=8))
    donations.mark_refunded(row, now)
    assert donations.record("tip-1", 1, 50, now) is False
    assert donations.find("tip-1")["refunded_at"]
    assert dict(db.get_user(1)) == before
    assert pay.founders_sold() == 1
    assert db.one("SELECT COUNT(*) FROM donations")[0] == 1


def test_database_upgrade_preserves_existing_users_and_purchases(tmp_path, now):
    path = str(tmp_path / "legacy.sqlite3")
    legacy = Database(path)
    legacy.get_user(1)
    Payments(legacy).record("old-charge", 1, 990, now, founder=True)
    legacy.execute("DROP TABLE IF EXISTS donations")
    legacy.conn.close()
    upgraded = Database(path)
    try:
        assert upgraded.get_user(1)["lifetime_at"]
        assert upgraded.one("SELECT charge_id FROM payments")[0] == "old-charge"
        assert upgraded.one("SELECT COUNT(*) FROM donations")[0] == 0
        assert upgraded.one("PRAGMA integrity_check")[0] == "ok"
    finally:
        upgraded.conn.close()
