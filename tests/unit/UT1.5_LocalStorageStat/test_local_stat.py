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
Description: UT1.5: LocalStorage stat behaviours.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.local import LocalStorage


def test_stat_missing_is_none(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    assert storage.stat("/missing") is None


def test_stat_file_has_size(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.write_bytes("/a.txt", b"hello")
    st = storage.stat("/a.txt")
    assert st is not None
    assert st.is_dir is False
    assert st.size == 5


def test_stat_dir_is_dir(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.create_dir("/d", parents=True, exist_ok=True)
    st = storage.stat("/d")
    assert st is not None
    assert st.is_dir is True
    assert st.size is None
