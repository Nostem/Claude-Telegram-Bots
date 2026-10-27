from telegram import Bot

from bots.tarot import texts
from bots.tarot.profile import PROFILE_PHOTO, apply_profile
from tests.fake_telegram import FakeTelegram


def test_profile_texts_fit_telegram_limits():
    assert len(texts.PROFILE_NAME) <= 64
    assert len(texts.SHORT_DESCRIPTION) <= 120
    assert len(texts.DESCRIPTION) <= 512


async def test_apply_profile_sets_everything():
    fake = FakeTelegram()
    async with Bot("123:abc", request=fake) as bot:
        await apply_profile(bot)
    methods = fake.methods()
    for method in ("setMyName", "setMyShortDescription", "setMyDescription", "setMyCommands",
                   "setMyProfilePhoto"):
        assert method in methods
    assert PROFILE_PHOTO.stat().st_size < 1_000_000
