"""Settings read from environment variables, one prefix per bot (e.g. TAROT_BOT_TOKEN)."""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    token: str
    db_path: str
    admin_chat_id: int | None      # private group where feedback arrives
    admin_user_ids: set[int]       # people allowed to run owner commands like /refund
    lifetime_stars: int            # regular Lifetime price in Telegram Stars
    founder_stars: int = 990       # launch price for the first founder_limit buyers
    founder_limit: int = 100       # 0 turns the founder price off

    @classmethod
    def from_env(cls, prefix, default_db):
        def env(name, default=None):
            return os.environ.get(f"{prefix}_{name}", default)

        token = env("BOT_TOKEN")
        if not token:
            raise SystemExit(f"Set {prefix}_BOT_TOKEN to the token from @BotFather.")
        admins = {int(x) for x in (env("ADMIN_USER_IDS") or "").replace(",", " ").split()}
        chat = env("ADMIN_CHAT_ID")
        return cls(
            token=token,
            db_path=env("DB_PATH", default_db),
            admin_chat_id=int(chat) if chat else None,
            admin_user_ids=admins,
            lifetime_stars=int(env("LIFETIME_STARS", "1650")),
            founder_stars=int(env("FOUNDER_STARS", "990")),
            founder_limit=int(env("FOUNDER_LIMIT", "100")),
        )
