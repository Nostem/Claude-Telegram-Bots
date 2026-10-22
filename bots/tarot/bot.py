"""The tarot bot's Telegram handlers. Run with: python -m bots.tarot"""
import asyncio
import io
import logging
from datetime import date

from PIL import Image
from telegram import BotCommand, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from bots.engine import handlers as engine
from bots.engine.config import Settings
from bots.engine.db import Database, utcnow
from bots.engine.feedback import Feedback
from bots.engine.handlers import btn, keyboard, reply, services
from bots.engine.payments import Payments
from bots.engine.schedules import Schedules, parse_time
from bots.engine.timezones import COMMON, describe, find_timezones

from . import render, texts
from .cards import Deck
from .service import Tarot

log = logging.getLogger(__name__)

DAILY_TIMES = ["06:00", "07:00", "08:00", "09:00"]
GROUPS = [("major", "✨ Major Arcana"), ("wands", "🔥 Wands"), ("cups", "💧 Cups"),
          ("swords", "🗡 Swords"), ("pentacles", "🪙 Pentacles")]
COMMANDS = [
    ("daily", "Your card for today"),
    ("card", "Look up a card"),
    ("cards", "Browse the deck"),
    ("journal", "Your past draws"),
    ("schedule", "Your daily card time"),
    ("settings", "Timezone, reversed cards and more"),
    ("feedback", "Report a problem or share an idea"),
    ("upgrade", "Lifetime access"),
    ("help", "What I can do"),
]


def user_row(context, update):
    return services(context)["db"].get_user(update.effective_user.id)


# Sending cards

def card_keyboard(card, reversed_):
    rev = int(reversed_)
    return keyboard([btn("📖 More", f"more:{card.id}:{rev}"), btn("📜 Waite, 1910", f"waite:{card.id}")])


def card_image(card, reversed_):
    if not reversed_:
        return card.image_path.read_bytes()
    out = io.BytesIO()
    Image.open(card.image_path).rotate(180).save(out, "JPEG", quality=90)
    return out.getvalue()


async def send_card(bot, db, chat_id, card, reversed_, heading=None):
    """Send a card image with its caption. Each image is uploaded to Telegram once; after
    that its file_id is reused, which is much faster."""
    # The file size is part of the key, so a replaced image is uploaded again.
    key = (f"{card.data['image']}:{card.image_path.stat().st_size}:"
           f"{'reversed' if reversed_ else 'upright'}")
    file_id = db.get_file_id(key)
    msg = await bot.send_photo(chat_id, file_id or card_image(card, reversed_),
                               caption=render.caption(card, reversed_, heading),
                               parse_mode=ParseMode.HTML, reply_markup=card_keyboard(card, reversed_))
    if not file_id:
        db.set_file_id(key, msg.photo[-1].file_id)
    return msg


async def send_daily(update, context, heading_new="Your card for today"):
    s = services(context)
    user = user_row(context, update)
    _, card, rev, is_new = s["tarot"].daily(user, utcnow())
    heading = f"🌅 {heading_new}" if is_new else "🌅 Today's card (you've already drawn it today)"
    await send_card(context.bot, s["db"], update.effective_chat.id, card, rev, heading)


async def send_scheduled(application, row):
    """Called by the engine's scheduler loop when a daily-card schedule is due."""
    s = application.bot_data
    user = s["db"].get_user(row["user_id"])
    _, card, rev, _ = s["tarot"].daily(user, utcnow())
    await send_card(application.bot, s["db"], user["id"], card, rev, "🌅 Your card for today")


# Onboarding and settings

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = user_row(context, update)
    if user["onboarded"]:
        await reply(update, "🌙 Welcome back. Here's what I can do:\n\n" + texts.HELP)
        return
    context.user_data["flow"] = "onboard"
    await reply(update, texts.WELCOME)
    await ask_timezone(update, context)


async def ask_timezone(update, context):
    rows = [[btn(label, f"tz:{zone}") for label, zone in COMMON[i:i + 2]] for i in range(0, len(COMMON), 2)]
    context.user_data["awaiting"] = {"type": "timezone"}
    await reply(update, texts.ASK_TIMEZONE, reply_markup=InlineKeyboardMarkup(rows))


