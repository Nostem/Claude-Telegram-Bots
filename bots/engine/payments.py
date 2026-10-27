"""Lifetime purchases in Telegram Stars, and refunds (spec section 13).

Refunds within 7 days are granted on request; the owner runs /refund in the bot.
"""
from datetime import timedelta

from .db import iso, parse_iso

PAYLOAD = "lifetime"
FOUNDER_PAYLOAD = "lifetime:founder"
REFUND_DAYS = 7


class Payments:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def is_lifetime(user):
        return bool(user["lifetime_at"])

    def founders_sold(self):
        return self.db.one("SELECT COUNT(*) FROM payments WHERE founder = 1 "
                           "AND refunded_at IS NULL")[0]

    def price(self, settings):
        """(stars, payload, founder spots left). The founder price applies until
        founder_limit founder purchases are made; refunds free a spot again."""
        left = settings.founder_limit - self.founders_sold()
        if settings.founder_limit > 0 and left > 0:
            return settings.founder_stars, FOUNDER_PAYLOAD, left
        return settings.lifetime_stars, PAYLOAD, 0

    @staticmethod
    def expected_stars(payload, settings):
        """The amount an invoice with this payload was sent for, or None if unknown."""
        return {PAYLOAD: settings.lifetime_stars, FOUNDER_PAYLOAD: settings.founder_stars}.get(payload)

    def is_founder(self, user_id):
        return self.db.one("SELECT 1 FROM payments WHERE user_id = ? AND founder = 1 "
                           "AND refunded_at IS NULL", (user_id,)) is not None

    def record(self, charge_id, user_id, stars, now, founder=False):
        self.db.get_user(user_id)   # make sure the user row exists before granting Lifetime
        with self.db.conn:
            self.db.conn.execute(
                "INSERT OR IGNORE INTO payments (charge_id, user_id, stars, founder, created_at) "
                "VALUES (?, ?, ?, ?, ?)", (charge_id, user_id, stars, int(founder), iso(now)))
            self.db.conn.execute("UPDATE users SET lifetime_at = ?, checkin_sent = 0 WHERE id = ?",
                                 (iso(now), user_id))

    def latest_for_user(self, user_id):
        return self.db.one("SELECT * FROM payments WHERE user_id = ? AND refunded_at IS NULL "
                           "ORDER BY created_at DESC", (user_id,))

    def find(self, charge_or_user):
        """Look up a payment by charge id, or the latest one for a user id."""
        row = self.db.one("SELECT * FROM payments WHERE charge_id = ?", (charge_or_user,))
        if row is None and str(charge_or_user).isdigit():
            row = self.latest_for_user(int(charge_or_user))
        return row

    @staticmethod
    def within_refund_window(payment, now):
        return now - parse_iso(payment["created_at"]) <= timedelta(days=REFUND_DAYS)

    def mark_refunded(self, payment, now):
        with self.db.conn:
            self.db.conn.execute("UPDATE payments SET refunded_at = ? WHERE charge_id = ?",
                                 (iso(now), payment["charge_id"]))
            self.db.conn.execute("UPDATE users SET lifetime_at = NULL WHERE id = ?",
                                 (payment["user_id"],))

    def due_checkins(self, now, after_days=14):
        """Lifetime users who bought at least 14 days ago and haven't been asked yet."""
        cutoff = iso(now - timedelta(days=after_days))
        return self.db.all("SELECT * FROM users WHERE lifetime_at IS NOT NULL "
                           "AND lifetime_at <= ? AND checkin_sent = 0", (cutoff,))
