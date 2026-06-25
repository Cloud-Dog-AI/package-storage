# Agent Instruction — Build `cloud_dog_storage` v0.1.0

**Package:** `cloud_dog_storage`  
**Standard:** PS-85 (Storage Interfaces)  
**Date:** 2026-02-18  
**Priority:** High — needed ASAP to support new package builds and eliminate duplication

---

## Purpose

Build the `cloud_dog_storage` backend package from scratch, following the design in REQUIREMENTS.md, ARCHITECTURE.md, and TESTS.md in this directory. The package provides a unified file/object storage abstraction with 5 pluggable backends.

**This package is NOT part of the current migration exercise** but is needed immediately to support new project development and future migration work.

---

## INTEGRITY WARRANTY — ZERO TOLERANCE

All clauses from `AGENT-INSTRUCTION.md` § "INTEGRITY WARRANTY — ZERO TOLERANCE" and `AGENT-INSTRUCTION-TIER2.md` apply in full. Additionally:

1. **EVERY BACKEND MUST BE FULLY FUNCTIONAL.** A backend that only implements `read_bytes`/`write_bytes` but stubs `list_dir`/`stat`/`copy_path` is INCOMPLETE. Every method listed in ARCHITECTURE.md CC1.1 that is NOT `NotSupportedError` for that backend MUST work.
2. **S3 SIGNING MUST BE REAL.** The S3 backend uses AWS SigV4 with `hashlib`/`hmac` — NOT `boto3`. The signing logic must produce valid Authorization headers. Test against MinIO or real S3.
3. **WEBDAV XML PARSING MUST BE REAL.** PROPFIND responses must be parsed from real XML — not string matching. Use `xml.etree.ElementTree`.
4. **GOOGLE DRIVE MUST HANDLE TOKEN REFRESH.** The OAuth2 refresh flow must actually call the token endpoint and update the stored access token. Not a stub.
5. **ASYNC WRAPPER MUST USE THREAD POOL.** `AsyncStorageBackend` must use `asyncio.to_thread` or `loop.run_in_executor` — NOT `async def` that just calls sync methods directly.
6. **CONFORMANCE SUITE MUST BE REUSABLE.** `testing/conformance.py` must work against ANY `StorageBackend` instance, not just `LocalStorage`.
7. **ALL IT TESTS MUST CLEAN UP.** Use `cloud_dog_test_*` prefix for all test files/directories. Delete after test. Verify deletion.
8. **CONFIG DELEGATION — ZERO TOLERANCE.** This package MUST NOT read `os.environ` for credentials, import `hvac`, navigate Vault JSON, or implement secret overlay/merge logic. See § Config Delegation below.

---

## Config Delegation — ZERO TOLERANCE (PS-80)

**`cloud_dog_config` is the ONLY package that may resolve secrets, read Vault, or parse config sources.** This package receives fully-resolved configuration — it MUST NOT navigate Vault JSON, call `hvac`, read `os.environ` for credentials, or implement its own secret resolution logic.

**Absolute prohibitions:**

1. **NO `os.environ` reads for credentials** — S3 keys, WebDAV passwords, FTP passwords, Google Drive tokens MUST come from `StorageConfig` objects populated by `cloud_dog_config`, never from direct `os.environ` access. (`os.environ` reads for _non-secret_ feature flags in test fixtures are permitted.)
2. **NO `hvac` imports** — only `cloud_dog_config` may import or use the `hvac` Vault client library.
3. **NO Vault path navigation** — no function may accept a `vault_config: dict` parameter, parse `CLOUD_DOG_*_VAULT_JSON` env vars, or navigate Vault section structures.
4. **NO secret overlay/merge functions** — no `overlay_secrets()`, `_resolve_runtime_provider_config()`, `_vault_from_env()`, `SecretResolver`, or equivalent.
5. **NO `secrets/` module** — no `secrets/` directory with overlay, resolver, or similar modules.
6. **NO `config/vault.py` module** — this package does NOT have a Vault integration module. Vault resolution is handled entirely by `cloud_dog_config`.

**How credentials flow:**
```
defaults.yaml → config.yaml → env-files → os.environ → cloud_dog_config compile phase
    ↓
${vault.storage.s3.secret_key} resolved → StorageConfig(s3=S3Config(secret_key="resolved_value"))
    ↓
S3Storage receives S3Config → uses self._secret_key directly
```

