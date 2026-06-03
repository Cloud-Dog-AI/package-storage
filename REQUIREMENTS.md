# platform-storage — Requirements

**Package:** `cloud_dog_storage`  
**Version:** 0.1.0 (pre-release)  
**Standard:** PS-85 (Storage Interfaces)  
**Status:** Draft  
**Last updated:** 2026-02-18

---

## Scope / Vision

### SV1.1
The package SHALL provide a single, reusable file/object storage library for all Cloud-Dog Python services, implementing PS-85.

### SV1.2
The package SHALL support pluggable storage backends (local filesystem, S3-compatible, WebDAV, FTP/FTPS, Google Drive), unified POSIX-style path addressing, consistent error handling, TLS configuration, and full observability — all behind stable interfaces.

### SV1.3
The package SHALL work with common Python web stacks (FastAPI recommended) but MUST NOT be coupled to a single framework. Both sync and async usage patterns MUST be supported.

### SV1.4
The package SHALL be compatible with existing storage implementations in file-mcp-server and notification-agent-mcp-server, providing a clean migration path that eliminates ~4,400 lines of duplicated storage code.

---

## Business Objectives

### BO1.1
Eliminate per-project reimplementation of file/object storage — centralise backend adapters, config models, error handling, security controls, and test infrastructure.

### BO1.2
Enable consistent storage behaviour across all services — same path model, same error taxonomy, same TLS handling, same credential management.

### BO1.3
Support progressive adoption: services can start with local filesystem and add S3/WebDAV/FTP/Google Drive backends via config change with zero code modification.

---

## Functional Requirements

### FR1.1 — Storage Backend Interface
The package MUST define an abstract `StorageBackend` interface:
- `read_bytes(path: str) -> bytes`
- `write_bytes(path: str, data: bytes, *, overwrite: bool = True) -> None`
- `delete_path(path: str, *, missing_ok: bool = False) -> None`
- `list_dir(path: str, *, recursive: bool = False) -> list[StorageEntry]`
- `stat(path: str) -> StorageStat | None`
- `exists(path: str) -> bool`
- `create_dir(path: str, *, parents: bool = True, exist_ok: bool = True) -> None`
- `copy_path(src: str, dst: str, *, overwrite: bool = False) -> None`
- `move_path(src: str, dst: str, *, overwrite: bool = False) -> None`
- `rename_path(src: str, dst: str, *, overwrite: bool = False) -> None` (delegates to `move_path`)
- `chmod_path(path: str, mode: int, *, recursive: bool = False) -> None`
- `iter_paths(roots: Iterable[str], *, max_depth: int | None = None) -> Iterable[str]`
- `get_url(path: str) -> str`

Operations not supported by a specific backend MUST raise `NotSupportedError`.

### FR1.2 — POSIX Path Model
All paths MUST use POSIX-style absolute paths (e.g., `/docs/readme.md`) relative to the backend's configured root/prefix:
- Leading `/` is always present.
- Path normalisation via `posixpath.normpath`.
- No `..` traversal allowed after normalisation.
- Backend-specific addressing (S3 keys, WebDAV URLs, FTP remote paths, Drive folder IDs) is handled internally.

### FR1.3 — Local Filesystem Backend
The package MUST provide a `LocalStorage` backend:
- Direct `pathlib.Path` operations.
- Full operation support: `read_bytes`, `write_bytes`, `delete_path`, `list_dir`, `stat`, `exists`, `create_dir`, `copy_path`, `move_path`, `chmod_path`.
- Configurable root directory. Resolved paths MUST be validated to stay within root (path traversal prevention).
- Disk space checking before large writes (configurable threshold).
- Subdirectory pattern support (e.g., `{year}/{month}/{day}`) for automatic file organisation.
- File permission management with configurable defaults.

### FR1.4 — S3-Compatible Backend
The package MUST provide an `S3Storage` backend:
- AWS SigV4 authentication using pure `requests` + `hashlib` (no mandatory `boto3` dependency).
- Path-style bucket addressing: `{endpoint}/{bucket}/{key}`.
- Operations: `read_bytes` (GET), `write_bytes` (PUT), `delete_path` (DELETE), `stat` (HEAD), `list_dir` (ListObjectsV2 with prefix/delimiter), `copy_path` (server-side copy via `x-amz-copy-source`), `move_path` (copy + delete).
- `create_dir` MUST raise `NotSupportedError`.
- `chmod_path` MUST raise `NotSupportedError`.
- Configurable: endpoint, bucket, region, access_key, secret_key, prefix, TLS.
- Support for S3-compatible providers: AWS S3, MinIO, Wasabi, DigitalOcean Spaces, Backblaze B2.

