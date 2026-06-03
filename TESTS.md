# platform-storage — TESTS.md

**Package:** `cloud_dog_storage`  
**Version:** 0.1.0 (pre-release)  
**Standard:** PS-85, PS-95  
**Status:** Draft  
**Last updated:** 2026-02-18

---

## Test Strategy

### Overview

Tests organised per PS-95 hierarchy:

- **UT** — Unit tests for individual components (backends with mocks/local, config models, errors, path sanitisation, factory)
- **ST** — System tests for end-to-end storage flows with local filesystem
- **IT** — Integration tests with real remote backends (S3, WebDAV, FTP, Google Drive — env-gated)
- **AT** — Application tests simulating real service usage patterns via FastAPI
- **QT** — Security tests for path traversal, credential redaction, TLS enforcement

### Test Principles

- `--env` mandatory for all test runs.
- Zero hardcoded values.
- UT tests use local filesystem (tmp_path) + MockStorageBackend.
- ST tests use local filesystem with full lifecycle.
- IT tests are env-gated (require real S3/WebDAV/FTP/Google Drive services).
- All IT tests MUST clean up created files/directories after completion.
- Stop on failure.

---

## Test Directory Structure

```
tests/
  conftest.py
  env-UT
  env-ST
  env-IT
  env-AT
  unit/
    UT1.1_StorageBackendInterface/
      test_backend_interface.py
    UT1.2_LocalStorageBasic/
      test_local_basic.py
    UT1.3_LocalStorageReadWrite/
      test_local_read_write.py
    UT1.4_LocalStorageListDir/
      test_local_list_dir.py
    UT1.5_LocalStorageStat/
      test_local_stat.py
    UT1.6_LocalStorageCopyMove/
      test_local_copy_move.py
    UT1.7_LocalStorageChmod/
      test_local_chmod.py
    UT1.8_LocalStorageCreateDir/
      test_local_create_dir.py
    UT1.9_LocalStorageDiskSpace/
      test_local_disk_space.py
    UT1.10_S3SigningLogic/
      test_s3_signing.py
    UT1.11_S3KeyMapping/
      test_s3_key_mapping.py
    UT1.12_WebDavPropfindParsing/
      test_webdav_propfind.py
    UT1.13_WebDavRetryLogic/
      test_webdav_retry.py
    UT1.14_FtpPathMapping/
      test_ftp_path_mapping.py
    UT1.15_GoogleDriveFolderIdExtraction/
      test_gdrive_folder_id.py
    UT1.16_GoogleDriveTokenRefresh/
      test_gdrive_token_refresh.py
    UT1.17_StorageConfigModels/
      test_config_models.py
    UT1.18_StorageConfigDefaults/
      test_config_defaults.py
    UT1.19_FactoryDispatch/
      test_factory_dispatch.py
    UT1.20_FactoryLazyImports/
      test_factory_lazy_imports.py
    UT1.21_ErrorTaxonomy/
      test_error_taxonomy.py
    UT1.22_PathSanitiser/
      test_path_sanitiser.py
    UT1.23_PathTraversalPrevention/
      test_path_traversal.py
    UT1.24_TlsConfigHelpers/
      test_tls_config.py
    UT1.25_StorageEntryModel/
      test_storage_entry.py
    UT1.26_StorageStatModel/
      test_storage_stat.py
    UT1.27_StoredFileModel/
      test_stored_file.py
    UT1.28_MockBackend/
      test_mock_backend.py
    UT1.29_AsyncWrapper/
      test_async_wrapper.py
    UT1.30_ObservabilityLogging/
      test_observability_logging.py
    UT1.31_NotSupportedErrorHandling/
      test_not_supported.py
    UT1.32_CleanPosixHelper/
      test_clean_posix.py
  system/
    ST1.1_LocalFullLifecycle/
      test_local_full_lifecycle.py
    ST1.2_LocalOverwriteSemantics/
      test_local_overwrite.py
    ST1.3_LocalRecursiveListing/
      test_local_recursive_listing.py
    ST1.4_LocalIterPaths/
      test_local_iter_paths.py
    ST1.5_FactoryConfigRoundTrip/
      test_factory_config_roundtrip.py
    ST1.6_ConfigFromDefaults/
      test_config_from_defaults.py
    ST1.7_VaultConfigIntegration/
      test_vault_config.py
    ST1.8_ConformanceSuiteLocal/
      test_conformance_local.py
    ST1.9_AsyncWrapperLifecycle/
      test_async_wrapper_lifecycle.py
    ST1.10_StoredFileSerialisation/
      test_stored_file_serialisation.py
  integration/
    IT1.1_S3ReadWriteDelete/
      test_s3_crud.py
    IT1.2_S3ListDir/
      test_s3_list_dir.py
    IT1.3_S3CopyMove/
      test_s3_copy_move.py
    IT1.4_S3StatExists/
      test_s3_stat_exists.py
    IT1.5_WebDavReadWriteDelete/
      test_webdav_crud.py
    IT1.6_WebDavListDir/
      test_webdav_list_dir.py
    IT1.7_WebDavCopyMove/
      test_webdav_copy_move.py
    IT1.8_WebDavCreateDir/
      test_webdav_create_dir.py
    IT1.9_FtpReadWriteDelete/
      test_ftp_crud.py
    IT1.10_FtpListDir/
      test_ftp_list_dir.py
    IT1.11_FtpCreateDir/
      test_ftp_create_dir.py
    IT1.12_FtpCopyMove/
      test_ftp_copy_move.py
    IT1.13_GoogleDriveReadWriteDelete/
      test_gdrive_crud.py
    IT1.14_GoogleDriveListDir/
      test_gdrive_list_dir.py
    IT1.15_GoogleDriveCreateDir/
      test_gdrive_create_dir.py
    IT1.16_GoogleDriveCopyMove/
      test_gdrive_copy_move.py
    IT1.17_S3ConformanceSuite/
      test_s3_conformance.py
    IT1.18_WebDavConformanceSuite/
      test_webdav_conformance.py
    IT1.19_FtpConformanceSuite/
      test_ftp_conformance.py
    IT1.20_GoogleDriveConformanceSuite/
      test_gdrive_conformance.py
  application/
    AT1.1_FastAPIFileUploadDownload/
      test_fastapi_file_ops.py
    AT1.2_FastAPIStorageDependency/
      test_fastapi_storage_dep.py
    AT1.3_AsyncStorageInFastAPI/
      test_async_storage_fastapi.py
    AT1.4_BackendSwitchViaConfig/
      test_backend_switch.py
    AT1.5_ConformanceSuiteRunner/
      test_conformance_runner.py
  security/
    QT1.1_PathTraversalAttack/
      test_path_traversal_attack.py
    QT1.2_CredentialRedactionInLogs/
      test_credential_redaction.py
    QT1.3_TlsEnforcement/
      test_tls_enforcement.py
    QT1.4_RootBoundaryEscape/
      test_root_boundary.py
    QT1.5_NullByteInjection/
      test_null_byte_injection.py
```

