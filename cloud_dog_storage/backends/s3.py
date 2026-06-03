"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: S3-compatible backend using AWS SigV4 over requests.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import quote, urljoin, urlparse
from xml.etree import ElementTree as ET

import requests

from cloud_dog_storage.config.models import S3Config, TlsConfig
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


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _aws_v4_signing_key(secret_key: str, date_yyyymmdd: str, region: str, service: str) -> bytes:
    k_date = _hmac(("AWS4" + secret_key).encode("utf-8"), date_yyyymmdd)
    k_region = _hmac(k_date, region)
    k_service = _hmac(k_region, service)
    return _hmac(k_service, "aws4_request")


def _canonical_query(params: dict[str, str]) -> str:
    items = sorted((quote(k, safe="-_.~"), quote(v, safe="-_.~")) for k, v in params.items())
    return "&".join(f"{k}={v}" for k, v in items)


def _canonical_headers(headers: dict[str, str]) -> tuple[str, str]:
    normalised = {key.strip().lower(): " ".join(value.strip().split()) for key, value in headers.items()}
    keys = sorted(normalised.keys())
    canonical = "".join(f"{key}:{normalised[key]}\n" for key in keys)
    signed = ";".join(keys)
    return canonical, signed


class S3Storage(StorageBackend):
    """S3-compatible backend using SigV4 signing."""

    backend_name = "s3"

    def __init__(self, config: S3Config, *, tls: TlsConfig | None = None, timeout_s: int = 30) -> None:
        if not config.endpoint:
            raise ConfigurationError("S3 storage requires s3.endpoint", backend_name=self.backend_name)
        if not config.bucket:
            raise ConfigurationError("S3 storage requires s3.bucket", backend_name=self.backend_name)
        if not config.access_key or not config.secret_key:
            raise ConfigurationError(
                "S3 storage requires s3.access_key and s3.secret_key",
                backend_name=self.backend_name,
            )

        self._endpoint = config.endpoint.rstrip("/")
        self._bucket = config.bucket
        self._region = (config.region or "us-east-1").strip() or "us-east-1"
        self._access_key = config.access_key
        self._secret_key = config.secret_key
        self._prefix = clean_posix(config.prefix or "/").lstrip("/")
        self._verify = build_requests_verify(tls or TlsConfig())
        self._timeout_s = int(timeout_s)

    def _key(self, path: str) -> str:
        rel = clean_posix(path).lstrip("/")
        if self._prefix:
            if rel:
                return f"{self._prefix.rstrip('/')}/{rel}"
            return self._prefix.rstrip("/")
        return rel

    def _object_url(self, key: str) -> str:
        base = f"{self._endpoint.rstrip('/')}/"
        safe_key = "/".join(quote(segment) for segment in key.split("/")) if key else ""
        return urljoin(base, f"{quote(self._bucket)}/{safe_key}")

    def _sign_request(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        payload: bytes = b"",
    ) -> dict[str, str]:
        parsed = urlparse(url)
        host = parsed.netloc
        canonical_uri = quote(parsed.path or "/", safe="/-_.~")
        canonical_query = _canonical_query(params or {})

        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        hdrs = {
            "host": host,
            "x-amz-date": amz_date,
            "x-amz-content-sha256": _sha256_hex(payload),
        }
        if headers:
            for key, value in headers.items():
                hdrs[key.lower()] = value

        canonical_headers, signed_headers = _canonical_headers(hdrs)
        canonical_request = (
            f"{method}\n"
            f"{canonical_uri}\n"
            f"{canonical_query}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{hdrs['x-amz-content-sha256']}"
        )

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self._region}/s3/aws4_request"
        string_to_sign = (
            f"{algorithm}\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        signing_key = _aws_v4_signing_key(self._secret_key, date_stamp, self._region, "s3")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        authorization = (
            f"{algorithm} "
            f"Credential={self._access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        out = dict(hdrs)
        out["Authorization"] = authorization
        return out

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        data: bytes = b"",
    ) -> requests.Response:
        signed_headers = self._sign_request(method=method, url=url, params=params, headers=headers, payload=data)
        try:
            return requests.request(
                method,
                url,
                params=params,
                headers=signed_headers,
                data=data,
                verify=self._verify,
                timeout=self._timeout_s,
            )
        except requests.RequestException as exc:
            raise BackendConnectionError(
                f"S3 request failed: {exc}",
                backend_name=self.backend_name,
            ) from exc

    def read_bytes(self, path: str) -> bytes:
        key = self._key(path)
        resp = self._request("GET", self._object_url(key))
        if resp.status_code == 404:
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        resp.raise_for_status()
        return resp.content

    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None:
        headers = {} if overwrite else {"If-None-Match": "*"}
        resp = self._request("PUT", self._object_url(self._key(path)), headers=headers, data=data)
        if resp.status_code == 412 and not overwrite:
            raise FileExistsError(clean_posix(path))
        resp.raise_for_status()

    def delete_path(self, path: str, *, missing_ok: bool = False) -> None:
        resp = self._request("DELETE", self._object_url(self._key(path)))
        if resp.status_code == 404 and missing_ok:
            return
        if resp.status_code == 404:
            raise StorageFileNotFoundError(clean_posix(path), backend=self.backend_name)
        resp.raise_for_status()

    def stat(self, path: str) -> StorageStat | None:
        resp = self._request("HEAD", self._object_url(self._key(path)))
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        size_text = resp.headers.get("Content-Length")
        try:
            size = int(size_text) if size_text is not None else None
        except ValueError:
            size = None
        return StorageStat(path=clean_posix(path), is_dir=False, size=size)

    def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]:
        prefix = self._key(path).rstrip("/")
        if prefix:
            prefix += "/"

        params: dict[str, str] = {"list-type": "2", "prefix": prefix}
        if not recursive:
            params["delimiter"] = "/"

        url = f"{self._endpoint.rstrip('/')}/{quote(self._bucket)}"
        resp = self._request("GET", url, params=params)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        entries: list[StorageEntry] = []
        for cp in root.findall(".//{*}CommonPrefixes/{*}Prefix"):
            pfx = cp.text or ""
            logical = "/" + pfx
            if self._prefix and logical.startswith("/" + self._prefix):
                logical = logical[len("/" + self._prefix) :]
            entries.append(StorageEntry(path=clean_posix(logical), is_dir=True))

        for obj in root.findall(".//{*}Contents"):
            key_el = obj.find("{*}Key")
            if key_el is None or not key_el.text:
                continue
            key = key_el.text
            if key.endswith("/") and not recursive:
                continue
            logical = "/" + key
            if self._prefix and logical.startswith("/" + self._prefix):
                logical = logical[len("/" + self._prefix) :]
            logical = clean_posix(logical)
            if logical == clean_posix(path):
                continue
            entries.append(StorageEntry(path=logical, is_dir=False))

        return entries

    def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        src_key = self._key(src)
        dst_key = self._key(dst)
        headers = {"x-amz-copy-source": f"/{self._bucket}/{src_key}"}
        if not overwrite:
            headers["x-amz-copy-source-if-none-match"] = "*"
        resp = self._request("PUT", self._object_url(dst_key), headers=headers)
        if resp.status_code == 412 and not overwrite:
            raise FileExistsError(clean_posix(dst))
        resp.raise_for_status()

    def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None:
        self.copy_path(src, dst, overwrite=overwrite)
        self.delete_path(src, missing_ok=False)

    def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
        _ = path
        _ = parents
        _ = exist_ok
        raise NotSupportedError("create_dir", backend=self.backend_name)

    def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None:
        _ = path
        _ = mode
        _ = recursive
        raise NotSupportedError("chmod_path", backend=self.backend_name)

    def get_url(self, path: str) -> str:
        return self._object_url(self._key(path))
