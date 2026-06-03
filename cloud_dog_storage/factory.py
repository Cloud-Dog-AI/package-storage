"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Factory for creating storage backend instances from config.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cloud_dog_storage.backends.local import LocalStorage
from cloud_dog_storage.errors import ConfigurationError

if TYPE_CHECKING:
    from cloud_dog_storage.backends.base import StorageBackend
    from cloud_dog_storage.config.models import StorageConfig


def build_storage_backend(config: StorageConfig) -> StorageBackend:
    """Create backend from typed storage configuration."""
    backend = (config.backend or "local").strip().lower()
    if backend in {"", "local", "filesystem", "fs"}:
        return LocalStorage(
            root_path=config.root_path,
            min_free_bytes=config.local.min_free_bytes,
            file_permissions=config.local.file_permissions,
            dir_permissions=config.local.dir_permissions,
            subdir_pattern=config.local.subdir_pattern,
        )
    if backend == "s3":
        from cloud_dog_storage.backends.s3 import S3Storage

        return S3Storage(config.s3, tls=config.tls, timeout_s=config.timeout_s)
    if backend == "webdav":
        from cloud_dog_storage.backends.webdav import WebDavStorage

        return WebDavStorage(config.webdav, tls=config.tls, timeout_s=config.timeout_s)
    if backend == "ftp":
        from cloud_dog_storage.backends.ftp import FtpStorage

        return FtpStorage(config.ftp, tls=config.tls, timeout_s=config.timeout_s)
    if backend in {"google_drive", "gdrive", "drive"}:
        from cloud_dog_storage.backends.google_drive import GoogleDriveStorage

        return GoogleDriveStorage(config.google_drive, tls=config.tls, timeout_s=config.timeout_s)
    raise ConfigurationError(f"Unknown storage backend: {backend}", backend_name=backend)
