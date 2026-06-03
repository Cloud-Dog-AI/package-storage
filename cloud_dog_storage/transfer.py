"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Shared file-transfer helpers for PS-94 file transfer flows.
Standard: PS-94 (File Transfer), PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import base64
import binascii
import mimetypes
import os
import re
from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from cloud_dog_storage.backends.local import LocalStorage

_LOCAL_FS = LocalStorage(root_path="/")
_FILENAME_RE = re.compile(r"[^A-Za-z0-9._ -]+")


@dataclass(slots=True, frozen=True)
class AttachmentDescriptor:
    """Attachment metadata extracted from a MIME message."""

    filename: str
    content_type: str
    size_bytes: int
    content_id: str | None
    part_id: str


def encode_base64(data: bytes, *, urlsafe: bool = False) -> str:
    """Encode bytes as ASCII base64 text."""
    encoder = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    return encoder(data).decode("ascii")


def decode_base64(encoded: str, *, urlsafe: bool = False) -> bytes:
    """Decode ASCII base64 text into bytes."""
    decoder = base64.urlsafe_b64decode if urlsafe else base64.b64decode
    try:
        return decoder(encoded.encode("ascii"))
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid base64 payload") from exc


def sanitize_filename(name: str) -> str:
    """Return a transfer-safe basename for a user-supplied filename."""
    candidate = os.path.basename((name or "").strip()).replace("\x00", "")
    candidate = candidate.replace("\\", "_").replace("/", "_")
    candidate = _FILENAME_RE.sub("_", candidate).strip(" .")
    return candidate or "file"


def validate_file_size(data: bytes, max_bytes: int) -> bool:
    """Return True when data length is within the supplied byte limit."""
    if max_bytes < 0:
        raise ValueError("max_bytes must be >= 0")
    return len(data) <= max_bytes


def detect_content_type(filename: str, data: bytes) -> str:
    """Best-effort content type detection from filename and common signatures."""
    guessed, _encoding = mimetypes.guess_type(filename or "")
    if guessed and guessed != "application/octet-stream":
        return guessed

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "application/zip"
    if data.startswith((b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        return "audio/mpeg"

    if data:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            return "application/octet-stream"
        return "text/plain"
    return "application/octet-stream"


def fetch_uri(uri: str, *, timeout_seconds: float = 30.0) -> bytes:
    """Fetch bytes from file://, http://, https://, or plain local paths."""
    if not uri or not uri.strip():
        raise ValueError("uri is required")

    parsed = urlparse(uri)
    if parsed.scheme in {"http", "https"}:
        request = Request(uri, headers={"User-Agent": "cloud-dog-storage/transfer"})
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            return response.read()

    if parsed.scheme == "file":
        path = unquote(parsed.path or "")
        if os.name == "nt" and parsed.netloc:
            path = f"//{parsed.netloc}{path}"
        return _read_local_path(path)

    if parsed.scheme:
        raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")

    return _read_local_path(uri)


def list_mime_attachments(
    message: Message, max_attachment_bytes: int | None = None
) -> list[AttachmentDescriptor]:
    """Return attachment descriptors for MIME parts with attachment disposition."""
    attachments: list[AttachmentDescriptor] = []
    for index, part in enumerate(message.walk(), start=1):
        disposition = (part.get("Content-Disposition") or "").lower()
        if "attachment" not in disposition:
            continue

        payload = part.get_payload(decode=True) or b""
        size_bytes = len(payload)
        if max_attachment_bytes is not None and not validate_file_size(payload, max_attachment_bytes):
            raise ValueError(f"Attachment exceeds max_attachment_bytes: {size_bytes}")

        filename = sanitize_filename(part.get_filename() or f"part-{index}")
        content_type = part.get_content_type() or detect_content_type(filename, payload)
        attachments.append(
            AttachmentDescriptor(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                content_id=part.get("Content-ID"),
                part_id=str(index),
            )
        )
    return attachments


def _read_local_path(path_text: str) -> bytes:
    path = str(Path(path_text).expanduser().resolve())
    stat = _LOCAL_FS.stat(path)
    if stat is None or stat.is_dir:
        raise FileNotFoundError(path)
    return _LOCAL_FS.read_bytes(path)