async def timezone_chosen(update, context, zone):
    s = services(context)
    user_id = update.effective_user.id
    context.user_data.pop("awaiting", None)
    s["db"].update_user(user_id, timezone=zone)
    s["schedules"].reschedule_user(user_id, zone, utcnow())
    await reply(update, f"✓ Timezone set to {describe(zone)}.")
    if context.user_data.get("flow") == "onboard":
        await reply(update, texts.ASK_REVERSALS,
                    reply_markup=keyboard([btn("Yes, use reversals", "rev:1"), btn("No, upright only", "rev:0")]))
    else:
        await show_settings(update, context)


async def timezone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await timezone_chosen(update, context, update.callback_query.data.split(":", 1)[1])


async def timezone_typed(update, context):
    matches = find_timezones(update.effective_message.text)
    if len(matches) == 1:
        await timezone_chosen(update, context, matches[0])
    elif matches:
        rows = [[btn(describe(z), f"tz:{z}")] for z in matches]
        await reply(update, "Which one did you mean?", reply_markup=InlineKeyboardMarkup(rows))
    else:
        await reply(update, "I couldn't find that place. Try a nearby big city, or a timezone "
                            "name like <code>Europe/London</code>.")


async def reversals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    on = query.data.endswith("1")
    services(context)["db"].update_user(update.effective_user.id, reversals=int(on))
    await query.edit_message_text(f"✓ Reversed cards {'on' if on else 'off'}.")
    if context.user_data.get("flow") == "onboard":
        await ask_daily_time(update, context, with_skip=True)
    else:
        await show_settings(update, context)


async def ask_daily_time(update, context, with_skip=False):
    row = [btn(t, f"dt:{t}") for t in DAILY_TIMES]
    extra = [btn("Another time", "dt:other")]
    if with_skip:
        extra.append(btn("Not now", "dt:none"))
    await reply(update, texts.ASK_DAILY_TIME, reply_markup=keyboard(row, extra))


async def daily_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":", 1)[1]
    if choice == "other":
        context.user_data["awaiting"] = {"type": "time"}
        await reply(update, "Type the time you'd like, for example <code>7:30</code> or <code>9pm</code>.")
    elif choice == "none":
        await query.edit_message_text("No problem. You can set a daily card any time with /schedule.")
        await finish_onboarding(update, context)
    else:
        await daily_time_chosen(update, context, choice)


async def daily_time_chosen(update, context, time_local):
    s = services(context)
    user = user_row(context, update)
    context.user_data.pop("awaiting", None)
    s["schedules"].set_daily(user["id"], time_local, user["timezone"], utcnow())
    await reply(update, f"✓ Your daily card will arrive at {time_local} every day.")
    if context.user_data.get("flow") == "onboard":
        await finish_onboarding(update, context)


async def time_typed(update, context):
    time_local = parse_time(update.effective_message.text)
    if time_local:
        await daily_time_chosen(update, context, time_local)
    else:
        await reply(update, "I didn't understand that time. Try something like <code>7:30</code> or <code>9pm</code>.")


async def finish_onboarding(update, context):
    services(context)["db"].update_user(update.effective_user.id, onboarded=1)
    context.user_data.pop("flow", None)
    await reply(update, "🌟 You're all set. Here's your first card:")
    await send_daily(update, context)
    await reply(update, "Type /help any time to see everything I can do.")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("flow", None)
    await show_settings(update, context)


async def show_settings(update, context):
    s = services(context)
    user = user_row(context, update)
    daily = s["schedules"].for_user(user["id"], "daily")
    daily_text = (f"{daily[0]['time_local']}{' (paused)' if daily[0]['paused'] else ''}"
                  if daily else "off")
    text = ("⚙️ <b>Settings</b>\n\n"
            f"🕰 Timezone: {describe(user['timezone'] or 'UTC')}\n"
            f"🔄 Reversed cards: {'on' if user['reversals'] else 'off'}\n"
            f"☀️ Daily card: {daily_text}\n"
            f"📣 What's new messages: {'on' if user['whats_new'] else 'off'}\n"
            f"✨ Plan: {'Lifetime' if user['lifetime_at'] else 'Free'}")
    rev_next = 0 if user["reversals"] else 1
    await reply(update, text, reply_markup=keyboard(
        [btn("Change timezone", "set:tz")],
        [btn(f"Turn reversals {'off' if user['reversals'] else 'on'}", f"rev:{rev_next}")],
        [btn("Daily card time", "set:daily")],
        [btn(f"Turn what's new {'off' if user['whats_new'] else 'on'}", "set:news")],
    ))


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    what = query.data.split(":", 1)[1]
    if what == "tz":
        await ask_timezone(update, context)
    elif what == "daily":
        await ask_daily_time(update, context)
    elif what == "news":
        user = user_row(context, update)
        services(context)["db"].update_user(user["id"], whats_new=0 if user["whats_new"] else 1)
        await show_settings(update, context)