### FR1.5 — WebDAV Backend
The package MUST provide a `WebDavStorage` backend:
- HTTP methods: GET, PUT, DELETE, PROPFIND, MKCOL, COPY, MOVE.
- PROPFIND XML parsing for directory listings and metadata extraction.
- Retry logic for transient failures with configurable:
  - `move_retry_count` (default: 2)
  - `move_retry_backoff_s` (default: 0.35)
  - `move_probe_timeout_s` (default: 5.0)
  - `move_retry_statuses` (default: 408, 409, 423, 425, 429, 500, 502, 503, 504)
- Move idempotency detection: source gone + destination present = success.
- Basic auth with configurable TLS/CA bundle.
- `chmod_path` MUST raise `NotSupportedError`.

### FR1.6 — FTP/FTPS Backend
The package MUST provide an `FtpStorage` backend:
- `ftplib.FTP` / `FTP_TLS` with configurable SSL context.
- MLSD for directory listing with NLST fallback for servers without MLSD support.
- Connection-per-operation pattern (connect, operate, quit) for thread safety.
- Operations: `read_bytes` (RETR), `write_bytes` (STOR), `delete_path` (DELE/RMD), `stat` (SIZE + CWD probe), `list_dir` (MLSD/NLST), `create_dir` (MKD chain), `copy_path` (client-side: read + write), `move_path` (RNFR/RNTO).
- Configurable: host, port, username, password, base_dir, use_tls, timeout.
- `chmod_path` MUST raise `NotSupportedError`.

### FR1.7 — Google Drive Backend
The package MUST provide a `GoogleDriveStorage` backend:
- Google Drive v3 REST API via `requests`.
- OAuth2 refresh token flow with automatic token refresh and configurable token URI.
- Path-to-folder-ID resolution: traverse folder hierarchy by name, caching folder IDs.
- Multipart upload for file creation and update.
- Folder creation via `application/vnd.google-apps.folder` MIME type.
- MIME type detection from file extension.
- Shared/team drive support (`supportsAllDrives`, `includeItemsFromAllDrives`).
- Folder ID extraction from folder URL (e.g., `/drive/folders/<id>`).
- `chmod_path` MUST raise `NotSupportedError`.

### FR1.8 — Storage Factory
The package MUST provide a factory function:
```python
def build_storage_backend(config: StorageConfig) -> StorageBackend:
```
- Dispatch based on `config.backend` string: `local`, `filesystem`, `fs`, `s3`, `webdav`, `ftp`, `google_drive`, `gdrive`, `drive`.
- Lazy imports for optional backend dependencies (`requests` for S3/WebDAV/Google Drive).
- Raise `ValueError` for unknown backend types.

### FR1.9 — Configuration Models
The package MUST define Pydantic `BaseModel` configuration classes:
- `StorageConfig` — top-level with `backend`, `root_path`, `tls`, and per-backend sub-models.
- `TlsConfig` — `insecure_skip_verify`, `ca_bundle_path`.
- `S3Config` — `endpoint`, `bucket`, `region`, `access_key`, `secret_key`, `prefix`.
- `WebDavConfig` — `base_url`, `username`, `password`, retry settings.
- `FtpConfig` — `host`, `port`, `username`, `password`, `base_dir`, `use_tls`.
- `GoogleDriveConfig` — `folder_id`, `folder_url`, `client_id`, `client_secret`, `refresh_token`, `access_token`, `redirect_uri`, `token_uri`.
- All credential fields MUST support Vault substitution via `cloud_dog_config` (PS-80).

### FR1.10 — Data Models
The package MUST define:
- `StorageEntry(path: str, is_dir: bool)` — frozen dataclass for directory listing results.
- `StorageStat(path: str, is_dir: bool, size: int | None)` — frozen dataclass for file metadata.
- `StoredFile(path: str, format: str, size_bytes: int, backend_name: str, stored_at: datetime, metadata: dict)` — high-level result model with `to_dict()` serialisation.

### FR1.11 — Error Taxonomy
The package MUST define a consistent error hierarchy:
- `StorageError` — base class.
- `NotSupportedError(operation, backend)` — unsupported operation.
- `StorageFileNotFoundError(path)` — file/path does not exist.
- `StoragePermissionError(path)` — insufficient permissions.
- `QuotaExceededError` — disk space or quota exhausted.
- `ConfigurationError` — invalid or missing backend configuration.
- `BackendConnectionError` — cannot connect to remote backend.
All errors MUST include `backend_name` and `path` where applicable.

### FR1.12 — Path Sanitisation
The package MUST provide a path sanitisation module:
- Remove `..` references after normalisation.
- Remove null bytes.
- Normalise double slashes.
- Local backend: verify resolved path stays within configured root.
- Remote backends: URL-encode path components where required.

### FR1.13 — TLS Configuration
All remote backends MUST support configurable TLS:
- `insecure_skip_verify: bool` — disable certificate verification (development only).
- `ca_bundle_path: str` — custom CA bundle file path.
- Default: verify certificates using system CA store.
- Applied consistently across S3, WebDAV, FTP/FTPS, Google Drive backends.

