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
Description: IT1.15: Google Drive create_dir (env-gated).
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import uuid

from cloud_dog_storage.backends.google_drive import GoogleDriveStorage
from cloud_dog_storage.config.models import GoogleDriveConfig, TlsConfig


def test_gdrive_create_dir(gdrive_env) -> None:
    backend = GoogleDriveStorage(
        GoogleDriveConfig(
            folder_id=gdrive_env["TEST_GDRIVE_FOLDER_ID"],
            client_id=gdrive_env["TEST_GDRIVE_CLIENT_ID"],
            client_secret=gdrive_env["TEST_GDRIVE_CLIENT_SECRET"],
            refresh_token=gdrive_env["TEST_GDRIVE_REFRESH_TOKEN"],
        ),
        tls=TlsConfig(),
        timeout_s=30,
    )

    name = f"cloud_dog_test_{uuid.uuid4().hex}"
    backend.create_dir(f"/{name}", parents=True, exist_ok=True)
