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
Description: UT1.31: NotSupportedError raised for unsupported operations.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import pytest

from cloud_dog_storage.backends.base import StorageBackend
from cloud_dog_storage.errors import NotSupportedError


class _B(StorageBackend):
    backend_name = "b"

    def read_bytes(self, path: str) -> bytes:
        raise AssertionError(path)

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        raise AssertionError(path, data, overwrite)

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        raise AssertionError(path, missing_ok)

    def list_dir(self, path: str, *, recursive: bool = False):
        raise AssertionError(path, recursive)

    def stat(self, path: str):
        _ = path
        return None


def test_get_url_not_supported() -> None:
    b = _B()
    with pytest.raises(NotSupportedError):
        b.get_url("/x")
