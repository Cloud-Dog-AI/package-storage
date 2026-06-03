# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Shared test configuration and fixtures for cloud_dog_storage.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_VAULT_VARS = ("VAULT_ADDR", "VAULT_TOKEN", "VAULT_MOUNT_POINT", "VAULT_CONFIG_PATH")
_VAULT_EXPR_RE = re.compile(r"\$\{\s*vault\.([a-zA-Z0-9_.-]+)\s*\}")
if str(PROJECT_ROOT) not in sys.path:
    # Ensure tests import the in-repo package instead of any stale site-package install.
    sys.path.insert(0, str(PROJECT_ROOT))


def _request_tier(request: pytest.FixtureRequest) -> str | None:
    """Infer test tier from test path."""
    parts = Path(str(request.node.fspath)).parts
    if "unit" in parts:
        return "UT"
    if "system" in parts:
        return "ST"
    if "integration" in parts:
        return "IT"
    if "application" in parts:
        return "AT"
    if "security" in parts:
        return "QT"
    return None


def _fail_or_skip_for_missing_external(request: pytest.FixtureRequest, message: str) -> None:
    """IT/AT/QT must fail when external dependencies are unavailable."""
    tier = _request_tier(request)
    if tier in {"IT", "AT", "QT"}:
        pytest.fail(message)
    pytest.skip(message)


def _env_truthy(key: str, default: str = "0") -> bool:
    return os.environ.get(key, default).strip().lower() in {"1", "true", "yes", "on"}


def _vault_payload() -> dict[str, Any] | None:
    if any(not os.environ.get(k) for k in REQUIRED_VAULT_VARS):
        return None
    url = (
        f"{os.environ['VAULT_ADDR'].rstrip('/')}/v1/"
        f"{os.environ['VAULT_MOUNT_POINT']}/data/{os.environ['VAULT_CONFIG_PATH']}"
    )
    raw = subprocess.check_output(
        ["curl", "-sS", "-H", f"X-Vault-Token: {os.environ['VAULT_TOKEN']}", url],
        text=True,
    )
    parsed = json.loads(raw)
    data = parsed.get("data", {}).get("data", {})
    if isinstance(data.get("json"), dict):
        return data["json"]
    if isinstance(data.get("content"), str):
        try:
            decoded = json.loads(data["content"])
            if isinstance(decoded, dict):
                return decoded
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def _resolve_vault_path(payload: dict[str, Any], path: str) -> Any:
    node: Any = payload
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(path)
        node = node[part]
    return node


def _resolve_env_value(raw: str, payload: dict[str, Any] | None) -> str:
    if "${" not in raw:
        return raw

    def _replace(match: re.Match[str]) -> str:
        if payload is None:
            return match.group(0)
        try:
            resolved = _resolve_vault_path(payload, match.group(1))
        except KeyError:
            return match.group(0)
        return "" if resolved is None else str(resolved)

    return _VAULT_EXPR_RE.sub(_replace, raw)


def _is_unresolved_vault(value: str | None) -> bool:
    if not value:
        return True
    return bool(_VAULT_EXPR_RE.search(value))


def pytest_addoption(parser):
    """Add --env option for test tier selection."""
    # `--env` is already used by other platform test plugins in this workspace.
    # When it is already registered, do not re-register it.
    try:
        parser.addoption(
            "--env",
            action="append",
            default=[],
            help="Test environment tiers to run: UT, ST, IT, AT, QT, or path to env file",
        )
    except ValueError:
        return


def _env_args(config) -> list[str]:  # type: ignore[no-untyped-def]
    raw = config.getoption("env")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return list(raw)


def _normalise_env_args_to_files(config) -> set[str]:  # type: ignore[no-untyped-def]
    """Expand tier tokens (UT/ST/IT/AT/QT) into env file paths for the workspace plugin."""
    tiers = {"UT", "ST", "IT", "AT", "QT"}
    args = _env_args(config)
    expanded: list[str] = []
    requested_tiers: set[str] = set()

    tests_dir = Path(__file__).resolve().parent
    for arg in args:
        token = arg.strip()
        upper = token.upper()
        if upper in tiers:
            requested_tiers.add(upper)
            expanded.append(str(tests_dir / f"env-{upper}"))
            continue
        expanded.append(token)
        name = Path(token).name.upper()
        if name.startswith("ENV-") and name[4:] in tiers:
            requested_tiers.add(name[4:])

    # Ensure downstream plugins see env file paths, not tier tokens.
    if hasattr(config, "option"):
        config.option.env = expanded
    return requested_tiers


def pytest_configure(config):
    """Load env files and enforce --env is supplied for every run (PS-95)."""
    requested_tiers = _normalise_env_args_to_files(config)
    config._cloud_dog_storage_requested_tiers = requested_tiers
    _load_env_files(config)
    if not _env_args(config):
        pytest.fail("Missing required --env argument (e.g. --env UT).")
    config.addinivalue_line("markers", "env: test environment tier")


