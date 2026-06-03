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
Description: UT1.27: StoredFile model tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.models import StoredFile


def test_to_dict_contains_expected_fields() -> None:
    f = StoredFile(path="/x", format="txt", size_bytes=3, backend_name="local", metadata={"a": 1})
    d = f.to_dict()
    assert d["path"] == "/x"
    assert d["format"] == "txt"
    assert d["size_bytes"] == 3
    assert d["backend_name"] == "local"
    assert "stored_at" in d
    assert d["metadata"]["a"] == 1
