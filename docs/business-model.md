# Business Model

Can one-time Lifetime purchases pay for servers that run forever? Yes: hosting is the
smallest cost, and each extra user costs almost nothing. The real question is sales
volume.

Figures below come from third-party sources (October 2026). Confirm them on Telegram's,
Fragment's and the hosting provider's own pages before setting prices.

## Costs

| Item | Cost |
|---|---|
| One small server (e.g. Hetzner, 2 CPUs, 4 GB RAM) | about €4–6 a month |
| Its IPv4 address | about €0.50 a month |
| Backups | about €1 a month |
| Telegram Bot API | free |
| AI | none (left out on purpose) |
| **Total** | **about $80–100 a year** |

**One server runs every bot in the product line.** The bots use SQLite and are
lightweight, and Telegram hosts card images after the first upload (the bot reuses
Telegram's file id), so bandwidth costs almost nothing. A server this size should handle
tens of thousands of users.

## Income per sale

- Telegram pays developers about **$0.013 per Star**.
- Withdrawals go through Fragment: at least 1,000 Stars at a time, each Star available 21
  days after it's received. Payouts arrive as TON (cryptocurrency), so expect a few
  percent in network and conversion fees.
- Buyers pay more than we receive: about $0.014–0.02 per Star, depending on how they buy
  Stars (app-store purchases cost the most).

| Price | Buyer pays (approx.) | We receive, before fees |
|---|---|---|
| 750 Stars (current default) | $11–15 | $9.75 |
| 1,000 Stars | $14–20 | $13.00 |
| 1,500 Stars | $21–30 | $19.50 |

**To decide:** whether the planned $10–20 is the buyer's price or our take. For a $10–20
take, the price is about 800–1,500 Stars.

## Break-even

About **10 sales a year** covers hosting for the whole product line. After that, nearly
everything is profit.

## Long-term risks

The server isn't the risk. Each Lifetime user costs a fraction of a cent a year. The real
risks are:

1. **Time:** support, fixes and new content.
2. **One-time revenue:** income depends on new sales, while costs continue.

## How it stays sustainable

1. **Fixed, tiny costs.** All bots on one server; nothing that costs more per user.
2. **More ways for existing users to buy:**
   - Each new bot is a new purchase, and every bot can mention the others.
   - The all-access bundle.
   - One-time add-ons: extra public-domain decks, seasonal content packs.
   - An optional tip jar in Stars.
   - Later, an optional AI add-on charged **per use**, so its cost is always covered by
     the person using it.
3. **Clear terms.** "Lifetime" means the lifetime of the product, with at least 30 days'
   notice and a chance to export the journal if a bot ever closes. This is in `/terms`.
   Not legal advice: worth a quick check by a professional before launch.
4. **Founder price.** A lower launch price for the first buyers, raised later. It rewards
   early users and spreads the word.

## The unknown: sales volume

Free-to-paid conversion is often quoted at around 2–5% of active users, though it varies
widely. At that rate, 100 sales a year (about $950 net at 750 Stars) needs very roughly
2,000–5,000 active free users. Growth is what matters: the free tier, shareable features
(inline card sharing, writing your name in runes) and the Reddit and Twitter launch.

## Sources

- [AdsGram: Telegram Stars prices and withdrawal](https://adsgram.ai/blog/adsgram/telegram-stars-explained-price-in-usd-how-to-earn-and-withdraw-)
- [AdminHub: withdrawing Telegram Stars](https://adminhub.tools/blog/withdraw-telegram-stars/)
- [StarsEarn calculator](https://starsearn.com/calculator)
- [Tribute: Stars for creators](https://tribute.top/blog/telegram-stars-creators-guide/)
- [Findstack: Hetzner 2026 price increase](https://findstack.com/resources/hetzner-price-increase-2026)
- [Deploywise: cheap VPS for developers](https://deploywise.dev/blog/cheap-vps-for-developers)
- [API Calculators: VPS comparison](https://apicalculators.com/cloud-vps-comparison)
