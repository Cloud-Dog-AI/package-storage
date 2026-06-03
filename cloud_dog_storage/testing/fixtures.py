"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Shared helper fixtures for storage test configuration.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cloud_dog_storage.config.models import (
    FtpConfig,
    S3Config,
    StorageConfig,
    TlsConfig,
    WebDavConfig,
)

if TYPE_CHECKING:
    from pathlib import Path


def temp_storage_config(tmp_path: Path) -> StorageConfig:
    """Create local storage config for temporary directory tests."""
    return StorageConfig(backend="local", root_path=str(tmp_path))


def s3_storage_config(
    endpoint: str,
    bucket: str,
    access_key: str,
    secret_key: str,
    *,
    region: str = "us-east-1",
    prefix: str = "",
    timeout_s: int = 30,
    tls: TlsConfig | None = None,
) -> StorageConfig:
    """Create StorageConfig for S3-compatible backends."""
    return StorageConfig(
        backend="s3",
        timeout_s=timeout_s,
        tls=tls or TlsConfig(),
        s3=S3Config(
            endpoint=endpoint,
            bucket=bucket,
            region=region,
            access_key=access_key,
            secret_key=secret_key,
            prefix=prefix,
        ),
    )


def webdav_storage_config(
    base_url: str,
    username: str,
    password: str,
    *,
    timeout_s: int = 30,
    tls: TlsConfig | None = None,
    move_retry_count: int = 2,
    move_retry_backoff_s: float = 0.35,
    move_probe_timeout_s: float = 5.0,
    move_retry_statuses: str = "408,409,423,425,429,500,502,503,504",
) -> StorageConfig:
    """Create StorageConfig for WebDAV backends."""
    return StorageConfig(
        backend="webdav",
        timeout_s=timeout_s,
        tls=tls or TlsConfig(),
        webdav=WebDavConfig(
            base_url=base_url,
            username=username,
            password=password,
            move_retry_count=move_retry_count,
            move_retry_backoff_s=move_retry_backoff_s,
            move_probe_timeout_s=move_probe_timeout_s,
            move_retry_statuses=move_retry_statuses,
        ),
    )


def ftp_storage_config(
    host: str,
    username: str,
    password: str,
    *,
    port: int = 21,
    base_dir: str = "/",
    use_tls: bool = False,
    timeout_s: int = 30,
    tls: TlsConfig | None = None,
) -> StorageConfig:
    """Create StorageConfig for FTP/FTPS backends."""
    return StorageConfig(
        backend="ftp",
        timeout_s=timeout_s,
        tls=tls or TlsConfig(),
        ftp=FtpConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            base_dir=base_dir,
            use_tls=use_tls,
        ),
    )
