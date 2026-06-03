"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: WebDAV backend with PROPFIND XML parsing and retry-aware moves.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import posixpath
import time
from dataclasses import dataclass
from urllib.parse import quote, urljoin, urlparse
from xml.etree import ElementTree as ET

import requests
from requests.auth import HTTPBasicAuth

from cloud_dog_storage.config.models import TlsConfig, WebDavConfig
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

_DEFAULT_MOVE_RETRY_STATUSES = {408, 409, 423, 425, 429, 500, 502, 503, 504}


def _join_url(base_url: str, rel_path: str) -> str:
    base = base_url.rstrip("/") + "/"
    rel = clean_posix(rel_path).lstrip("/")
    if not rel:
        return base.rstrip("/")
    parts = [quote(segment) for segment in rel.split("/")]
    return urljoin(base, "/".join(parts))


def _dav_ns(tag: str) -> str:
    return f"{{DAV:}}{tag}"


def _parse_retry_statuses(value: str) -> set[int]:
    cleaned = (value or "").strip()
    if not cleaned:
        return set(_DEFAULT_MOVE_RETRY_STATUSES)
    out: set[int] = set()
    for token in cleaned.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            status = int(token)
        except ValueError:
            continue
        if 100 <= status <= 599:
            out.add(status)
    return out or set(_DEFAULT_MOVE_RETRY_STATUSES)


@dataclass(frozen=True)
class DavItem:
    path: str
    is_dir: bool
    size: int | None = None


def parse_propfind_xml(body: bytes, *, base_url: str) -> list[DavItem]:
    """Parse WebDAV PROPFIND XML body into logical path items."""
    out: list[DavItem] = []
    root = ET.fromstring(body)
    for response in root.findall(_dav_ns("response")):
        href_el = response.find(_dav_ns("href"))
        if href_el is None or not href_el.text:
            continue

        href = href_el.text
        base_path = urlparse(base_url).path.rstrip("/")
        href_path = urlparse(href).path
        rel = href_path[len(base_path) :] if base_path and href_path.startswith(base_path) else href_path
        logical = clean_posix(rel)

        propstat = response.find(_dav_ns("propstat"))
        prop = propstat.find(_dav_ns("prop")) if propstat is not None else None
        is_dir = False
        size: int | None = None
        if prop is not None:
            rtype = prop.find(_dav_ns("resourcetype"))
            if rtype is not None and rtype.find(_dav_ns("collection")) is not None:
                is_dir = True
            clen = prop.find(_dav_ns("getcontentlength"))
            if clen is not None and clen.text:
                try:
                    size = int(clen.text.strip())
                except ValueError:
                    size = None

        out.append(DavItem(path=logical, is_dir=is_dir, size=size))

    return out


