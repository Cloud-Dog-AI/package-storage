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
Description: UT1.12: WebDAV PROPFIND XML parsing tests.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from cloud_dog_storage.backends.webdav import parse_propfind_xml


def test_parse_propfind_xml_basic() -> None:
    xml = b"""<?xml version='1.0' encoding='utf-8'?>
<d:multistatus xmlns:d='DAV:'>
  <d:response>
    <d:href>/dav/</d:href>
    <d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop></d:propstat>
  </d:response>
  <d:response>
    <d:href>/dav/a.txt</d:href>
    <d:propstat><d:prop><d:getcontentlength>5</d:getcontentlength></d:prop></d:propstat>
  </d:response>
</d:multistatus>"""

    items = parse_propfind_xml(xml, base_url="https://host/dav")
    assert items[0].path == "/"
    assert items[0].is_dir is True
    assert items[1].path == "/a.txt"
    assert items[1].is_dir is False
    assert items[1].size == 5