### FR1.14 — Async Wrapper
The package MUST provide an `AsyncStorageBackend` wrapper:
- Wraps any sync `StorageBackend` instance.
- Runs blocking operations in a thread pool executor (`asyncio.to_thread` or `loop.run_in_executor`).
- Same method signatures with `async` prefix.
- Used by async frameworks (FastAPI, notification-agent) without blocking the event loop.

### FR1.15 — FastAPI Integration
The package SHOULD provide optional FastAPI integration:
- `get_storage_backend` dependency that creates/returns backend from app config.
- Example: `storage = Depends(get_storage_backend)`.
- No FastAPI import at package top level (lazy import).

### FR1.16 — Observability
The package MUST log all storage operations:
- Operation type, backend name, path, outcome (success/failure), duration.
- Use `cloud_dog_logging` (PS-40) when available, stdlib `logging` fallback.
- Credentials MUST NEVER appear in log output.
- Operation counter and timing metrics SHOULD be exposed.

### FR1.17 — Vault Integration (via cloud_dog_config)
All storage credentials (S3 access_key/secret_key, WebDAV username/password, FTP credentials, Google Drive client_secret/refresh_token) MUST arrive pre-resolved by `cloud_dog_config` (PS-80) variable substitution (e.g. `${vault.storage.s3.secret_key}`). This package MUST NOT read `os.environ` for credentials, import `hvac`, navigate Vault JSON structures, or implement its own secret resolution logic. Graceful degradation when `cloud_dog_config` is not installed is permitted (fall back to constructor arguments).

### FR1.18 — Disk Space Checking
The local filesystem backend SHOULD check available disk space before writes:
- Configurable minimum free space threshold (default: 100 MB).
- Raise `QuotaExceededError` when insufficient space detected.
- Optional: skip check when threshold is 0.

### FR1.19 — Conformance Test Suite
The package MUST include a conformance test suite:
- Reusable test functions that validate any `StorageBackend` implementation.
- Covers: read/write round-trip, overwrite semantics, delete (existing + missing_ok), list_dir (flat + recursive), stat, exists, copy, move, error cases.
- Consumer projects run conformance tests against their configured backend.

### FR1.20 — Mock Backend
The package MUST provide an in-memory `MockStorageBackend`:
- Implements full `StorageBackend` interface using in-memory dictionaries.
- Used by consumer project unit tests.
- Supports all operations including `create_dir`, `copy_path`, `move_path`.
- Thread-safe.

### FR1.21 — Configuration via Platform Config
The package MUST consume configuration via `cloud_dog_config` (PS-80):
- All credential fields populated by `cloud_dog_config` variable substitution (e.g. `${vault.storage.s3.secret_key}`) — no direct `os.environ` reads for credentials in this package.
- All storage settings in config namespace (e.g., `storage.*`).
- Support for profile-based configuration (multiple named storage configurations).

---

## Non-Functional Requirements

### NF1.1
Runtime dependencies limited to: `pydantic` (config models). Optional: `requests` (S3, WebDAV, Google Drive), `cloud_dog_config`, `cloud_dog_logging`, `fastapi`.

### NF1.2
Storage operations (local read/write) MUST complete in < 5ms for files under 1 MB (excluding network latency for remote backends).

### NF1.3
The package MUST work with Python 3.10+.

### NF1.4
Remote backends MUST support configurable timeouts (default: 30 seconds).

### NF1.5
The package MUST be publishable to a package registry (`<your-package-index>`).

---

## Cyber Security

### CS1.1
Path traversal attacks MUST be prevented by sanitisation and root-boundary enforcement.

### CS1.2
Credentials MUST NEVER be logged, included in error messages, or stored in plaintext config files.

### CS1.3
TLS MUST be enforced by default for all remote backends; `insecure_skip_verify` only for development.

### CS1.4
OAuth2 tokens (Google Drive) MUST be refreshed automatically; expired tokens MUST NOT be reused.

### CS1.5
S3 request signing MUST use AWS SigV4 with proper credential scoping.

---

## Acceptance Criteria

A project is compliant when:
- It uses `cloud_dog_storage` for all file/object storage operations.
- Backend selection is config-driven (PS-80).
- No raw filesystem I/O outside the storage abstraction for business data.
- Credentials are sourced from `cloud_dog_config` (PS-80) — never committed or read directly from `os.environ`/`hvac`/Vault.
- Path inputs are sanitised against traversal attacks.
- TLS is correctly configured for remote backends.
- Storage operations are logged with backend name, path, and outcome.
- No direct `os.environ`, `hvac`, or Vault reads for credentials — all config via `cloud_dog_config` (PS-80).
- Conformance test suite passes for all configured backends.
