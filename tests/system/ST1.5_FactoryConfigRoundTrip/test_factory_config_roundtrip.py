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
Description: ST1.5: Config to backend round-trip.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.config.models import StorageConfig
from cloud_dog_storage.factory import build_storage_backend


def test_config_round_trip(tmp_path) -> None:
    cfg = StorageConfig(backend="local", root_path=str(tmp_path))
    backend = build_storage_backend(cfg)
    backend.write_bytes("/a.txt", b"x")
    assert backend.read_bytes("/a.txt") == b"x"