---

## Coverage Map (Requirements → Tests)

### Functional Requirements
- **FR1.1** → UT1.1 (backend interface completeness)
- **FR1.2** → UT1.32, UT1.22, UT1.23 (POSIX path model, sanitisation, traversal prevention)
- **FR1.3** → UT1.2–UT1.9, ST1.1–ST1.4, ST1.8 (local filesystem backend)
- **FR1.4** → UT1.10, UT1.11, IT1.1–IT1.4, IT1.17 (S3 backend)
- **FR1.5** → UT1.12, UT1.13, IT1.5–IT1.8, IT1.18 (WebDAV backend)
- **FR1.6** → UT1.14, IT1.9–IT1.12, IT1.19 (FTP backend)
- **FR1.7** → UT1.15, UT1.16, IT1.13–IT1.16, IT1.20 (Google Drive backend)
- **FR1.8** → UT1.19, UT1.20, ST1.5 (factory)
- **FR1.9** → UT1.17, UT1.18, ST1.6 (config models)
- **FR1.10** → UT1.25, UT1.26, UT1.27, ST1.10 (data models)
- **FR1.11** → UT1.21, UT1.31 (error taxonomy)
- **FR1.12** → UT1.22, UT1.23, QT1.1, QT1.4, QT1.5 (path sanitisation)
- **FR1.13** → UT1.24, QT1.3 (TLS configuration)
- **FR1.14** → UT1.29, ST1.9, AT1.3 (async wrapper)
- **FR1.15** → AT1.1, AT1.2, AT1.3 (FastAPI integration)
- **FR1.16** → UT1.30, QT1.2 (observability)
- **FR1.17** → ST1.7 (Vault integration)
- **FR1.18** → UT1.9 (disk space checking)
- **FR1.19** → ST1.8, IT1.17–IT1.20, AT1.5 (conformance suite)
- **FR1.20** → UT1.28 (mock backend)
- **FR1.21** → ST1.6, ST1.7 (platform config integration)

