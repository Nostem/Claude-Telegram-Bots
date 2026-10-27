# Claude Telegram Bots

Paid Telegram bots on spiritual and metaphysical topics: a free tier plus a one-time
Lifetime unlock in Telegram Stars. The first bot is **Tarot Companion**.

- Product ideas and decisions: [`docs/bot-ideas.md`](docs/bot-ideas.md)
- Tarot bot spec: [`docs/tarot-bot-spec.md`](docs/tarot-bot-spec.md)
- Card content plan: [`docs/card-content-plan.md`](docs/card-content-plan.md)
- Card review pages: [`docs/review/`](docs/review/)
- Business model and costs: [`docs/business-model.md`](docs/business-model.md)

## Layout

| Path | What's there |
|---|---|
| `bots/engine/` | Shared by every bot: database, schedules, timezones, feedback, payments, common handlers |
| `bots/tarot/` | The tarot bot: card search, daily card, journal, onboarding and settings |
| `content/tarot/` | The 78 card files and the cleaned 1909 card images |
| `tools/` | Content tools: image download and cleanup, card and Waite-quote checks, review pages |
| `tests/` | Unit tests and whole-conversation tests against a fake Telegram API |

## Running the tarot bot

1. **Create the bot.** In Telegram, message [@BotFather](https://t.me/BotFather), send
   `/newbot`, and copy the token it gives you.
2. **Install:** `pip install -r requirements.txt` (Python 3.11 or newer).
3. **Set the token** as an environment variable (in a cloud environment, add it as a
   secret rather than pasting it anywhere):
   ```
   export TAROT_BOT_TOKEN=123456:ABC...
   ```
4. **Run:** `python -m bots.tarot`. Then open your bot in Telegram and send `/start`.

### Owner settings (optional, needed for feedback and refunds)

| Variable | What it does |
|---|---|
| `TAROT_ADMIN_USER_IDS` | Your Telegram user id (comma-separated for several people). Allows `/refund`. |
| `TAROT_ADMIN_CHAT_ID` | A private group where feedback arrives. Replies there go back to the user. |
| `TAROT_LIFETIME_STARS` | Lifetime price in Stars (default 750). |
| `TAROT_DB_PATH` | Database file (default `data/tarot.sqlite3`). |

To find the ids: send `/myid` to the bot for your user id. For the group, create a
private group, add the bot, and send `/myid` there (group ids start with `-100`). Restart
the bot after setting them.

**In the feedback group:** reply to a feedback message to answer the user. Reply with
`/done`, `/planned` or `/wontdo` to set its status; `/done` also tells the user.

**Refunds:** `/refund <user id>` in a private chat with the bot. Payments older than 7
days need `/refund <user id> force`.

## Tests

```
pip install -r requirements-dev.txt
python -m pytest
python tools/check_cards.py
python tools/check_waite.py
```
