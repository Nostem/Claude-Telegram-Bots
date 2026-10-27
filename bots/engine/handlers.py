"""Telegram handlers shared by every bot: feedback, payments, data deletion and the
loop that sends scheduled messages.

Each bot stores its services in application.bot_data (see `services`) and passes a
Brand with its own wording.
"""
import asyncio
import logging
from dataclasses import dataclass
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.constants import ParseMode
from telegram.error import Forbidden
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler,
                          PreCheckoutQueryHandler, filters)

from .db import utcnow
from .feedback import KINDS, LIFETIME_MENU
from .payments import FOUNDER_PAYLOAD, REFUND_DAYS

log = logging.getLogger(__name__)
LOOP_SECONDS = 30


@dataclass
class Brand:
    name: str                  # "Tarot Companion"
    lifetime_title: str        # invoice title
    lifetime_pitch: str        # what Lifetime unlocks, shown before buying (HTML)
    lifetime_thanks: str       # shown after buying (HTML)
    terms: str                 # /terms text (HTML)


def services(context):
    return context.bot_data


def btn(text, data):
    return InlineKeyboardButton(text, callback_data=data)


def keyboard(*rows):
    return InlineKeyboardMarkup([list(r) for r in rows])


async def reply(update, text, **kwargs):
    """Answer in the chat the update came from, whether a message or a button press."""
    kwargs.setdefault("parse_mode", ParseMode.HTML)
    return await update.effective_chat.send_message(text, **kwargs)


def is_lifetime(context, user_id):
    s = services(context)
    return s["payments"].is_lifetime(s["db"].get_user(user_id))


# Feedback

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_lifetime(context, user_id):
        rows = [[btn(KINDS[k], f"fb:{k}")] for k in LIFETIME_MENU]
        await reply(update, "What would you like to tell us?", reply_markup=InlineKeyboardMarkup(rows))
    else:
        await start_feedback(update, context, "bug")


async def feedback_kind_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await start_feedback(update, context, update.callback_query.data.split(":", 1)[1])


async def start_feedback(update, context, kind, card_id=None, card_name=None):
    s, user_id = services(context), update.effective_user.id
    if not s["feedback"].allowed(kind, is_lifetime(context, user_id)):
        await reply(update, "Ideas and card feedback are part of Lifetime. You can always "
                            "report something broken with /feedback.")
        return
    if not s["feedback"].can_send(user_id, utcnow()):
        await reply(update, "You've sent several messages today. Thank you! Please try again "
                            "tomorrow.")
        return
    context.user_data["awaiting"] = {"type": "feedback", "kind": kind, "card_id": card_id,
                                     "card_name": card_name}
    prompts = {
        "bug": "🐞 What went wrong? Describe what happened, and add a screenshot if it helps.",
        "payment": "💳 What's the problem with your payment? We'll reply here.",
        "idea": "💡 What would make this better? Tell us your idea.",
        "card": f"🃏 What's wrong with {escape(card_name) if card_name else 'the card'}? "
                "A typo, or a meaning you disagree with?",
        "other": "💬 Go ahead, we're listening.",
        "checkin": "👋 How's it going? Anything you wish it did?",
    }
    await reply(update, prompts[kind] + "\n\n<i>Send /cancel to stop.</i>")


