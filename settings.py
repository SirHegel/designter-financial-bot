"""Carga y valida la configuración sensible desde el entorno."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Mapping


class ConfigurationError(ValueError):
    """Indica que el proceso no puede arrancar de forma segura."""


def _required(environment: Mapping[str, str], name: str) -> str:
    value = environment.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"falta la variable {name}")
    return value


def _parse_chat_ids(raw_value: str) -> frozenset[int]:
    values = [item.strip() for item in raw_value.split(",")]
    if not values or any(not item for item in values):
        raise ConfigurationError("TELEGRAM_ALLOWED_CHAT_IDS debe contener IDs separados por comas")

    try:
        chat_ids = frozenset(int(item) for item in values)
    except ValueError as error:
        raise ConfigurationError(
            "TELEGRAM_ALLOWED_CHAT_IDS solo puede contener números enteros"
        ) from error

    if 0 in chat_ids:
        raise ConfigurationError("TELEGRAM_ALLOWED_CHAT_IDS no admite el ID 0")
    return chat_ids


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = field(repr=False)
    telegram_allowed_chat_ids: frozenset[int]
    google_service_account: dict[str, object] = field(repr=False)
    google_sheets_document: str

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if environment is None else environment
        token = _required(source, "TELEGRAM_BOT_TOKEN")
        chat_ids = _parse_chat_ids(_required(source, "TELEGRAM_ALLOWED_CHAT_IDS"))
        try:
            service_account = json.loads(_required(source, "GOOGLE_SERVICE_ACCOUNT_JSON"))
        except json.JSONDecodeError as error:
            raise ConfigurationError(
                "GOOGLE_SERVICE_ACCOUNT_JSON debe contener un objeto JSON válido"
            ) from error
        if not isinstance(service_account, dict) or not service_account:
            raise ConfigurationError(
                "GOOGLE_SERVICE_ACCOUNT_JSON debe contener un objeto JSON no vacío"
            )

        document = source.get("GOOGLE_SHEETS_DOCUMENT", "BaseDatos_Finanzas").strip()
        if not document:
            raise ConfigurationError("GOOGLE_SHEETS_DOCUMENT no puede estar vacío")

        return cls(
            telegram_bot_token=token,
            telegram_allowed_chat_ids=chat_ids,
            google_service_account=service_account,
            google_sheets_document=document,
        )
