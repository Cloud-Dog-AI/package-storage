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
Description: UT1.6: LocalStorage copy_path and move_path behaviours.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import pytest

from cloud_dog_storage.backends.local import LocalStorage


def test_copy_then_move_file(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.write_bytes("/a.txt", b"hello")
    storage.copy_path("/a.txt", "/b.txt", overwrite=False)
    assert storage.read_bytes("/b.txt") == b"hello"

    storage.move_path("/b.txt", "/c.txt", overwrite=False)
    assert storage.exists("/c.txt") is True


def test_copy_overwrite_false_raises(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.write_bytes("/a.txt", b"1")
    storage.write_bytes("/b.txt", b"2")
    with pytest.raises(FileExistsError):
        storage.copy_path("/a.txt", "/b.txt", overwrite=False)
