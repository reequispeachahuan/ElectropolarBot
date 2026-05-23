import pytest

from app.notifications.telegram_bot import TelegramNotifier, build_action_keyboard


def test_build_action_keyboard_is_empty_without_seace_url():
    assert build_action_keyboard() is None


def test_build_action_keyboard_includes_seace_url():
    keyboard = build_action_keyboard("https://example.com")

    assert keyboard is not None
    assert keyboard.inline_keyboard[0][0].url == "https://example.com"


def test_telegram_notifier_requires_token():
    notifier = TelegramNotifier(token=" ", chat_id="123")

    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        notifier._application(require_chat=True)


def test_telegram_notifier_requires_chat_for_sending():
    notifier = TelegramNotifier(token="token", chat_id="")

    with pytest.raises(RuntimeError, match="TELEGRAM_CHAT_ID"):
        notifier._application(require_chat=True)
