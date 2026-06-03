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
Description: UT1.10: S3 SigV4 signing helper tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.s3 import _aws_v4_signing_key, _canonical_query, _sha256_hex


def test_sha256_hex() -> None:
    assert _sha256_hex(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_signing_key_is_stable() -> None:
    key = _aws_v4_signing_key("wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY", "20120215", "us-east-1", "s3")
    assert isinstance(key, (bytes, bytearray))
    assert len(key) == 32


def test_canonical_query_sorted_and_encoded() -> None:
    q = _canonical_query({"b": "2", "a": "1", "space": "a b"})
    assert q == "a=1&b=2&space=a%20b"
