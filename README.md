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
| `content/brand/` | Profile photo, description picture and font (Cormorant Garamond, SIL Open Font License); made by `tools/make_brand_images.py` |
| `tools/` | Content tools: image download and cleanup, card and Waite-quote checks, review pages |
| `tests/` | Unit tests and whole-conversation tests against a fake Telegram API |
| `deploy/` | Running the bots on a server: [`deploy/README.md`](deploy/README.md) |

## Running the tarot bot

1. **Create the bot.** In Telegram, message [@BotFather](https://t.me/BotFather), send
   `/newbot`, and copy the token it gives you.
2. **Install:** `pip install -r requirements.txt` (Python 3.11 or newer).
3. **Set the token** as an environment variable (in a cloud environment, add it as a
   secret rather than pasting it anywhere):
   ```
   export TAROT_BOT_TOKEN=123456:ABC...
   ```
4. **Set up the bot's profile** (name, descriptions, command menu, profile photo):
   `python -m bots.tarot.profile`. Then upload `content/brand/description.jpg` in
   @BotFather: `/mybots` → your bot → **Edit Bot** → **Edit Description Picture**. The
   Bot API can't set that picture.
5. **Run:** `python -m bots.tarot`. Then open your bot in Telegram and send `/start`.

To keep it running for everyone, put it on a server: see [`deploy/README.md`](deploy/README.md).

### Owner settings (optional, needed for feedback and refunds)

| Variable | What it does |
|---|---|
| `TAROT_ADMIN_USER_IDS` | Your Telegram user id (comma-separated for several people). Allows `/refund`. |
| `TAROT_ADMIN_CHAT_ID` | A private group where feedback arrives. Replies there go back to the user. |
| `TAROT_LIFETIME_STARS` | Regular Lifetime price in Stars (default 1650, which pays out about $20 after fees). |
| `TAROT_FOUNDER_STARS` | Launch price for the first buyers (default 990). |
| `TAROT_FOUNDER_LIMIT` | How many founder purchases before the regular price applies (default 100; 0 turns it off). |
| `TAROT_DB_PATH` | Database file (default `data/tarot.sqlite3`). |

To find the ids: send `/myid` to the bot for your user id. For the group, create a
private group, add the bot, and send `/myid` there (group ids start with `-100`). Restart
the bot after setting them.

**In the feedback group:** reply to a feedback message to answer the user. Reply with
`/done`, `/planned` or `/wontdo` to set its status; `/done` also tells the user.

**Refunds:** `/refund <user id>` in a private chat with the bot. Payments older than 7
days need `/refund <user id> force`.

## Optional Stars donations

Users can send `/donate` and choose **25, 50, 100 or 500 Stars**, or choose
**Custom amount** and type a whole number from **1 to 10,000**. `/donate 75`
opens an invoice directly; `/cancel` exits a custom-amount prompt. Telegram
shows its own payment confirmation: opening an invoice does not pay it.

Donations are voluntary, one-time support. They do **not** grant Lifetime,
founder status or any other perks, and Lifetime users can donate too. Stars
are credited to the **bot's balance**, not a personal Stars balance. The owner
can redeem eligible rewards under Telegram's current rules.

Each donation has a separate receipt in the same SQLite database; duplicate
Telegram payment updates do not record it twice. `/delete_my_data` removes
personal settings, draws and feedback but retains purchase/donation receipts
for payment support and refunds. `/terms` discloses this retention.
Checkout approvals are stored so an already-approved Lifetime payment remains
valid if the owner changes prices before Telegram delivers its receipt. The
matched approval is removed when that purchase is recorded. Reply routes are
scoped by chat and message ID to keep private owner-chat support distinct from
group support.

Users can request a full refund within seven days through `/paysupport`.
Configure `TAROT_ADMIN_CHAT_ID` to receive support messages in your private
group. Without that setting, **payment-support** messages go to the configured
owner with the lowest numeric `TAROT_ADMIN_USER_IDS` value, in their private
bot chat. That owner must first send `/start` and keep the bot unblocked.
Replies to the forwarded support message are relayed back to the user.
Ordinary feedback still requires the configured group for forwarding. If
payment support cannot be forwarded, it is saved and the user is told that
the owner could not be notified. Payment support has its own five-requests-per-
24-hours quota, separate from ordinary feedback.

**Owner only:** `/refund_donation <charge id or user id>` refunds a donation;
using a user id chooses their latest unrefunded donation. Add `force` for a
payment older than seven days. Donation refunds leave Lifetime untouched.
The existing `/refund` command continues to handle Lifetime purchases only.
If a donation refund times out, the bot leaves its receipt unchanged and shows
the exact charge-ID command to retry. A confirmed `CHARGE_ALREADY_REFUNDED`
response reconciles an earlier completed refund; an ambiguous timeout alone
is never recorded as a successful refund.

## Tests

```
pip install -r requirements-dev.txt
python -m pytest
python tools/check_cards.py
python tools/check_waite.py
```
