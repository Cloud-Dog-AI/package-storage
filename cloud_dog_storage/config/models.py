"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Pydantic models for storage backend configuration.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TlsConfig(BaseModel):
    """TLS options shared by remote backends."""

    insecure_skip_verify: bool = False
    ca_bundle_path: str = ""


class LocalConfig(BaseModel):
    """Local filesystem backend options."""

    min_free_bytes: int = 100 * 1024 * 1024
    file_permissions: str = "0644"
    dir_permissions: str = "0755"
    subdir_pattern: str = ""


class S3Config(BaseModel):
    """S3-compatible backend options."""

    endpoint: str = ""
    bucket: str = ""
    region: str = "us-east-1"
    access_key: str = ""
    secret_key: str = ""
    prefix: str = ""


class WebDavConfig(BaseModel):
    """WebDAV backend options."""

    base_url: str = ""
    username: str = ""
    password: str = ""
    move_retry_count: int = 2
    move_retry_backoff_s: float = 0.35
    move_probe_timeout_s: float = 5.0
    move_retry_statuses: str = "408,409,423,425,429,500,502,503,504"


class FtpConfig(BaseModel):
    """FTP/FTPS backend options."""

    host: str = ""
    port: int = 21
    username: str = ""
    password: str = ""
    base_dir: str = "/"
    use_tls: bool = False


class GoogleDriveConfig(BaseModel):
    """Google Drive backend options."""

    folder_id: str = ""
    folder_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    refresh_token: str = ""
    access_token: str = ""
    redirect_uri: str = ""
    token_uri: str = "https://oauth2.googleapis.com/token"


class StorageConfig(BaseModel):
    """Top-level storage configuration object."""

    backend: str = "local"
    root_path: str = ""
    timeout_s: int = 30
    tls: TlsConfig = Field(default_factory=TlsConfig)
    local: LocalConfig = Field(default_factory=LocalConfig)
    s3: S3Config = Field(default_factory=S3Config)
    webdav: WebDavConfig = Field(default_factory=WebDavConfig)
    ftp: FtpConfig = Field(default_factory=FtpConfig)
    google_drive: GoogleDriveConfig = Field(default_factory=GoogleDriveConfig)
