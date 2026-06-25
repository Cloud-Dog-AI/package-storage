# Agent Instruction — Fix cloud_dog_storage

**Package:** `cloud_dog_storage`  
**Version:** 0.1.0 → 0.1.1  
**Date:** 2026-02-18 (post-build quality audit)  
**Scope:** 6 quality issues + QUALITY-GATE.md + PyPI publish  
**Estimated effort:** 1–2 hours

---

## Status: ⚠️ 6 ISSUES FOUND

Independent audit of the v0.1.0 build confirmed **all 26 source modules present, 78 tests pass, lint/format clean, config delegation clean**. The package is fundamentally solid — all 5 backend implementations are real (not stubs), with proper error handling, path sanitisation, and TLS configuration. The issues below are quality/consistency fixes, not architectural problems.

**Verified on 2026-02-18 (post-build audit):**

| Check | Result |
|-------|--------|
| **Source files** | ✅ **26 .py files** across 7 sub-packages |
| **Test directories** | ✅ **72 dirs** (32 UT + 10 ST + 20 IT + 5 AT + 5 QT) |
| **ruff check** | ✅ "All checks passed!" |
| **ruff format** | ✅ "99 files already formatted" |
| **Tests** | ✅ **78 passed, 21 skipped** (IT tests requiring live services) |
| **Config delegation** | ✅ Zero violations |
| **Build** | ✅ wheel + sdist in `dist/` |
| **Import** | ✅ `import-ok v0.1.0` |
| **QUALITY-GATE.md** | ❌ Missing |
| **PyPI** | ❌ Not published |

**Total outstanding: 6 code fixes + 1 new file + 1 publish = 8 items.**

---

## Governing Documents (read ALL before starting)

1. `packages/backend/AGENT-INSTRUCTION.md` — especially § Config Delegation, § Integrity Warranty
2. `packages/backend/platform-storage/REQUIREMENTS.md`
3. `packages/backend/platform-storage/ARCHITECTURE.md`
4. `packages/backend/platform-storage/TESTS.md`
5. `RULES.md`

---

## Issues to Fix (6 code items + 2 deliverables)

### Issue 1 — `datetime.utcnow()` deprecation (models.py:42)

**What:** `StoredFile.stored_at` default uses `datetime.utcnow` which is deprecated since Python 3.12 and returns a naive datetime.

**Where:** `cloud_dog_storage/models.py` line 42

**Current:**
```python
stored_at: datetime = field(default_factory=datetime.utcnow)
```

