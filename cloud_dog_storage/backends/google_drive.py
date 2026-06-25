"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Google Drive backend using v3 REST API and OAuth2 refresh flow.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import json
import mimetypes
import posixpath
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests

from cloud_dog_storage.config.models import GoogleDriveConfig, TlsConfig
from cloud_dog_storage.errors import (
    BackendConnectionError,
    ConfigurationError,
    NotSupportedError,
    StorageFileNotFoundError,
)
from cloud_dog_storage.models import StorageEntry, StorageStat
from cloud_dog_storage.security.path_sanitiser import clean_posix
from cloud_dog_storage.security.tls import build_requests_verify

from .base import StorageBackend

FOLDER_MIME = "application/vnd.google-apps.folder"


def extract_folder_id(folder_id: str | None, folder_url: str | None) -> str | None:
    """Extract Google Drive folder ID from explicit ID or known URL patterns."""
    if folder_id and folder_id.strip():
        return folder_id.strip()
    if not folder_url:
        return None
    parsed = urlparse(folder_url)
    parts = [part for part in parsed.path.split("/") if part]
    if "folders" in parts:
        idx = parts.index("folders")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    query = parse_qs(parsed.query)
    if query.get("id"):
        return query["id"][0]
    return None


class GoogleDriveStorage(StorageBackend):
    """Google Drive backend with token refresh and path-based folder traversal."""

    backend_name = "google_drive"

    def __init__(self, config: GoogleDriveConfig, *, tls: TlsConfig | None = None, timeout_s: int = 30) -> None:
        folder_id = extract_folder_id(config.folder_id, config.folder_url)
        if not folder_id:
            raise ConfigurationError(
                "Google Drive storage requires google_drive.folder_id or google_drive.folder_url",
                backend_name=self.backend_name,
            )
        if not config.client_id or not config.client_secret:
            raise ConfigurationError(
                "Google Drive storage requires google_drive.client_id and google_drive.client_secret",
                backend_name=self.backend_name,
            )
        if not (config.refresh_token or config.access_token):
            raise ConfigurationError(
                "Google Drive storage requires google_drive.refresh_token or google_drive.access_token",
                backend_name=self.backend_name,
            )

        self._folder_id = folder_id
        self._client_id = config.client_id
        self._client_secret = config.client_secret
        self._refresh_token = config.refresh_token
        self._access_token = config.access_token
        self._token_uri = (config.token_uri or "https://oauth2.googleapis.com/token").strip()
        self._timeout_s = int(timeout_s)
        self._token_expires_at: float | None = None
        self._verify = build_requests_verify(tls or TlsConfig())

    def _token(self) -> str:
        now = time.time()
        if self._access_token and self._token_expires_at and now < self._token_expires_at - 30:
            return self._access_token
        if self._access_token and not self._refresh_token:
            return self._access_token
        if not self._refresh_token:
            raise BackendConnectionError("Google Drive refresh token not configured", backend_name=self.backend_name)

        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
        }
        try:
            resp = requests.post(self._token_uri, data=data, timeout=self._timeout_s, verify=self._verify)
        except requests.RequestException as exc:
            raise BackendConnectionError(
                f"Google Drive token refresh failed: {exc}", backend_name=self.backend_name
            ) from exc

        resp.raise_for_status()
        payload = resp.json()
        token = payload.get("access_token")
        if not token:
            raise BackendConnectionError(
                "Google Drive token refresh response missing access_token",
                backend_name=self.backend_name,
            )

        self._access_token = token
        expires_in = payload.get("expires_in")
        if isinstance(expires_in, int):
            self._token_expires_at = time.time() + expires_in
        return token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token()}"}

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:  # type: ignore[no-untyped-def]
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.update(self._headers())
        params = dict(kwargs.pop("params", {}) or {})
        if "googleapis.com/drive/v3/" in url:
            params.setdefault("supportsAllDrives", True)
            if url.rstrip("/").endswith("/files"):
                params.setdefault("includeItemsFromAllDrives", True)
        try:
            return requests.request(
                method,
                url,
                headers=headers,
                params=params,
                timeout=self._timeout_s,
                verify=self._verify,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise BackendConnectionError(f"Google Drive request failed: {exc}", backend_name=self.backend_name) from exc

    def _lookup_child(self, parent_id: str, name: str) -> dict[str, Any] | None:
        escaped_name = name.replace("'", "\\'")
        query = f"'{parent_id}' in parents and name = '{escaped_name}' and trashed = false"
        resp = self._request(
            "GET",
            "https://www.googleapis.com/drive/v3/files",
            params={"q": query, "fields": "files(id,name,mimeType,size,parents)"},
        )
        resp.raise_for_status()
        files = resp.json().get("files", [])
        return files[0] if files else None

    def _get_metadata(self, file_id: str) -> dict[str, Any]:
        resp = self._request(
            "GET",
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={"fields": "id,name,mimeType,size,parents"},
        )
        if resp.status_code == 404:
            raise StorageFileNotFoundError(file_id, backend=self.backend_name)
        resp.raise_for_status()
        return resp.json()

    def _create_folder(self, parent_id: str, name: str) -> dict[str, Any]:
        payload = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]}
        resp = self._request(
            "POST",
            "https://www.googleapis.com/drive/v3/files",
            json=payload,
            params={"fields": "id,name,mimeType,size,parents"},
        )
        resp.raise_for_status()
        return resp.json()

    def _resolve_path(self, path: str, *, create_dirs: bool = False) -> tuple[str, bool]:
        logical = clean_posix(path)
        if logical == "/":
            return self._folder_id, True

        current = self._folder_id
        parts = [part for part in logical.split("/") if part]
        for idx, part in enumerate(parts):
            child = self._lookup_child(current, part)
            is_last = idx == len(parts) - 1
            if child is None:
                if create_dirs or not is_last:
                    child = self._create_folder(current, part)
                else:
                    raise StorageFileNotFoundError(logical, backend=self.backend_name)
            current = child["id"]

        info = self._get_metadata(current)
        return current, info.get("mimeType") == FOLDER_MIME

    def read_bytes(self, path: str) -> bytes:
        file_id, is_dir = self._resolve_path(path)
        if is_dir:
            raise IsADirectoryError(clean_posix(path))
        resp = self._request(
            "GET",
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={"alt": "media"},
            stream=True,
        )
        if resp.status_code == 404:
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        resp.raise_for_status()
        return resp.content

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        logical = clean_posix(path)
        parent_path = clean_posix(posixpath.dirname(logical))
        name = posixpath.basename(logical)
        if not name:
            raise ValueError("File name is required")

        parent_id, _ = self._resolve_path(parent_path, create_dirs=True)
        existing = self._lookup_child(parent_id, name)
        if existing and not overwrite:
            raise FileExistsError(logical)

        mime_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        metadata = {"name": name, "parents": [parent_id]}

        if existing:
            payload = {
                "metadata": ("metadata", json.dumps({"name": name}), "application/json"),
                "file": (name, data, mime_type),
            }
            resp = self._request(
                "PATCH",
                f"https://www.googleapis.com/upload/drive/v3/files/{existing['id']}",
                params={"uploadType": "multipart"},
                files=payload,
            )
        else:
            payload = {
                "metadata": ("metadata", json.dumps(metadata), "application/json"),
                "file": (name, data, mime_type),
            }
            resp = self._request(
                "POST",
                "https://www.googleapis.com/upload/drive/v3/files",
                params={"uploadType": "multipart"},
                files=payload,
            )
        resp.raise_for_status()

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        try:
            file_id, _ = self._resolve_path(path)
        except StorageFileNotFoundError:
            if missing_ok:
                return
            raise

        resp = self._request("DELETE", f"https://www.googleapis.com/drive/v3/files/{file_id}")
        if resp.status_code == 404 and missing_ok:
            return
        if resp.status_code == 404:
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        resp.raise_for_status()

    def stat(self, path: str) -> StorageStat | None:
        try:
            file_id, is_dir = self._resolve_path(path)
        except StorageFileNotFoundError:
            return None

        meta = self._get_metadata(file_id)
        size = None
        if not is_dir and meta.get("size") is not None:
            try:
                size = int(meta["size"])
            except (TypeError, ValueError):
                size = None
        return StorageStat(path=clean_posix(path), is_dir=is_dir, size=size)

    def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]:
        root_path = clean_posix(path)
        root_id, is_dir = self._resolve_path(root_path)
        if not is_dir:
            raise NotADirectoryError(root_path)

        out: list[StorageEntry] = []
        queue: list[tuple[str, str]] = [(root_id, root_path)]
        while queue:
            parent_id, logical_parent = queue.pop(0)
            query = f"'{parent_id}' in parents and trashed = false"
            resp = self._request(
                "GET",
                "https://www.googleapis.com/drive/v3/files",
                params={
                    "q": query,
                    "fields": (
                        "files(id,name,mimeType,size,parents,createdTime,modifiedTime,"
                        "version,md5Checksum,webViewLink)"
                    ),
                },
            )
            resp.raise_for_status()
            files = resp.json().get("files", [])
            for item in files:
                child_path = clean_posix(posixpath.join(logical_parent, item.get("name", "")))
                child_is_dir = item.get("mimeType") == FOLDER_MIME
                size = None
                if not child_is_dir and item.get("size") is not None:
                    try:
                        size = int(item["size"])
                    except (TypeError, ValueError):
                        size = None
                out.append(
                    StorageEntry(
                        path=child_path,
                        is_dir=child_is_dir,
                        size=size,
                        created_at=item.get("createdTime"),
                        modified_at=item.get("modifiedTime"),
                        metadata={
                            "drive_file_id": item.get("id"),
                            "drive_revision": item.get("version"),
                            "drive_md5_checksum": item.get("md5Checksum"),
                            "drive_web_view_link": item.get("webViewLink"),
                        },
                    )
                )
                if recursive and child_is_dir:
                    queue.append((item["id"], child_path))

        return out

    def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        _ = exist_ok
        logical = clean_posix(path)
        if logical == "/":
            return

        parts = [part for part in logical.split("/") if part]
        current = self._folder_id
        for part in parts:
            child = self._lookup_child(current, part)
            if child is None:
                child = self._create_folder(current, part)
            elif child.get("mimeType") != FOLDER_MIME:
                raise NotADirectoryError(logical)
            current = child["id"]
            if not parents:
                break

    def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        src_id, src_is_dir = self._resolve_path(src)
        if src_is_dir:
            raise NotSupportedError("copy_path_directory", backend=self.backend_name)

        dst_logical = clean_posix(dst)
        parent_path = clean_posix(posixpath.dirname(dst_logical))
        name = posixpath.basename(dst_logical)
        parent_id, _ = self._resolve_path(parent_path, create_dirs=True)
        existing = self._lookup_child(parent_id, name)

        if existing and not overwrite:
            raise FileExistsError(dst_logical)
        if existing and overwrite:
            self._request("DELETE", f"https://www.googleapis.com/drive/v3/files/{existing['id']}").raise_for_status()

        resp = self._request(
            "POST",
            f"https://www.googleapis.com/drive/v3/files/{src_id}/copy",
            json={"name": name, "parents": [parent_id]},
        )
        resp.raise_for_status()

    def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        src_id, _ = self._resolve_path(src)
        dst_logical = clean_posix(dst)
        parent_path = clean_posix(posixpath.dirname(dst_logical))
        name = posixpath.basename(dst_logical)
        parent_id, _ = self._resolve_path(parent_path, create_dirs=True)
        existing = self._lookup_child(parent_id, name)

        if existing and not overwrite:
            raise FileExistsError(dst_logical)
        if existing and overwrite:
            self._request("DELETE", f"https://www.googleapis.com/drive/v3/files/{existing['id']}").raise_for_status()

        meta = self._get_metadata(src_id)
        prev_parents = ",".join(meta.get("parents") or [])
        resp = self._request(
            "PATCH",
            f"https://www.googleapis.com/drive/v3/files/{src_id}",
            params={"addParents": parent_id, "removeParents": prev_parents},
            json={"name": name},
        )
        resp.raise_for_status()

    def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None:
        _ = path
        _ = mode
        _ = recursive
        raise NotSupportedError("chmod_path", backend=self.backend_name)

    def get_url(self, path: str) -> str:
        file_id, _ = self._resolve_path(path)
        return f"https://drive.google.com/file/d/{file_id}/view"
