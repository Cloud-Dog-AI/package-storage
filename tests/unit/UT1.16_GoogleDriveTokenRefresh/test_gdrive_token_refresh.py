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
Description: UT1.16: Google Drive OAuth2 refresh flow tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.google_drive import GoogleDriveStorage
from cloud_dog_storage.config.models import GoogleDriveConfig, TlsConfig


class _Resp:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("bad")

    def json(self):
        return self._payload


def test_refresh_updates_access_token(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_post(url, data, timeout, verify):
        _ = url
        _ = data
        _ = timeout
        _ = verify
        calls["n"] += 1
        return _Resp({"access_token": "t1", "expires_in": 3600})

    def fake_request(method, url, **kwargs):
        _ = method
        _ = url
        _ = kwargs
        return _Resp({"files": []})

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr("requests.request", fake_request)

    backend = GoogleDriveStorage(
        GoogleDriveConfig(
            folder_id="F",
            client_id="cid",
            client_secret="csec",
            refresh_token="rt",
            access_token="",
        ),
        tls=TlsConfig(),
        timeout_s=30,
    )

    token1 = backend._token()
    token2 = backend._token()
    assert token1 == "t1"
    assert token2 == "t1"
    assert calls["n"] == 1
