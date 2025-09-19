"""Utility for consistent payload logging across scripts."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

_LOGGER_NAME = "payload_logger"
_LOG_FILE = Path(__file__).with_name("payloads.log")


def _get_logger() -> logging.Logger:
    """Configure (once) and return the shared payload logger."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter(
            fmt="%(asctime)s\t%(levelname)s\t%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def log_payload(source: str, payload: object, context: Optional[str] = None) -> None:
    """Write payload information to the shared log file.

    Args:
        source: Name of the caller (script/module).
        payload: Payload data to be logged.
        context: Optional additional context (e.g. MQTT topic).
    """
    logger = _get_logger()
    payload_text = str(payload)
    if context:
        logger.info("%s | %s | %s", source, context, payload_text)
    else:
        logger.info("%s | %s", source, payload_text)
