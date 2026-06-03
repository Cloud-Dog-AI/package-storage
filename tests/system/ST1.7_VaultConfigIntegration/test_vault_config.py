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
Description: ST1.7: Config delegation integration (cloud_dog_config) (env-gated).
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cloud_dog_storage.config.models import StorageConfig


def test_cloud_dog_config_bind_model_if_available(vault_env, tmp_path: Path) -> None:
    _ = vault_env
    try:
        from cloud_dog_config import bind_model, get_config, load_config  # type: ignore
    except Exception:
        pytest.skip("cloud_dog_config not installed")

    defaults = tmp_path / "defaults.yaml"
    defaults.write_text(
        "storage:\n  backend: local\n  root_path: /tmp\n",
        encoding="utf-8",
    )
    load_config(defaults_yaml=str(defaults), config_yaml=str(tmp_path / "config.yaml"), vault_enabled=False)

    cfg = bind_model(get_config(), "storage", StorageConfig)
    assert isinstance(cfg, StorageConfig)


def test_package_has_no_vault_modules() -> None:
    base = Path(__file__).resolve().parents[3] / "cloud_dog_storage"
    assert not (base / "config" / "vault.py").exists()
    assert not (base / "secrets").exists()