# Cards

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_daily(update, context)


async def card_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await reply(update, "Which card? For example <code>/card three of cups</code> or "
                            "<code>/card the moon</code>. Or browse them all with /cards.")
        return
    await look_up(update, context, query)


async def look_up(update, context, query):
    card = services(context)["deck"].find(query)
    if card is None:
        await reply(update, "I couldn't find that card. Try a name like <i>queen of cups</i> or "
                            "<i>the tower</i>, or browse with /cards.")
        return
    await send_card(context.bot, services(context)["db"], update.effective_chat.id, card, False)


async def cards_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [[btn(label, f"browse:{group}")] for group, label in GROUPS]
    await reply(update, "📚 <b>Browse the deck</b>", reply_markup=InlineKeyboardMarkup(rows))


async def browse_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group = query.data.split(":", 1)[1]
    if group == "back":
        await query.edit_message_text("📚 <b>Browse the deck</b>", parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup(
                                          [[btn(label, f"browse:{g}")] for g, label in GROUPS]))
        return
    cards = services(context)["deck"].in_group(group)
    rows = [[btn(c.name, f"show:{c.id}") for c in cards[i:i + 2]] for i in range(0, len(cards), 2)]
    rows.append([btn("⬅️ Back", "browse:back")])
    label = dict(GROUPS)[group]
    await query.edit_message_text(f"📚 <b>{label}</b>", parse_mode=ParseMode.HTML,
                                  reply_markup=InlineKeyboardMarkup(rows))


async def show_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    s = services(context)
    card = s["deck"][query.data.split(":", 1)[1]]
    await send_card(context.bot, s["db"], update.effective_chat.id, card, False)


async def more_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, card_id, rev = query.data.split(":")
    card = services(context)["deck"][card_id]
    markup = None
    if engine.is_lifetime(context, update.effective_user.id):
        markup = keyboard([btn("⚠️ Something wrong with this card?", f"report:{card_id}")])
    await reply(update, render.full_text(card, rev == "1"), reply_markup=markup)


async def waite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    card = services(context)["deck"][query.data.split(":", 1)[1]]
    await reply(update, render.waite_text(card))


async def report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    card = services(context)["deck"][update.callback_query.data.split(":", 1)[1]]
    await engine.start_feedback(update, context, "card", card_id=card.id, card_name=card.name)


# Journal and schedule

async def journal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_journal(update, context, 0)


async def journal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await show_journal(update, context, int(update.callback_query.data.split(":", 1)[1]))


async def show_journal(update, context, page, per_page=10):
    s = services(context)
    user = user_row(context, update)
    lifetime = s["payments"].is_lifetime(user)
    entries, visible, hidden = s["tarot"].journal_page(user, utcnow(), lifetime, page, per_page)
    if not entries:
        text = "📓 Your journal is empty. Draw your first card with /daily."
        if hidden:
            text = (f"📓 You have {hidden} saved draw{'s' if hidden != 1 else ''} older than 7 "
                    "days. Unlock them with /upgrade.")
        await reply(update, text)
        return
    lines = ["📓 <b>Your journal</b>" + ("" if lifetime else " (last 7 days)"), ""]
    for row, cards in entries:
        day = date.fromisoformat(row["local_date"]).strftime("%a %d %b %Y")
        lines.append(f"<b>{day}</b> · {', '.join(render.card_line(c, r) for c, r in cards)}")
    nav = []
    if page > 0:
        nav.append(btn("⬅️ Newer", f"jr:{page - 1}"))
    if (page + 1) * per_page < visible:
        nav.append(btn("Older ➡️", f"jr:{page + 1}"))
    rows = [nav] if nav else []
    if hidden:
        lines += ["", f"🔒 {hidden} older draw{'s are' if hidden != 1 else ' is'} saved. "
                      "Lifetime unlocks your full journal."]
        rows.append([btn("✨ See Lifetime", "upgrade")])
    await reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(rows) if rows else None)


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = services(context)
    user = user_row(context, update)
    daily = s["schedules"].for_user(user["id"], "daily")
    if not daily:
        await ask_daily_time(update, context)
        return
    row = daily[0]
    state = "paused" if row["paused"] else "on"
    await reply(update, f"☀️ <b>Daily card:</b> {row['time_local']} every day ({state}).",
                reply_markup=keyboard(
                    [btn("Change time", "set:daily")],
                    [btn("Resume" if row["paused"] else "Pause", f"sp:{row['id']}:{0 if row['paused'] else 1}"),
                     btn("Turn off", f"sd:{row['id']}")]))


