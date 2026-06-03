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
Description: AT1.3: AsyncStorageBackend usage inside FastAPI endpoints.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import asyncio

import pytest


def test_async_storage_in_fastapi(tmp_path) -> None:
    try:
        from fastapi import FastAPI
    except Exception:
        pytest.fail("fastapi not installed")

    from cloud_dog_storage.async_wrapper import AsyncStorageBackend
    from cloud_dog_storage.backends.local import LocalStorage

    app = FastAPI()
    backend = AsyncStorageBackend(LocalStorage(root_path=tmp_path))
    app.state.storage_backend = backend

    async def _run() -> None:
        await backend.write_bytes("/a.txt", b"x")
        assert await backend.read_bytes("/a.txt") == b"x"

    asyncio.run(_run())