def pytest_collection_modifyitems(config, items):
    """Skip tests not matching the requested --env tiers."""
    requested = getattr(config, "_cloud_dog_storage_requested_tiers", set())
    if not requested:
        requested = {e.upper() for e in _env_args(config) if not os.path.isfile(e)}
    # If only env files were provided, run everything (env-file selection is handled by file content).
    if not requested:
        requested = {"UT", "ST", "IT", "AT", "QT"}

    tier_map = {
        "unit": "UT",
        "system": "ST",
        "integration": "IT",
        "application": "AT",
        "security": "QT",
    }

    skip = pytest.mark.skip(reason="Not in requested --env tiers")
    skip_gdrive = _env_truthy("CLOUD_DOG_STORAGE_SKIP_GDRIVE", "1")
    gdrive_skip = pytest.mark.skip(reason="Google Drive integration tests are deferred by directive")

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
        if skip_gdrive and ("googledrive" in str(item.fspath).lower() or "gdrive" in item.name.lower()):
            item.add_marker(gdrive_skip)


def _load_env_files(config):
    """Source any env files passed via --env."""
    payload: dict[str, Any] | None = None
    for env_arg in _env_args(config):
        if os.path.isfile(env_arg):
            with open(env_arg) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, val = line.partition("=")
                        env_key = key.strip()
                        raw_value = val.strip()
                        if _VAULT_EXPR_RE.search(raw_value):
                            payload = payload or _vault_payload()
                        resolved = _resolve_env_value(raw_value, payload)
                        current = os.environ.get(env_key)
                        if current and not _is_unresolved_vault(current):
                            continue
                        os.environ[env_key] = resolved


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
def vault_env(request: pytest.FixtureRequest):
    """Validate Vault environment variables are set."""
    required = ["VAULT_ADDR", "VAULT_TOKEN", "VAULT_MOUNT_POINT"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        _fail_or_skip_for_missing_external(request, f"Vault env vars not set: {', '.join(missing)}")
    # Validate reachability quickly to avoid long hangs during external-service tests.
    addr = os.environ.get("VAULT_ADDR", "")
    try:
        parsed = urlparse(addr)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not host:
            raise ValueError("missing hostname")
        with socket.create_connection((host, port), timeout=1.5):
            pass
    except Exception:
        _fail_or_skip_for_missing_external(request, "Vault not reachable from this environment")
    return {k: os.environ[k] for k in required}


@pytest.fixture
def s3_env(request: pytest.FixtureRequest):
    """Validate S3 test environment."""
    required = ["TEST_S3_ENDPOINT", "TEST_S3_ACCESS_KEY", "TEST_S3_SECRET_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        _fail_or_skip_for_missing_external(request, f"S3 env vars not set: {', '.join(missing)}")

    bucket = os.environ.get("TEST_S3_BUCKET", "").strip()
    if not bucket:
        try:
            import boto3

            endpoint = os.environ["TEST_S3_ENDPOINT"]
            region = os.environ.get("TEST_S3_REGION", "us-east-1")
            client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=os.environ["TEST_S3_ACCESS_KEY"],
                aws_secret_access_key=os.environ["TEST_S3_SECRET_KEY"],
                region_name=region,
            )
            buckets = [b.get("Name", "").strip() for b in client.list_buckets().get("Buckets", [])]
            buckets = [b for b in buckets if b]
            if buckets:
                bucket = buckets[0]
            else:
                bucket = os.environ.get("TEST_S3_AUTOCREATE_BUCKET", "cloud-dog-storage-it")
                create_args: dict[str, Any] = {"Bucket": bucket}
                if region != "us-east-1":
                    create_args["CreateBucketConfiguration"] = {"LocationConstraint": region}
                client.create_bucket(**create_args)
        except Exception as exc:
            _fail_or_skip_for_missing_external(
                request,
                f"S3 bucket not configured and auto-discovery failed: {exc}",
            )
        os.environ["TEST_S3_BUCKET"] = bucket

    return {
        "TEST_S3_ENDPOINT": os.environ["TEST_S3_ENDPOINT"],
        "TEST_S3_BUCKET": os.environ["TEST_S3_BUCKET"],
        "TEST_S3_ACCESS_KEY": os.environ["TEST_S3_ACCESS_KEY"],
        "TEST_S3_SECRET_KEY": os.environ["TEST_S3_SECRET_KEY"],
    }


@pytest.fixture
def webdav_env(request: pytest.FixtureRequest):
    """Validate WebDAV test environment."""
    required = ["TEST_WEBDAV_URL", "TEST_WEBDAV_USERNAME", "TEST_WEBDAV_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        _fail_or_skip_for_missing_external(request, f"WebDAV env vars not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in required}


@pytest.fixture
def ftp_env(request: pytest.FixtureRequest):
    """Validate FTP test environment."""
    required = ["TEST_FTP_HOST", "TEST_FTP_USERNAME", "TEST_FTP_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        _fail_or_skip_for_missing_external(request, f"FTP env vars not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in required}


@pytest.fixture
def gdrive_env(request: pytest.FixtureRequest):
    """Validate Google Drive test environment."""
    if _env_truthy("CLOUD_DOG_STORAGE_SKIP_GDRIVE", "1"):
        pytest.skip("Google Drive integration tests are excluded for this run")
    required = [
        "TEST_GDRIVE_FOLDER_ID",
        "TEST_GDRIVE_CLIENT_ID",
        "TEST_GDRIVE_CLIENT_SECRET",
        "TEST_GDRIVE_REFRESH_TOKEN",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        _fail_or_skip_for_missing_external(request, f"Google Drive env vars not set: {', '.join(missing)}")
    return {k: os.environ[k] for k in required}
