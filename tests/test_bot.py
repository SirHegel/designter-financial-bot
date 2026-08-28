import sys
import unittest
from zoneinfo import ZoneInfo
from types import SimpleNamespace
from unittest.mock import patch

from bot import build_bot
from settings import Settings


class FakeSheet:
    def __init__(self):
        self.rows = []
        self.cleared_ranges = []
        self.values = [
            ["Fecha", "Categoría", "Concepto", "Valor"],
            ["2026-08-28", "JHON", "Ingreso", "1000"],
            ["2026-08-28", "DESIGNTER", "Ingreso", "2000"],
            ["2026-08-28", "GASTO", "Pago", "-500"],
        ]

    def append_row(self, row, **options):
        self.rows.append((row, options))

    def batch_clear(self, ranges):
        self.cleared_ranges.append(ranges)

    def get_all_values(self):
        return self.values


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
        fake_client = SimpleNamespace(
            open_by_key=lambda _document_id: FakeDocument(sheet)
        )
        fake_gspread = SimpleNamespace(
            WorksheetNotFound=type("WorksheetNotFound", (Exception,), {}),
            service_account_from_dict=lambda *_args, **_options: fake_client,
        )
        fake_telebot = SimpleNamespace(TeleBot=lambda _token: fake_bot)

        settings = Settings(
            telegram_bot_token="test-only-value",
            telegram_allowed_chat_ids=frozenset({123, -900}),
            telegram_allowed_user_ids=frozenset({123, 10, 20}),
            google_service_account={"type": "service_account"},
            google_sheets_document_id="sheet_id_12345678901234567890",
            finance_timezone=ZoneInfo("America/Bogota"),
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

    @staticmethod
    def command_handler(bot, command):
        return next(
            callback
            for filters, callback in bot.handlers
            if command in filters.get("commands", [])
        )

    def test_rejects_a_chat_outside_the_allowlist(self):
        bot, sheet = self.build_test_bot()
        message = SimpleNamespace(
            chat=SimpleNamespace(id=999),
            from_user=SimpleNamespace(id=123),
            text="designter 1000",
        )

        self.catch_all_handler(bot)(message)

        self.assertEqual(sheet.rows, [])
        self.assertIn("no está autorizado", bot.replies[0][1])

    def test_writes_authorized_messages_as_raw_values(self):
        bot, sheet = self.build_test_bot()
        message = SimpleNamespace(
            chat=SimpleNamespace(id=123),
            from_user=SimpleNamespace(id=123),
            text="designter 1.000",
        )

        self.catch_all_handler(bot)(message)

        row, options = sheet.rows[0]
        self.assertEqual(row[1:], ["DESIGNTER", "designter 1.000", 1000.0])
        self.assertEqual(options, {"value_input_option": "RAW"})

    def test_group_requires_both_chat_and_user_allowlists(self):
        bot, sheet = self.build_test_bot()
        message = SimpleNamespace(
            chat=SimpleNamespace(id=-900),
            from_user=SimpleNamespace(id=999),
            text="designter 1000",
        )

        self.catch_all_handler(bot)(message)

        self.assertEqual(sheet.rows, [])
        self.assertIn("no está autorizado", bot.replies[-1][1])

    def test_only_requesting_actor_can_confirm_deletion(self):
        bot, sheet = self.build_test_bot()
        requester = SimpleNamespace(
            chat=SimpleNamespace(id=-900), from_user=SimpleNamespace(id=10), text=""
        )
        other_user = SimpleNamespace(
            chat=SimpleNamespace(id=-900), from_user=SimpleNamespace(id=20), text=""
        )

        self.command_handler(bot, "borrartodo")(requester)
        self.command_handler(bot, "confirmar")(other_user)
        self.assertEqual(sheet.cleared_ranges, [])

        self.command_handler(bot, "confirmar")(requester)
        self.assertEqual(sheet.cleared_ranges, [["A2:E"]])

    def test_deletion_confirmation_expires(self):
        bot, sheet = self.build_test_bot()
        message = SimpleNamespace(
            chat=SimpleNamespace(id=-900), from_user=SimpleNamespace(id=10), text=""
        )

        with patch("bot.time.monotonic", side_effect=[100.0, 401.0]):
            self.command_handler(bot, "borrartodo")(message)
            self.command_handler(bot, "confirmar")(message)

        self.assertEqual(sheet.cleared_ranges, [])

    def test_summary_uses_the_authorized_sheet_values(self):
        bot, _sheet = self.build_test_bot()
        message = SimpleNamespace(
            chat=SimpleNamespace(id=123), from_user=SimpleNamespace(id=123), text=""
        )

        self.command_handler(bot, "resumen")(message)

        response = bot.replies[-1][1]
        self.assertIn("1,000", response)
        self.assertIn("2,000", response)
        self.assertIn("500", response)
        self.assertIn("2,500", response)


if __name__ == "__main__":
    unittest.main()
