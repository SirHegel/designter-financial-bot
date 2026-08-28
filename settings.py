"""Carga y valida la configuración sensible desde el entorno."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ConfigurationError(ValueError):
    """Indica que el proceso no puede arrancar de forma segura."""


def _required(environment: Mapping[str, str], name: str) -> str:
    value = environment.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"falta la variable {name}")
    return value


def _parse_ids(raw_value: str, name: str, *, positive: bool = False) -> frozenset[int]:
    values = [item.strip() for item in raw_value.split(",")]
    if not values or any(not item for item in values):
        raise ConfigurationError(f"{name} debe contener IDs separados por comas")

    try:
        chat_ids = frozenset(int(item) for item in values)
    except ValueError as error:
        raise ConfigurationError(f"{name} solo puede contener números enteros") from error

    if 0 in chat_ids or (positive and any(identifier < 0 for identifier in chat_ids)):
        qualifier = "IDs positivos" if positive else "IDs distintos de 0"
        raise ConfigurationError(f"{name} solo admite {qualifier}")
    return chat_ids


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = field(repr=False)
    telegram_allowed_chat_ids: frozenset[int]
    telegram_allowed_user_ids: frozenset[int]
    google_service_account: dict[str, object] = field(repr=False)
    google_sheets_document_id: str
    finance_timezone: ZoneInfo

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if environment is None else environment
        token = _required(source, "TELEGRAM_BOT_TOKEN")
        chat_ids = _parse_ids(
            _required(source, "TELEGRAM_ALLOWED_CHAT_IDS"),
            "TELEGRAM_ALLOWED_CHAT_IDS",
        )
        user_ids = _parse_ids(
            _required(source, "TELEGRAM_ALLOWED_USER_IDS"),
            "TELEGRAM_ALLOWED_USER_IDS",
            positive=True,
        )
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
        required_fields = {"type", "client_email", "private_key", "token_uri"}
        if service_account.get("type") != "service_account" or any(
            not service_account.get(name) for name in required_fields
        ):
            raise ConfigurationError(
                "GOOGLE_SERVICE_ACCOUNT_JSON no contiene una cuenta de servicio completa"
            )

        document_id = _required(source, "GOOGLE_SHEETS_DOCUMENT_ID")
        if not re.fullmatch(r"[A-Za-z0-9_-]{20,200}", document_id):
            raise ConfigurationError("GOOGLE_SHEETS_DOCUMENT_ID no tiene un formato válido")
        timezone_name = source.get("FINANCE_TIMEZONE", "America/Bogota").strip()
        try:
            finance_timezone = ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ConfigurationError("FINANCE_TIMEZONE no contiene una zona IANA válida") from error

        return cls(
            telegram_bot_token=token,
            telegram_allowed_chat_ids=chat_ids,
            telegram_allowed_user_ids=user_ids,
            google_service_account=service_account,
            google_sheets_document_id=document_id,
            finance_timezone=finance_timezone,
        )