async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE, awaiting):
    """Called by the bot's message router while a feedback prompt is open."""
    s, msg = services(context), update.effective_message
    context.user_data.pop("awaiting", None)
    now = utcnow()
    user = s["db"].get_user(update.effective_user.id)
    text = msg.text or msg.caption or ""
    fid = s["feedback"].record(user["id"], awaiting["kind"], text, now, awaiting.get("card_id"))
    admin_chat = s["settings"].admin_chat_id
    if admin_chat:
        try:
            header = s["feedback"].header(fid, awaiting["kind"], user, now, awaiting.get("card_name"))
            head_msg = await context.bot.send_message(
                admin_chat, header + "\n\nReply to this message to answer the user. "
                "Reply /done, /planned or /wontdo to set its status.")
            copy = await context.bot.copy_message(admin_chat, msg.chat_id, msg.message_id,
                                                  reply_to_message_id=head_msg.message_id)
            s["feedback"].link_admin_message(head_msg.message_id, fid)
            s["feedback"].link_admin_message(copy.message_id, fid)
        except Exception:
            log.exception("could not forward feedback %s", fid)
    await reply(update, "Thanks, we read every one of these. 🙏")


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The owner replied in the feedback group: pass the reply on to the user."""
    s, msg = services(context), update.effective_message
    fb = s["feedback"].for_admin_message(msg.reply_to_message.message_id)
    if fb is None:
        return
    try:
        await context.bot.send_message(fb["user_id"], "💬 <b>Reply from the team</b>",
                                       parse_mode=ParseMode.HTML)
        await context.bot.copy_message(fb["user_id"], msg.chat_id, msg.message_id)
        s["feedback"].link_admin_message(msg.message_id, fb["id"])
        await msg.reply_text("✓ Sent to the user.")
    except Forbidden:
        await msg.reply_text("The user has blocked the bot, so the reply couldn't be sent.")


async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/done, /planned or /wontdo as a reply to a feedback message."""
    s, msg = services(context), update.effective_message
    if not msg.reply_to_message:
        await msg.reply_text("Reply to a feedback message with this command.")
        return
    fb = s["feedback"].for_admin_message(msg.reply_to_message.message_id)
    if fb is None:
        await msg.reply_text("That isn't a feedback message.")
        return
    status = {"done": "done", "planned": "planned", "wontdo": "wont_do"}[
        msg.text.split()[0].lstrip("/").split("@")[0].lower()]
    s["feedback"].set_status(fb["id"], status)
    note = f"✓ Feedback {fb['id']} marked {status.replace('_', ' ')}."
    if status == "done" and fb["kind"] in ("idea", "card", "bug", "other"):
        snippet = (fb["text"] or "")[:120]
        try:
            await context.bot.send_message(
                fb["user_id"],
                f"✨ You told us: “{escape(snippet)}”\n\nIt's done now. Thank you for helping "
                "make this better!", parse_mode=ParseMode.HTML)
            note += " The user was told."
        except Forbidden:
            note += " The user has blocked the bot."
    await msg.reply_text(note)


# Payments

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = services(context)
    if update.callback_query:
        await update.callback_query.answer()
    if is_lifetime(context, update.effective_user.id):
        await reply(update, "You already have Lifetime. Thank you! 💛")
        return
    brand, settings = s["brand"], s["settings"]
    stars, payload, spots_left = s["payments"].price(settings)
    pitch = brand.lifetime_pitch
    if payload == FOUNDER_PAYLOAD:
        pitch += (f"\n\n🌟 <b>Founder price: {stars:,} Stars</b> instead of "
                  f"{settings.lifetime_stars:,}, for our first {settings.founder_limit} "
                  f"supporters. {spots_left} founder spot{'s' if spots_left != 1 else ''} left.")
    await reply(update, pitch)
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=brand.lifetime_title,
        description=f"One payment, no subscription. Full refund within {REFUND_DAYS} days if "
                    "you change your mind. See /terms.",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice("Lifetime (founder price)" if payload == FOUNDER_PAYLOAD
                             else "Lifetime access", stars)],
    )


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    expected = services(context)["payments"].expected_stars(query.invoice_payload,
                                                            services(context)["settings"])
    # A founder invoice stays valid even if the last spot went while the buyer was paying.
    if expected is None or query.total_amount != expected:
        await query.answer(ok=False, error_message="Something went wrong. Please try /upgrade again.")
    elif is_lifetime(context, query.from_user.id):
        await query.answer(ok=False, error_message="You already have Lifetime.")
    else:
        await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, pay = services(context), update.effective_message.successful_payment
    founder = pay.invoice_payload == FOUNDER_PAYLOAD
    s["payments"].record(pay.telegram_payment_charge_id, update.effective_user.id,
                         pay.total_amount, utcnow(), founder=founder)
    thanks = s["brand"].lifetime_thanks
    if founder:
        thanks += "\n\n🌟 <b>You're one of our founders.</b> Thank you for believing in this early."
    await reply(update, thanks)


