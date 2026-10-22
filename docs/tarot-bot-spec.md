# Tarot Bot — Feature Spec (draft)

Status: draft for discussion. Items marked **[DECIDE]** need a decision.

## 1. Principles

- **No subscriptions.** Free tier plus a one-time lifetime unlock, paid in Telegram Stars.
- **Your data is yours.** Export at any time, delete everything with one command, never
  used for AI or shared.
- **No AI** in v1.
- **Works the way readers work:** the bot can draw cards for you, and you can also log
  draws from your own physical deck.

## 2. Free vs. Lifetime

| Feature | Free | Lifetime |
|---|---|---|
| Card lookup (all 78: image, meanings, symbolism) | ✅ | ✅ |
| Inline sharing (`@bot three of cups` in any chat) | ✅ | ✅ |
| Daily single card (`/daily`, once per day) | ✅ | ✅ |
| Scheduled draws | 1 schedule, 1 card | Unlimited*, 1–5 cards or any spread |
| On-demand draws (`/draw`) | — | 1–5 cards, any number of times |
| Named spreads | — | ✅ |
| Log a physical deck draw | — | ✅ |
| Journal: everything saved | ✅ | ✅ |
| Journal: view and search | Last 7 days | Full history |
| Notes, tags, mood on draws | — | ✅ |
| "How did it play out?" follow-ups | — | ✅ |
| 78-day challenge | — | ✅ |
| Moon-timed draws | — | ✅ |
| Stats and monthly recap | — | ✅ |
| Your own card meanings | — | ✅ |
| Learn mode (flashcards and quizzes) | 5 questions a day | Unlimited |
| Export | CSV, all data | CSV, Markdown, JSON, PDF |
| Delete all data | ✅ | ✅ |

\* A cap of about 10 schedules per user prevents abuse.

Recommendation: always save free users' draws, so upgrading unlocks their full history
right away ("you have 43 draws waiting"). Basic export stays free, so people's data is
never held back to make them pay.

**[DECIDE]** Agree with saving free users' draws, and with keeping basic export free?

## 3. Commands

| Command | What it does |
|---|---|
| `/start` | Onboarding: welcome, set timezone, reversals on or off, offer a daily card at a chosen time |
| `/card <name>` | Look up a card. Handles messy input: "3 cups", "three of cups", "hanged man", "XIII" |
| `/cards` | Browse by Major Arcana and each suit, using buttons |
| `/daily` | Today's card. If you already drew today, it shows the same card again |
| `/draw [1-5]` | Draw cards (Lifetime) |
| `/spread` | Choose a named spread (Lifetime) |
| `/log` | Record a physical-deck draw: pick cards, mark reversed, add a question (Lifetime) |
| `/journal` | Browse, search and filter past draws |
| `/schedule` | List, add, edit, pause and delete recurring draws |
| `/challenge` | Start, pause, view or reset the 78-day challenge (Lifetime) |
| `/stats` | Your patterns (Lifetime) |
| `/learn` | Flashcards and quizzes |
| `/export` | Choose a format and receive the file in chat |
| `/settings` | Timezone, reversals, deck scope, follow-up delay, card text length |
| `/upgrade` | Lifetime unlock purchase (Stars invoice) |
| `/delete_my_data` | Delete everything, after a confirmation |
| `/help` | Help |
| `/terms`, `/paysupport` | Terms and payment support. Telegram requires these for bots that take payments |

## 4. Card content

Each of the 78 cards has:
- Image (1909 Pamela Colman Smith scans, public domain)
- Upright meaning: short (1 line) and full (a paragraph)
- Reversed meaning: short and full
- Keywords, upright and reversed
- Symbolism: what is shown in the image and what it means
- Element, astrological link, numerology, yes/no lean
- Questions to reflect on (2–3 prompts)

All text must be **our own writing**; we can't copy modern tarot books. A. E. Waite's 1910
*Pictorial Key to the Tarot* is public domain and can serve as a historical base, rewritten
in plain modern language.

Display: the card message shows the image and the short meaning first. A **More** button
expands to the full meaning, symbolism and reflection questions. This keeps chats tidy.

## 5. Draws and spreads

- Draws of 1–5 cards. Multi-card draws arrive as one album, followed by a summary listing
  each position and card.
- Settings: reversals on or off (and how often reversals appear), and deck scope (full
  deck, Major Arcana only, or one suit).
