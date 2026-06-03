"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Testing utility exports for conformance and mock backends.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from cloud_dog_storage.testing.conformance import ConformanceResult, run_conformance_suite
from cloud_dog_storage.testing.mock_backend import MockStorageBackend

__all__ = ["ConformanceResult", "MockStorageBackend", "run_conformance_suite"]
