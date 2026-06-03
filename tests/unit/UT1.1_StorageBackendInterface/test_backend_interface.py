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
Description: UT1.1: StorageBackend interface completeness tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.base import StorageBackend


class _Backend(StorageBackend):
    backend_name = "x"

    def __init__(self) -> None:
        self.stat_calls = 0

    def read_bytes(self, path: str) -> bytes:
        raise AssertionError(path)

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        raise AssertionError(path, data, overwrite)

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        raise AssertionError(path, missing_ok)

    def list_dir(self, path: str, *, recursive: bool = False):
        raise AssertionError(path, recursive)

    def stat(self, path: str):
        self.stat_calls += 1
        return None


def test_backend_has_required_methods() -> None:
    b = _Backend()
    for name in (
        "read_bytes",
        "write_bytes",
        "delete_path",
        "list_dir",
        "stat",
        "exists",
        "create_dir",
        "copy_path",
        "move_path",
        "rename_path",
        "chmod_path",
        "iter_paths",
        "get_url",
    ):
        assert hasattr(b, name)


def test_exists_delegates_to_stat() -> None:
    b = _Backend()
    assert b.exists("/x") is False
    assert b.stat_calls == 1