async def schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    s = services(context)
    user = user_row(context, update)
    parts = query.data.split(":")
    owned = {r["id"] for r in s["schedules"].for_user(user["id"])}
    schedule_id = int(parts[1])
    if schedule_id not in owned:
        return
    if parts[0] == "sp":
        paused = parts[2] == "1"
        s["schedules"].set_paused(schedule_id, paused, user["timezone"], utcnow())
        await query.edit_message_text(f"✓ Daily card {'paused' if paused else 'resumed'}.")
    else:
        s["schedules"].delete(schedule_id)
        await query.edit_message_text("✓ Daily card turned off. Turn it back on with /schedule.")


# Everything else

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update, texts.HELP)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Plain messages: answers to an open question, otherwise a card search."""
    awaiting = context.user_data.get("awaiting")
    kind = awaiting["type"] if awaiting else None
    if kind == "feedback":
        await engine.receive_feedback(update, context, awaiting)
    elif kind == "timezone" and update.effective_message.text:
        await timezone_typed(update, context)
    elif kind == "time" and update.effective_message.text:
        await time_typed(update, context)
    elif update.effective_message.text:
        await look_up(update, context, update.effective_message.text)


def build_application(settings, db=None, request=None):
    """The configured bot. Tests pass a database and a fake Telegram `request`."""
    db = db or Database(settings.db_path)
    deck = Deck()
    builder = (Application.builder().token(settings.token)
               .post_init(_post_init).post_shutdown(_post_shutdown))
    if request:
        builder = builder.request(request).get_updates_request(request)
    application = builder.build()
    application.bot_data.update(
        db=db, deck=deck, settings=settings, brand=texts.BRAND, tarot=Tarot(db, deck),
        schedules=Schedules(db), feedback=Feedback(db), payments=Payments(db))

    private = filters.ChatType.PRIVATE
    application.add_handler(CommandHandler("start", start, private))
    application.add_handler(CommandHandler("help", help_command, private))
    application.add_handler(CommandHandler("daily", daily_command, private))
    application.add_handler(CommandHandler("card", card_command, private))
    application.add_handler(CommandHandler("cards", cards_command, private))
    application.add_handler(CommandHandler("journal", journal_command, private))
    application.add_handler(CommandHandler("schedule", schedule_command, private))
    application.add_handler(CommandHandler("settings", settings_command, private))
    application.add_handler(CallbackQueryHandler(timezone_callback, pattern=r"^tz:"))
    application.add_handler(CallbackQueryHandler(reversals_callback, pattern=r"^rev:"))
    application.add_handler(CallbackQueryHandler(daily_time_callback, pattern=r"^dt:"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^set:"))
    application.add_handler(CallbackQueryHandler(browse_callback, pattern=r"^browse:"))
    application.add_handler(CallbackQueryHandler(show_callback, pattern=r"^show:"))
    application.add_handler(CallbackQueryHandler(more_callback, pattern=r"^more:"))
    application.add_handler(CallbackQueryHandler(waite_callback, pattern=r"^waite:"))
    application.add_handler(CallbackQueryHandler(report_callback, pattern=r"^report:"))
    application.add_handler(CallbackQueryHandler(journal_callback, pattern=r"^jr:"))
    application.add_handler(CallbackQueryHandler(schedule_callback, pattern=r"^s[pd]:"))
    engine.register(application)
    application.add_handler(MessageHandler(
        private & (filters.TEXT | filters.PHOTO) & ~filters.COMMAND, text_router))
    return application


async def _post_init(application):
    await application.bot.set_my_commands([BotCommand(c, d) for c, d in COMMANDS])
    application.bot_data["scheduler"] = asyncio.create_task(
        engine.run_scheduler(application, send_scheduled))


async def _post_shutdown(application):
    task = application.bot_data.get("scheduler")
    if task:
        task.cancel()


def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = Settings.from_env("TAROT", "data/tarot.sqlite3")
    build_application(settings).run_polling(allowed_updates=Update.ALL_TYPES)
