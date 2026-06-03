# platform-storage — Architecture

**Package:** `cloud_dog_storage`  
**Version:** 0.1.0 (pre-release)  
**Standard:** PS-85 (Storage Interfaces)  
**Status:** Draft  
**Last updated:** 2026-02-18

---

## OV1 — Overview

`cloud_dog_storage` is a drop-in Python library that implements the PS-85 Storage Interfaces standard. It provides a unified file/object storage abstraction with pluggable backends (local filesystem, S3-compatible, WebDAV, FTP/FTPS, Google Drive), consistent error handling, TLS configuration, path sanitisation, and observability — all behind stable, framework-agnostic interfaces.

### Design Goals

- **Pluggable backends**: Same API surface regardless of underlying storage system.
- **Single implementation**: Eliminate ~4,400 lines of duplicated storage code across file-mcp-server and notification-agent.
- **Progressive adoption**: Start with local filesystem, switch to S3/WebDAV/FTP/Google Drive via config change — zero code modification.
- **Framework-optional**: Core library has no web framework dependency; FastAPI integration is an optional module.
- **Sync + async**: Sync primary API with async wrapper for event-loop-based frameworks.

### Donor Codebases

| Source | Lines | Contribution |
|--------|------:|-------------|
| `file-mcp-server/src/file_tools/storage/` | 1,482 | Primary — cleanest abstraction, 5 backends, factory, config models |
| `notification-agent/src/core/storage/` | 2,967 | Async patterns, `StoredFile` model, error hierarchy, disk space checking |
| `expert-agent/src/core/multimedia/` | ~900 | Local-only patterns, MIME detection, metadata tracking |

---

## SA1 — Module Layout

```
cloud_dog_storage/
  __init__.py                        # Public API: StorageBackend, build_storage_backend, errors, models
  backends/
    __init__.py                      # Backend exports
    base.py                          # StorageBackend ABC + NotSupportedError
    local.py                         # LocalStorage — pathlib-based local filesystem
    s3.py                            # S3Storage — SigV4 pure-requests S3-compatible
    webdav.py                        # WebDavStorage — WebDAV over HTTP(S) with retry
    ftp.py                           # FtpStorage — FTP/FTPS with MLSD fallback
    google_drive.py                  # GoogleDriveStorage — Drive v3 REST API + OAuth2
  config/
    __init__.py                      # Config exports
    models.py                        # Pydantic: StorageConfig, S3Config, WebDavConfig, FtpConfig, GoogleDriveConfig, TlsConfig
  models.py                          # StorageEntry, StorageStat, StoredFile dataclasses
  errors.py                          # StorageError hierarchy: NotSupportedError, FileNotFoundError, PermissionError, QuotaExceededError, ConfigurationError, BackendConnectionError
  factory.py                         # build_storage_backend(config) → StorageBackend
  async_wrapper.py                   # AsyncStorageBackend — thread-pool wrapper for sync backends
  security/
    __init__.py                      # Security exports
    path_sanitiser.py                # Path traversal prevention, normalisation, root boundary enforcement
    tls.py                           # TLS/CA bundle configuration helpers
  observability/
    __init__.py                      # Observability exports
    logging.py                       # cloud_dog_logging integration with stdlib fallback
  api/
    __init__.py                      # API integration exports
    fastapi/
      __init__.py                    # FastAPI exports
      deps.py                        # Depends(get_storage_backend) — DI helper
  testing/
    __init__.py                      # Testing exports
    conformance.py                   # Reusable conformance test suite for any StorageBackend
    fixtures.py                      # Shared test fixtures (temp dirs, config builders)
    mock_backend.py                  # In-memory MockStorageBackend for consumer tests
```

**Total modules: 26** (including `__init__.py` files)

---

