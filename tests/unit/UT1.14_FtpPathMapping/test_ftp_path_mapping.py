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
Description: UT1.14: FTP path mapping tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.ftp import FtpStorage
from cloud_dog_storage.config.models import FtpConfig, TlsConfig


def test_remote_path_root_dir() -> None:
    ftp = FtpStorage(FtpConfig(host="h", base_dir="/"), tls=TlsConfig(), timeout_s=30)
    assert ftp._remote_path("/a/b.txt") == "/a/b.txt"


def test_remote_path_custom_base_dir() -> None:
    ftp = FtpStorage(FtpConfig(host="h", base_dir="/base"), tls=TlsConfig(), timeout_s=30)
    assert ftp._remote_path("/a/b.txt") == "/base/a/b.txt"
