"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: In-memory thread-safe mock storage backend for tests.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import posixpath
import threading

from cloud_dog_storage.backends.base import StorageBackend
from cloud_dog_storage.errors import StorageFileNotFoundError
from cloud_dog_storage.models import StorageEntry, StorageStat
from cloud_dog_storage.security.path_sanitiser import clean_posix


class MockStorageBackend(StorageBackend):
    """In-memory storage backend implementing full StorageBackend interface."""

    backend_name = "mock"

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}
        self._dirs: set[str] = {"/"}
        self._lock = threading.Lock()

    def _ensure_parent_dirs(self, path: str) -> None:
        current = "/"
        for part in [p for p in clean_posix(path).split("/") if p][:-1]:
            current = clean_posix(posixpath.join(current, part))
            self._dirs.add(current)

    def _assert_exists(self, path: str) -> None:
        if path in self._files or path in self._dirs:
            return
        raise StorageFileNotFoundError(path, backend=self.backend_name)

    def read_bytes(self, path: str) -> bytes:
        logical = clean_posix(path)
        with self._lock:
            if logical not in self._files:
                raise StorageFileNotFoundError(logical, backend=self.backend_name)
            return self._files[logical]

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        logical = clean_posix(path)
        with self._lock:
            if logical in self._files and not overwrite:
                raise FileExistsError(logical)
            self._ensure_parent_dirs(logical)
            self._files[logical] = data

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        logical = clean_posix(path)
        with self._lock:
            if logical in self._files:
                del self._files[logical]
                return
            if logical in self._dirs:
                for key in list(self._files):
                    if key.startswith(logical.rstrip("/") + "/"):
                        del self._files[key]
                for key in list(self._dirs):
                    if key != "/" and key.startswith(logical.rstrip("/") + "/"):
                        self._dirs.remove(key)
                if logical != "/":
                    self._dirs.remove(logical)
                return
            if not missing_ok:
                raise StorageFileNotFoundError(logical, backend=self.backend_name)

    def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]:
        root = clean_posix(path)
        with self._lock:
            self._assert_exists(root)
            out: list[StorageEntry] = []
            prefix = root.rstrip("/") + "/"
            for directory in sorted(self._dirs):
                if directory == root or not directory.startswith(prefix):
                    continue
                remainder = directory[len(prefix) :]
                if not recursive and "/" in remainder:
                    continue
                out.append(StorageEntry(path=directory, is_dir=True))
            for file_path in sorted(self._files):
                if not file_path.startswith(prefix):
                    continue
                remainder = file_path[len(prefix) :]
                if not recursive and "/" in remainder:
                    continue
                out.append(StorageEntry(path=file_path, is_dir=False))
            return out

    def stat(self, path: str) -> StorageStat | None:
        logical = clean_posix(path)
        with self._lock:
            if logical in self._dirs:
                return StorageStat(path=logical, is_dir=True, size=None)
            data = self._files.get(logical)
            if data is None:
                return None
            return StorageStat(path=logical, is_dir=False, size=len(data))

    def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        logical = clean_posix(path)
        with self._lock:
            if logical in self._files:
                raise FileExistsError(logical)
            if logical in self._dirs and not exist_ok:
                raise FileExistsError(logical)
            if parents:
                current = "/"
                for part in [p for p in logical.split("/") if p]:
                    current = clean_posix(posixpath.join(current, part))
                    self._dirs.add(current)
            else:
                self._dirs.add(logical)

    def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        source = clean_posix(src)
        target = clean_posix(dst)
        with self._lock:
            if source in self._files:
                if target in self._files and not overwrite:
                    raise FileExistsError(target)
                self._ensure_parent_dirs(target)
                self._files[target] = self._files[source]
                return
            if source not in self._dirs:
                raise StorageFileNotFoundError(source, backend=self.backend_name)
            if target in self._dirs and not overwrite:
                raise FileExistsError(target)
            self._dirs.add(target)
            src_prefix = source.rstrip("/") + "/"
            dst_prefix = target.rstrip("/") + "/"
            for directory in list(self._dirs):
                if directory.startswith(src_prefix):
                    self._dirs.add(dst_prefix + directory[len(src_prefix) :])
            for file_path, content in list(self._files.items()):
                if file_path.startswith(src_prefix):
                    self._files[dst_prefix + file_path[len(src_prefix) :]] = content

    def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        source = clean_posix(src)
        target = clean_posix(dst)
        with self._lock:
            if source == target:
                return
        self.copy_path(source, target, overwrite=overwrite)
        self.delete_path(source, missing_ok=False)

    def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None:
        _ = mode
        _ = recursive
        logical = clean_posix(path)
        with self._lock:
            self._assert_exists(logical)

    def get_url(self, path: str) -> str:
        return f"mock://{clean_posix(path).lstrip('/')}"
