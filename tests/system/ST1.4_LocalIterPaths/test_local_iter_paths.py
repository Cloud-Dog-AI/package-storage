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
Description: ST1.4: Local iter_paths behaviour.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.local import LocalStorage


def test_iter_paths(tmp_path) -> None:
    s = LocalStorage(root_path=tmp_path)
    s.create_dir("/d/sub", parents=True, exist_ok=True)
    s.write_bytes("/d/a.txt", b"a")
    s.write_bytes("/d/sub/b.txt", b"b")

    paths = set(s.iter_paths(["/d"]))
    assert "/d/a.txt" in paths
    assert "/d/sub/b.txt" in paths
