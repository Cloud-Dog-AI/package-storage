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
Description: AT1.2: FastAPI dependency returns cached backend.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import pytest


def test_dep_caches_backend(tmp_path) -> None:
    try:
        from fastapi import FastAPI
    except Exception:
        pytest.fail("fastapi not installed")

    from cloud_dog_storage.api.fastapi.deps import get_storage_backend
    from cloud_dog_storage.config.models import StorageConfig

    app = FastAPI()
    app.state.storage_config = StorageConfig(backend="local", root_path=str(tmp_path))

    req = type("R", (), {"app": app})()
    b1 = get_storage_backend(req)
    b2 = get_storage_backend(req)
    assert b1 is b2