## SA2 — Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     Service (FastAPI / CLI / MCP)                  │
│                                                                    │
│  api/fastapi/deps.py ──→ get_storage_backend                      │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              factory.py                                   │      │
│  │  build_storage_backend(config) → StorageBackend           │      │
│  │         │                                                 │      │
│  │         ├──→ local.py ──→ pathlib.Path / os               │      │
│  │         ├──→ s3.py ──→ S3 endpoint (SigV4 + requests)     │      │
│  │         ├──→ webdav.py ──→ WebDAV server (HTTP)           │      │
│  │         ├──→ ftp.py ──→ FTP/FTPS server (ftplib)          │      │
│  │         └──→ google_drive.py ──→ Drive v3 API (OAuth2)    │      │
│  └─────────────────────────────────────────────────────────┘      │
│         │ StorageBackend interface                                  │
│         ▼                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │ security/     │    │ observability│    │ config/      │         │
│  │ path_sanit.   │    │ logging.py   │    │ models.py    │         │
│  │ tls.py        │    │              │    │              │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│         │                   │                   │                   │
│         └─────────┬─────────┘                   │                   │
│                   ▼                             │                   │
│           ┌──────────────┐              ┌──────┘                   │
│           │ models.py    │              │                           │
│           │ StorageEntry │              │ cloud_dog_config (opt.)   │
│           │ StorageStat  │              │   bind_model() populates  │
│           │ StoredFile   │              │   StorageConfig with      │
│           └──────────────┘              │   pre-resolved creds      │
│                                         │ cloud_dog_logging (opt.)  │
│                                         └───────────────────────────│
│                                                                    │
│  ┌────────────────────────────────────────┐                        │
│  │ async_wrapper.py                        │                        │
│  │ AsyncStorageBackend(backend) → async    │                        │
│  │ Wraps sync backend in thread pool       │                        │
│  └────────────────────────────────────────┘                        │
└────────────────────────────────────────────────────────────────────┘
```

---

## CC1 — Core Components

### CC1.1 Storage Backend Interface (`backends/base.py`)

```python
class StorageBackend:
    """
    Minimal file-like API over a backing store.

    Paths are POSIX-style absolute paths (e.g. `/docs/readme.md`) within the
    backend's configured root/prefix. Scope enforcement happens separately.
    """

    backend_name: str = "unknown"

    def read_bytes(self, path: str) -> bytes: ...
    def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None: ...
    def delete_path(self, path: str, *, missing_ok: bool = False) -> None: ...
    def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]: ...
    def stat(self, path: str) -> StorageStat | None: ...
    def exists(self, path: str) -> bool: ...
    def create_dir(self, path: str, *, parents: bool = True, exist_ok: bool = True) -> None: ...
    def copy_path(self, src: str, dst: str, *, overwrite: bool = False) -> None: ...
    def move_path(self, src: str, dst: str, *, overwrite: bool = False) -> None: ...
    def rename_path(self, src: str, dst: str, *, overwrite: bool = False) -> None: ...
    def chmod_path(self, path: str, mode: int, *, recursive: bool = False) -> None: ...
    def iter_paths(self, roots: Iterable[str], *, max_depth: int | None = None) -> Iterable[str]: ...
    def get_url(self, path: str) -> str: ...
```

Default implementations:
- `exists` → delegates to `stat() is not None`.
- `rename_path` → delegates to `move_path`.
- `iter_paths` → recursive `list_dir` + yield non-dir entries.
- `get_url` → raises `NotSupportedError` (overridden by backends that support URLs).
- `create_dir`, `copy_path`, `move_path`, `chmod_path` → raise `NotSupportedError` unless overridden.

### CC1.2 Local Filesystem Backend (`backends/local.py`)

```python
class LocalStorage(StorageBackend):
    backend_name = "local"

    def __init__(self, root_path: str | Path = "") -> None: ...
```

- All operations via `pathlib.Path`.
- Root boundary enforcement: every resolved path checked against `root_path`.
- Full support for all operations including `chmod_path`.
- Disk space checking via `shutil.disk_usage`.
- Subdirectory pattern support for automatic file organisation.

### CC1.3 S3-Compatible Backend (`backends/s3.py`)

```python
class S3Storage(StorageBackend):
    backend_name = "s3"

    def __init__(self, config: S3Config, *, tls: TlsConfig | None = None, timeout_s: int = 30) -> None: ...
```

- AWS SigV4 signing (pure Python: `hashlib.sha256` + `hmac`).
- No `boto3` dependency — uses `requests` for HTTP.
- Path-style addressing: `{endpoint}/{bucket}/{key}`.
- Key mapping: POSIX path → S3 key with configurable prefix.
- ListObjectsV2 for `list_dir` with prefix/delimiter emulation.
- Server-side copy via `x-amz-copy-source` header.

### CC1.4 WebDAV Backend (`backends/webdav.py`)

```python
class WebDavStorage(StorageBackend):
    backend_name = "webdav"

    def __init__(self, config: WebDavConfig, *, tls: TlsConfig | None = None, timeout_s: int = 30) -> None: ...
```

- PROPFIND XML parsing for directory listings.
- Retry logic with configurable status codes and exponential backoff.
- MKCOL for directory creation (parent chain if `parents=True`).
- COPY/MOVE with `Destination` header and `Overwrite` flag.
- Move idempotency detection.

### CC1.5 FTP/FTPS Backend (`backends/ftp.py`)

```python
class FtpStorage(StorageBackend):
    backend_name = "ftp"

    def __init__(self, config: FtpConfig, *, tls: TlsConfig | None = None, timeout_s: int = 30) -> None: ...
