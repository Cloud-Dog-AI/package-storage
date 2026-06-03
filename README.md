# platform-storage

**Package:** `cloud_dog_storage`  
**Standard:** PS-85 (Storage Interfaces)  
**Status:** Design complete, build-ready (`v0.1.0`)

## Purpose

Drop-in Python library implementing the PS-85 Storage Interfaces standard. Provides a unified file/object storage abstraction with pluggable backends, consistent error handling, TLS configuration, path sanitisation, and observability.

## Key Features

- **5 storage backends**: Local filesystem, S3-compatible, WebDAV, FTP/FTPS, Google Drive
- **Unified POSIX path model**: Same `/path/to/file` addressing regardless of backend
- **Config-driven backend selection**: Switch from local to S3 via config change — zero code modification
- **Sync + async**: Sync primary API with `AsyncStorageBackend` wrapper for event-loop frameworks
- **Security**: Path traversal prevention, root boundary enforcement, credential redaction, TLS configuration
- **Error taxonomy**: Consistent `StorageError` hierarchy across all backends
- **Factory pattern**: `build_storage_backend(config)` creates the right backend from config
- **Conformance suite**: Reusable tests that validate any backend implementation
- **Mock backend**: In-memory `MockStorageBackend` for consumer project unit tests
- **FastAPI integration**: Optional `Depends(get_storage_backend)` helper
- **Config delegation**: Credentials pre-resolved by `cloud_dog_config` (PS-80) — no direct Vault/env reads in this package

## Dependencies

- **Required:** `pydantic`
- **Optional:** `requests` (S3, WebDAV, Google Drive), `cloud_dog_config`, `cloud_dog_logging`, `fastapi`

## Documents

- [REQUIREMENTS.md](REQUIREMENTS.md) — Functional and non-functional requirements (21 FRs)
- [ARCHITECTURE.md](ARCHITECTURE.md) — Module layout, component design, integration patterns
- [TESTS.md](TESTS.md) — Test plan, directory structure, coverage map (72 tests: 32 UT + 10 ST + 20 IT + 5 AT + 5 QT)

## Quick Start

```python
from cloud_dog_storage import build_storage_backend
from cloud_dog_storage.config.models import StorageConfig

# Via cloud_dog_config (recommended — credentials pre-resolved from Vault)
from cloud_dog_config import get_config, bind_model
config = bind_model(get_config(), "storage", StorageConfig)
storage = build_storage_backend(config)

# Or direct construction (when cloud_dog_config not installed)
config = StorageConfig(backend="local", root_path="/data/files")
storage = build_storage_backend(config)

# Use (same API for all backends)
storage.write_bytes("/reports/q1.pdf", pdf_data)
data = storage.read_bytes("/reports/q1.pdf")
entries = storage.list_dir("/reports", recursive=True)
storage.delete_path("/reports/q1.pdf")

# Async usage
from cloud_dog_storage import AsyncStorageBackend
async_storage = AsyncStorageBackend(storage)
data = await async_storage.read_bytes("/reports/q1.pdf")
```

## Reference Implementations

Existing code in these projects informed the package design:

| Project | Storage Code | Backends |
|---------|-------------|----------|
| `file-mcp-server` | `src/file_tools/storage/` (1,482L) | Local, S3, WebDAV, FTP, Google Drive |
| `notification-agent` | `src/core/storage/` (2,967L) | Local, S3, WebDAV, FTP |
| `expert-agent` | `src/core/multimedia/` (~900L) | Local only |

## Standards Alignment

| Standard | Alignment |
|----------|-----------|
| PS-85 | Primary standard — Storage Interfaces |
| PS-80 | Config delegation — credentials pre-resolved by `cloud_dog_config`, no direct Vault reads |
| PS-40 | Structured logging, credential redaction |
| PS-90 | Path sanitisation, TLS enforcement, credential handling |
| PS-95 | Test hierarchy (UT/ST/IT/AT/QT), conformance suite |
| PS-00 | Config-driven, testable, auditable |

---

## Licence

Apache-2.0 — Copyright (c) 2026 Cloud-Dog, Viewdeck Engineering Limited
