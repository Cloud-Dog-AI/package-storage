"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Storage logging helpers with sensitive value redaction.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

SENSITIVE_KEYS = ("password", "secret", "token", "key", "credential")


def get_storage_logger(name: str = "cloud_dog_storage") -> logging.Logger:
    """Get storage logger with optional cloud_dog_logging integration."""
    try:
        from cloud_dog_logging import get_logger as cloud_get_logger  # type: ignore

        return cloud_get_logger(name)
    except Exception:
        return logging.getLogger(name)


def redact_sensitive(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return redacted copy of mapping values."""
    out: dict[str, Any] = {}
    for key, value in values.items():
        key_lower = key.lower()
        if any(token in key_lower for token in SENSITIVE_KEYS):
            out[key] = "***REDACTED***"
            continue
        out[key] = value
    return out


def log_operation(
    logger: logging.Logger,
    *,
    operation: str,
    backend_name: str,
    path: str,
    success: bool,
    started_at: float,
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Emit structured storage operation logs with duration and redacted fields."""
    duration_ms = round((time.monotonic() - started_at) * 1000.0, 2)
    payload = {
        "operation": operation,
        "backend_name": backend_name,
        "path": path,
        "success": success,
        "duration_ms": duration_ms,
    }
    if extra:
        payload.update(redact_sensitive(extra))
    logger.info("storage_operation", extra=payload)
