"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: FastAPI dependency exports for storage backends.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from cloud_dog_storage.api.fastapi.deps import get_storage_backend

__all__ = ["get_storage_backend"]
