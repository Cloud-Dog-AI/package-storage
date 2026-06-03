"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Base storage backend interface and default behaviour.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cloud_dog_storage.errors import NotSupportedError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from cloud_dog_storage.models import StorageEntry, StorageStat


class StorageBackend:
    """Minimal file-like API over a backing store."""

    backend_name: str = "unknown"

    def read_bytes(self, path: str) -> bytes:
        raise NotImplementedError

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        raise NotImplementedError

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        raise NotImplementedError

    def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]:
        raise NotImplementedError

    def stat(self, path: str) -> StorageStat | None:
        raise NotImplementedError

    def exists(self, path: str) -> bool:
        """Check path existence via `stat` by default."""
        return self.stat(path) is not None

    def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        raise NotSupportedError("create_dir", backend=self.backend_name)

    def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        raise NotSupportedError("copy_path", backend=self.backend_name)

    def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        raise NotSupportedError("move_path", backend=self.backend_name)

    def rename_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        self.move_path(src, dst, overwrite=overwrite)

    def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None:
        raise NotSupportedError("chmod_path", backend=self.backend_name)

    def iter_paths(self, roots: Iterable[str], *, max_depth: int | None = None) -> Iterable[str]:
        """Enumerate file paths under the given roots."""
        for root in roots:
            queue: list[tuple[str, int]] = [(root, 0)]
            while queue:
                current, depth = queue.pop(0)
                for entry in self.list_dir(current, recursive=False):
                    next_depth = depth + 1
                    if entry.is_dir:
                        if max_depth is None or next_depth <= max_depth:
                            queue.append((entry.path, next_depth))
                        continue
                    if max_depth is None or next_depth <= max_depth:
                        yield entry.path

    def append_text(self, path: str, text: str, *, encoding: str = "utf-8") -> None:
        """Append text to a file."""
        raise NotSupportedError("append_text", backend=self.backend_name)

    def copy_with_metadata(self, src: str, dst: str) -> None:
        """Copy a file preserving metadata (timestamps, permissions)."""
        raise NotSupportedError("copy_with_metadata", backend=self.backend_name)

    def disk_usage(self) -> tuple[int, int, int]:
        """Return (total, used, free) bytes for the backend's storage."""
        raise NotSupportedError("disk_usage", backend=self.backend_name)

    def get_url(self, path: str) -> str:
        raise NotSupportedError("get_url", backend=self.backend_name)