async def refund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner only: /refund <charge id or user id> [force]"""
    s, msg = services(context), update.effective_message
    if update.effective_user.id not in s["settings"].admin_user_ids:
        return
    if not context.args:
        await msg.reply_text("Usage: /refund <charge id or user id> [force]")
        return
    payment = s["payments"].find(context.args[0])
    now = utcnow()
    if payment is None:
        await msg.reply_text("No payment found.")
        return
    if payment["refunded_at"]:
        await msg.reply_text("That payment was already refunded.")
        return
    if not s["payments"].within_refund_window(payment, now) and "force" not in context.args[1:]:
        await msg.reply_text(f"That payment is older than {REFUND_DAYS} days. Add 'force' to "
                             "refund it anyway.")
        return
    await context.bot.refund_star_payment(payment["user_id"], payment["charge_id"])
    s["payments"].mark_refunded(payment, now)
    await msg.reply_text(f"Refunded {payment['stars']} Stars and removed Lifetime.")
    try:
        await context.bot.send_message(payment["user_id"], "Your refund has been processed and "
                                       "your Stars are on their way back. Lifetime has been removed.")
    except Forbidden:
        pass


async def paysupport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update, f"💳 <b>Payment support</b>\n\nLifetime is a single payment in Telegram "
                        f"Stars. If you change your mind, you can get a full refund within "
                        f"{REFUND_DAYS} days of buying.")
    await start_feedback(update, context, "payment")


async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update, services(context)["brand"].terms, disable_web_page_preview=True)


# Deleting data

async def delete_my_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update, "⚠️ This permanently deletes everything we store about you: settings, "
                        "journal, schedules and feedback. It can't be undone.\n\n"
                        "<i>A Lifetime purchase is tied to your Telegram account and stays valid "
                        "after deletion; only the payment record itself is kept.</i>",
                reply_markup=keyboard([btn("Delete everything", "del:yes"), btn("Cancel", "del:no")]))


async def delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "del:yes":
        s = services(context)
        user_id = update.effective_user.id
        lifetime_at = s["db"].get_user(user_id)["lifetime_at"]
        s["db"].delete_user(user_id)
        if lifetime_at:   # keep what they paid for
            s["db"].get_user(user_id)
            s["db"].update_user(user_id, lifetime_at=lifetime_at, checkin_sent=1)
        context.user_data.clear()
        await query.edit_message_text("Done. Everything has been deleted. Send /start any time "
                                      "to begin again.")
    else:
        await query.edit_message_text("Cancelled. Nothing was deleted.")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the ids needed for setup (ADMIN_USER_IDS and ADMIN_CHAT_ID)."""
    await update.effective_message.reply_text(
        f"Your user id: {update.effective_user.id}\nThis chat's id: {update.effective_chat.id}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("awaiting", None)
    await reply(update, "Cancelled.")


# Scheduled messages

async def scheduler_tick(application, send_scheduled, now):
    """Send everything due at `now`: scheduled messages and two-week check-ins."""
    s = application.bot_data
    for row in s["schedules"].due(now):
        try:
            await send_scheduled(application, row)
        except Forbidden:
            # The user blocked the bot; stop sending until they come back.
            s["schedules"].set_paused(row["id"], True, row["timezone"], now)
            continue
        except Exception:
            log.exception("scheduled send failed for schedule %s", row["id"])
        s["schedules"].mark_run(row, now)
    for user in s["payments"].due_checkins(now):
        s["db"].update_user(user["id"], checkin_sent=1)
        try:
            await application.bot.send_message(
                user["id"], "👋 You've had Lifetime for two weeks now. How's it going? "
                "Anything you wish it did?", reply_markup=keyboard([btn("Tell us", "fb:checkin")]))
        except Forbidden:
            pass


async def run_scheduler(application, send_scheduled):
    """Run scheduler_tick every 30 seconds until the bot stops."""
    while True:
        try:
            await scheduler_tick(application, send_scheduled, utcnow())
        except Exception:
            log.exception("scheduler loop error")
        await asyncio.sleep(LOOP_SECONDS)


def register(application):
    """Add the shared handlers. Call before the bot's own catch-all message handler."""
    settings = application.bot_data["settings"]
    application.add_handler(CommandHandler("feedback", feedback_command, filters.ChatType.PRIVATE))
    application.add_handler(CallbackQueryHandler(feedback_kind_callback, pattern=r"^fb:"))
    application.add_handler(CommandHandler("upgrade", upgrade, filters.ChatType.PRIVATE))
    application.add_handler(CallbackQueryHandler(upgrade, pattern=r"^upgrade$"))
    application.add_handler(PreCheckoutQueryHandler(precheckout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    application.add_handler(CommandHandler("refund", refund))
    application.add_handler(CommandHandler("paysupport", paysupport, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("terms", terms))
    application.add_handler(CommandHandler("delete_my_data", delete_my_data, filters.ChatType.PRIVATE))
    application.add_handler(CallbackQueryHandler(delete_confirm, pattern=r"^del:"))
    application.add_handler(CommandHandler("cancel", cancel, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("myid", myid))
    if settings.admin_chat_id:
        group = filters.Chat(settings.admin_chat_id)
        application.add_handler(CommandHandler(["done", "planned", "wontdo"], admin_status, group))
        application.add_handler(MessageHandler(group & filters.REPLY & ~filters.COMMAND, admin_reply))
