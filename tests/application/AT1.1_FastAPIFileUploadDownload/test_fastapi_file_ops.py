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
Description: AT1.1: FastAPI upload/download against LocalStorage.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import pytest

try:
    from fastapi import Depends, FastAPI
    from fastapi.responses import Response

    _FASTAPI_AVAILABLE = True
except Exception:
    Depends = FastAPI = Response = None  # type: ignore[assignment]
    _FASTAPI_AVAILABLE = False


def test_fastapi_file_ops(tmp_path) -> None:
    if not _FASTAPI_AVAILABLE:
        pytest.fail("fastapi not installed")

    from cloud_dog_storage.api.fastapi import get_storage_backend
    from cloud_dog_storage.config.models import StorageConfig

    app = FastAPI()  # type: ignore[misc]
    app.state.storage_config = StorageConfig(backend="local", root_path=str(tmp_path))

    @app.post("/files/{path:path}")
    def upload(path: str, body: bytes, storage=Depends(get_storage_backend)):
        storage.write_bytes("/" + path, body)
        return {"ok": True}

    @app.get("/files/{path:path}")
    def download(path: str, storage=Depends(get_storage_backend)):
        data = storage.read_bytes("/" + path)
        return Response(content=data)  # type: ignore[misc]

    req = type("R", (), {"app": app})()
    backend = get_storage_backend(req)
    assert upload("a.txt", b"hi", storage=backend)["ok"] is True

    resp = download("a.txt", storage=backend)
    assert resp.status_code == 200
    assert resp.body == b"hi"
