"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Cloud-Dog AI platform storage library — pluggable file/object storage backends.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from cloud_dog_storage.backends.base import StorageBackend
from cloud_dog_storage.errors import (
    BackendConnectionError,
    ConfigurationError,
    NotSupportedError,
    QuotaExceededError,
    StorageError,
    StorageFileNotFoundError,
    StoragePermissionError,
)
from cloud_dog_storage.factory import build_storage_backend
from cloud_dog_storage.models import StorageEntry, StorageStat, StoredFile

__all__ = [
    "AsyncStorageBackend",
    "BackendConnectionError",
    "ConfigurationError",
    "NotSupportedError",
    "QuotaExceededError",
    "StorageBackend",
    "StorageEntry",
    "StorageError",
    "StorageFileNotFoundError",
    "StoragePermissionError",
    "StorageStat",
    "StoredFile",
    "build_storage_backend",
]

__version__ = "0.1.0"


def __getattr__(name: str):
    """Lazy import for AsyncStorageBackend to avoid pulling asyncio at import time."""
    if name == "AsyncStorageBackend":
        from cloud_dog_storage.async_wrapper import AsyncStorageBackend

        return AsyncStorageBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
