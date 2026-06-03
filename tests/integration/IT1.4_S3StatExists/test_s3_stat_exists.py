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
Description: IT1.4: S3 stat/exists (env-gated).
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import uuid

from cloud_dog_storage.backends.s3 import S3Storage
from cloud_dog_storage.config.models import S3Config, TlsConfig


def test_s3_stat_exists(s3_env) -> None:
    prefix = f"cloud_dog_test_{uuid.uuid4().hex}"
    backend = S3Storage(
        S3Config(
            endpoint=s3_env["TEST_S3_ENDPOINT"],
            bucket=s3_env["TEST_S3_BUCKET"],
            access_key=s3_env["TEST_S3_ACCESS_KEY"],
            secret_key=s3_env["TEST_S3_SECRET_KEY"],
            prefix=prefix,
        ),
        tls=TlsConfig(),
        timeout_s=30,
    )

    backend.write_bytes("/a.txt", b"123")
    assert backend.exists("/a.txt") is True
    st = backend.stat("/a.txt")
    assert st is not None
    assert st.size == 3
    backend.delete_path("/a.txt", missing_ok=True)
