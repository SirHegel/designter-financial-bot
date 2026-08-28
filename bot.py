"""Bot de Telegram para registrar movimientos financieros en Google Sheets."""

from __future__ import annotations

import logging
import re
from datetime import datetime

from settings import ConfigurationError, Settings


LOGGER = logging.getLogger(__name__)
GOOGLE_SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
)


def build_bot(settings: Settings):
    """Construye el bot después de validar toda la configuración local."""
    import gspread
    import telebot

    bot = telebot.TeleBot(settings.telegram_bot_token)
    client = gspread.service_account_from_dict(
        settings.google_service_account,
        scopes=GOOGLE_SCOPES,
    )
    document = client.open(settings.google_sheets_document)
    pending_deletions: set[int] = set()

    def is_authorized(message) -> bool:
        chat_id = message.chat.id
        if chat_id in settings.telegram_allowed_chat_ids:
            return True
        bot.reply_to(message, "⛔ Este chat no está autorizado para usar el bot.")
        return False

    def current_month_sheet():
        """Obtiene o crea la pestaña correspondiente al mes actual."""
        month_name = datetime.now().strftime("%m-%Y")
        try:
            return document.worksheet(month_name)
        except gspread.WorksheetNotFound:
            sheet = document.add_worksheet(title=month_name, rows="1000", cols="5")
            sheet.append_row(["Fecha", "Categoría", "Concepto", "Valor"])
            return sheet

    @bot.message_handler(commands=["utilidades", "resumen"])
    def command_summary(message):
        """Calcula el balance financiero a partir de Google Sheets."""
        if not is_authorized(message):
            return

        try:
            records = current_month_sheet().get_all_values()
            personal_income, business_income, expenses = 0.0, 0.0, 0.0

            for row in records[1:]:
                if len(row) < 4:
                    continue
                try:
                    value = float(row[3].replace(",", "."))
                except (TypeError, ValueError):
                    continue

                category = row[1]
                if value < 0:
                    expenses += abs(value)
                elif category == "JHON":
                    personal_income += value
                elif category == "DESIGNTER":
                    business_income += value

            profit = personal_income + business_income - expenses
            summary = (
                "📊 *BALANCE DESIGNTER*\n\n"
                f"👤 *Jhon:* `${personal_income:,.0f}`\n"
                f"🚀 *Designter:* `${business_income:,.0f}`\n"
                f"🔻 *Gastos:* `${expenses:,.0f}`\n"
                "──────────────────\n"
                f"📈 *Utilidad Neta:* `${profit:,.0f}`"
            )
            bot.reply_to(message, summary, parse_mode="Markdown")
        except Exception:
            LOGGER.warning("No fue posible calcular el resumen financiero.")
            bot.reply_to(message, "❌ Error al calcular los datos.")

    @bot.message_handler(commands=["borrartodo"])
    def request_deletion(message):
        if not is_authorized(message):
            return
        pending_deletions.add(message.chat.id)
        bot.reply_to(
            message,
            "⚠️ *ADVERTENCIA:* ¿Borrar los datos del mes?\nEscribe /confirmar.",
            parse_mode="Markdown",
        )

    @bot.message_handler(commands=["confirmar"])
    def confirm_deletion(message):
        if not is_authorized(message):
            return
        if message.chat.id not in pending_deletions:
            bot.reply_to(message, "No hay un borrado pendiente para este chat.")
            return

        current_month_sheet().batch_clear(["A2:E1000"])
        pending_deletions.discard(message.chat.id)
        bot.reply_to(message, "✅ Datos borrados. Balance en ceros.")

    @bot.message_handler(func=lambda message: True)
    def process_text(message):
        """Extrae montos y categorías de mensajes de chats autorizados."""
        if not is_authorized(message):
            return
        if not message.text or message.text.startswith("/"):
            return

        try:
            text = message.text.lower()
            numbers = re.findall(r"\d+", text.replace(".", ""))
            if not numbers:
                return
            value = float(numbers[0])

            if "gasto" in text or "gaste" in text:
                category = "GASTO"
                final_value = -value
            elif "designter" in text:
                category = "DESIGNTER"
                final_value = value
            else:
                category = "JHON"
                final_value = value

            sheet = current_month_sheet()
            sheet.append_row(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    category,
                    message.text,
                    final_value,
                ],
                value_input_option="RAW",
            )
            bot.reply_to(message, f"✅ *{category}* guardado: `${value:,.0f}`")
        except Exception:
            LOGGER.warning("No fue posible registrar el movimiento financiero.")
            bot.reply_to(message, "❌ Error al registrar el movimiento.")

    return bot


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        settings = Settings.from_environment()
    except ConfigurationError as error:
        raise SystemExit(f"Configuración inválida: {error}") from error

    bot = build_bot(settings)
    LOGGER.info("Bot de Designter iniciado.")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
