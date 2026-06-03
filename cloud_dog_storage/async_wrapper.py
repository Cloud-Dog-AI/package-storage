"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Async wrapper that delegates sync storage operations to a thread pool.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING

from cloud_dog_storage.models import StorageEntry, StorageStat, StoredFile
from cloud_dog_storage.security.path_sanitiser import clean_posix

if TYPE_CHECKING:
    from collections.abc import Iterable

    from cloud_dog_storage.backends.base import StorageBackend


class AsyncStorageBackend:
    """Wrap a synchronous backend and execute operations in a thread pool.

    This wrapper uses an explicit ThreadPoolExecutor instead of the event loop default
    executor to avoid environment-specific default executor issues.
    """

    def __init__(self, backend: StorageBackend, *, max_workers: int | None = None) -> None:
        self._backend = backend
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="cloud_dog_storage",
        )

    @property
    def backend_name(self) -> str:
        return self._backend.backend_name

    def close(self) -> None:
        """Shut down the internal executor."""
        self._executor.shutdown(wait=False, cancel_futures=True)

    async def _run(self, func, /, *args, **kwargs):  # type: ignore[no-untyped-def]
        # In some environments, the event-loop self-pipe wake mechanism is unreliable, causing
        # `await loop.run_in_executor(...)` to hang if the thread finishes after the loop blocks.
        # Submitting directly and polling via `asyncio.wait(..., timeout=...)` guarantees the loop
        # wakes periodically to process the completion callback.
        cfut = self._executor.submit(partial(func, *args, **kwargs))
        afut = asyncio.wrap_future(cfut)
        while True:
            done, _ = await asyncio.wait({afut}, timeout=0.05)
            if done:
                return await afut

    async def read_bytes(self, path: str) -> bytes:
        return await self._run(self._backend.read_bytes, path)

    async def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        await self._run(self._backend.write_bytes, path, data, overwrite=overwrite)

    async def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        await self._run(self._backend.delete_path, path, missing_ok=missing_ok)

    async def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]:
        return await self._run(self._backend.list_dir, path, recursive=recursive)

    async def stat(self, path: str) -> StorageStat | None:
        return await self._run(self._backend.stat, path)

    async def exists(self, path: str) -> bool:
        return await self._run(self._backend.exists, path)

    async def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        await self._run(self._backend.create_dir, path, parents=parents, exist_ok=exist_ok)

    async def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        await self._run(self._backend.copy_path, src, dst, overwrite=overwrite)

    async def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        await self._run(self._backend.move_path, src, dst, overwrite=overwrite)

    async def rename_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        await self._run(self._backend.rename_path, src, dst, overwrite=overwrite)

    async def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None:
        await self._run(self._backend.chmod_path, path, mode, recursive=recursive)

    async def iter_paths(self, roots: Iterable[str], *, max_depth: int | None = None) -> list[str]:
        return await self._run(lambda: list(self._backend.iter_paths(roots, max_depth=max_depth)))

    async def get_url(self, path: str) -> str:
        return await self._run(self._backend.get_url, path)

    async def store_file(
        self,
        content: bytes,
        filename: str,
        content_type: str,
        metadata: dict | None = None,
    ) -> StoredFile:
        logical = clean_posix(filename)
        await self.write_bytes(logical, content, overwrite=True)
        extension = os.path.splitext(logical)[1].lstrip(".") or (
            content_type.split("/")[-1] if "/" in content_type else "bin"
        )
        return StoredFile(
            path=logical,
            format=extension,
            size_bytes=len(content),
            backend_name=self.backend_name,
            metadata=metadata or {},
        )

    async def get_file_content(self, path: str) -> bytes:
        return await self.read_bytes(path)

    async def delete_file(self, path: str) -> bool:
        if not await self.exists(path):
            return False
        await self.delete_path(path, missing_ok=True)
        return True

    async def file_exists(self, path: str) -> bool:
        return await self.exists(path)

    async def get_file_url(self, path: str) -> str:
        return await self.get_url(path)