### Cyber Security
- **CS1.1** → UT1.22, UT1.23, QT1.1, QT1.4, QT1.5 (path traversal + null byte)
- **CS1.2** → UT1.30, QT1.2 (credential redaction)
- **CS1.3** → UT1.24, QT1.3 (TLS enforcement)
- **CS1.4** → UT1.16 (Google Drive token refresh)
- **CS1.5** → UT1.10 (S3 SigV4 signing)

---

## Unit Tests (UT) — Selected Detail

### UT1.1: Storage Backend Interface
- **Scope**: Verify abstract interface completeness
- **What is being tested**: All required methods present; default `exists` delegates to `stat`; default `rename_path` delegates to `move_path`; `NotSupportedError` raised for unimplemented optional ops; `backend_name` attribute
- **Related Requirements**: FR1.1
- **Related Architecture**: CC1.1, backends/base.py

### UT1.2: Local Storage Basic
- **Scope**: Basic LocalStorage operations
- **What is being tested**: Constructor accepts `root_path`; `backend_name` is `"local"`; read non-existent file → `StorageFileNotFoundError`; write + read round-trip; delete existing file; delete missing file with `missing_ok=True` → no error; delete missing file with `missing_ok=False` → error
- **Related Requirements**: FR1.3
- **Related Architecture**: CC1.2, backends/local.py

### UT1.10: S3 Signing Logic
- **Scope**: AWS SigV4 request signing correctness
- **What is being tested**: Canonical request construction; string-to-sign derivation; signing key generation; authorization header format; date handling; content hash; query parameter encoding
- **Related Requirements**: FR1.4, CS1.5
- **Related Architecture**: CC1.3, backends/s3.py

### UT1.12: WebDAV PROPFIND Parsing
- **Scope**: PROPFIND XML response parsing
- **What is being tested**: Parse valid multistatus response → correct `StorageEntry` list; handle collections (directories); extract content-length for files; handle missing properties; handle namespace variations
- **Related Requirements**: FR1.5
- **Related Architecture**: CC1.4, backends/webdav.py

### UT1.15: Google Drive Folder ID Extraction
- **Scope**: Extract folder ID from various URL formats
- **What is being tested**: Direct folder ID → returned as-is; URL format `/drive/folders/<id>` → extracted; URL format `open?id=<id>` → extracted; empty/None → None; invalid URL → None
- **Related Requirements**: FR1.7
- **Related Architecture**: CC1.6, backends/google_drive.py

### UT1.19: Factory Dispatch
- **Scope**: Factory creates correct backend for each config type
- **What is being tested**: `backend="local"` → `LocalStorage`; `backend="s3"` → `S3Storage`; `backend="webdav"` → `WebDavStorage`; `backend="ftp"` → `FtpStorage`; `backend="google_drive"` → `GoogleDriveStorage`; aliases (`fs`, `filesystem`, `gdrive`, `drive`); unknown backend → `ValueError`
- **Related Requirements**: FR1.8
- **Related Architecture**: CC1.7, factory.py

