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
Description: UT1.22: Path sanitiser tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.security.path_sanitiser import clean_posix


def test_clean_posix_defaults_to_root() -> None:
    assert clean_posix("") == "/"


def test_clean_posix_adds_leading_slash() -> None:
    assert clean_posix("foo/bar") == "/foo/bar"


def test_clean_posix_normalises_traversal() -> None:
    assert clean_posix("/../../../etc/passwd") == "/etc/passwd"


def test_clean_posix_normalises_double_slashes() -> None:
    assert clean_posix("/a//b///c") == "/a/b/c"


def test_clean_posix_removes_null_bytes() -> None:
    assert clean_posix("/a\\x00b") == "/ab"
