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
Description: UT1.2: LocalStorage basic behaviours.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import pytest

from cloud_dog_storage.backends.local import LocalStorage
from cloud_dog_storage.errors import StorageFileNotFoundError


def test_read_missing_raises(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    with pytest.raises(StorageFileNotFoundError):
        storage.read_bytes("/missing.txt")


def test_write_read_delete_round_trip(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.write_bytes("/a.txt", b"hello")
    assert storage.read_bytes("/a.txt") == b"hello"
    storage.delete_path("/a.txt")
    with pytest.raises(StorageFileNotFoundError):
        storage.read_bytes("/a.txt")


def test_delete_missing_ok(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.delete_path("/missing.txt", missing_ok=True)