**Fix:**
```python
stored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

**Also add** `timezone` to the existing `datetime` import:
```python
from datetime import datetime, timezone
```

---

### Issue 2 — `ValueError` instead of `ConfigurationError` (factory.py:48)

**What:** Unknown backend type raises `ValueError` instead of the package's own `ConfigurationError`. This breaks the error taxonomy — consumers catching `StorageError` will not catch this.

**Where:** `cloud_dog_storage/factory.py` line 48

**Current:**
```python
raise ValueError(f"Unknown storage backend: {backend}")
```

**Fix:**
```python
raise ConfigurationError(f"Unknown storage backend: {backend}", backend_name=backend)
```

**Also add** `ConfigurationError` to the imports at the top of `factory.py`:
```python
from cloud_dog_storage.errors import ConfigurationError
```

---

### Issue 3 — SA1 module count incorrect in ARCHITECTURE.md

**What:** ARCHITECTURE.md line 72 says "Total modules: 22" but there are **26 .py files** (8 `__init__.py` + 18 functional modules). The count was wrong before (said 24) and was incorrectly adjusted when `vault.py` was removed.

**Where:** `ARCHITECTURE.md` line 72

**Fix:** Change `**Total modules: 22**` to `**Total modules: 26**` (including `__init__.py` files)

---

### Issue 4 — scaffold/pyproject.toml line-length inconsistency

**What:** `scaffold/pyproject.toml` has `line-length = 100` but the actual `pyproject.toml` (and all 7 other backend packages) use `line-length = 120`.

**Where:** `scaffold/pyproject.toml` line 48

**Fix:** Change `line-length = 100` to `line-length = 120`

---

### Issue 5 — `testing/fixtures.py` is minimal (22 lines, 1 function)

**What:** The fixtures module contains only `temp_storage_config()` — a single helper that duplicates what the `local_storage_config` fixture in `conftest.py` already provides. For a reusable library module, it should provide config builders for all 5 backends, not just local. Consumer projects will need S3/WebDAV/FTP/GDrive test config builders too.

**Where:** `cloud_dog_storage/testing/fixtures.py`

**What to do:**
1. Keep `temp_storage_config()` (local).
2. Add `s3_storage_config(endpoint, bucket, access_key, secret_key, **kwargs) -> StorageConfig`.
3. Add `webdav_storage_config(base_url, username, password, **kwargs) -> StorageConfig`.
4. Add `ftp_storage_config(host, username, password, **kwargs) -> StorageConfig`.
5. Add `gdrive_storage_config(folder_id, client_id, client_secret, refresh_token, **kwargs) -> StorageConfig`.
6. All builders should return `StorageConfig` with sensible defaults.

---

### Issue 6 — `backends/__init__.py` exports incomplete

**What:** `backends/__init__.py` (24 lines) should export all 5 backend classes for convenient imports like `from cloud_dog_storage.backends import S3Storage`. Check current exports match all backend classes.

**Where:** `cloud_dog_storage/backends/__init__.py`

**What to do:** Ensure `__all__` includes: `StorageBackend`, `LocalStorage`, `S3Storage`, `WebDavStorage`, `FtpStorage`, `GoogleDriveStorage`. Use lazy imports (or conditional TYPE_CHECKING imports) so optional dependencies are not required at import time — only the local backend should be eagerly imported.

---

### Issue 7 — Create QUALITY-GATE.md

**What:** All other built packages have a `QUALITY-GATE.md` documenting actual verification evidence. This was not created by the build agent.

**What to do:** Create `QUALITY-GATE.md` with the following sections:
1. **Package metadata** — name, version, date
2. **SA1 module layout** — 26/26 files present, list each
3. **Tests** — actual pytest output: 78 passed, 21 skipped, 0 failed
4. **Lint** — "All checks passed!"
5. **Format** — "99 files already formatted"
6. **Build** — wheel + sdist file names and sizes
7. **Config delegation** — grep result (zero hits)
8. **Import check** — `import-ok v0.1.0`

Run the verification commands to populate with **real, current output** after applying Issues 1–6. Do NOT copy/paste example output — run and capture.

---

### Issue 8 — Publish to PyPI

**What:** The v0.1.1 wheel must be published to the private PyPI registry.

**What to do:**
1. Bump version in `pyproject.toml` from `0.1.0` to `0.1.1`.
2. Bump version in `cloud_dog_storage/__init__.py` (`__version__`) from `0.1.0` to `0.1.1`.
3. Remove old `dist/` contents.
4. Build: `.venv/bin/python -m build --no-isolation`
5. Publish: `twine upload --repository-url https://pypi.cloud-dog.net/ -u admin -p StGeprge2008 dist/*`
6. Verify: `pip install --index-url https://pypi.cloud-dog.net/simple/ cloud_dog_storage==0.1.1`

---

## Execution Order

1. **Issue 1** — Fix `datetime.utcnow()` deprecation
2. **Issue 2** — Fix `ValueError` → `ConfigurationError` in factory
3. **Issue 3** — Fix SA1 module count in ARCHITECTURE.md
4. **Issue 4** — Fix scaffold pyproject.toml line-length
5. **Issue 5** — Expand `testing/fixtures.py` with all backend config builders
6. **Issue 6** — Fix `backends/__init__.py` exports
7. **Issue 7** — Create QUALITY-GATE.md (run verification commands, capture real output)
8. **Issue 8** — Bump version to 0.1.1, build, publish to PyPI

---

## Verification Commands (run ALL after every change)

```bash
cd /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/packages/backend/platform-storage

# 1. Config delegation check — MUST return zero hits
grep -rn "os.environ\|import hvac\|overlay_secrets\|from cloud_dog_storage.secrets" cloud_dog_storage/ --include="*.py" | grep -v __pycache__
# → zero results

# 2. Lint
.venv/bin/ruff check cloud_dog_storage tests

# 3. Format
.venv/bin/ruff format --check cloud_dog_storage tests

# 4. Tests
.venv/bin/pytest tests -v \
  --env UT --env ST --env AT --env QT \
  --env /opt/iac/Development/cloud-dog-ai/env-vault-admin

# 5. Build
.venv/bin/python -m build --no-isolation

# 6. Import check
.venv/bin/pip install --force-reinstall --no-deps dist/cloud_dog_storage-0.1.1-py3-none-any.whl
.venv/bin/python -c "import cloud_dog_storage; print(f'import-ok v{cloud_dog_storage.__version__}')"
```

---

## Done Criteria

You are done when **ALL** of the following are true:

