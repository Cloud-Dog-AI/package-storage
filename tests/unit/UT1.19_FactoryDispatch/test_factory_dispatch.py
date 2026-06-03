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
Description: UT1.19: Factory dispatch tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import pytest

from cloud_dog_storage.config.models import StorageConfig
from cloud_dog_storage.errors import ConfigurationError
from cloud_dog_storage.factory import build_storage_backend


def test_local_aliases(tmp_path) -> None:
    for backend in ("local", "filesystem", "fs", ""):
        cfg = StorageConfig(backend=backend, root_path=str(tmp_path))
        b = build_storage_backend(cfg)
        assert b.backend_name == "local"


def test_unknown_backend_raises() -> None:
    with pytest.raises(ConfigurationError):
        build_storage_backend(StorageConfig(backend="nope"))
