"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Shared test configuration and fixtures for cloud_dog_storage.
Standard: PS-85, PS-95
**************************************************
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def pytest_addoption(parser):
    """Add --env option for test tier selection."""
    parser.addoption(
        "--env",
        action="append",
        default=[],
        help="Test environment tiers to run: UT, ST, IT, AT, QT, or path to env file",
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests not matching the requested --env tiers."""
    requested = {e.upper() for e in config.getoption("env") if not os.path.isfile(e)}
    if not requested:
        return

    tier_map = {
        "unit": "UT",
        "system": "ST",
        "integration": "IT",
        "application": "AT",
        "security": "QT",
    }

    skip = pytest.mark.skip(reason="Not in requested --env tiers")
    for item in items:
        parts = Path(item.fspath).parts
        tier = None
        for part in parts:
            low = part.lower()
            if low in tier_map:
                tier = tier_map[low]
                break
        if tier and tier not in requested:
            item.add_marker(skip)


def _load_env_files(config):
    """Source any env files passed via --env."""
    for env_arg in config.getoption("env"):
        if os.path.isfile(env_arg):
            with open(env_arg) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, val = line.partition("=")
                        os.environ.setdefault(key.strip(), val.strip())


def pytest_configure(config):
    """Load env files and register markers."""
    _load_env_files(config)
    config.addinivalue_line("markers", "env: test environment tier")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_storage_root(tmp_path):
    """Provide a temporary directory for local storage tests."""
    root = tmp_path / "storage_root"
    root.mkdir()
    return root


@pytest.fixture
def local_storage_config(tmp_storage_root):
    """Build a StorageConfig pointing to a temp local directory."""
    from cloud_dog_storage.config.models import StorageConfig

    return StorageConfig(backend="local", root_path=str(tmp_storage_root))


@pytest.fixture
def local_backend(tmp_storage_root):
    """Create a LocalStorage backend with a temp root."""
    from cloud_dog_storage.backends.local import LocalStorage

    return LocalStorage(root_path=tmp_storage_root)


@pytest.fixture
def mock_backend():
    """Create a MockStorageBackend for unit tests."""
    from cloud_dog_storage.testing.mock_backend import MockStorageBackend

    return MockStorageBackend()


@pytest.fixture
def vault_env():
    """Validate Vault environment variables are set. Skip if not."""
    required = ["VAULT_ADDR", "VAULT_TOKEN", "VAULT_MOUNT_POINT"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        pytest.skip(f"Vault env vars not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in required}


@pytest.fixture
def s3_env():
    """Validate S3 test environment. Skip if not configured."""
    required = ["TEST_S3_ENDPOINT", "TEST_S3_BUCKET", "TEST_S3_ACCESS_KEY", "TEST_S3_SECRET_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        pytest.skip(f"S3 env vars not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in required}


@pytest.fixture
def webdav_env():
    """Validate WebDAV test environment. Skip if not configured."""
    required = ["TEST_WEBDAV_URL", "TEST_WEBDAV_USERNAME", "TEST_WEBDAV_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        pytest.skip(f"WebDAV env vars not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in required}


@pytest.fixture
def ftp_env():
    """Validate FTP test environment. Skip if not configured."""
    required = ["TEST_FTP_HOST", "TEST_FTP_USERNAME", "TEST_FTP_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        pytest.skip(f"FTP env vars not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in required}


@pytest.fixture
def gdrive_env():
    """Validate Google Drive test environment. Skip if not configured."""
    required = [
        "TEST_GDRIVE_FOLDER_ID",
        "TEST_GDRIVE_CLIENT_ID",
        "TEST_GDRIVE_CLIENT_SECRET",
        "TEST_GDRIVE_REFRESH_TOKEN",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        pytest.skip(f"Google Drive env vars not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in required}
