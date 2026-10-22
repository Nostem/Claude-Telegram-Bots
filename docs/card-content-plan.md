# Card Content Plan

How we write the 78 card entries for the tarot bot: what each entry contains, the voice,
length limits, sources, images and the review process.

Sample entries for approval:
- [`content/tarot/cards/major-00-the-fool.yaml`](../content/tarot/cards/major-00-the-fool.yaml)
- [`content/tarot/cards/swords-03.yaml`](../content/tarot/cards/swords-03.yaml)
- [`content/tarot/cards/cups-queen.yaml`](../content/tarot/cards/cups-queen.yaml)

## 1. What each card entry contains

| Field | Length | Shown where |
|---|---|---|
| `name` | — | Everywhere |
| `keywords.upright` / `keywords.reversed` | 5 each | Card caption, quiz |
| `short.upright` / `short.reversed` | ≤ 140 characters | Card caption, draw summaries, schedules |
| `meaning.upright` / `meaning.reversed` | 80–130 words | **More** button |
| `in_context.love` / `.work` / `.advice` | 1 sentence each (≤ 140 characters) | **More** button, spreads |
| `symbolism` | 4–6 items | **More** button, learn mode |
| `reflection` | 3 questions | **More** button, journal prompts, challenge |
| `yes_no` | Yes / No / Maybe | Yes/no draws |
| `correspondences` | number, element, astrology, Hebrew letter (Majors) | **More** button, stats |
| `waite_1910` | Waite's original keywords, quoted | **Historical meaning** button |
| `image` | Filename | Card display |

The "Love / Work / Advice" lines weren't in the earlier spec, but app users ask for
them constantly ("what does this mean for love?"). They also make spreads read better.

### Telegram limits
- A photo caption can hold at most 1,024 characters. The card caption shows the name,
  keywords and short meaning, which stays well under that.
- A message can hold at most 4,096 characters. The full **More** view fits in one
  message.

## 2. Voice and style

**Tone:** warm, grounded and plain. Like a thoughtful friend who knows tarot well, not a
mystic speaking in riddles.

**Rules:**
1. Speak to the reader as "you."
2. Describe energy and options, not fixed fate: "may," "invites," "asks you to," never
   "you will."
3. **Reversals are not "the bad version."** Each reversal is one of these: the upright
   energy blocked, turned inward, delayed, or overdone. Pick the one that fits the card.
4. Hard cards (Death, Tower, Three of Swords, Ten of Swords and so on) are honest without
   being frightening. No predictions of death, illness, accidents or disasters.
5. No medical, legal or financial advice. Point to real help when it fits, such as
   "talk to someone you trust, or a professional."
6. **Court cards describe energies anyone can have.** They may also point to a person,
   but never by gender, age or looks ("a caring, sensitive person in your life," not
   "a fair-haired woman").
7. Tie the meaning back to the image ("notice her throne is on dry land…"). This helps
   people learn to read the cards without the bot.
8. Plain language: short sentences, no jargon, no "thee/thou."
9. Every word is our own. Don't paraphrase modern tarot books or websites.

## 3. Sources

| Source | Status | How we use it |
|---|---|---|
| A. E. Waite, *The Pictorial Key to the Tarot* (1910) | Public domain | Quoted in `waite_1910` as historical meaning; a starting point for our own writing |
| Golden Dawn correspondences (*Book T*, about 1890s) | Public domain; these facts aren't copyrightable anyway | Elements, astrology, Hebrew letters |
| Modern tarot books and websites | Copyrighted | **Not used** |

Waite's meanings are often dated or odd. For example, his Queen of Cups is "a perfect
spouse and a good mother." Quoting them separately as history is interesting, and it
shows why we write our own.

## 4. Images

- Use scans of the **original 1909 Pamela Colman Smith printing**. These are public domain
  in the US, and in the UK and EU since 2022. **Don't** use the US Games 1971 recoloring,
  which is what most "Rider-Waite" images online are.
- Source: the **"RWS1909" set on Wikimedia Commons**, scans of an original 1909 "Roses &
  Lilies" printing. Avoid the more common "RWS Tarot 00 Fool.jpg" style files: they are a
  1910 "Pam-A" printing from a less clearly documented source. Every image is credited
  in `content/tarot/images/CREDITS.md`.
- Quick check for the wrong version: US Games cards have "© 1971 U.S. Games" printed
  along the right edge, and brighter, flatter colors.
- Keep the **vintage look**, but polished. `tools/clean_card_images.py` turns `raw/` scans
  into `cards/` images the same way for every card: straighten, crop the worn edges,
  brighten the paper without changing the colors, sharpen slightly, and add an even
  cream border. Run `python3 tools/clean_card_images.py` after adding raw scans.
- File names match the card IDs, for example `major-00-the-fool.jpg`.
- Reversed cards are shown by rotating the image 180° in code, so we only store 78 files.
- After the first upload, keep Telegram's `file_id` for each image, so later sends are
  instant.
- Never use the name "Rider-Waite" (a US Games trademark). Call it "Smith-Waite" or "RWS."

## 5. Card IDs and files

One YAML file per card in `content/tarot/cards/`:

- Major Arcana: `major-00-the-fool` … `major-21-the-world`
- Minor Arcana: `{suit}-{01..10}`, for example `swords-03`. The Ace is `01`.
- Court cards: `{suit}-{page|knight|queen|king}`, for example `cups-queen`
- Suits: `wands`, `cups`, `swords`, `pentacles`

YAML is easy to read and edit, and works well in git reviews. When the bot starts, it
loads all 78 files and checks them. A test checks every field and length limit, so a bad
edit can't break the bot.

Card name search also needs a list of aliases ("3 of swords", "three swords", "III
swords", "Death", "XIII"). These are generated in code, not written by hand.

## 6. Writing workflow

1. **You approve the 3 samples.** Adjust the voice, length or fields until they feel
   right.
2. Write in batches, with your review after each:
   - Batch 1: Major Arcana (22 cards)
   - Batches 2–5: one suit each (14 cards per suit)
3. The test checks every batch's fields and lengths before you review it.
4. A final consistency pass checks that reversals follow rule 3, that keywords aren't
   repeated too often, and that the voice is the same across all 78 cards.

That's 78 cards at about 600 words each, roughly 45,000 words in total.

## 7. Open questions

- Should reversed meanings also get love, work and advice lines? That would add 234
  short lines. Recommendation: not in v1. The reversed meaning already covers it.
- Is `yes_no` worth keeping? It's popular, but some serious readers dislike it.
  Recommendation: keep it, but only use it when someone asks for a yes/no draw.
