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
Description: UT1.23: Root boundary enforcement tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import pytest

from cloud_dog_storage.errors import StoragePermissionError
from cloud_dog_storage.security.path_sanitiser import validate_within_root


def test_validate_within_root_blocks_escape(tmp_path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(StoragePermissionError):
        validate_within_root("/../../etc/passwd", root)


def test_validate_within_root_blocks_symlink_escape(tmp_path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    (outside / "secret.txt").write_text("x", encoding="utf-8")

    link = root / "link"
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(StoragePermissionError):
        validate_within_root("/link/secret.txt", root)