```

- Connection-per-operation for thread safety.
- MLSD with NLST fallback for directory listing.
- SSL context for FTPS with configurable verification.
- Client-side copy (read + write) since FTP has no server-side copy.

### CC1.6 Google Drive Backend (`backends/google_drive.py`)

```python
class GoogleDriveStorage(StorageBackend):
    backend_name = "google_drive"

    def __init__(self, config: GoogleDriveConfig, *, tls: TlsConfig | None = None, timeout_s: int = 30) -> None: ...
```

- OAuth2 token refresh with configurable token URI.
- Path resolution: hierarchical folder-ID lookup with child-name queries.
- Multipart upload (metadata JSON + file content).
- Shared/team drive support.
- Folder ID extraction from URL.

### CC1.7 Storage Factory (`factory.py`)

```python
def build_storage_backend(config: StorageConfig) -> StorageBackend:
    """Create backend from config. Lazy-imports optional dependencies."""
```

Dispatch map:
- `local`, `filesystem`, `fs`, `""` → `LocalStorage`
- `s3` → `S3Storage`
- `webdav` → `WebDavStorage`
- `ftp` → `FtpStorage`
- `google_drive`, `gdrive`, `drive` → `GoogleDriveStorage`

Lazy imports ensure unused backends don't require their dependencies.

### CC1.8 Async Wrapper (`async_wrapper.py`)

```python
class AsyncStorageBackend:
    """Wraps a sync StorageBackend, running operations in a thread pool."""

    def __init__(self, backend: StorageBackend) -> None: ...

    async def read_bytes(self, path: str) -> bytes: ...
    async def write_bytes(self, path: str, data: bytes, *, overwrite: bool = True) -> None: ...
    async def delete_path(self, path: str, *, missing_ok: bool = False) -> None: ...
    async def list_dir(self, path: str, *, recursive: bool = False) -> list[StorageEntry]: ...
    async def stat(self, path: str) -> StorageStat | None: ...
    async def exists(self, path: str) -> bool: ...
    async def store_file(self, content: bytes, filename: str, content_type: str, metadata: dict | None = None) -> StoredFile: ...
    async def get_file_content(self, path: str) -> bytes: ...
    async def delete_file(self, path: str) -> bool: ...
    async def file_exists(self, path: str) -> bool: ...
    async def get_file_url(self, path: str) -> str: ...
```

Uses `asyncio.to_thread` (Python 3.9+) or `loop.run_in_executor` for thread-pool delegation.

Also provides the high-level `store_file` / `get_file_content` / `delete_file` / `file_exists` / `get_file_url` interface matching notification-agent's `StorageBackend` ABC, for backward compatibility.

### CC1.9 Path Sanitiser (`security/path_sanitiser.py`)

```python
def clean_posix(path: str) -> str:
    """Normalise to POSIX absolute path; remove traversal and null bytes."""

def validate_within_root(path: str, root: str) -> str:
    """Resolve path and verify it stays within root. Raises StoragePermissionError."""

def url_encode_path(path: str) -> str:
    """URL-encode path components for remote backends."""
```

### CC1.10 Configuration Models (`config/models.py`)

```python
class TlsConfig(BaseModel):
    insecure_skip_verify: bool = False
    ca_bundle_path: str = ""

class S3Config(BaseModel):
    endpoint: str = ""
    bucket: str = ""
    region: str = "us-east-1"
    access_key: str = ""
    secret_key: str = ""
    prefix: str = ""

class WebDavConfig(BaseModel):
    base_url: str = ""
    username: str = ""
    password: str = ""
    move_retry_count: int = 2
    move_retry_backoff_s: float = 0.35
    move_probe_timeout_s: float = 5.0
    move_retry_statuses: str = "408,409,423,425,429,500,502,503,504"

class FtpConfig(BaseModel):
    host: str = ""
    port: int = 21
    username: str = ""
    password: str = ""
    base_dir: str = "/"
    use_tls: bool = False

class GoogleDriveConfig(BaseModel):
    folder_id: str = ""
    folder_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    refresh_token: str = ""
    access_token: str = ""
    redirect_uri: str = ""
    token_uri: str = "https://oauth2.googleapis.com/token"

class StorageConfig(BaseModel):
    backend: str = "local"
    root_path: str = ""
    timeout_s: int = 30
    tls: TlsConfig = Field(default_factory=TlsConfig)
    s3: S3Config = Field(default_factory=S3Config)
    webdav: WebDavConfig = Field(default_factory=WebDavConfig)
    ftp: FtpConfig = Field(default_factory=FtpConfig)
    google_drive: GoogleDriveConfig = Field(default_factory=GoogleDriveConfig)
```

### CC1.11 Error Hierarchy (`errors.py`)

```python
class StorageError(Exception):
    """Base class for all storage errors."""

