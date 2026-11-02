# One-time Stars donations

## Intent and scope
Add voluntary support to Sors Diei with `/donate`. The user delegated amount and implementation choices. Use the existing Python/python-telegram-bot/SQLite stack, with no new dependencies or recurring billing. Donations provide no perks, founder status, or Lifetime access.

## Chosen approach
Use standalone XTR invoices, with buttons for **25, 50, 100, 500 Stars** and a custom whole-number amount **1–10,000**. `/donate 75` is a direct shortcut; Custom asks for the amount and `/cancel` exits. Presets reduce friction; custom amounts preserve choice. Bound the input length before integer conversion. Do not use Telegram's invoice tip fields: they do not support Stars.

Alternatives: fixed-only amounts would be simpler but exclude user-chosen support; a channel's paid reactions require a channel and take users away from this bot. Standalone invoices fit the existing bot and were delegated to the implementer rather than explicitly selected by the user.

## Payment safety
- Add a separate `donations` SQLite table (charge ID primary key, user ID, Stars, UTC creation and optional refund timestamps). Existing databases upgrade additively at initialization.
- Payloads are canonical `donation:<amount>`. Accept only bounded whole-number amounts and XTR; precheckout must match the payload amount. Existing Lifetime checks remain intact.
- Successful payments dispatch by validated payload/currency/amount. Unknown/malformed payments grant nothing. Duplicate donation deliveries are idempotent, including after refund. Donation processing never changes Lifetime or founder sales.
- Owner-only `/refund_donation <charge ID or user ID> [force]` refunds donations, with the existing seven-day window and explicit override. Donation refunds never change Lifetime; `/refund` continues to address only Lifetime purchases.
- Clearly disclose voluntary/no-perks support, no subscription, payment support and refund policy. Keep transaction records for payment support when other user data is deleted. Never claim funds go straight into a personal Stars balance.

## Integration
Register `/donate` in the shared engine and the tarot command menu/help. Connect custom amount handling to the existing private text router. Keep donation-specific rules and persistence in `bots/engine/donations.py`; shared payment dispatch remains in `handlers.py`. Document owner refund and deployment steps in README/deploy README.

## Verification and release boundary
Use real in-memory/on-disk SQLite and the existing fake Telegram transport for offline conversation/payment tests. Cover additive upgrades, bounds, currency/amount/payload tampering, Lifetime donors, duplicates, refunds, cancel, data deletion, and menu registration. Run the entire existing suite and both content validators. Obtain a fresh whole-branch review. Push a feature branch/PR; merging master, production deployment, and spending/refunding real Stars require explicit approval. Do not use the live bot token in tests.

## Review-driven safety requirements
- Donation refund timeouts preserve the local receipt and provide an exact charge-ID retry. Only provider success or the explicit `CHARGE_ALREADY_REFUNDED` outcome confirms a refund; retry reconciles the receipt without recharging/refunding twice. No separate pending-state table is needed because the durable charge ID plus retry reconciles this outcome.
- Payment support gets a separate five-requests-per-24-hours quota. A limited support request stays in support state until cancel, rather than turning the next message into card lookup.
- If the group is absent, payment support forwards to the lowest configured owner ID's private bot chat, with reply relaying. This establishes a monitored alternative for this deployment; ordinary feedback remains group-only. Failed forwarding is acknowledged accurately instead of promising delivery.
- A Lifetime receipt grants access only on its first atomic insert; duplicate/refunded delivery cannot reset access or check-in state. This fixes an inherited issue identified by the payment-safety review.
- Persist accepted Lifetime checkout quotes by user, payload and amount, so a price change between checkout approval and successful settlement cannot discard a paid purchase. Remove matched approvals on receipt insertion. An old invoice not yet approved is still checked against current prices; this preserves the existing precheckout policy.
- Scope new support reply links by chat ID and message ID using additive `feedback_routes`; retain legacy group links for the configured group only. This prevents same-numbered messages in separate chats from crossing support conversations.