### UT1.22: Path Sanitiser
- **Scope**: Path normalisation and sanitisation
- **What is being tested**: `clean_posix("")` → `"/"`; `clean_posix("foo/bar")` → `"/foo/bar"`; `clean_posix("/../../../etc/passwd")` → `"/etc/passwd"` (normalised); `clean_posix("/a//b///c")` → `"/a/b/c"`; null byte removal; trailing slash handling
- **Related Requirements**: FR1.12, CS1.1
- **Related Architecture**: CC1.9, security/path_sanitiser.py

### UT1.28: Mock Backend
- **Scope**: In-memory mock backend for consumer tests
- **What is being tested**: Full StorageBackend interface works in-memory; write → read round-trip; list_dir; stat; exists; copy; move; delete; create_dir; thread-safe
- **Related Requirements**: FR1.20
- **Related Architecture**: CC1.13, testing/mock_backend.py

### UT1.29: Async Wrapper
- **Scope**: AsyncStorageBackend wraps sync backend
- **What is being tested**: `async read_bytes` → calls sync `read_bytes` in thread pool; `async write_bytes` → calls sync `write_bytes`; all async methods available; exceptions propagated correctly; compatibility methods (`store_file`, `get_file_content`, `delete_file`, `file_exists`)
- **Related Requirements**: FR1.14
- **Related Architecture**: CC1.8, async_wrapper.py

---

## System Tests (ST) — Selected Detail

### ST1.1: Local Full Lifecycle
- **Scope**: Complete file lifecycle on local filesystem
- **What is being tested**: Create dir → write file → stat → exists → read → overwrite → list_dir → copy → move → delete → confirm gone; all via `LocalStorage` with `tmp_path`
- **Related Requirements**: FR1.3
- **Related Architecture**: CC1.2

### ST1.5: Factory Config Round-Trip
- **Scope**: Config → factory → backend → operations
- **What is being tested**: Build `StorageConfig` → `build_storage_backend()` → write/read/delete via returned backend; verify backend_name matches config
- **Related Requirements**: FR1.8, FR1.9
- **Related Architecture**: CC1.7, CC1.10

### ST1.7: Config Delegation via cloud_dog_config
- **Scope**: Load storage config via `cloud_dog_config` `bind_model()` (env-gated)
- **What is being tested**: Source Vault env → `get_config()` → `bind_model(cfg, "storage", StorageConfig)` → verify credential fields are pre-resolved by `cloud_dog_config` (not by this package); skip if `cloud_dog_config` not installed. Also verify: no `os.environ` reads for credentials, no `hvac` imports, no Vault path navigation in the package source.
- **Related Requirements**: FR1.17, FR1.21
- **Related Architecture**: CC1.10, config/models.py

### ST1.8: Conformance Suite Local
- **Scope**: Run conformance test suite against LocalStorage
- **What is being tested**: `run_conformance_suite(LocalStorage(tmp_path))` → all tests pass; covers: read/write, overwrite, delete, list_dir, stat, exists, copy, move, error cases
- **Related Requirements**: FR1.19
- **Related Architecture**: CC1.13, testing/conformance.py

---

## Integration Tests (IT) — Selected Detail

### IT1.1: S3 Read/Write/Delete
- **Scope**: Full CRUD against real S3-compatible endpoint (env-gated)
- **What is being tested**: Write file → read back → verify content matches → delete → confirm gone; uses `cloud_dog_test_*` prefix; cleans up after test
- **Related Requirements**: FR1.4
- **Related Architecture**: CC1.3

### IT1.5: WebDAV Read/Write/Delete
- **Scope**: Full CRUD against real WebDAV server (env-gated)
- **What is being tested**: Write file → read back → verify → delete; create_dir; list_dir; PROPFIND metadata; retry on transient failure
- **Related Requirements**: FR1.5
- **Related Architecture**: CC1.4