class WebDavStorage(StorageBackend):
    """WebDAV backend with configurable retry and move idempotency handling."""

    backend_name = "webdav"

    def __init__(self, config: WebDavConfig, *, tls: TlsConfig | None = None, timeout_s: int = 30) -> None:
        if not config.base_url:
            raise ConfigurationError("WebDAV storage requires webdav.base_url", backend_name=self.backend_name)

        self._base_url = config.base_url.rstrip("/")
        self._auth = HTTPBasicAuth(config.username or "", config.password or "")
        self._verify = build_requests_verify(tls or TlsConfig())
        self._timeout_s = float(timeout_s)
        self._move_retry_count = int(config.move_retry_count)
        self._move_retry_backoff_s = float(config.move_retry_backoff_s)
        self._move_probe_timeout_s = float(config.move_probe_timeout_s)
        self._move_retry_statuses = _parse_retry_statuses(config.move_retry_statuses)

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: bytes | None = None,
        timeout_s: float | None = None,
        stream: bool = False,
    ) -> requests.Response:
        try:
            return requests.request(
                method,
                url,
                headers=headers,
                data=data,
                auth=self._auth,
                verify=self._verify,
                timeout=(timeout_s if timeout_s is not None else self._timeout_s),
                stream=stream,
            )
        except requests.RequestException as exc:
            raise BackendConnectionError(f"WebDAV request failed: {exc}", backend_name=self.backend_name) from exc

    def _is_transient_status(self, status_code: int) -> bool:
        return status_code in self._move_retry_statuses

    def _path_exists(self, path: str) -> bool:
        url = _join_url(self._base_url, path)
        resp = self._request("PROPFIND", url, headers={"Depth": "0"}, timeout_s=self._move_probe_timeout_s)
        if resp.status_code == 404:
            return False
        return resp.status_code < 400

    def _move_already_applied(self, src: str, dst: str) -> bool:
        return (not self._path_exists(src)) and self._path_exists(dst)

    def read_bytes(self, path: str) -> bytes:
        resp = self._request("GET", _join_url(self._base_url, path))
        if resp.status_code == 404:
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        resp.raise_for_status()
        return resp.content

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        headers = {} if overwrite else {"If-None-Match": "*"}
        url = _join_url(self._base_url, path)
        for attempt in range(1, self._move_retry_count + 2):
            resp = self._request("PUT", url, headers=headers, data=data)
            if resp.status_code in {200, 201, 204}:
                return
            if resp.status_code == 412 and not overwrite:
                raise FileExistsError(clean_posix(path))
            if self._is_transient_status(resp.status_code) and attempt <= self._move_retry_count:
                time.sleep(self._move_retry_backoff_s * attempt)
                continue
            resp.raise_for_status()

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        resp = self._request("DELETE", _join_url(self._base_url, path))
        if resp.status_code == 404 and missing_ok:
            return
        if resp.status_code == 404:
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        resp.raise_for_status()

    def stat(self, path: str) -> StorageStat | None:
        resp = self._request("PROPFIND", _join_url(self._base_url, path), headers={"Depth": "0"})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        items = parse_propfind_xml(resp.content, base_url=self._base_url)
        if not items:
            return None
        item = items[0]
        return StorageStat(path=item.path, is_dir=item.is_dir, size=item.size)

    def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]:
        resp = self._request(
            "PROPFIND",
            _join_url(self._base_url, path),
            headers={"Depth": "infinity" if recursive else "1"},
        )
        if resp.status_code == 404:
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        resp.raise_for_status()
        items = parse_propfind_xml(resp.content, base_url=self._base_url)
        base = clean_posix(path)
        out = [StorageEntry(path=item.path, is_dir=item.is_dir) for item in items if clean_posix(item.path) != base]
        return out

    def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        target = clean_posix(path)
        parts = [part for part in target.split("/") if part]
        current = "/"
        for part in parts:
            current = clean_posix(posixpath.join(current, part))
            resp = self._request("MKCOL", _join_url(self._base_url, current))
            if resp.status_code in {200, 201, 204}:
                continue
            if resp.status_code in {405, 409}:
                if resp.status_code == 409 and not parents:
                    resp.raise_for_status()
                if exist_ok or resp.status_code == 405:
                    continue
            resp.raise_for_status()

    def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        headers = {
            "Destination": _join_url(self._base_url, dst),
            "Overwrite": "T" if overwrite else "F",
        }
        resp = self._request("COPY", _join_url(self._base_url, src), headers=headers)
        if resp.status_code == 412 and not overwrite:
            raise FileExistsError(clean_posix(dst))
        resp.raise_for_status()

    def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        headers = {
            "Destination": _join_url(self._base_url, dst),
            "Overwrite": "T" if overwrite else "F",
        }
        for attempt in range(1, self._move_retry_count + 2):
            try:
                resp = self._request("MOVE", _join_url(self._base_url, src), headers=headers)
                if resp.status_code in {200, 201, 204}:
                    return
                if resp.status_code == 412 and not overwrite:
                    raise FileExistsError(clean_posix(dst))
                if self._is_transient_status(resp.status_code):
                    if self._move_already_applied(src, dst):
                        return
                    if attempt <= self._move_retry_count:
                        time.sleep(self._move_retry_backoff_s * attempt)
                        continue
                resp.raise_for_status()
                return
            except requests.RequestException:
                if self._move_already_applied(src, dst):
                    return
                if attempt <= self._move_retry_count:
                    time.sleep(self._move_retry_backoff_s * attempt)
                    continue
                raise

    def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None:
        _ = path
        _ = mode
        _ = recursive
        raise NotSupportedError("chmod_path", backend=self.backend_name)

    def get_url(self, path: str) -> str:
        return _join_url(self._base_url, path)
