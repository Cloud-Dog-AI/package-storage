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
Description: UT1.24: TLS helper tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import ssl

from cloud_dog_storage.config.models import TlsConfig
from cloud_dog_storage.security.tls import build_requests_verify, build_ssl_context


def test_requests_verify_default() -> None:
    assert build_requests_verify(TlsConfig()) is True


def test_requests_verify_insecure() -> None:
    assert build_requests_verify(TlsConfig(insecure_skip_verify=True)) is False


def test_ssl_context_insecure() -> None:
    ctx = build_ssl_context(TlsConfig(insecure_skip_verify=True))
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_NONE
