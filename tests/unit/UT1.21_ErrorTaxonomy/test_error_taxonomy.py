# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: UT1.21: Error taxonomy tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.errors import (
    BackendConnectionError,
    ConfigurationError,
    NotSupportedError,
    QuotaExceededError,
    StorageError,
    StorageFileNotFoundError,
    StoragePermissionError,
)


def test_error_attributes() -> None:
    err = StorageFileNotFoundError("/x", backend="b")
    assert isinstance(err, StorageError)
    assert err.backend_name == "b"
    assert err.path == "/x"


def test_not_supported_has_operation() -> None:
    err = NotSupportedError("op", backend="b")
    assert err.operation == "op"


def test_other_errors_construct() -> None:
    _ = BackendConnectionError("x", backend_name="b")
    _ = ConfigurationError("x", backend_name="b")
    _ = StoragePermissionError("/p", backend="b")
    _ = QuotaExceededError("x", backend_name="b")