1. `ruff check` passes — "All checks passed!"
2. `ruff format --check` passes — "0 files would be reformatted" (or "N files already formatted")
3. `pytest` shows **≥78 passed** (with `--env UT --env ST --env AT --env QT`)
4. `python -m build` produces a v0.1.1 wheel
5. All 78 previously passing tests still pass — **no test deletions or weakening**
6. `datetime.utcnow()` replaced with `datetime.now(timezone.utc)` in models.py
7. `factory.py` raises `ConfigurationError` (not `ValueError`) for unknown backend
8. ARCHITECTURE.md SA1 count reads "26"
9. `scaffold/pyproject.toml` line-length is 120
10. `testing/fixtures.py` has config builders for all 5 backends (≥5 functions, ≥60 lines)
11. `backends/__init__.py` exports all 5 backend classes + StorageBackend with lazy imports
12. QUALITY-GATE.md exists with **actual** (not fabricated) verification evidence
13. Published to `pypi.cloud-dog.net` as v0.1.1
14. Config delegation grep returns zero hits
15. `__version__` in `__init__.py` reads `"0.1.1"`
16. `pyproject.toml` version reads `"0.1.1"`

---

## Anti-Patterns (DO NOT)

1. **DO NOT** fabricate QUALITY-GATE.md output. Run the commands and capture actual results.
2. **DO NOT** delete or weaken any existing tests.
3. **DO NOT** change the public API (StorageBackend, build_storage_backend, error classes, data models).
4. **DO NOT** add `os.environ` reads, `import hvac`, or any Vault logic to library code.
5. **DO NOT** create a `config/vault.py` or `secrets/` module.
6. **DO NOT** change backend implementations beyond the specified fixes.
7. **DO NOT** add new dependencies to `pyproject.toml` `[project.dependencies]`.

---

## Key File Quick Reference

| File | Lines | Action |
|------|------:|--------|
| `cloud_dog_storage/models.py` | 55 | **FIX** — `datetime.utcnow()` → `datetime.now(timezone.utc)` |
| `cloud_dog_storage/factory.py` | 49 | **FIX** — `ValueError` → `ConfigurationError` + add import |
| `cloud_dog_storage/testing/fixtures.py` | 23 | **EXPAND** — add 4 more backend config builders |
| `cloud_dog_storage/backends/__init__.py` | 24 | **FIX** — ensure complete lazy exports |
| `ARCHITECTURE.md` | ~497 | **FIX** — module count 22 → 26 |
| `scaffold/pyproject.toml` | 64 | **FIX** — line-length 100 → 120 |
| `QUALITY-GATE.md` | — | **CREATE** — verification evidence |
| `pyproject.toml` | 64 | **UPDATE** — version 0.1.0 → 0.1.1 |
| `cloud_dog_storage/__init__.py` | 49 | **UPDATE** — `__version__` 0.1.0 → 0.1.1 |

---

## MANDATORY COMPLETION REPORT

When finished, write your report to:
**`/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/packages/backend/platform-storage/working/W28A-118-FIX-STORAGE-REPORT.md`**

Your report MUST include ALL of the following:

### 1. Run summary
- List every file changed and what was changed
- List every test fixed and how

### 2. Test results (REAL counts from actual runs)
```
QT: Xp / Yf
UT: Xp / Yf
ST: Xp / Yf
IT: Xp / Yf
AT: Xp / Yf
Ruff: X issues
```

### 3. Verdict
State one of: **PASS** (100% green) / **PARTIAL** (some fixed, some remain) / **FAIL** (no improvement) / **BLOCKED** (cannot proceed)

If not PASS, list every remaining failure with classification: `CODE_BUG`, `ENV_CONFIG`, `INFRA_MISSING`, `EXT_SERVICE`

### 4. Evidence logs
All logs MUST be saved to `working/` directory:
```
working/w28a-118-qt.log
working/w28a-118-ut.log
working/w28a-118-st.log
working/w28a-118-it.log
working/w28a-118-at.log
working/w28a-118-ruff.log
```

### 5. RULES.md COMPLIANCE WARRANTY

Copy this EXACTLY into your report:
```
I warrant that:
1. I have read RULES.md IN FULL before starting work
2. ALL code I produced is 100% compliant with RULES.md
3. ALL test results reported are REAL — exact counts from actual runs
4. I have NOT weakened any test
5. I have NOT stored, copied, or exposed any credentials
6. ALL credentials come from Vault or git-ignored env files
7. I have NOT modified files outside this package
```
