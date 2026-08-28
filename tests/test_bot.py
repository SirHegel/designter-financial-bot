import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from bot import build_bot
from settings import Settings


class FakeSheet:
    def __init__(self):
        self.rows = []

    def append_row(self, row, **options):
        self.rows.append((row, options))


class FakeDocument:
    def __init__(self, sheet):
        self.sheet = sheet

    def worksheet(self, _name):
        return self.sheet


class FakeBot:
    def __init__(self, _token):
        self.handlers = []
        self.replies = []

    def message_handler(self, **filters):
        def register(callback):
            self.handlers.append((filters, callback))
            return callback

        return register

    def reply_to(self, message, text, **options):
        self.replies.append((message, text, options))


class BotTests(unittest.TestCase):
    def build_test_bot(self):
        sheet = FakeSheet()
        fake_bot = FakeBot("test-only-value")
        fake_gspread = SimpleNamespace(
            WorksheetNotFound=type("WorksheetNotFound", (Exception,), {}),
            service_account_from_dict=lambda *_args, **_options: SimpleNamespace(
                open=lambda _name: FakeDocument(sheet)
            ),
        )
        fake_telebot = SimpleNamespace(TeleBot=lambda _token: fake_bot)

        settings = Settings(
            telegram_bot_token="test-only-value",
            telegram_allowed_chat_ids=frozenset({123}),
            google_service_account={"kind": "test"},
            google_sheets_document="TestDocument",
        )
        with patch.dict(
            sys.modules,
            {"gspread": fake_gspread, "telebot": fake_telebot},
        ):
            built_bot = build_bot(settings)
        return built_bot, sheet

    @staticmethod
    def catch_all_handler(bot):
        return next(callback for filters, callback in bot.handlers if "func" in filters)

    def test_rejects_a_chat_outside_the_allowlist(self):
        bot, sheet = self.build_test_bot()
        message = SimpleNamespace(chat=SimpleNamespace(id=999), text="designter 1000")

        self.catch_all_handler(bot)(message)

        self.assertEqual(sheet.rows, [])
        self.assertIn("no está autorizado", bot.replies[0][1])

    def test_writes_authorized_messages_as_raw_values(self):
        bot, sheet = self.build_test_bot()
        message = SimpleNamespace(chat=SimpleNamespace(id=123), text="designter 1.000")

        self.catch_all_handler(bot)(message)

        row, options = sheet.rows[0]
        self.assertEqual(row[1:], ["DESIGNTER", "designter 1.000", 1000.0])
        self.assertEqual(options, {"value_input_option": "RAW"})


if __name__ == "__main__":
    unittest.main()