class NotSupportedError(StorageError):
    def __init__(self, operation: str, *, backend: str) -> None: ...

class StorageFileNotFoundError(StorageError):
    def __init__(self, path: str, *, backend: str = "") -> None: ...

class StoragePermissionError(StorageError):
    def __init__(self, path: str, *, backend: str = "") -> None: ...

class QuotaExceededError(StorageError): ...

class ConfigurationError(StorageError): ...

class BackendConnectionError(StorageError): ...
```

### CC1.12 FastAPI Integration (`api/fastapi/deps.py`)

```python
from cloud_dog_storage import build_storage_backend, StorageConfig

def get_storage_backend(request: Request) -> StorageBackend:
    """FastAPI Depends() helper. Reads config from app.state.storage_config."""
```

Optional module — no FastAPI import at package top level.

### CC1.13 Testing Infrastructure (`testing/`)

```python
# conformance.py
def run_conformance_suite(backend: StorageBackend, *, skip_unsupported: bool = True) -> list[ConformanceResult]:
    """Run full conformance test suite against any backend."""

# mock_backend.py
class MockStorageBackend(StorageBackend):
    """In-memory backend for consumer project unit tests."""
    backend_name = "mock"

# fixtures.py
def temp_storage_config(tmp_path: Path) -> StorageConfig:
    """Create a local storage config pointing to a temp directory."""
```

---

## DP1 — Dependency Policy

| Dependency | Status | Notes |
|-----------|--------|-------|
| `pydantic` | Required | Config models |
| `requests` | Optional | S3, WebDAV, Google Drive backends |
| `cloud_dog_config` | Optional | Config loading + `bind_model()` for pre-resolved credentials (PS-80). This package MUST NOT import `hvac` or resolve Vault secrets itself. |
| `cloud_dog_logging` | Optional | Structured logging |
| `fastapi` | Optional | FastAPI dependency injection |

All optional dependencies are lazy-imported. The package degrades gracefully when they are absent.

---

## SE1 — Security Architecture

- **Path sanitisation**: All paths normalised and checked for traversal before use.
- **Root boundary**: Local backend validates resolved paths stay within root.
- **TLS**: All remote backends use verified TLS by default; insecure mode for dev only.
- **Credentials**: Never logged, never in error messages, never hardcoded.
- **S3 signing**: AWS SigV4 with proper credential scoping and request hashing.
- **OAuth2**: Google Drive tokens refreshed automatically; expired tokens never reused.
- **Disk space**: Local backend checks free space before writes.

---

## Integration Pattern

Services consume the package as follows:

```python
from cloud_dog_storage import build_storage_backend
from cloud_dog_config import get_config, bind_model
from cloud_dog_storage.config.models import StorageConfig

# From cloud_dog_config (PS-80) — credentials pre-resolved via ${vault.storage.*}
config = bind_model(get_config(), "storage", StorageConfig)

# Create backend
storage = build_storage_backend(config)

# Use
data = storage.read_bytes("/reports/2026/q1.pdf")
storage.write_bytes("/exports/report.csv", csv_data)
entries = storage.list_dir("/uploads", recursive=True)

# Async usage
from cloud_dog_storage import AsyncStorageBackend
async_storage = AsyncStorageBackend(storage)
data = await async_storage.read_bytes("/reports/2026/q1.pdf")
```

### FastAPI Integration

```python
from cloud_dog_storage.api.fastapi import get_storage_backend

@app.get("/files/{path:path}")
async def read_file(path: str, storage=Depends(get_storage_backend)):
    try:
        data = storage.read_bytes(f"/{path}")
        return Response(content=data)
    except StorageFileNotFoundError:
        raise HTTPException(404, "File not found")
```

### Migration from file-mcp-server

```python
# Before (project-local):
from file_tools.storage import build_storage_backend
from file_tools.config.models import ProfileConfig

storage = build_storage_backend(profile)

# After (package):
from cloud_dog_storage import build_storage_backend
from cloud_dog_config import get_config, bind_model
from cloud_dog_storage.config.models import StorageConfig

config = bind_model(get_config(), "storage", StorageConfig)
storage = build_storage_backend(config)
# Same StorageBackend interface — minimal code changes
```

### Migration from notification-agent

```python
# Before (project-local):
from core.storage.factory import StorageFactory
backend = StorageFactory.create(channel_config)
stored_file = await backend.store_file(content, filename, content_type)

# After (package):
from cloud_dog_storage import build_storage_backend, AsyncStorageBackend
from cloud_dog_config import get_config, bind_model
from cloud_dog_storage.config.models import StorageConfig

config = bind_model(get_config(), "storage", StorageConfig)
backend = AsyncStorageBackend(build_storage_backend(config))
stored_file = await backend.store_file(content, filename, content_type)
```
