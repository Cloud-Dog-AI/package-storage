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
Description: ST1.1: Local backend full lifecycle flow.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.local import LocalStorage


def test_local_full_lifecycle(tmp_path) -> None:
    s = LocalStorage(root_path=tmp_path)
    s.create_dir("/d", parents=True, exist_ok=True)
    s.write_bytes("/d/a.txt", b"1")
    assert s.exists("/d/a.txt") is True
    assert s.read_bytes("/d/a.txt") == b"1"

    s.write_bytes("/d/a.txt", b"2", overwrite=True)
    assert s.read_bytes("/d/a.txt") == b"2"

    entries = s.list_dir("/d", recursive=True)
    assert any(e.path.endswith("a.txt") for e in entries)

    s.copy_path("/d/a.txt", "/d/b.txt", overwrite=True)
    s.move_path("/d/b.txt", "/d/c.txt", overwrite=True)

    s.delete_path("/d/c.txt", missing_ok=False)
    s.delete_path("/d/a.txt", missing_ok=False)
    s.delete_path("/d", missing_ok=True)
