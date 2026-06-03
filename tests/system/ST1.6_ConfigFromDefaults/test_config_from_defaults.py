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
Description: ST1.6: StorageConfig model validation from defaults.yaml.
Standard: PS-85 (Storage Interfaces), PS-95 (Testing)
**************************************************
"""

from __future__ import annotations

from pathlib import Path

import yaml

from cloud_dog_storage.config.models import StorageConfig


def test_defaults_yaml_loads_and_validates() -> None:
    defaults = Path(__file__).resolve().parents[3] / "defaults.yaml"
    raw = yaml.safe_load(defaults.read_text(encoding="utf-8"))
    cfg = StorageConfig.model_validate(raw["storage"])
    assert cfg.backend == "local"
    assert cfg.timeout_s == 30
