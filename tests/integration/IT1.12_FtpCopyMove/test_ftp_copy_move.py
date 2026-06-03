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
Description: IT1.12: FTP copy/move (env-gated).
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import uuid

from cloud_dog_storage.backends.ftp import FtpStorage
from cloud_dog_storage.config.models import FtpConfig


def test_ftp_copy_move(ftp_env) -> None:
    backend = FtpStorage(
        FtpConfig(
            host=ftp_env["TEST_FTP_HOST"], username=ftp_env["TEST_FTP_USERNAME"], password=ftp_env["TEST_FTP_PASSWORD"]
        )
    )

    base = f"/cloud_dog_test_{uuid.uuid4().hex}"
    backend.create_dir(base, parents=True, exist_ok=True)
    backend.write_bytes(f"{base}/a.txt", b"x")
    backend.copy_path(f"{base}/a.txt", f"{base}/b.txt", overwrite=True)
    backend.move_path(f"{base}/b.txt", f"{base}/c.txt", overwrite=True)
    assert backend.read_bytes(f"{base}/c.txt") == b"x"

    backend.delete_path(f"{base}/a.txt", missing_ok=True)
    backend.delete_path(f"{base}/c.txt", missing_ok=True)
    backend.delete_path(base, missing_ok=True)
