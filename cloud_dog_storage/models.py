"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Storage data models for entries, stats, and stored file metadata.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class StorageStat:
    """File-system-like stat information for a storage path."""

    path: str
    is_dir: bool
    size: int | None = None


@dataclass(frozen=True)
class StorageEntry:
    """Directory entry for list operations."""

    path: str
    is_dir: bool


@dataclass(frozen=True)
class StoredFile:
    """High-level result model for compatibility storage operations."""

    path: str
    format: str
    size_bytes: int
    backend_name: str
    stored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serialisable dictionary."""
        return {
            "path": self.path,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "backend_name": self.backend_name,
            "stored_at": self.stored_at.isoformat(),
            "metadata": dict(self.metadata),
        }
