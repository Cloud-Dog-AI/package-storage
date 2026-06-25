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
Description: UT1.25: StorageEntry model tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import dataclasses

import pytest

from cloud_dog_storage.backends.google_drive import GoogleDriveStorage
from cloud_dog_storage.config.models import GoogleDriveConfig, TlsConfig
from cloud_dog_storage.models import StorageEntry


def test_entry_is_frozen() -> None:
    e = StorageEntry(path="/x", is_dir=False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.path = "/y"  # type: ignore[misc]


def test_entry_accepts_optional_backend_metadata() -> None:
    e = StorageEntry(
        path="/x",
        is_dir=False,
        size=12,
        modified_at="2026-06-17T09:01:00.000Z",
        metadata={"drive_file_id": "file-id", "drive_revision": "7"},
    )

    assert e.size == 12
    assert e.modified_at == "2026-06-17T09:01:00.000Z"
    assert e.metadata == {"drive_file_id": "file-id", "drive_revision": "7"}


class _Response:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_google_drive_list_dir_maps_entry_metadata(monkeypatch) -> None:
    def fake_post(url, data, timeout, verify):
        _ = url
        _ = data
        _ = timeout
        _ = verify
        return _Response({"access_token": "t1", "expires_in": 3600})

    def fake_request(method, url, **kwargs):
        _ = method
        _ = url
        _ = kwargs
        return _Response(
            {
                "files": [
                    {
                        "id": "drive-file-id",
                        "name": "result.md",
                        "mimeType": "text/markdown",
                        "size": "42",
                        "createdTime": "2026-06-17T09:00:00.000Z",
                        "modifiedTime": "2026-06-17T09:01:00.000Z",
                        "version": "7",
                        "md5Checksum": "abc123",
                        "webViewLink": "https://drive.google.com/file/d/drive-file-id/view",
                    }
                ]
            }
        )

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
    entries = backend.list_dir("/", recursive=False)

    assert len(entries) == 1
    assert entries[0].path == "/result.md"
    assert entries[0].size == 42
    assert entries[0].created_at == "2026-06-17T09:00:00.000Z"
    assert entries[0].modified_at == "2026-06-17T09:01:00.000Z"
    assert entries[0].metadata == {
        "drive_file_id": "drive-file-id",
        "drive_revision": "7",
        "drive_md5_checksum": "abc123",
        "drive_web_view_link": "https://drive.google.com/file/d/drive-file-id/view",
    }
