"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Storage error taxonomy shared by all backends.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations


class StorageError(RuntimeError):
    """Base class for all storage errors."""

    def __init__(self, message: str, *, backend_name: str = "", path: str = "") -> None:
        super().__init__(message)
        self.backend_name = backend_name
        self.path = path


class NotSupportedError(StorageError):
    """Raised when a backend does not support an operation."""

    def __init__(self, operation: str, *, backend: str) -> None:
        super().__init__(f"Not supported for backend: {operation} (backend={backend})", backend_name=backend)
        self.operation = operation


class StorageFileNotFoundError(StorageError):
    """Raised when a file/path does not exist."""

    def __init__(self, path: str, *, backend: str = "") -> None:
        super().__init__(f"Path not found: {path}", backend_name=backend, path=path)


class StoragePermissionError(StorageError):
    """Raised when operation is not authorised for a path."""

    def __init__(self, path: str, *, backend: str = "") -> None:
        super().__init__(f"Permission denied for path: {path}", backend_name=backend, path=path)


class QuotaExceededError(StorageError):
    """Raised when backend quota or disk free-space threshold is exceeded."""


class ConfigurationError(StorageError):
    """Raised when backend configuration is invalid."""


class BackendConnectionError(StorageError):
    """Raised when backend connection cannot be established."""
