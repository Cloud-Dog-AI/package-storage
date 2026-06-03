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
Description: IT1.18: Conformance suite against WebDAV (env-gated).
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.webdav import WebDavStorage
from cloud_dog_storage.config.models import WebDavConfig
from cloud_dog_storage.testing.conformance import run_conformance_suite


def test_webdav_conformance(webdav_env) -> None:
    backend = WebDavStorage(
        WebDavConfig(
            base_url=webdav_env["TEST_WEBDAV_URL"],
            username=webdav_env["TEST_WEBDAV_USERNAME"],
            password=webdav_env["TEST_WEBDAV_PASSWORD"],
        )
    )
    results = run_conformance_suite(backend, skip_unsupported=True)
    assert all(r.passed for r in results)
