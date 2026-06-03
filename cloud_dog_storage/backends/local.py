"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Local filesystem storage backend with root-boundary enforcement.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from cloud_dog_storage.errors import QuotaExceededError, StorageFileNotFoundError, StoragePermissionError
from cloud_dog_storage.models import StorageEntry, StorageStat
from cloud_dog_storage.security.path_sanitiser import clean_posix, validate_within_root

from .base import StorageBackend


def _parse_octal(value: str, *, fallback: int) -> int:
    cleaned = (value or "").strip()
    if not cleaned:
        return fallback
    try:
        return int(cleaned, 8)
    except ValueError:
        return fallback


class LocalStorage(StorageBackend):
    """Local filesystem backend with secure root scoping."""

    backend_name = "local"

    def __init__(
        self,
        root_path: str | Path = "",
        *,
        min_free_bytes: int = 100 * 1024 * 1024,
        file_permissions: str = "0644",
        dir_permissions: str = "0755",
        subdir_pattern: str = "",
    ) -> None:
        base = Path(root_path or ".").expanduser().resolve()
        base.mkdir(parents=True, exist_ok=True)
        self._root = base
        self._min_free_bytes = max(0, int(min_free_bytes))
        self._file_permissions = _parse_octal(file_permissions, fallback=0o644)
        self._dir_permissions = _parse_octal(dir_permissions, fallback=0o755)
        self._subdir_pattern = subdir_pattern

    def _resolve(self, path: str) -> Path:
        return validate_within_root(path, self._root)

    def _logical_path(self, actual: Path) -> str:
        rel = actual.resolve().relative_to(self._root)
        return clean_posix("/" + str(rel).replace("\\", "/"))

    def _check_disk_space(self, required_bytes: int) -> None:
        if self._min_free_bytes <= 0:
            return
        free = shutil.disk_usage(self._root).free
        if free < required_bytes + self._min_free_bytes:
            raise QuotaExceededError(
                f"Insufficient disk space for write ({required_bytes} bytes requested)",
                backend_name=self.backend_name,
            )

    def read_bytes(self, path: str) -> bytes:
        target = self._resolve(path)
        if not target.exists() or not target.is_file():
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        try:
            return target.read_bytes()
        except PermissionError as exc:
            raise StoragePermissionError(clean_posix(path), backend=self.backend_name) from exc

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        target = self._resolve(path)
        if target.exists() and not overwrite:
            raise FileExistsError(clean_posix(path))
        target.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(target.parent, self._dir_permissions)
        self._check_disk_space(len(data))
        try:
            target.write_bytes(data)
            os.chmod(target, self._file_permissions)
        except PermissionError as exc:
            raise StoragePermissionError(clean_posix(path), backend=self.backend_name) from exc

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        target = self._resolve(path)
        if not target.exists():
            if missing_ok:
                return
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        except PermissionError as exc:
            raise StoragePermissionError(clean_posix(path), backend=self.backend_name) from exc

    def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]:
        target = self._resolve(path)
        if not target.exists() or not target.is_dir():
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        entries: list[StorageEntry] = []
        if recursive:
            for current, dirnames, filenames in os.walk(target):
                current_path = Path(current)
                for name in dirnames:
                    child = current_path / name
                    entries.append(StorageEntry(path=self._logical_path(child), is_dir=True))
                for name in filenames:
                    child = current_path / name
                    entries.append(StorageEntry(path=self._logical_path(child), is_dir=False))
        else:
            for child in target.iterdir():
                entries.append(StorageEntry(path=self._logical_path(child), is_dir=child.is_dir()))
        return sorted(entries, key=lambda item: item.path)

    def stat(self, path: str) -> StorageStat | None:
        target = self._resolve(path)
        if not target.exists():
            return None
        size = target.stat().st_size if target.is_file() else None
        return StorageStat(path=clean_posix(path), is_dir=target.is_dir(), size=size)

    def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        target = self._resolve(path)
        target.mkdir(parents=parents, exist_ok=exist_ok)
        os.chmod(target, self._dir_permissions)

    def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        source = self._resolve(src)
        if not source.exists():
            raise StorageFileNotFoundError(clean_posix(src), backend=self.backend_name)
        target = self._resolve(dst)
        if target.exists() and not overwrite:
            raise FileExistsError(clean_posix(dst))
        if source.is_dir():
            if target.exists() and overwrite:
                shutil.rmtree(target)
            shutil.copytree(source, target, dirs_exist_ok=overwrite)
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        source = self._resolve(src)
        if not source.exists():
            raise StorageFileNotFoundError(clean_posix(src), backend=self.backend_name)
        target = self._resolve(dst)
        if target.exists() and not overwrite:
            raise FileExistsError(clean_posix(dst))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and overwrite:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(source), str(target))

    def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None:
        target = self._resolve(path)
        if not target.exists():
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        if recursive and target.is_dir():
            for current, dirnames, filenames in os.walk(target):
                os.chmod(current, mode)
                for name in dirnames:
                    os.chmod(Path(current) / name, mode)
                for name in filenames:
                    os.chmod(Path(current) / name, mode)
            return
        os.chmod(target, mode)

    def append_text(self, path: str, text: str, *, encoding: str = "utf-8") -> None:
        """Append text to a file, creating it and parent directories if needed."""
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._check_disk_space(len(text.encode(encoding)))
        try:
            with target.open("a", encoding=encoding) as handle:
                handle.write(text)
        except PermissionError as exc:
            raise StoragePermissionError(clean_posix(path), backend=self.backend_name) from exc

    def copy_with_metadata(self, src: str, dst: str) -> None:
        """Copy a file preserving metadata (timestamps, permissions) via shutil.copy2."""
        source = self._resolve(src)
        if not source.exists():
            raise StorageFileNotFoundError(clean_posix(src), backend=self.backend_name)
        target = self._resolve(dst)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def disk_usage(self) -> tuple[int, int, int]:
        """Return (total, used, free) bytes for the filesystem containing the root."""
        usage = shutil.disk_usage(self._root)
        return (usage.total, usage.used, usage.free)

    def get_url(self, path: str) -> str:
        return self._resolve(path).as_uri()
