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
Description: UT1.3: LocalStorage read/write and overwrite semantics.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import pytest

from cloud_dog_storage.backends.local import LocalStorage


def test_overwrite_false_raises(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.write_bytes("/a.bin", b"1", overwrite=True)
    with pytest.raises(FileExistsError):
        storage.write_bytes("/a.bin", b"2", overwrite=False)


def test_overwrite_true_replaces(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.write_bytes("/a.bin", b"1")
    storage.write_bytes("/a.bin", b"2")
    assert storage.read_bytes("/a.bin") == b"2"
