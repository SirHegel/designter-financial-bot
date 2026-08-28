import unittest

from settings import ConfigurationError, Settings


class SettingsTests(unittest.TestCase):
    def valid_environment(self) -> dict[str, str]:
        return {
            "TELEGRAM_BOT_TOKEN": "test-only-value",
            "TELEGRAM_ALLOWED_CHAT_IDS": "123,-456",
            "GOOGLE_SERVICE_ACCOUNT_JSON": '{"kind":"test"}',
            "GOOGLE_SHEETS_DOCUMENT": "TestDocument",
        }

    def test_loads_valid_configuration(self):
        settings = Settings.from_environment(self.valid_environment())

        self.assertEqual(settings.telegram_bot_token, "test-only-value")
        self.assertEqual(settings.telegram_allowed_chat_ids, frozenset({123, -456}))
        self.assertEqual(settings.google_sheets_document, "TestDocument")
        self.assertEqual(settings.google_service_account, {"kind": "test"})
        self.assertNotIn("test-only-value", repr(settings))
        self.assertNotIn("kind", repr(settings))

    def test_requires_telegram_token(self):
        environment = self.valid_environment()
        environment["TELEGRAM_BOT_TOKEN"] = ""

        with self.assertRaisesRegex(ConfigurationError, "TELEGRAM_BOT_TOKEN"):
            Settings.from_environment(environment)

    def test_rejects_invalid_chat_allowlist(self):
        environment = self.valid_environment()
        environment["TELEGRAM_ALLOWED_CHAT_IDS"] = "123,not-a-number"

        with self.assertRaisesRegex(ConfigurationError, "números enteros"):
            Settings.from_environment(environment)

    def test_rejects_invalid_service_account_json(self):
        environment = self.valid_environment()
        environment["GOOGLE_SERVICE_ACCOUNT_JSON"] = "not-json"

        with self.assertRaisesRegex(ConfigurationError, "objeto JSON válido"):
            Settings.from_environment(environment)


if __name__ == "__main__":
    unittest.main()
