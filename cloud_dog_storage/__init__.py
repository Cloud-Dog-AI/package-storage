"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Public API exports for cloud_dog_storage.
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
from cloud_dog_storage import path_utils
from cloud_dog_storage.transfer import (
    AttachmentDescriptor,
    decode_base64,
    detect_content_type,
    encode_base64,
    fetch_uri,
    list_mime_attachments,
    sanitize_filename,
    validate_file_size,
)

__all__ = [
    "AsyncStorageBackend",
    "AttachmentDescriptor",
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
    "decode_base64",
    "detect_content_type",
    "encode_base64",
    "fetch_uri",
    "list_mime_attachments",
    "path_utils",
    "sanitize_filename",
    "validate_file_size",
]

__version__ = "0.1.4"


def __getattr__(name: str):
    """Lazy import async wrapper to avoid unnecessary asyncio imports."""
    if name == "AsyncStorageBackend":
        from cloud_dog_storage.async_wrapper import AsyncStorageBackend

        return AsyncStorageBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
