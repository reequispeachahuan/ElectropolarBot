from __future__ import annotations

from dataclasses import dataclass

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application

from app.config.settings import settings


@dataclass(frozen=True)
class TelegramChat:
    chat_id: int | str
    title: str
    chat_type: str
    username: str | None = None


def build_action_keyboard(seace_url: str | None = None) -> InlineKeyboardMarkup | None:
    if not seace_url:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton("Ver en SEACE", url=seace_url)]])


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self.token = token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id

    async def test_connection(self) -> str:
        app = self._application(require_chat=False)
        async with app:
            bot = await app.bot.get_me()
        return bot.username or bot.first_name or str(bot.id)

    async def recent_chats(self) -> list[TelegramChat]:
        app = self._application(require_chat=False)
        async with app:
            updates = await app.bot.get_updates(timeout=10)

        chats: dict[int | str, TelegramChat] = {}
        for update in updates:
            chat = update.effective_chat
            if chat is None:
                continue
            title = chat.title or chat.full_name or chat.username or str(chat.id)
            chats[chat.id] = TelegramChat(
                chat_id=chat.id,
                title=title,
                chat_type=chat.type,
                username=chat.username,
            )
        return list(chats.values())

    async def send_message(self, text: str, seace_url: str | None = None) -> int:
        app = self._application(require_chat=True)
        async with app:
            message = await app.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=build_action_keyboard(seace_url),
                disable_web_page_preview=True,
            )
        return message.message_id

    def _application(self, require_chat: bool) -> Application:
        token = (self.token or "").strip()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN es obligatorio")
        if require_chat and not str(self.chat_id or "").strip():
            raise RuntimeError("TELEGRAM_CHAT_ID es obligatorio")
        return Application.builder().token(token).build()
