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
Description: UT1.30: Observability logging redaction tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.observability.logging import redact_sensitive


def test_redact_sensitive_keys() -> None:
    data = {
        "access_key": "AKIA...",
        "secret_key": "S",
        "password": "P",
        "refresh_token": "T",
        "path": "/x",
    }
    redacted = redact_sensitive(data)
    assert redacted["access_key"] == "***REDACTED***"
    assert redacted["secret_key"] == "***REDACTED***"
    assert redacted["password"] == "***REDACTED***"
    assert redacted["refresh_token"] == "***REDACTED***"
    assert redacted["path"] == "/x"
