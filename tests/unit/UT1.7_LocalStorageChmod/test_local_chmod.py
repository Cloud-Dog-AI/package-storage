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
Description: UT1.7: LocalStorage chmod_path behaviours.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import os

from cloud_dog_storage.backends.local import LocalStorage


def test_chmod_sets_mode(tmp_path) -> None:
    storage = LocalStorage(root_path=tmp_path)
    storage.write_bytes("/a.txt", b"x")
    storage.chmod_path("/a.txt", 0o600)
    actual = (os.stat(tmp_path / "a.txt").st_mode) & 0o777
    assert actual == 0o600
