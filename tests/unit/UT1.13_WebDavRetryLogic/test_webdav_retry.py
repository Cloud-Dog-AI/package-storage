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
Description: UT1.13: WebDAV retry logic tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.webdav import WebDavStorage
from cloud_dog_storage.config.models import WebDavConfig


class _Resp:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.content = b""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"status={self.status_code}")


def test_write_retries_transient(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_request(method, url, **kwargs):
        _ = method
        _ = url
        _ = kwargs
        calls["n"] += 1
        if calls["n"] == 1:
            return _Resp(500)
        return _Resp(201)

    monkeypatch.setattr("requests.request", fake_request)

    backend = WebDavStorage(WebDavConfig(base_url="https://dav.invalid"))
    backend.write_bytes("/a.txt", b"x", overwrite=True)
    assert calls["n"] == 2
