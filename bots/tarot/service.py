"""Tarot logic that doesn't depend on Telegram, so it can be tested directly."""
from datetime import timedelta

from bots.engine.timezones import local_now

FREE_JOURNAL_DAYS = 7


class Tarot:
    def __init__(self, db, deck):
        self.db = db
        self.deck = deck

    def daily(self, user, now, source="daily"):
        """Today's card for the user. Drawn once per local day; asking again shows the
        same card. Returns (draw_id, card, reversed, is_new)."""
        today = local_now(user["timezone"], now).date().isoformat()
        existing = self.db.find_draw(user["id"], today, "daily")
        if existing:
            card_id, rev = self.db.draw_cards(existing["id"])[0]
            return existing["id"], self.deck[card_id], rev, False
        [(card_id, rev)] = self.deck.draw(1, bool(user["reversals"]))
        draw_id = self.db.add_draw(user["id"], today, "daily", [(card_id, rev)])
        return draw_id, self.deck[card_id], rev, True

    def journal_page(self, user, now, lifetime, page=0, per_page=10):
        """(entries, total_visible, hidden_count). Free users see the last 7 days; older
        draws stay saved and appear once they unlock Lifetime."""
        since = None
        if not lifetime:
            since = (local_now(user["timezone"], now).date()
                     - timedelta(days=FREE_JOURNAL_DAYS - 1)).isoformat()
        rows = self.db.recent_draws(user["id"], per_page, page * per_page, since_date=since)
        entries = [(row, [(self.deck[c], r) for c, r in self.db.draw_cards(row["id"])])
                   for row in rows]
        visible = self.db.count_draws(user["id"], since)
        hidden = self.db.count_draws(user["id"]) - visible
        return entries, visible, hidden
