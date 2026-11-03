# Inline card sharing design

## Intent and approval
Implement the recommendation accepted in chat: search or browse cards from `@SorsDiei_bot`, select a preview, and post its image with name, keywords and short upright meaning. Offer an **Open full interpretation** URL into the bot's private chat. The user explicitly requested implementation; use native execution with one independent whole-branch review.

## Approach
Use Telegram photo inline results with public, immutable GitHub-hosted JPEG URLs (the artwork already exists in the public repository). Prefer an existing upright Telegram photo file ID when available. This avoids uploading the whole deck into the owner's chat. A text-only article loses the requested card image; pre-uploading every card would create needless live-message traffic. Both were rejected in favor of photo results with a cached-photo fast path.

## Behavior
- Empty/whitespace query: all 78 cards in Major Arcana, Wands, Cups, Swords, Pentacles order; 20 results per page, then 18 on the last page.
- Search by card name, partial words, rank, suit and existing aliases; exact/alias match first, then deterministic matching cards; typo fallback only when there are no direct matches.
- Accept `major`/`major arcana` as the Major Arcana group. Non-Latin, punctuation-only or unrelated nonempty searches return no results, not the full deck.
- An unmatched query always receives a valid empty answer; malformed/out-of-range offsets receive an empty final page. No offset reuse can trigger external requests or unbounded integer parsing.
- Posts include the existing escaped upright caption (under Telegram's 1024-character parsed limit), unique stable IDs, image thumbnails, and a URL button `https://t.me/<current bot username>?start=card_<card-id>`.
- Card deep links work before and after onboarding, show the card and full interpretation, and do not overwrite timezone, onboarding state, open prompts, schedules, entitlements, or daily draws. Invalid `card_` payloads return a useful message instead of starting onboarding or selecting a different card.
- Inline queries do not create users, record queries, write journals, send private messages, consume premium access, or run network uploads.
- No new dependencies or database migration. Existing private-chat commands and donation/payment behavior remain unchanged.
- No new support for reversed inline imagery in this iteration; browsing/sharing is upright.

## Verification/release boundary
Run offline integration tests through the actual configured Application and fake API transport, the full suite, content validators, dependency and whitespace checks. Verify every public artwork URL without sending messages to users. Independently review the branch. Implementation does not authorize a merge or production deployment; report the tested artifact and ask before release. No test broadcasts or automatic deployment announcements.