### IT1.9: FTP Read/Write/Delete
- **Scope**: Full CRUD against real FTP server (env-gated)
- **What is being tested**: Write file → read back → verify → delete; create_dir; list_dir; move; FTPS if configured
- **Related Requirements**: FR1.6
- **Related Architecture**: CC1.5

### IT1.13: Google Drive Read/Write/Delete
- **Scope**: Full CRUD against real Google Drive (env-gated)
- **What is being tested**: Write file → read back → verify → delete; create folder; list folder; copy; move; token refresh
- **Related Requirements**: FR1.7
- **Related Architecture**: CC1.6

### IT1.17–IT1.20: Backend Conformance Suites
- **Scope**: Run full conformance suite against each real backend
- **What is being tested**: `run_conformance_suite(S3Storage(...))`, etc. → all applicable tests pass; `skip_unsupported=True` for ops that backend cannot do
- **Related Requirements**: FR1.19
- **Related Architecture**: CC1.13

---

## Application Tests (AT) — Selected Detail

### AT1.1: FastAPI File Upload/Download
- **Scope**: File operations through FastAPI endpoint using storage backend
- **What is being tested**: POST file → stored via backend; GET file → returned; DELETE file → removed; uses TestClient
- **Related Requirements**: FR1.15
- **Related Architecture**: CC1.12

### AT1.4: Backend Switch Via Config
- **Scope**: Switch backend type via config without code change
- **What is being tested**: Write file with local backend → switch config to mock backend → write file → both backends have expected state; demonstrates config-driven backend selection
- **Related Requirements**: FR1.8, BO1.3
- **Related Architecture**: CC1.7

---

## Security Tests (QT) — Selected Detail

### QT1.1: Path Traversal Attack
- **Scope**: Verify path traversal is blocked
- **What is being tested**: `../../etc/passwd` → sanitised or rejected; `%2e%2e/` URL encoding → blocked; `/valid/../../../escape` → blocked; all backends
- **Related Requirements**: FR1.12, CS1.1
- **Related Architecture**: CC1.9

### QT1.2: Credential Redaction in Logs
- **Scope**: Verify credentials never appear in log output
- **What is being tested**: Enable logging → perform S3/WebDAV/FTP/Google Drive operations → capture log output → grep for access_key, secret_key, password, refresh_token → zero matches
- **Related Requirements**: FR1.16, CS1.2
- **Related Architecture**: CC1.11, observability/logging.py

### QT1.4: Root Boundary Escape
- **Scope**: Verify local storage root boundary cannot be escaped
- **What is being tested**: LocalStorage(root="/tmp/test") → read_bytes("/tmp/test/../../etc/passwd") → `StoragePermissionError`; symlink outside root → blocked
- **Related Requirements**: FR1.12, CS1.1
- **Related Architecture**: CC1.2, CC1.9

---

## Test Summary

| Tier | Count | Scope |
|------|------:|-------|
| **UT** | 32 | Unit tests — backends, config, errors, models, factory, security |
| **ST** | 10 | System tests — full lifecycle, config round-trip, conformance, Vault |
| **IT** | 20 | Integration tests — real S3, WebDAV, FTP, Google Drive (env-gated) |
| **AT** | 5 | Application tests — FastAPI integration, backend switching |
| **QT** | 5 | Security tests — traversal, credential redaction, TLS, boundary, null byte |
| **Total** | **72** | |

---

## Test Run Commands

```bash
# UT only (no external services required)
pytest tests/ -v --env UT

# ST (local filesystem only)
pytest tests/ -v --env ST

# IT (requires real services — source Vault env first)
set -a; source <your-vault-env-file>; set +a
pytest tests/ -v --env IT

# AT (FastAPI test client)
pytest tests/ -v --env AT

# QT (security tests)
pytest tests/ -v --env QT

# Full matrix
set -a; source <your-vault-env-file>; set +a
pytest tests/ -v --env UT --env ST --env IT --env AT --env QT

# Lint + format
ruff check cloud_dog_storage tests
ruff format --check cloud_dog_storage tests
```
