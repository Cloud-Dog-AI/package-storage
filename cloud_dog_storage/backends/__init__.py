"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Storage backend exports with lazy imports for optional backends.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cloud_dog_storage.backends.base import StorageBackend
from cloud_dog_storage.backends.local import LocalStorage

if TYPE_CHECKING:
    from cloud_dog_storage.backends.ftp import FtpStorage
    from cloud_dog_storage.backends.s3 import S3Storage
    from cloud_dog_storage.backends.webdav import WebDavStorage

__all__ = [
    "FtpStorage",
    "LocalStorage",
    "S3Storage",
    "StorageBackend",
    "WebDavStorage",
]


def __getattr__(name: str):
    # Optional backends must not be imported unless explicitly requested.
    if name == "S3Storage":
        from cloud_dog_storage.backends.s3 import S3Storage

        return S3Storage
    if name == "WebDavStorage":
        from cloud_dog_storage.backends.webdav import WebDavStorage

        return WebDavStorage
    if name == "FtpStorage":
        from cloud_dog_storage.backends.ftp import FtpStorage

        return FtpStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
