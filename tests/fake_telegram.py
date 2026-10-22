"""A stand-in for Telegram's Bot API, so whole conversations can be tested offline.

Every API call the bot makes is recorded in `calls` as (method, parameters) and answered
with a plausible response.
"""
import itertools
import json

from telegram import Update
from telegram.request import BaseRequest

BOT_ID = 999
USER_ID = 111
ADMIN_CHAT = -100500


class FakeTelegram(BaseRequest):
    def __init__(self):
        self.calls = []
        self._ids = itertools.count(1000)
        self.fail_for = set()   # chat ids that raise "bot was blocked"

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    @property
    def read_timeout(self):
        return None

    def _message(self, chat_id, **extra):
        chat_type = "private" if int(chat_id) > 0 else "supergroup"
        return {"message_id": next(self._ids), "date": 0,
                "chat": {"id": int(chat_id), "type": chat_type}, **extra}

    async def do_request(self, url, method, request_data=None, *args, **kwargs):
        name = url.rsplit("/", 1)[1]
        params = request_data.parameters if request_data else {}
        self.calls.append((name, params))
        chat_id = params.get("chat_id")
        if chat_id is not None and int(chat_id) in self.fail_for:
            return 403, json.dumps({"ok": False, "error_code": 403,
                                    "description": "Forbidden: bot was blocked by the user"}).encode()
        if name == "getMe":
            result = {"id": BOT_ID, "is_bot": True, "first_name": "Tarot", "username": "tarot_test_bot"}
        elif name == "sendPhoto":
            result = self._message(chat_id, photo=[{"file_id": f"photo-{next(self._ids)}",
                                                    "file_unique_id": "u", "width": 1, "height": 1}])
        elif name in ("sendMessage", "sendInvoice", "editMessageText"):
            result = self._message(chat_id or USER_ID, text=params.get("text", ""))
        elif name == "copyMessage":
            result = {"message_id": next(self._ids)}
        else:
            result = True
        return 200, json.dumps({"ok": True, "result": result}).encode()

    # Helpers for tests

    def methods(self):
        return [name for name, _ in self.calls]

    def last(self, method):
        return next(p for name, p in reversed(self.calls) if name == method)

    def texts(self):
        return [p.get("text") or p.get("caption") or "" for name, p in self.calls
                if name in ("sendMessage", "sendPhoto", "editMessageText")]


class Updates:
    """Builds Update objects as Telegram would send them."""

    def __init__(self, bot):
        self.bot = bot
        self._ids = itertools.count(1)

    def _user(self, user_id):
        return {"id": user_id, "is_bot": False, "first_name": "Test"}

    def message(self, text=None, user_id=USER_ID, chat_id=None, reply_to=None, photo=False, **extra):
        chat_id = chat_id or user_id
        msg = {"message_id": next(self._ids), "date": 0, "from": self._user(user_id),
               "chat": {"id": chat_id, "type": "private" if chat_id > 0 else "supergroup"}, **extra}
        if text is not None:
            msg["text"] = text
            if text.startswith("/"):
                msg["entities"] = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]
        if photo:
            msg["photo"] = [{"file_id": "p", "file_unique_id": "u", "width": 1, "height": 1}]
        if reply_to:
            msg["reply_to_message"] = {"message_id": reply_to, "date": 0,
                                       "chat": msg["chat"], "from": {"id": BOT_ID, "is_bot": True,
                                                                     "first_name": "Tarot"}}
        return Update.de_json({"update_id": next(self._ids), "message": msg}, self.bot)

    def callback(self, data, user_id=USER_ID):
        cq = {"id": str(next(self._ids)), "from": self._user(user_id), "chat_instance": "c", "data": data,
              "message": {"message_id": next(self._ids), "date": 0,
                          "chat": {"id": user_id, "type": "private"}, "text": "x"}}
        return Update.de_json({"update_id": next(self._ids), "callback_query": cq}, self.bot)

    def pre_checkout(self, payload="lifetime", user_id=USER_ID, amount=750):
        q = {"id": "pcq", "from": self._user(user_id), "currency": "XTR", "total_amount": amount,
             "invoice_payload": payload}
        return Update.de_json({"update_id": next(self._ids), "pre_checkout_query": q}, self.bot)

    def payment(self, user_id=USER_ID, amount=750, charge="charge-abc"):
        return self.message(user_id=user_id, successful_payment={
            "currency": "XTR", "total_amount": amount, "invoice_payload": "lifetime",
            "telegram_payment_charge_id": charge, "provider_payment_charge_id": ""})
