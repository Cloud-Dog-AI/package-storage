"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: FTP/FTPS backend with MLSD fallback and connection-per-operation behaviour.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import io
import posixpath
from ftplib import FTP, FTP_TLS, error_perm

from cloud_dog_storage.config.models import FtpConfig, TlsConfig
from cloud_dog_storage.errors import (
    BackendConnectionError,
    ConfigurationError,
    NotSupportedError,
    StorageFileNotFoundError,
)
from cloud_dog_storage.models import StorageEntry, StorageStat
from cloud_dog_storage.security.path_sanitiser import clean_posix
from cloud_dog_storage.security.tls import build_ssl_context

from .base import StorageBackend


class FtpStorage(StorageBackend):
    """FTP/FTPS backend with thread-safe connection-per-operation semantics."""

    backend_name = "ftp"

    def __init__(self, config: FtpConfig, *, tls: TlsConfig | None = None, timeout_s: int = 30) -> None:
        if not config.host:
            raise ConfigurationError("FTP storage requires ftp.host", backend_name=self.backend_name)
        self._host = config.host
        self._port = int(config.port)
        self._username = config.username or ""
        self._password = config.password or ""
        self._base_dir = clean_posix(config.base_dir or "/")
        self._use_tls = bool(config.use_tls)
        self._timeout_s = int(timeout_s)
        self._ssl_context = build_ssl_context(tls or TlsConfig()) if self._use_tls else None

    def _connect(self) -> FTP:
        try:
            ftp = FTP_TLS(context=self._ssl_context) if self._use_tls else FTP()
            ftp.connect(self._host, self._port, timeout=self._timeout_s)
            ftp.login(self._username, self._password)
            if self._use_tls and isinstance(ftp, FTP_TLS):
                ftp.prot_p()
            if self._base_dir != "/":
                ftp.cwd(self._base_dir)
            return ftp
        except Exception as exc:
            raise BackendConnectionError(f"FTP connection failed: {exc}", backend_name=self.backend_name) from exc

    def _remote_path(self, path: str) -> str:
        relative = clean_posix(path).lstrip("/")
        if not relative:
            return self._base_dir
        if self._base_dir == "/":
            return "/" + relative
        return posixpath.join(self._base_dir, relative)

    def read_bytes(self, path: str) -> bytes:
        ftp = self._connect()
        try:
            buffer = io.BytesIO()
            ftp.retrbinary(f"RETR {self._remote_path(path)}", buffer.write)
            return buffer.getvalue()
        except error_perm as exc:
            if str(exc).startswith("550"):
                raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name) from exc
            raise
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        ftp = self._connect()
        remote = self._remote_path(path)
        try:
            if not overwrite:
                try:
                    ftp.size(remote)
                    raise FileExistsError(clean_posix(path))
                except error_perm:
                    pass
            ftp.storbinary(f"STOR {remote}", io.BytesIO(data))
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        ftp = self._connect()
        remote = self._remote_path(path)
        try:
            try:
                ftp.delete(remote)
                return
            except error_perm as exc:
                if str(exc).startswith("550"):
                    try:
                        ftp.rmd(remote)
                        return
                    except error_perm as exc_dir:
                        if str(exc_dir).startswith("550") and missing_ok:
                            return
                        if str(exc_dir).startswith("550"):
                            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name) from exc_dir
                        raise
                raise
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def stat(self, path: str) -> StorageStat | None:
        ftp = self._connect()
        remote = self._remote_path(path)
        try:
            try:
                size = ftp.size(remote)
                if size is not None:
                    return StorageStat(path=clean_posix(path), is_dir=False, size=int(size))
            except error_perm:
                pass

            current = ftp.pwd()
            try:
                ftp.cwd(remote)
                ftp.cwd(current)
                return StorageStat(path=clean_posix(path), is_dir=True, size=None)
            except error_perm:
                return None
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]:
        ftp = self._connect()
        root = clean_posix(path)

        def list_one(directory: str) -> list[tuple[str, bool]]:
            remote = self._remote_path(directory)
            items: list[tuple[str, bool]] = []
            try:
                for name, facts in ftp.mlsd(remote):
                    if name in {".", ".."}:
                        continue
                    items.append((name, facts.get("type") == "dir"))
                return items
            except Exception:
                for full in ftp.nlst(remote):
                    name = posixpath.basename(full.rstrip("/"))
                    if not name or name in {".", ".."}:
                        continue
                    is_dir = False
                    current = ftp.pwd()
                    try:
                        ftp.cwd(posixpath.join(remote, name))
                        ftp.cwd(current)
                        is_dir = True
                    except Exception:
                        is_dir = False
                    items.append((name, is_dir))
                return items

        try:
            out: list[StorageEntry] = []
            queue: list[str] = [root]
            while queue:
                current = queue.pop(0)
                for name, is_dir in list_one(current):
                    child = clean_posix(posixpath.join(current, name))
                    out.append(StorageEntry(path=child, is_dir=is_dir))
                    if recursive and is_dir:
                        queue.append(child)
            return out
        except error_perm as exc:
            if str(exc).startswith("550"):
                raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name) from exc
            raise
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        ftp = self._connect()
        try:
            target = clean_posix(path)
            parts = [part for part in target.split("/") if part]
            current = "/"
            for part in parts:
                current = clean_posix(posixpath.join(current, part))
                remote = self._remote_path(current)
                try:
                    ftp.mkd(remote)
                except error_perm as exc:
                    if exist_ok and str(exc).startswith("550"):
                        continue
                    raise
                if not parents:
                    break
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        data = self.read_bytes(src)
        self.write_bytes(dst, data, overwrite=overwrite)

    def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        ftp = self._connect()
        source = self._remote_path(src)
        target = self._remote_path(dst)
        try:
            if not overwrite:
                try:
                    ftp.size(target)
                    raise FileExistsError(clean_posix(dst))
                except error_perm:
                    pass
            ftp.rename(source, target)
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()

    def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None:
        _ = path
        _ = mode
        _ = recursive
        raise NotSupportedError("chmod_path", backend=self.backend_name)

    def get_url(self, path: str) -> str:
        return f"ftp://{self._host}:{self._port}{self._remote_path(path)}"
