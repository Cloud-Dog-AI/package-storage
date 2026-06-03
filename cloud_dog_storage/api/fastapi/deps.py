"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: FastAPI dependency provider for storage backend access.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from typing import TYPE_CHECKING

try:
    # Optional dependency: only imported when FastAPI integration is used.
    from starlette.requests import Request
except Exception:  # pragma: no cover
    Request = object  # type: ignore[assignment]

from cloud_dog_storage.config.models import StorageConfig
from cloud_dog_storage.factory import build_storage_backend

if TYPE_CHECKING:
    from cloud_dog_storage.backends.base import StorageBackend


def get_storage_backend(request: Request) -> "StorageBackend":
    """Return storage backend from app state, creating it from `storage_config` if needed."""
    app_state = request.app.state
    backend = getattr(app_state, "storage_backend", None)
    if backend is not None:
        return backend

    config = getattr(app_state, "storage_config", None)
    if config is None:
        raise RuntimeError("FastAPI app.state.storage_config or app.state.storage_backend is required")

    if isinstance(config, StorageConfig):
        backend = build_storage_backend(config)
    else:
        backend = build_storage_backend(StorageConfig.model_validate(config))

    app_state.storage_backend = backend
    return backend
