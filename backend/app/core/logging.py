"""Logging helpers with sensitive field redaction."""

import logging
from collections.abc import Mapping
from typing import Any

from app.core.config import settings

SENSITIVE_KEYS = {
    "address",
    "cipher",
    "id_card",
    "id_no",
    "license_no",
    "phone",
    "secret",
    "token",
}


def redact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in SENSITIVE_KEYS:
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