**How consuming projects use this package:**
```python
from cloud_dog_storage import build_storage_backend
from cloud_dog_config import get_config, bind_model
from cloud_dog_storage.config.models import StorageConfig

# cloud_dog_config resolves ${vault.storage.*} variables automatically
config = bind_model(get_config(), "storage", StorageConfig)
storage = build_storage_backend(config)
```

**When `cloud_dog_config` is NOT installed**, constructing `StorageConfig` directly with pre-populated values is the fallback:
```python
from cloud_dog_storage import build_storage_backend
from cloud_dog_storage.config.models import StorageConfig, S3Config

config = StorageConfig(backend="s3", s3=S3Config(
    endpoint="https://s3.cloud-dog.net",
    bucket="files",
    access_key="pre-resolved-value",
    secret_key="pre-resolved-value",
))
storage = build_storage_backend(config)
```

**Verification command (run after build):**
```bash
# Must return zero hits (excluding test fixtures and conftest.py vault_env fixture)
grep -rn "os.environ\|import hvac\|vault_config\|overlay_secrets\|_vault_from_env\|VAULT_JSON\|SecretResolver" cloud_dog_storage/  --include="*.py" | grep -v __pycache__
```

---

## Governing Documents

Read these in order before writing any code:

1. **`packages/backend/AGENT-INSTRUCTION.md`** — Master agent instruction (INTEGRITY WARRANTY, config delegation, Vault, file headers, UK English) — **READ § "Config Delegation — ZERO TOLERANCE" FIRST**
2. **`docs/standards/85-storage-interfaces.md`** — PS-85 v1.0 (Storage Interfaces standard) — THE AUTHORITY
3. **`packages/backend/platform-storage/REQUIREMENTS.md`** — 21 FRs + NFRs + CS
4. **`packages/backend/platform-storage/ARCHITECTURE.md`** — Module layout (22 modules), component design, integration patterns
5. **`packages/backend/platform-storage/TESTS.md`** — 72 tests (32 UT + 10 ST + 20 IT + 5 AT + 5 QT)
6. **`docs/standards/80-config-mgmt.md`** — PS-80 (config precedence, Vault)
7. **`docs/standards/40-logging-observability.md`** — PS-40 (logging format)
8. **`docs/standards/90-security.md`** — PS-90 (path sanitisation, TLS, credentials)
9. **`docs/standards/95-testing.md`** — PS-95 (test hierarchy, --env enforcement)
10. **`RULES.md`** — UK English, file headers, no hardcoded values

---

## Donor Codebases — STUDY THESE

The implementation draws heavily from two existing codebases. **Study them before writing code:**

### Primary donor: `file-mcp-server/src/file_tools/storage/`

| File | Lines | Use |
|------|------:|-----|
| `base.py` | 82 | `StorageBackend` class, `NotSupportedError`, `StorageStat`, `StorageEntry` — **copy pattern exactly** |
| `local.py` | 64 | `LocalStorage` — pathlib delegation |
| `s3.py` | 299 | `S3Storage` — SigV4 signing, pure requests, ListObjectsV2 XML parsing |
| `webdav.py` | 344 | `WebDavStorage` — PROPFIND parsing, retry, move idempotency |
| `ftp.py` | 277 | `FtpStorage` — MLSD/NLST, connection-per-op, FTP_TLS |
| `google_drive.py` | 365 | `GoogleDriveStorage` — OAuth2 refresh, path→folder-ID, multipart upload |
| `factory.py` | 34 | `build_storage_backend()` — lazy imports |

### Secondary donor: `notification-agent/src/core/storage/`

| File | Lines | Use |
|------|------:|-----|
| `base.py` | 173 | `StorageBackend` ABC (async), `StoredFile`, error hierarchy — **merge error classes** |
| `filesystem.py` | 386 | Disk space checking, subdirectory patterns, permission management |
| `s3.py` | 283 | Async S3 via `aioboto3` — **DO NOT copy boto3 pattern, use pure requests from file-mcp** |
| `factory.py` | 109 | `StorageFactory` with registry pattern — merge with file-mcp factory |
| `storage_manager.py` | 416 | High-level manager — **extract `StoredFile` model and MIME logic** |