- Spreads in v1:
  - 1 card: daily focus
  - 3 cards: past / present / future
  - 3 cards: situation / action / outcome
  - 5 cards: relationship
  - 10 cards: Celtic Cross
  - 12 cards: year ahead, one per month
- Draws are random and the bot remembers what it drew, so results can't be redrawn by
  scrolling up.

After every draw, buttons appear: **📝 Note**, **🏷 Tag**, **🙂 Mood**, **⭐ Pin**, **Done**.

## 6. Physical deck logging (`/log`)

1. Choose a spread, or "free-form" with N cards.
2. For each position, type a card name or pick one from buttons; mark it reversed if so.
3. Add an optional question and notes.

The entry is saved like any other draw and marked "physical deck." The bot also shows the
meanings of the cards you logged.

## 7. Journal

- Each entry stores: date and time, source (daily, draw, spread, scheduled, challenge or
  physical), question, cards with positions and reversals, notes, tags, mood, pinned
  flag, and the follow-up answer.
- Browse in pages, newest first. Filter by card, tag, mood, source or date range.
  Search inside notes.
- **Follow-up:** N days after a draw that has a question (3 by default, adjustable),
  the bot asks "How did this play out?" The answer is saved with the entry. Users can
  turn this off.

## 8. Schedules

- Each schedule has a time, days (every day, weekdays or chosen days), timezone, and
  content (N cards, a named spread, or the challenge card).
- Examples: "1 card at 07:00 every day" and "3 cards on Sunday at 20:00."
- Users can pause or resume. Schedules keep running even when the bot restarts, because
  they are stored in the database rather than in memory.
- If Telegram can't deliver a message (for example, the user blocked the bot), the
  schedule pauses itself.

## 9. 78-day challenge

- The deck is shuffled once and the order saved, so you see every card once with no
  repeats.
- One card per day at your chosen time, with progress shown ("Day 23/78") and a streak.
- Each card gets a prompt: "Write one line about what this card means to you today."
- When you finish, you get a summary of the whole deck, and the challenge can restart with
  a new shuffle.
- **[DECIDE]** Missed days: (a) the card is still sent and the day counts, (b) the
  challenge waits until you open the last card, or (c) the user chooses.
  Recommendation: (b). Then the challenge is about engaging with each card, not a timer.

## 10. Moon-timed draws (Lifetime)

- Optional automatic spreads on each new moon (intentions) and full moon (release and
  review).
- Moon phases are calculated locally with an astronomy library, so no paid API is needed.

## 11. Stats

- Most-drawn cards, balance of Major vs. Minor Arcana, suits and elements, reversal ratio.
- "Cards that keep showing up" over the last 30 days.
- Streaks for daily draws and the challenge.
- An optional monthly recap message on the 1st.
- Physical-deck draws are included, with an option to see them separately.

## 12. Export

| Format | Use |
|---|---|
| CSV | Spreadsheets. One row per card per draw |
| Markdown | Notion, Obsidian, plain reading |
| JSON | Full backup. Can be imported again later |
| PDF | A nicely laid out journal, good for printing |

The bot sends the file in chat. Filters: all data, or a date range.

## 13. Payments

- `/upgrade` sends a Telegram Stars invoice (currency XTR) for the lifetime unlock.
- Unlocks are tied to the Telegram user ID.
- **[DECIDE]** Price in Stars, aiming for roughly $10–20. Check how many Stars users pay
  per dollar in each app store.
- **[DECIDE]** Refund policy, for example a full refund within 14 days on request.
  Telegram lets the bot refund Stars.
- Later: an all-access bundle that unlocks every bot in the product line.

## 14. Privacy and data

- Data stored: Telegram user ID, settings, journal and schedules. Nothing else.
- `/delete_my_data` deletes everything permanently.
- A short, plain-language privacy page linked from `/start` and `/terms`.

## 15. Onboarding (`/start`)

1. Welcome, with a one-paragraph explanation of what the bot does.
2. Timezone: type a city or the current time. Telegram doesn't give bots the user's
   timezone.
3. Reversals: on or off.
4. "Want a card every morning? Pick a time." The free schedule starts here.
5. Draw the first card right away.

## 16. Out of scope for v1

AI readings, other decks or deck uploads, group readings, a web dashboard, reading for
other people, and other languages.

## 17. Technical notes (to discuss)

- Python with `python-telegram-bot` or `aiogram`.
- SQLite to start, with a path to move to Postgres.
- A scheduler loop that checks the database every minute, so schedules survive restarts.
- Hosting on a small VPS or Fly.io, about $5 a month.
