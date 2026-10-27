"""SQLite storage shared by every bot. Each bot keeps its own database file.

Times are stored as UTC ISO strings. Queries are small and fast, so the standard
sqlite3 module is used directly, even from async handlers.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,             -- Telegram user id
    created_at TEXT NOT NULL,
    timezone TEXT,                      -- IANA name, e.g. Europe/London
    reversals INTEGER NOT NULL DEFAULT 1,
    onboarded INTEGER NOT NULL DEFAULT 0,
    lifetime_at TEXT,                   -- set when Lifetime is bought
    checkin_sent INTEGER NOT NULL DEFAULT 0,
    whats_new INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS draws (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    local_date TEXT NOT NULL,           -- the user's date when drawn, YYYY-MM-DD
    source TEXT NOT NULL,               -- daily, scheduled, draw, spread, physical, challenge
    question TEXT,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS draws_user ON draws(user_id, created_at);

CREATE TABLE IF NOT EXISTS draw_cards (
    draw_id INTEGER NOT NULL REFERENCES draws(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    card_id TEXT NOT NULL,
    reversed INTEGER NOT NULL,
    PRIMARY KEY (draw_id, position)
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    kind TEXT NOT NULL,                 -- daily (the free daily card)
    time_local TEXT NOT NULL,           -- HH:MM in the user's timezone
    days TEXT NOT NULL DEFAULT '0123456',  -- weekdays, Monday = 0
    paused INTEGER NOT NULL DEFAULT 0,
    next_run_utc TEXT
);
CREATE INDEX IF NOT EXISTS schedules_due ON schedules(paused, next_run_utc);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,                 -- bug, idea, card, payment, other, checkin
    card_id TEXT,
    text TEXT,
    status TEXT NOT NULL DEFAULT 'new'  -- new, planned, done, wont_do
);

CREATE TABLE IF NOT EXISTS feedback_messages (
    admin_message_id INTEGER PRIMARY KEY,  -- message in the owner's group
    feedback_id INTEGER NOT NULL REFERENCES feedback(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    charge_id TEXT PRIMARY KEY,         -- telegram_payment_charge_id
    user_id INTEGER NOT NULL,
    stars INTEGER NOT NULL,
    founder INTEGER NOT NULL DEFAULT 0,  -- bought at the founder price
    created_at TEXT NOT NULL,
    refunded_at TEXT
);

CREATE TABLE IF NOT EXISTS media (
    key TEXT PRIMARY KEY,               -- image file name plus orientation
    file_id TEXT NOT NULL               -- Telegram's id, so images upload only once
);
"""


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_iso(text):
    return datetime.fromisoformat(text) if text else None


class Database:
    def __init__(self, path):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def execute(self, sql, params=()):
        with self.conn:
            return self.conn.execute(sql, params)

    def one(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()

    def all(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    # Users

    def get_user(self, user_id):
        """The user's row, created on first contact."""
        self.execute("INSERT OR IGNORE INTO users (id, created_at) VALUES (?, ?)",
                     (user_id, iso(utcnow())))
        return self.one("SELECT * FROM users WHERE id = ?", (user_id,))

    def update_user(self, user_id, **fields):
        cols = ", ".join(f"{name} = ?" for name in fields)
        self.execute(f"UPDATE users SET {cols} WHERE id = ?", (*fields.values(), user_id))

    def delete_user(self, user_id):
        """Remove everything stored about a user (/delete_my_data). Payment records are
        kept without a link to any other data, because refunds need the charge id."""
        with self.conn:
            self.conn.execute("DELETE FROM draws WHERE user_id = ?", (user_id,))
            self.conn.execute("DELETE FROM schedules WHERE user_id = ?", (user_id,))
            self.conn.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
            self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    # Draws

    def add_draw(self, user_id, local_date, source, cards, question=None):
        """cards: list of (card_id, reversed). Returns the new draw id."""
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO draws (user_id, created_at, local_date, source, question) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, iso(utcnow()), local_date, source, question))
            draw_id = cur.lastrowid
            self.conn.executemany(
                "INSERT INTO draw_cards (draw_id, position, card_id, reversed) VALUES (?, ?, ?, ?)",
                [(draw_id, i, card_id, int(rev)) for i, (card_id, rev) in enumerate(cards)])
        return draw_id

    def draw_cards(self, draw_id):
        rows = self.all("SELECT card_id, reversed FROM draw_cards WHERE draw_id = ? ORDER BY position",
                        (draw_id,))
        return [(r["card_id"], bool(r["reversed"])) for r in rows]

    def find_draw(self, user_id, local_date, source):
        return self.one("SELECT * FROM draws WHERE user_id = ? AND local_date = ? AND source = ?",
                        (user_id, local_date, source))

    def recent_draws(self, user_id, limit, offset=0, since_date=None):
        sql = "SELECT * FROM draws WHERE user_id = ?"
        params = [user_id]
        if since_date:
            sql += " AND local_date >= ?"
            params.append(since_date)
        sql += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
        return self.all(sql, (*params, limit, offset))

    def count_draws(self, user_id, since_date=None):
        sql, params = "SELECT COUNT(*) FROM draws WHERE user_id = ?", [user_id]
        if since_date:
            sql += " AND local_date >= ?"
            params.append(since_date)
        return self.one(sql, params)[0]

    # Media cache

    def get_file_id(self, key):
        row = self.one("SELECT file_id FROM media WHERE key = ?", (key,))
        return row["file_id"] if row else None

    def set_file_id(self, key, file_id):
        self.execute("INSERT OR REPLACE INTO media (key, file_id) VALUES (?, ?)", (key, file_id))
