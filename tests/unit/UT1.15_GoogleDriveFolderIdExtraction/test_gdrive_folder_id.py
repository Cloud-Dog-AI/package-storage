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
Description: UT1.15: Google Drive folder ID extraction tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.google_drive import extract_folder_id


def test_extract_from_id() -> None:
    assert extract_folder_id("abc", None) == "abc"


def test_extract_from_drive_folders_url() -> None:
    assert extract_folder_id(None, "https://drive.google.com/drive/folders/XYZ") == "XYZ"


def test_extract_from_open_id_url() -> None:
    assert extract_folder_id(None, "https://drive.google.com/open?id=QWE") == "QWE"


def test_extract_invalid_returns_none() -> None:
    assert extract_folder_id("", "https://example.invalid/") is None
