import unittest

from settings import ConfigurationError, Settings


class SettingsTests(unittest.TestCase):
    def valid_environment(self) -> dict[str, str]:
        return {
            "TELEGRAM_BOT_TOKEN": "test-only-value",
            "TELEGRAM_ALLOWED_CHAT_IDS": "123,-456",
            "TELEGRAM_ALLOWED_USER_IDS": "123,456",
            "GOOGLE_SERVICE_ACCOUNT_JSON": (
                '{"type":"service_account","client_email":"bot@example.test",'
                '"private_key":"test-key","token_uri":"https://example.test/token"}'
            ),
            "GOOGLE_SHEETS_DOCUMENT_ID": "sheet_id_12345678901234567890",
            "FINANCE_TIMEZONE": "America/Bogota",
        }

    def test_loads_valid_configuration(self):
        settings = Settings.from_environment(self.valid_environment())

        self.assertEqual(settings.telegram_bot_token, "test-only-value")
        self.assertEqual(settings.telegram_allowed_chat_ids, frozenset({123, -456}))
        self.assertEqual(settings.telegram_allowed_user_ids, frozenset({123, 456}))
        self.assertEqual(settings.google_sheets_document_id, "sheet_id_12345678901234567890")
        self.assertEqual(settings.finance_timezone.key, "America/Bogota")
        self.assertNotIn("test-only-value", repr(settings))
        self.assertNotIn("client_email", repr(settings))

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

    def test_requires_positive_authorized_user_ids(self):
        environment = self.valid_environment()
        environment["TELEGRAM_ALLOWED_USER_IDS"] = "123,-456"

        with self.assertRaisesRegex(ConfigurationError, "IDs positivos"):
            Settings.from_environment(environment)

    def test_rejects_invalid_service_account_json(self):
        environment = self.valid_environment()
        environment["GOOGLE_SERVICE_ACCOUNT_JSON"] = "not-json"

        with self.assertRaisesRegex(ConfigurationError, "objeto JSON válido"):
            Settings.from_environment(environment)

    def test_rejects_incomplete_service_account(self):
        environment = self.valid_environment()
        environment["GOOGLE_SERVICE_ACCOUNT_JSON"] = '{"type":"service_account"}'

        with self.assertRaisesRegex(ConfigurationError, "cuenta de servicio completa"):
            Settings.from_environment(environment)

    def test_requires_an_immutable_spreadsheet_id(self):
        environment = self.valid_environment()
        environment["GOOGLE_SHEETS_DOCUMENT_ID"] = "BaseDatos_Finanzas"

        with self.assertRaisesRegex(ConfigurationError, "formato válido"):
            Settings.from_environment(environment)

    def test_rejects_an_unknown_finance_timezone(self):
        environment = self.valid_environment()
        environment["FINANCE_TIMEZONE"] = "Bogota/Inventada"

        with self.assertRaisesRegex(ConfigurationError, "zona IANA válida"):
            Settings.from_environment(environment)


if __name__ == "__main__":
    unittest.main()
