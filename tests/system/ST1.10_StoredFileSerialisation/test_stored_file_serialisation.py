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
Description: ST1.10: StoredFile serialisation flow.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import asyncio

from cloud_dog_storage.async_wrapper import AsyncStorageBackend
from cloud_dog_storage.backends.local import LocalStorage


def test_stored_file_to_dict(tmp_path) -> None:
    backend = LocalStorage(root_path=tmp_path)
    a = AsyncStorageBackend(backend)

    async def _run() -> None:
        stored = await a.store_file(b"hello", "/x.txt", "text/plain", metadata={"k": "v"})
        payload = stored.to_dict()
        assert payload["path"] == "/x.txt"
        assert payload["metadata"]["k"] == "v"

    asyncio.run(_run())
