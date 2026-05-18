from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application

from app.config.settings import settings


def build_action_keyboard(seace_url: str | None = None) -> InlineKeyboardMarkup:
    buttons = []
    if seace_url:
        buttons.append([InlineKeyboardButton("Ver en SEACE", url=seace_url)])
    buttons.extend(
        [
            [InlineKeyboardButton("Marcar como revisar", callback_data="status:revisar_bases")],
            [InlineKeyboardButton("Marcar como postular", callback_data="status:postular")],
            [InlineKeyboardButton("Descartar", callback_data="status:descartada")],
            [InlineKeyboardButton("Asignar a técnico", callback_data="assign:tecnico")],
        ]
    )
    return InlineKeyboardMarkup(buttons)


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self.token = token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id

    async def send_message(self, text: str, seace_url: str | None = None) -> None:
        if not self.token or not self.chat_id:
            raise RuntimeError("TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID son obligatorios para enviar alertas")
        app = Application.builder().token(self.token).build()
        async with app:
            await app.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=build_action_keyboard(seace_url),
                disable_web_page_preview=True,
            )
