"""Optional one-time Stars support, independent of Lifetime entitlements."""
import re
from datetime import timedelta

from .db import iso, parse_iso
from .payments import REFUND_DAYS

PRESETS = (25, 50, 100, 500)
MAX_STARS = 10_000
PREFIX = "donation:"


class Donations:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def amount(text):
        """Bound text length before conversion; Stars must be whole positive units."""
        if not isinstance(text, str):
            return None
        text = text.strip()
        if not re.fullmatch(r"[0-9]{1,5}", text):
            return None
        stars = int(text)
        return stars if 1 <= stars <= MAX_STARS else None

    @classmethod
    def expected_stars(cls, payload):
        if not isinstance(payload, str) or not payload.startswith(PREFIX):
            return None
        stars = cls.amount(payload[len(PREFIX):])
        return stars if stars is not None and payload == f"{PREFIX}{stars}" else None

    def record(self, charge_id, user_id, stars, now):
        """Return True only for a new receipt; replays never alter an existing one."""
        if type(stars) is not int or not 1 <= stars <= MAX_STARS:
            raise ValueError("Donation amount must be 1–10,000 whole Stars")
        cur = self.db.execute(
            "INSERT OR IGNORE INTO donations (charge_id, user_id, stars, created_at) "
            "VALUES (?, ?, ?, ?)", (charge_id, user_id, stars, iso(now)))
        return cur.rowcount == 1

    def find(self, charge_or_user):
        row = self.db.one("SELECT * FROM donations WHERE charge_id = ?", (charge_or_user,))
        value = str(charge_or_user)
        if row is None and re.fullmatch(r"[0-9]{1,19}", value):
            user_id = int(value)
            if user_id <= 2**63 - 1:
                row = self.db.one(
                    "SELECT * FROM donations WHERE user_id = ? AND refunded_at IS NULL "
                    "ORDER BY created_at DESC, rowid DESC LIMIT 1", (user_id,))
        return row

    @staticmethod
    def within_refund_window(donation, now):
        return now - parse_iso(donation["created_at"]) <= timedelta(days=REFUND_DAYS)

    def mark_refunded(self, donation, now):
        self.db.execute("UPDATE donations SET refunded_at = ? WHERE charge_id = ?",
                        (iso(now), donation["charge_id"]))
