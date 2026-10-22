"""Feedback from users to the owner (spec section 14).

Messages are saved and forwarded to the owner's private Telegram group. The owner replies
there and the bot passes the reply on, so the owner's own account is never shown. No names
or usernames are forwarded.
"""
from datetime import timedelta

from .db import iso, parse_iso

KINDS = {
    "bug": "🐞 Something's broken",
    "idea": "💡 Idea or request",
    "card": "🃏 Card content",
    "other": "💬 Other",
    "payment": "💳 Payment problem",
    "checkin": "👋 Two-week check-in",
}
OPEN_TO_ALL = {"bug", "payment"}   # everything else needs Lifetime
LIFETIME_MENU = ["bug", "idea", "card", "other"]
DAILY_LIMIT = 5
STATUSES = {"planned", "done", "wont_do"}


class Feedback:
    def __init__(self, db):
        self.db = db

    def allowed(self, kind, lifetime):
        return kind in OPEN_TO_ALL or lifetime

    def sent_today(self, user_id, now):
        since = iso(now - timedelta(days=1))
        return self.db.one("SELECT COUNT(*) FROM feedback WHERE user_id = ? AND created_at > ?",
                           (user_id, since))[0]

    def can_send(self, user_id, now):
        return self.sent_today(user_id, now) < DAILY_LIMIT

    def record(self, user_id, kind, text, now, card_id=None):
        cur = self.db.execute(
            "INSERT INTO feedback (user_id, created_at, kind, card_id, text) VALUES (?, ?, ?, ?, ?)",
            (user_id, iso(now), kind, card_id, text))
        return cur.lastrowid

    def link_admin_message(self, admin_message_id, feedback_id):
        self.db.execute("INSERT OR REPLACE INTO feedback_messages (admin_message_id, feedback_id) "
                        "VALUES (?, ?)", (admin_message_id, feedback_id))

    def for_admin_message(self, admin_message_id):
        return self.db.one(
            "SELECT f.* FROM feedback f JOIN feedback_messages m ON m.feedback_id = f.id "
            "WHERE m.admin_message_id = ?", (admin_message_id,))

    def set_status(self, feedback_id, status):
        if status not in STATUSES:
            raise ValueError(status)
        self.db.execute("UPDATE feedback SET status = ? WHERE id = ?", (status, feedback_id))

    def header(self, feedback_id, kind, user, now, card_name=None, extra=None):
        """First line of the message the owner sees. Settings, never identity."""
        parts = [f"#{kind} · feedback {feedback_id}"]
        if card_name:
            parts.append(f"card: {card_name}")
        if user["lifetime_at"]:
            days = (now - parse_iso(user["lifetime_at"])).days
            parts.append(f"Lifetime for {days} day{'s' if days != 1 else ''}")
        else:
            parts.append("free user")
        parts.append(f"tz {user['timezone'] or 'not set'}")
        if extra:
            parts.append(extra)
        return " · ".join(parts)
