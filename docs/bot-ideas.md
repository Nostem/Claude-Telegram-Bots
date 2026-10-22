# Bot Ideas

A product line of paid Telegram bots on spiritual and metaphysical topics. They all share
one core engine: payments (Telegram Stars), scheduling, journal, export, timezone
handling and feedback. Each new bot is mostly new content on top of that engine.

The tarot bot is the first product.

## Product line

| Bot | Main features |
|---|---|
| **Tarot** (first product) | Card reference (image, upright and reversed meanings, symbolism), draws of 1–5 cards and named spreads, logging draws from a physical deck, journal with "how did it play out?" follow-ups, recurring scheduled draws, 78-day no-repeat challenge, stats, export |
| **Moon & astrology** | Moon phase alerts, void-of-course moon, retrograde warnings, personal transits from your birth chart, new and full moon intention prompts |
| **Oracle / I Ching / runes** | Same draw, journal and schedule features with different content. I Ching translations and runes have public-domain sources |
| **Dream journal** | Quick voice or text capture in the morning, symbol tags, recurring-theme stats, export |
| **Manifestation / 369 tracker** | Scheduled prompts at 3, 6 and 9, streaks, scripting journal |
| **Wheel of the Year** | Sabbat reminders, correspondences, ritual checklists |
| **Numerology** | Personal year, month and day numbers sent daily, life path, name number |
| **Crystals & herbs** | Look-up reference, "what helps with X," logging your own collection |

Sell each bot on its own, plus an **all-access bundle** at a discount.

## Decisions so far

- **Pricing:** one-time lifetime unlock, roughly $10–20 per bot, with a discounted
  all-access bundle. Paid in Telegram Stars, which Telegram requires for digital goods.
- **Free tier:** yes. Card lookups and one daily draw are free. The lifetime unlock adds
  the journal, export, schedules and spreads.
- **AI:** not included for now. It may come later as an optional paid add-on, priced
  separately so lifetime buyers don't create ongoing costs.
- **Feedback:** built into every bot with `/feedback`. Anyone can report bugs; Lifetime
  users can also send ideas and card feedback. Messages arrive in a private Telegram group,
  and replies go back through the bot. Details in `docs/tarot-bot-spec.md`, section 14.
- **Marketing:** start with Reddit and Twitter/X posts, then rely on word of mouth.
  Inline mode (`@bot card name` in any chat) helps spread the bot naturally.

## Open questions

- Check the copyright on card images before charging money. Use scans of the original
  1909 Pamela Colman Smith deck, not the US Games 1971 recoloring. Avoid the
  "Rider-Waite" trademark; call it "Smith-Waite" or "RWS."
- Confirm current Telegram Stars payout rates and withdrawal holds from Telegram's
  official terms.
- Check each subreddit's self-promotion rules before posting.
