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
| **Elder Futhark runes** | The 24 runes as a reference, rune of the day, rune casts and spreads, journal, 24-day challenge, learning the three aettir, writing your name in runes. Details below |
| **Oracle / I Ching** | Same draw, journal and schedule features with different content. I Ching translations have public-domain sources |
| **Dream journal** | Quick voice or text capture in the morning, symbol tags, recurring-theme stats, export |
| **Manifestation / 369 tracker** | Scheduled prompts at 3, 6 and 9, streaks, scripting journal |
| **Wheel of the Year** | Sabbat reminders, correspondences, ritual checklists |
| **Numerology** | Personal year, month and day numbers sent daily, life path, name number |
| **Crystals & herbs** | Look-up reference, "what helps with X," logging your own collection |

Sell each bot on its own, plus an **all-access bundle** at a discount.

## Elder Futhark rune bot

The oldest runic alphabet: 24 runes in three groups of eight, called *aettir* (Freyr's,
Heimdall's and Tyr's). It reuses the tarot bot's engine almost as is, with runes in
place of cards.

**Free**
- Look up any rune by name, letter or sound: *Fehu*, *F*, "the cattle rune", or the
  rune character itself (ᚠ). Each rune shows its shape, name, sound, meaning, merkstave
  (reversed) meaning, its aett, and keywords.
- Rune of the day, with the same once-per-day rule as the daily tarot card.
- One scheduled daily rune.
- **Write your name in runes:** type a name and get it back in Elder Futhark letters,
  with a note on how each sound was matched. Easy to share, so it doubles as marketing.

**Lifetime**
- Casts and spreads: single rune, three runes for the Norns (past, present, future), a
  five-rune cross, and a nine-rune cast.
- Logging casts from your own physical rune set.
- Journal with notes and "how did it play out?" follow-ups, export, and stats.
- **24-day challenge:** one rune a day, no repeats, through all three aettir.
- **Learn the aettir:** flashcards and quizzes, one aett at a time.

**Content notes**
- **Reversed runes:** about nine runes look the same upside down (such as Gebo, Isa and
  Jera), so they have no reversed meaning. The bot only offers reversals for runes that
  can actually be reversed.
- **The blank rune:** often included in modern sets, but it was added in the 1980s and
  isn't part of the historical Futhark. Offer it as an optional setting, off by default,
  and explain where it comes from.
- **Sources:** the Old English, Old Norwegian and Old Icelandic rune poems are public
  domain and give historical meanings, though they describe the later runic alphabets
  rather than the Elder Futhark itself. As with the tarot cards, all modern meanings are
  our own writing.
- **Images:** rune shapes are simple and also exist as Unicode characters (ᚠ ᚢ ᚦ ᚨ…), so
  we can draw our own clean rune images with no copyright concerns.
- **Respectful framing:** a few runes have been misused by hate groups. The content
  should stay rooted in history and personal reflection, and the bot shouldn't use any
  of those altered symbols.

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
