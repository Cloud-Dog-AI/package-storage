"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Path normalisation and root-boundary validation helpers.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import posixpath
from pathlib import Path
from urllib.parse import quote, unquote

from cloud_dog_storage.errors import StoragePermissionError


def clean_posix(path: str) -> str:
    """Normalise to POSIX absolute path and remove unsafe bytes."""
    raw = path or ""
    # Normalise any percent-encoded traversal attempts before cleaning.
    text = unquote(raw) if "%" in raw else raw
    # Remove real and common-encoded null-byte injection forms.
    text = text.replace("\x00", "").replace("\\x00", "")
    if not text:
        return "/"
    if not text.startswith("/"):
        text = "/" + text
    norm = posixpath.normpath(text)
    if not norm.startswith("/"):
        norm = "/" + norm
    return norm


def validate_within_root(path: str, root: str | Path) -> Path:
    """Resolve a path under a root and reject root-boundary escape attempts."""
    root_path = Path(root).expanduser().resolve()
    raw = path or ""
    # Decode percent-encoding first so `%2e%2e` becomes `..` and `%00` becomes a real null.
    decoded = unquote(raw) if "%" in raw else raw
    decoded = decoded.replace("\x00", "").replace("\\x00", "")

    # Treat the input as a logical path relative to `root`, even if it starts with `/`.
    # Use POSIX normalisation but do not collapse leading traversal away from the root.
    relative = decoded.lstrip("/").replace("\\", "/")
    relative = posixpath.normpath(relative)
    resolved = root_path if relative in ("", ".") else (root_path / relative).resolve()
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise StoragePermissionError(clean_posix(path), backend="local") from exc
    return resolved


def url_encode_path(path: str) -> str:
    """URL-encode each path segment while preserving path separators."""
    normalised = clean_posix(path)
    if normalised == "/":
        return "/"
    parts = [quote(part, safe="-_.~") for part in normalised.lstrip("/").split("/")]
    return "/" + "/".join(parts)
