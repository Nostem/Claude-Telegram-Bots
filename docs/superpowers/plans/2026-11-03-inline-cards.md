# Inline card sharing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make inline card search, browse-all pagination and shareable photo posts work.

**Architecture:** A focused `bots/tarot/inline.py` module handles deterministic search and photo-result construction. The existing Application registers its handler and `/start` recognizes strict card deep links. Reuse Deck, caption/full_text rendering, and the media cache; never upload media in an inline query.

**Tech Stack:** Existing Python 3.11+, python-telegram-bot, SQLite, pytest; no new dependencies.

**Spec:** docs/superpowers/specs/2026-11-03-inline-cards-design.md

## Global Constraints
- 78 upright cards; 20 results/page; photo captions below 1024 parsed characters.
- Real public JPEG URLs pinned to existing commit 71c782a1ddee56ee8e60c756d09f9e45dc31444a; cached upright file IDs preferred.
- Inline queries create no user or journal records, send no messages and perform no uploads.
- No database migration, dependency additions, entitlement changes, merge or deployment.

## Review Focus
- Partial ambiguous queries such as `queen`, suit aliases and filler words must show relevant results, not a single arbitrary fuzzy card.
- Invalid, huge or stale pagination offsets must terminate safely and never repeat a page forever.
- Cold media caches must return sendable public artwork without owner-chat uploads or token-bearing URLs.
- Deep links for new users and users inside an active prompt must not mutate onboarding/settings or intercept ordinary `/start`.
- Every card must satisfy caption, stable ID, deep-link payload and public JPEG requirements; unsupported input must still get an answer.

---

### Task 1: Deterministic card search and paging

**Files:**
- Create: `bots/tarot/inline.py`
- Create: `tests/test_inline.py`

**Interfaces:**
- Consumes: existing `Deck.cards`, `Deck.find(query)`, `Deck.in_group(group)`, `_words`, `SUIT_ALIASES`, `RANKS`, `ROMAN`.
- Produces: `search_cards(deck: Deck, query: str) -> list[Card]`; `card_page(deck: Deck, query: str, offset: str) -> tuple[list[Card], str]`.

- [ ] **Step 1: Write search tests**: empty query yields 78 unique cards starting `major-00-the-fool`; `moon`, `3 cups`, `queen of coins`, `III swords`, `hanged`, `mooon` resolve to the literal expected card IDs; `queen` has four queens; `cups`/`chalices` have fourteen Cups; `major arcana` has 22; punctuation/non-Latin/unmatched queries are empty.
- [ ] **Step 2: Run RED**: `python -m pytest -q tests/test_inline.py`; expected missing feature failures.
- [ ] **Step 3: Implement search and page helpers** with exact matches first, normalized prefix/token matches next and existing fuzzy lookup only as fallback. Use stable deck order and bounded ASCII decimal offset validation.
- [ ] **Step 4: Add/run pagination tests**: pages contain 20,20,20,18 distinct cards; final offset is empty; negative, nondecimal, oversized and beyond-end offsets return `([], '')`. Expected targeted tests green.
- [ ] **Step 5: Run full suite and commit**: `python -m pytest -q -p no:cacheprovider`; expected all pass; `git commit -m 'feat: add deterministic inline card search and paging'`.

### Task 2: Inline photo integration, full-meaning deep links and docs

**Files:**
- Modify: `bots/tarot/inline.py`, `bots/tarot/bot.py`, `bots/tarot/texts.py`, `tests/fake_telegram.py`, `tests/test_inline.py`, `README.md`, `deploy/README.md`

**Interfaces:**
- Consumes: Task 1 helpers and existing `render.caption`, `render.full_text`, `db.get_file_id`, `send_card`.
- Produces: async `inline_query(update, context)` registered as `InlineQueryHandler`; strict `/start card_<id>` handling before normal onboarding.

- [ ] **Step 1: Write integration RED tests** through real Application with FakeTelegram transport. Add `Updates.inline(query, offset='', user_id=USER_ID)` fixture builder. Assert answerInlineQuery payloads for empty/search/no-match/invalid-offset; assert one answer, no sendMessage/sendPhoto, no user/draw changes. Assert cached photos use the correct upright key and cold photos have public JPEG URLs, short captions, URL-only full-meaning buttons, stable unique IDs and `next_offset`.
- [ ] **Step 2: Run RED**: `python -m pytest -q tests/test_inline.py`; expected missing answerInlineQuery or deep-link behavior failures.
- [ ] **Step 3: Implement handler** returning cached/photo results with explicit 60s public cache, `next_offset`, gallery layout and zero upload calls. Register handler in build_application. Link to the actual bot username; no hard-coded production account in tests.
- [ ] **Step 4: Write deep-link RED tests**: `/start card_major-18-the-moon` shows that image and full meaning for a new user and an onboarded user, produces no draw/schedule and preserves prompt/timezone/onboarding. Invalid or extra payload arguments return useful text and no card. Ordinary `/start` still onboards normally. Implement the strict card-link path.
- [ ] **Step 5: Document usage and release checks**, including blank-query browsing, aliases, upright sharing, private full-meaning links, BotFather inline prerequisite, public images, no query storage and no deployment broadcasts.
- [ ] **Step 6: Run all checks and commit**: full `pytest`, `tools/check_cards.py`, `tools/check_waite.py`, `pip check`, `git diff --check`; expected all pass. Validate all 78 public JPEG URLs and caption/deep-link limits. `git commit -m 'feat: answer inline card queries and open full interpretations'`.

## Final review and handoff
- [ ] Independent whole-branch review with the spec, plan, exact base/head and ledger rulings. Fix significant findings using RED→GREEN then full suite; document minor limitations.
- [ ] Publish the reviewed feature branch/PR and read its exact head back. Do not merge or deploy without release approval.
