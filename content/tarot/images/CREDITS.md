# Card image credits

**Artwork:** Pamela Colman Smith, for the Smith-Waite (RWS) tarot deck, published by
Rider & Son, London, 1909. Public domain: published before 1931 (US), and the artist died
in 1951 (life + 70 years).

**Scans:** the "RWS1909" set on Wikimedia Commons, scans of an original 1909 "Roses &
Lilies" printing from Saskia Jansen's personal collection. These are **not** the US Games
1971 recoloring, which carries a "© 1971 U.S. Games" line on the card edge and must not
be used.

| File (in `raw/` and `cards/`) | Card | Commons file |
|---|---|---|
| `major-00-the-fool.jpg` | The Fool | [File:RWS1909 - 00 Fool.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_00_Fool.jpeg) |
| `major-01-the-magician.jpg` | The Magician | [File:RWS1909 - 01 Magician.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_01_Magician.jpeg) |
| `major-02-the-high-priestess.jpg` | The High Priestess | [File:RWS1909 - 02 High Priestess.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_02_High_Priestess.jpeg) |
| `major-03-the-empress.jpg` | The Empress | [File:RWS1909 - 03 Empress.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_03_Empress.jpeg) |
| `major-04-the-emperor.jpg` | The Emperor | [File:RWS1909 - 04 Emperor.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_04_Emperor.jpeg) |
| `major-05-the-hierophant.jpg` | The Hierophant | [File:RWS1909 - 05 Hierophant.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_05_Hierophant.jpeg) |
| `major-06-the-lovers.jpg` | The Lovers | [File:RWS1909 - 06 Lovers.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_06_Lovers.jpeg) |
| `major-07-the-chariot.jpg` | The Chariot | [File:RWS1909 - 07 Chariot.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_07_Chariot.jpeg) |
| `major-08-strength.jpg` | Strength | [File:RWS1909 - 08 Strength.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_08_Strength.jpeg) |
| `major-09-the-hermit.jpg` | The Hermit | [File:RWS1909 - 09 Hermit.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_09_Hermit.jpeg) |
| `major-10-wheel-of-fortune.jpg` | Wheel of Fortune | [File:RWS1909 - 10 Wheel of Fortune.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_10_Wheel_of_Fortune.jpeg) |
| `major-11-justice.jpg` | Justice | [File:RWS1909 - 11 Justice.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_11_Justice.jpeg) |
| `major-12-the-hanged-man.jpg` | The Hanged Man | [File:RWS1909 - 12 Hanged Man.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_12_Hanged_Man.jpeg) |
| `major-13-death.jpg` | Death | [File:RWS1909 - 13 Death.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_13_Death.jpeg) |
| `major-14-temperance.jpg` | Temperance | [File:RWS1909 - 14 Temperance.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_14_Temperance.jpeg) |
| `major-15-the-devil.jpg` | The Devil | [File:RWS1909 - 15 Devil.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_15_Devil.jpeg) |
| `major-16-the-tower.jpg` | The Tower | [File:RWS1909 - 16 Tower.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_16_Tower.jpeg) |
| `major-17-the-star.jpg` | The Star | [File:RWS1909 - 17 Star.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_17_Star.jpeg) |
| `major-18-the-moon.jpg` | The Moon | [File:RWS1909 - 18 Moon.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_18_Moon.jpeg) |
| `major-19-the-sun.jpg` | The Sun | [File:RWS1909 - 19 Sun.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_19_Sun.jpeg) |
| `major-20-judgement.jpg` | Judgement | [File:RWS1909 - 20 Judgement.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_20_Judgement.jpeg) |
| `major-21-the-world.jpg` | The World | [File:RWS1909 - 21 World.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_21_World.jpeg) |
| `swords-03.jpg` | Three of Swords | [File:RWS1909 - Swords 03.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_Swords_03.jpeg) |
| `cups-queen.jpg` | Queen of Cups | [File:RWS1909 - Cups 13.jpeg](https://commons.wikimedia.org/wiki/File:RWS1909_-_Cups_13.jpeg) |

## How these copies were made

Wikimedia Commons is blocked by this environment's network policy. These review copies
came from the [mariano-fu/arcana](https://github.com/mariano-fu/arcana) project, which
resized the same RWS1909 Commons files to 600 px wide WebP. Its `CREDITS.md` records
each file's Commons source. We converted them to JPEG (quality 88).

- `raw/`: the scans as downloaded, unedited.
- `cards/`: the cleaned-up images the bot uses, made by `tools/clean_card_images.py`. The
  script straightens each card, crops the worn scan edges, brightens the paper while
  keeping the original colors, sharpens the line work slightly, and adds an even cream
  border.

**Before launch:** download the full-resolution originals (about 825 × 1429 px) directly
from Commons, check each file page still states the 1909 printing and public domain, and
regenerate all 78 images with one consistent process.
