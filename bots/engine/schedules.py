"""Recurring messages, such as the daily card at 07:00.

Each schedule stores its next run time in UTC. A loop checks the database every 30
seconds and sends whatever is due, so schedules survive restarts.
"""
import re
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .db import iso, parse_iso

TIME_RE = re.compile(r"^\s*(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?\s*$", re.I)


def parse_time(text):
    """'7', '07:30', '7.30pm' or '19:30' -> 'HH:MM', or None if it isn't a valid time."""
    m = TIME_RE.match(text or "")
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").lower()
    if ampm:
        if not 1 <= hour <= 12:
            return None
        hour = hour % 12 + (12 if ampm == "pm" else 0)
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"


def next_run(time_local, days, tz_name, after):
    """The first moment after `after` (a UTC datetime) when the schedule should fire.

    time_local is 'HH:MM' in the user's timezone and days holds the weekdays it runs
    (Monday = 0). Daylight saving changes are handled by zoneinfo: a time that doesn't
    exist on a spring-forward day runs an hour later, as wall clocks do.
    """
    tz = ZoneInfo(tz_name or "UTC")
    hour, minute = map(int, time_local.split(":"))
    local_day = after.astimezone(tz).date()
    for offset in range(8):
        day = local_day + timedelta(days=offset)
        if str(day.weekday()) not in days:
            continue
        candidate = datetime.combine(day, time(hour, minute), tzinfo=tz)
        # Round-trip through UTC to normalize times skipped by a DST change.
        candidate_utc = candidate.astimezone(timezone.utc)
        if candidate_utc > after:
            return candidate_utc
    raise ValueError(f"no run found for days={days!r}")


class Schedules:
    def __init__(self, db):
        self.db = db

    def for_user(self, user_id, kind=None):
        sql, params = "SELECT * FROM schedules WHERE user_id = ?", [user_id]
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        return self.db.all(sql + " ORDER BY time_local", params)

    def set_daily(self, user_id, time_local, tz_name, now):
        """Create or update the user's daily-card schedule."""
        existing = self.for_user(user_id, "daily")
        run = iso(next_run(time_local, "0123456", tz_name, now))
        if existing:
            self.db.execute("UPDATE schedules SET time_local = ?, paused = 0, next_run_utc = ? "
                            "WHERE id = ?", (time_local, run, existing[0]["id"]))
        else:
            self.db.execute("INSERT INTO schedules (user_id, kind, time_local, next_run_utc) "
                            "VALUES (?, 'daily', ?, ?)", (user_id, time_local, run))

    def set_paused(self, schedule_id, paused, tz_name, now):
        row = self.db.one("SELECT * FROM schedules WHERE id = ?", (schedule_id,))
        run = None if paused else iso(next_run(row["time_local"], row["days"], tz_name, now))
        self.db.execute("UPDATE schedules SET paused = ?, next_run_utc = ? WHERE id = ?",
                        (int(paused), run, schedule_id))

    def delete(self, schedule_id):
        self.db.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))

    def reschedule_user(self, user_id, tz_name, now):
        """Recompute run times after the user changes timezone."""
        for row in self.for_user(user_id):
            if not row["paused"]:
                self.db.execute("UPDATE schedules SET next_run_utc = ? WHERE id = ?",
                                (iso(next_run(row["time_local"], row["days"], tz_name, now)), row["id"]))

    def due(self, now):
        return self.db.all(
            "SELECT s.*, u.timezone FROM schedules s JOIN users u ON u.id = s.user_id "
            "WHERE s.paused = 0 AND s.next_run_utc <= ? ORDER BY s.next_run_utc", (iso(now),))

    def mark_run(self, row, now):
        """Move a schedule to its next run, skipping any runs missed while offline."""
        after = max(now, parse_iso(row["next_run_utc"]))
        self.db.execute("UPDATE schedules SET next_run_utc = ? WHERE id = ?",
                        (iso(next_run(row["time_local"], row["days"], row["timezone"], after)), row["id"]))