### Extraction strategy

1. Start with `file-mcp-server/storage/base.py` as the backbone.
2. Add `exists()`, `get_url()` from notification-agent.
3. Merge error hierarchy from notification-agent `base.py`.
4. Copy backends from file-mcp-server (they are the cleanest).
5. Add `LocalStorage` root boundary enforcement from notification-agent `filesystem.py`.
6. Add disk space checking from notification-agent `filesystem.py`.
7. Add `StoredFile` model from notification-agent `base.py`.
8. Add `AsyncStorageBackend` wrapper (new code, using `asyncio.to_thread`).
9. Add Pydantic config models (upgrade from file-mcp's models).
10. Add path sanitiser (consolidate `_clean_posix` + `_sanitize_path` from both).
11. Add conformance test suite and mock backend (new code).

---

## Build Order

```
Phase 1 — Core (no external deps):
  1. errors.py                    — Error hierarchy
  2. models.py                    — StorageEntry, StorageStat, StoredFile
  3. security/path_sanitiser.py   — clean_posix, validate_within_root
  4. security/tls.py              — TLS config helpers
  5. backends/base.py             — StorageBackend ABC
  6. backends/local.py            — LocalStorage
  7. config/models.py             — Pydantic config models
  8. factory.py                   — build_storage_backend (local only first)
  9. __init__.py                  — Public API

Phase 2 — Remote backends (requires `requests`):
  10. backends/s3.py              — S3Storage (SigV4)
  11. backends/webdav.py          — WebDavStorage
  12. backends/ftp.py             — FtpStorage
  13. backends/google_drive.py    — GoogleDriveStorage
  14. factory.py                  — Add lazy imports for all backends

Phase 3 — Advanced features:
  15. async_wrapper.py            — AsyncStorageBackend
  16. observability/logging.py    — Logging integration
  17. api/fastapi/deps.py         — FastAPI dependency
  NOTE: There is NO config/vault.py — Vault resolution is cloud_dog_config's job.

Phase 4 — Testing infrastructure:
  18. testing/mock_backend.py     — MockStorageBackend
  19. testing/conformance.py      — Conformance test suite
  20. testing/fixtures.py         — Shared test fixtures

Phase 5 — Tests:
  21. All UT tests (32)
  22. All ST tests (10)
  23. All IT tests (20) — env-gated
  24. All AT tests (5)
  25. All QT tests (5)
```

---

## File Header (MANDATORY)

Every `.py` file MUST start with:

```python
"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: <one-line description>
Standard: PS-85 (Storage Interfaces)
**************************************************
"""
```

---

## Key Implementation Details

### `_clean_posix` helper (from file-mcp-server)

This function is used by ALL remote backends. Extract it to `security/path_sanitiser.py`:

```python
def clean_posix(path: str) -> str:
    """Normalise to POSIX absolute path."""
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    norm = posixpath.normpath(path)
    if not norm.startswith("/"):
        norm = "/" + norm
    return norm
```

### S3 SigV4 Signing (from file-mcp-server `s3.py`)

The existing implementation in file-mcp-server works correctly. Key functions:
- `_sha256_hex(data: bytes) -> str`
- `_hmac(key: bytes, msg: str) -> bytes`
- `_aws_v4_signing_key(secret_key, date, region, service) -> bytes`
- `_canonical_query(params) -> str`
- `_canonical_headers(headers) -> tuple[str, str]`

Copy these functions exactly. They produce valid SigV4 signatures.

### WebDAV PROPFIND XML Parsing (from file-mcp-server `webdav.py`)

The `_parse_propfind_xml` function parses `{DAV:}response` elements. Copy the implementation and ensure it handles:
- `{DAV:}href` → path extraction
- `{DAV:}resourcetype` → `{DAV:}collection` → is_dir
- `{DAV:}getcontentlength` → size
- Namespace handling via `{DAV:}` prefix

### Google Drive OAuth2 (from file-mcp-server `google_drive.py`)

Token refresh flow:
1. Check `_access_token` and `_token_expires_at`.
2. If expired or near-expiry (30s buffer), POST to `_token_uri` with `client_id`, `client_secret`, `refresh_token`, `grant_type=refresh_token`.
3. Update `_access_token` and `_token_expires_at`.
4. If no `refresh_token` and `access_token` exists, use it as-is (will fail when expired).

### AsyncStorageBackend (NEW CODE)

```python
import asyncio
from cloud_dog_storage.backends.base import StorageBackend

class AsyncStorageBackend:
    def __init__(self, backend: StorageBackend) -> None:
        self._backend = backend

    async def read_bytes(self, path: str) -> bytes:
        return await asyncio.to_thread(self._backend.read_bytes, path)

    # ... same pattern for all methods
```

Also provide compatibility methods matching notification-agent's interface:
- `store_file(content, filename, content_type, metadata)` → write_bytes + return StoredFile
- `get_file_content(path)` → read_bytes
- `delete_file(path)` → delete_path, return bool
- `file_exists(path)` → exists
- `get_file_url(path)` → get_url

### MockStorageBackend (NEW CODE)

In-memory dict-based implementation:

```python
class MockStorageBackend(StorageBackend):
    backend_name = "mock"

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}
        self._dirs: set[str] = {"/"}
```

Implement all operations against `_files` and `_dirs`. Thread-safe via `threading.Lock`.

---

## Test Service Preconditions

| Test Tier | Requires | How to Provide |
|-----------|----------|---------------|
| **UT** | Nothing external | tmp_path + MockStorageBackend |
| **ST** | Local filesystem | tmp_path (pytest built-in) |
| **IT (S3)** | S3-compatible endpoint | Set `TEST_S3_ENDPOINT`, `TEST_S3_BUCKET`, `TEST_S3_ACCESS_KEY`, `TEST_S3_SECRET_KEY` |
| **IT (WebDAV)** | WebDAV server | Set `TEST_WEBDAV_URL`, `TEST_WEBDAV_USERNAME`, `TEST_WEBDAV_PASSWORD` |
| **IT (FTP)** | FTP server | Set `TEST_FTP_HOST`, `TEST_FTP_USERNAME`, `TEST_FTP_PASSWORD` |
| **IT (Google Drive)** | Google Drive OAuth | Set `TEST_GDRIVE_FOLDER_ID`, `TEST_GDRIVE_CLIENT_ID`, `TEST_GDRIVE_CLIENT_SECRET`, `TEST_GDRIVE_REFRESH_TOKEN` |
| **AT** | FastAPI test client | `httpx` TestClient |
| **QT** | Nothing external | Mock-based security tests |

### Vault Config Sections

| Section | Keys | Use |
|---------|------|-----|
| `dev.storage.s3` | `endpoint`, `bucket`, `access_key`, `secret_key` | IT S3 tests |
| `dev.storage.webdav` | `base_url`, `username`, `password` | IT WebDAV tests |
| `dev.storage.ftp` | `host`, `port`, `username`, `password` | IT FTP tests |
| `dev.storage.google_drive` | `folder_id`, `client_id`, `client_secret`, `refresh_token` | IT Google Drive tests |

---

## Verification Commands

```bash
# Setup
cd /path/to/platform-storage
python -m venv .venv
source .venv/bin/activate
pip install -e ".[all,dev]"

# Lint + format
ruff check cloud_dog_storage tests
ruff format --check cloud_dog_storage tests

# Config delegation verification (MUST return zero hits)
grep -rn "os.environ\|import hvac\|vault_config\|overlay_secrets\|_vault_from_env\|VAULT_JSON\|SecretResolver" cloud_dog_storage/  --include="*.py" | grep -v __pycache__

# UT + ST (no external services)
pytest tests/ -v --env UT --env ST

# IT (requires Vault / test services)
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
pytest tests/ -v --env IT

# Full matrix
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
pytest tests/ -v --env UT --env ST --env IT --env AT --env QT

# Build
python -m build --no-isolation

# Install + import check
pip install --force-reinstall --no-deps dist/cloud_dog_storage-0.1.0-py3-none-any.whl
python -c "from cloud_dog_storage import StorageBackend, build_storage_backend; print('import-ok')"
python -c "from cloud_dog_storage.config.models import StorageConfig; print('config-ok')"
```

---

## Done Criteria

The package is DONE when ALL of the following are true:

1. **SA1 completeness**: All 22 modules from ARCHITECTURE.md SA1 exist and contain real implementation (not stubs).
2. **Lint**: `ruff check cloud_dog_storage tests` — zero errors.
3. **Format**: `ruff format --check cloud_dog_storage tests` — all files formatted.
4. **Config delegation verified**: `grep -rn "os.environ\|import hvac\|vault_config\|overlay_secrets" cloud_dog_storage/ --include="*.py" | grep -v __pycache__` returns **zero hits**.
5. **UT+ST tests**: `pytest tests/ -v --env UT --env ST` — all pass, zero failures.
6. **IT tests**: At minimum, S3 and WebDAV IT tests pass against real services. FTP and Google Drive IT tests pass or skip gracefully.
7. **AT tests**: FastAPI integration tests pass.
8. **QT tests**: All security tests pass (path traversal, credential redaction, TLS, boundary, null byte).
9. **Build**: `python -m build --no-isolation` produces `.tar.gz` + `.whl`.
10. **Import**: `python -c "from cloud_dog_storage import StorageBackend, build_storage_backend; print('import-ok')"` works.
11. **No hardcoded values**: Zero hardcoded URLs, paths, credentials, timeouts.
12. **File headers**: Every `.py` file has the license header.
13. **UK English**: All docstrings and comments use UK English spelling.
14. **No `config/vault.py`**: The package directory MUST NOT contain a `config/vault.py` or `secrets/` module.

---

## Anti-Patterns to Avoid (Lessons Learned)

These issues were found in previous package builds. Do NOT repeat them:

1. **DO NOT** create stub modules that raise `NotImplementedError` for everything and claim the package is done.
2. **DO NOT** use `boto3` for S3 — the pure-requests SigV4 approach from file-mcp-server is intentional (minimal deps, offline-friendly).
3. **DO NOT** implement only `read_bytes`/`write_bytes` and skip `list_dir`/`stat`/`copy_path`/`move_path`. Every required method MUST work.
4. **DO NOT** skip the conformance test suite — it is what ensures all backends behave consistently.
5. **DO NOT** log credentials. Ever. In any backend. In any error message. In any exception.
6. **DO NOT** hardcode test file paths or URLs. Use `tmp_path` for local, env vars for remote.
7. **DO NOT** leave IT test files behind. Every IT test MUST clean up.
8. **DO NOT** create fake async by wrapping sync calls without a thread pool. Use `asyncio.to_thread`.
9. **DO NOT** skip path sanitisation. The `clean_posix` + `validate_within_root` functions are security-critical.
10. **DO NOT** implement WebDAV PROPFIND parsing with string matching. Use `xml.etree.ElementTree`.
11. **DO NOT** create a `config/vault.py` module. This package does NOT read Vault. All credentials arrive pre-resolved via `cloud_dog_config`.
12. **DO NOT** read `os.environ` for any credential (access_key, secret_key, password, client_secret, refresh_token). Backend constructors receive typed Pydantic config objects with credentials already populated.
13. **DO NOT** create a `secrets/` directory or any secret overlay/resolver/merge functions.

---

## Expected Output

After successful build, the package directory should look like:

```
platform-storage/
  cloud_dog_storage/
    __init__.py
    async_wrapper.py
    errors.py
    factory.py
    models.py
    backends/
      __init__.py
      base.py
      local.py
      s3.py
      webdav.py
      ftp.py
      google_drive.py
    config/
      __init__.py
      models.py             # NO vault.py — credentials arrive pre-resolved
    security/
      __init__.py
      path_sanitiser.py
      tls.py
    observability/
      __init__.py
      logging.py
    api/
      __init__.py
      fastapi/
        __init__.py
        deps.py
    testing/
      __init__.py
      conformance.py
      fixtures.py
      mock_backend.py
  tests/
    conftest.py
    env-UT
    env-ST
    env-IT
    env-AT
    unit/        (32 test files)
    system/      (10 test files)
    integration/ (20 test files)
    application/ (5 test files)
    security/    (5 test files)
  pyproject.toml
  defaults.yaml
  README.md
  dist/
    cloud_dog_storage-0.1.0.tar.gz
    cloud_dog_storage-0.1.0-py3-none-any.whl
```
