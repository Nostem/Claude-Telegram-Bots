"""Fixed wording for the tarot bot (Telegram HTML)."""
from bots.engine.handlers import Brand

NAME = "Tarot Companion"

WELCOME = (
    "🌙 <b>Welcome to Tarot Companion.</b>\n\n"
    "Look up any of the 78 cards, get a card each day, and keep a journal of your draws. "
    "Card art is the original 1909 Smith-Waite deck.\n\n"
    "No subscriptions, no ads, and your journal is never used for AI. Let's set a few "
    "things up first."
)

ASK_TIMEZONE = ("🕰 <b>Where are you?</b>\n\nThis is so your daily card arrives at the right "
                "time. Pick one, or type your city (for example: Toronto, Manila, Europe/Paris).")

ASK_REVERSALS = (
    "🔄 <b>Use reversed cards?</b>\n\n"
    "A card drawn upside down has its own meaning, often the card's energy blocked, turned "
    "inward or overdone. Some readers love them, others skip them. You can change this "
    "any time in /settings."
)

ASK_DAILY_TIME = "☀️ <b>Want a card every day?</b>\n\nPick a time and it will arrive each morning."

HELP = (
    "<b>What I can do</b>\n\n"
    "/daily · your card for today\n"
    "/card <i>name</i> · look up a card, e.g. <code>/card three of cups</code>\n"
    "/cards · browse the whole deck\n"
    "/journal · your past draws\n"
    "/schedule · your daily card time\n"
    "/settings · timezone, reversed cards and more\n"
    "/feedback · report a problem or share an idea\n"
    "/upgrade · Lifetime access\n"
    "/delete_my_data · delete everything we store\n"
    "/terms · terms and privacy\n\n"
    "You can also just type a card's name."
)

TERMS = (
    "<b>Terms and privacy</b>\n\n"
    "<b>What we store:</b> your Telegram user id, your settings (timezone, reversed cards, "
    "schedule), your journal of draws, and any feedback you send. Nothing else. We never see "
    "your phone number, and we don't sell or share your data.\n\n"
    "<b>Your journal is yours:</b> it is never used to train AI.\n\n"
    "<b>Feedback</b> is read by a person and used only to improve the bot.\n\n"
    "<b>Deleting:</b> /delete_my_data deletes everything, permanently.\n\n"
    "<b>Lifetime</b> is a one-time payment in Telegram Stars. Full refund within 7 days on "
    "request through /paysupport.\n\n"
    "<b>Tarot is for reflection and entertainment.</b> It isn't medical, legal, financial "
    "or psychological advice. If you're struggling, please reach out to someone you trust "
    "or a professional."
)

LIFETIME_PITCH = (
    "✨ <b>Lifetime: pay once, keep it forever</b>\n\n"
    "Free stays free: card lookup, a daily card, and your last 7 days of journal.\n\n"
    "Lifetime adds:\n"
    "• Your <b>full journal</b>, including every draw you've already made\n"
    "• Draws of 1 to 5 cards, and named spreads up to the Celtic Cross\n"
    "• Logging readings from your own physical deck\n"
    "• Notes, tags, mood and \"how did it play out?\" follow-ups\n"
    "• Unlimited schedules, the 78-day challenge and moon-timed draws\n"
    "• Stats, your own card meanings, and export to PDF, Markdown and more\n"
    "• Sending ideas and card feedback straight to us\n\n"
    "No subscription, ever."
)

LIFETIME_THANKS = (
    "💛 <b>Thank you! Lifetime is yours.</b>\n\n"
    "Your full journal is unlocked now. If anything ever feels off, /feedback reaches us "
    "directly. Changed your mind? You can get a full refund within 7 days through /paysupport."
)

BRAND = Brand(name=NAME, lifetime_title=f"{NAME} Lifetime", lifetime_pitch=LIFETIME_PITCH,
              lifetime_thanks=LIFETIME_THANKS, terms=TERMS)
