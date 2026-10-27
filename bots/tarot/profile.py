"""Apply the bot's public profile: name, descriptions, command menu and profile photo.

Run once after creating the bot, and again whenever the texts or photo change:
    python -m bots.tarot.profile

The description picture (shown above "What can this bot do?") can't be set through the
Bot API; upload content/brand/description.jpg in @BotFather: /mybots > your bot >
Edit Bot > Edit Description Picture.
"""
import asyncio
from pathlib import Path

from telegram import Bot, BotCommand, InputProfilePhotoStatic

from bots.engine.config import Settings

from . import texts
from .bot import COMMANDS

PROFILE_PHOTO = Path(__file__).resolve().parents[2] / "content" / "brand" / "profile.jpg"


async def apply_profile(bot):
    await bot.set_my_name(texts.PROFILE_NAME)
    await bot.set_my_short_description(texts.SHORT_DESCRIPTION)
    await bot.set_my_description(texts.DESCRIPTION)
    await bot.set_my_commands([BotCommand(c, d) for c, d in COMMANDS])
    await bot.set_my_profile_photo(InputProfilePhotoStatic(PROFILE_PHOTO.read_bytes()))


async def main():
    settings = Settings.from_env("TAROT", "data/tarot.sqlite3")
    async with Bot(settings.token) as bot:
        await apply_profile(bot)
        me = await bot.get_me()
    print(f"Profile updated for @{me.username}. Now upload content/brand/description.jpg "
          "in @BotFather: /mybots > your bot > Edit Bot > Edit Description Picture.")


if __name__ == "__main__":
    asyncio.run(main())
