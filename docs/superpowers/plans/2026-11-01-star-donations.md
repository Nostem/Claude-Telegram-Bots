# Stars Donations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one-time optional XTR donations without affecting Lifetime purchases.

**Architecture:** A separate donations ledger and rule module validates amounts/payloads and stores idempotent transactions. Shared handlers route donation invoices/checkout/success/refunds separately from Lifetime, and the tarot router/menu expose the feature.

**Tech Stack:** Python 3.11+, python-telegram-bot 22.8, SQLite, pytest; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-11-01-star-donations-design.md`

## Global Constraints
- Presets: 25, 50, 100, 500 Stars. Custom: whole numbers 1–10,000 inclusive.
- Currency XTR; canonical payload `donation:<amount>`; no tip fields, recurring billing or perks.
- Preserve existing data, Lifetime/refund behavior and founder counts.
- Donation refunds are owner-only with the existing seven-day window and `force` override.
- No live credentials or real money in tests. Feature branch/PR only; release requires approval.

## Review Focus
- Duplicate/refunded delivery must not re-record a donation or resurrect entitlements: task 1 tests duplicate and refunded replay.
- Donation from an existing Lifetime user and its refund must leave the original purchase unchanged: task 1 covers both.
- Malformed, wrong-currency and amount-mismatched successful payments must not grant access or enter a ledger: task 1 exercises each.
- An already-running database must gain the table without losing users/payments: task 1 opens a legacy-shaped on-disk database.
- Custom input must not become a card lookup or survive `/cancel`: task 1 uses conversation-level assertions.

### Task 1: Implement and verify donations end to end

**Files:**
- Create: `bots/engine/donations.py`, `tests/test_donations.py`
- Modify: `bots/engine/db.py`, `bots/engine/handlers.py`, `bots/tarot/bot.py`, `bots/tarot/texts.py`
- Modify tests: `tests/test_bot_flows.py`, `tests/fake_telegram.py`
- Documentation: `README.md`, `deploy/README.md`

**Interfaces:**
- Consumes: `Database.execute/one/all`, `Settings.admin_user_ids`, existing `Payments` Lifetime API, `REFUND_DAYS`, `iso/parse_iso`, existing bot test fixture and fake update builders.
- Produces: `Donations(db)` with `amount(text) -> int | None`, `expected_stars(payload) -> int | None`, `record(charge_id,user_id,stars,now) -> bool`, `find(charge_or_user) -> Row | None`, `mark_refunded(row,now)`, `within_refund_window(row,now) -> bool`; `PRESETS=(25,50,100,500)` and `MAX_STARS=10000`.
- Produces handler functions `donate`, `donation_callback`, `donation_amount`, `refund_donation`; `application.bot_data['donations']`.

- [ ] **Step 1: Write failing tests.** Extend fake checkout/payment builders with optional currency. In existing conversation tests assert `/donate` presents literal preset callbacks, Custom sets amount state, `/donate 75`/custom `75` send one XTR invoice for 75 with `donation:75`, and bounds/invalid/cancel never send invoices. Assert donation checkout works for existing Lifetime users, tampering is rejected, donation success is recorded once and leaves Lifetime/founders unchanged, refunds require the owner and preserve Lifetime, seven-day/force behavior works, data deletion retains donation receipts, and menu/help expose donate. Add real SQLite rule/migration tests in `tests/test_donations.py`.
- [ ] **Step 2: Run RED.** `/Users/fredm/.hermes/cache/scratch/claude-telegram-bots-venv/bin/python -m pytest -q tests/test_donations.py tests/test_bot_flows.py`. Expected: new tests fail because donate behavior/table/module is absent; existing tests stay green. Record exact failure evidence.
- [ ] **Step 3: Implement.** Add the additive table and module; wire separate invoice/checkout/success/refund paths and private custom input. Validate successful Lifetime payments as well as donations before any grant. Add help/menu/terms and operational documentation. Avoid unrelated changes.
- [ ] **Step 4: Run GREEN and full verification.** Run bare `python -m pytest -q -p no:cacheprovider` through the scratch interpreter, then `python tools/check_cards.py`, `python tools/check_waite.py`, `python -m pip check`, `git diff --check`. Expected: every test/content/dependency check passes; no live API calls.
- [ ] **Step 5: Commit.** Commit the feature and tests on `feat/star-donations`. Generate a whole-branch review package from base `400784e0b7f66c34ee30775a86d4d79603b93a4b`, dispatch an independent review, fix Important/Critical findings with RED→GREEN and green full suite, then push branch and open a PR. Verify the remote PR branch/head by reading it back; do not merge or deploy without approval.
