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

from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path

import pytest

from cloud_dog_storage.transfer import (
    decode_base64,
    detect_content_type,
    encode_base64,
    fetch_uri,
    list_mime_attachments,
    sanitize_filename,
    validate_file_size,
)


def test_base64_round_trip() -> None:
    payload = b"cloud-dog-transfer"
    encoded = encode_base64(payload)
    assert decode_base64(encoded) == payload


def test_base64_invalid_payload_raises() -> None:
    with pytest.raises(ValueError, match="Invalid base64 payload"):
        decode_base64("%%%not-base64%%%")


def test_sanitize_filename_strips_path_and_unsafe_bytes() -> None:
    assert sanitize_filename("../unsafe\\name?.png") == "unsafe_name_.png"
    assert sanitize_filename("") == "file"


def test_validate_file_size() -> None:
    assert validate_file_size(b"abc", 3) is True
    assert validate_file_size(b"abcd", 3) is False


def test_detect_content_type_prefers_extension_then_magic() -> None:
    assert detect_content_type("image.png", b"plain") == "image/png"
    assert detect_content_type("unknown.bin", b"%PDF-1.4") == "application/pdf"
    assert detect_content_type("unknown.bin", "hello".encode("utf-8")) == "text/plain"


def test_fetch_uri_reads_local_path(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello transfer", encoding="utf-8")
    assert fetch_uri(str(sample)) == b"hello transfer"


def test_fetch_uri_reads_file_scheme(tmp_path: Path) -> None:
    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"\x00\x01\x02")
    assert fetch_uri(sample.as_uri()) == b"\x00\x01\x02"


def test_fetch_uri_rejects_unsupported_scheme() -> None:
    with pytest.raises(ValueError, match="Unsupported URI scheme"):
        fetch_uri("ftp://example.com/file.txt")


def test_list_mime_attachments_returns_sanitised_metadata() -> None:
    message = EmailMessage()
    message.set_content("body")
    message.add_attachment(
        b"payload",
        maintype="application",
        subtype="octet-stream",
        filename="../unsafe name.bin",
    )

    attachments = list_mime_attachments(message)
    assert len(attachments) == 1
    attachment = attachments[0]
    assert attachment.filename == "unsafe name.bin"
    assert attachment.size_bytes == 7
    assert attachment.part_id == "3"


def test_list_mime_attachments_enforces_size_limit() -> None:
    message = EmailMessage()
    message.set_content("body")
    message.add_attachment(
        b"oversized",
        maintype="application",
        subtype="octet-stream",
        filename="attachment.bin",
    )

    with pytest.raises(ValueError, match="Attachment exceeds max_attachment_bytes"):
        list_mime_attachments(message, max_attachment_bytes=4)
