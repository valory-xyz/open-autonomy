# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Test base configurations."""

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest
import yaml
from aea.configurations.data_types import PublicId
from aea.exceptions import AEAValidationError
from aea.helpers.io import open_file
from aea.helpers.yaml_utils import yaml_load_all

from autonomy.configurations.base import Service
from autonomy.configurations.loader import load_service_config

from tests.conftest import ROOT_DIR
from tests.test_autonomy.base import get_dummy_service_config


class TestServiceConfig:
    """Test `Service` component."""

    cwd: Path
    t: Path
    service_file: Path

    @classmethod
    def setup_class(
        cls,
    ) -> None:
        """Setup test class."""
        cls.cwd = Path.cwd()

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.t = Path(tempfile.TemporaryDirectory().name)
        self.t.mkdir()
        self.service_file = self.t / "service.yaml"

        os.chdir(self.t)

    def _write_service(self, data: List[Dict]) -> None:
        """Write service config to a file."""
        with open(self.service_file, "w+") as fp:
            yaml.dump_all(data, fp)

    def test_load_service(
        self,
    ) -> None:
        """Test load service."""
        dummy_service = get_dummy_service_config()
        self._write_service(dummy_service)

        service = load_service_config(self.t)
        for key, value in service.json.items():
            if key == "overrides":
                continue
            assert value == dummy_service[0][key]

    def test_check_overrides_valid_fail_missing_overrides(
        self,
    ) -> None:
        """Test check_overrides_valid method."""

        dummy_service = get_dummy_service_config(file_number=2)
        dummy_service[0]["number_of_agents"] = 6
        self._write_service(dummy_service)

        with pytest.raises(
            AEAValidationError,
            match=re.escape(
                "Not enough overrides for component (skill, valory/dummy_skill:0.1.0); Number of agents: 6"
            ),
        ):
            load_service_config(self.t)

    def test_check_repeatetive_overrides(
        self,
    ) -> None:
        """Test check_overrides_valid method."""

        dummy_service = get_dummy_service_config(file_number=2)
        (skill_config,) = [
            override for override in dummy_service if override.get("type") == "skill"
        ]
        dummy_service.append(skill_config)
        self._write_service(dummy_service)

        with pytest.raises(
            AEAValidationError,
            match=re.escape(
                "Overrides for component (skill, valory/dummy_skill:0.1.0) are defined more than once"
            ),
        ):
            load_service_config(self.t)

    def test_process_metadata(
        self,
    ) -> None:
        """Test process metadata."""

        _, component_override, _ = get_dummy_service_config(file_number=2)
        configuration, component_id, has_multiple_overrides = Service.process_metadata(
            component_override.copy()
        )

        assert has_multiple_overrides
        assert "public_id" not in configuration
        assert "type" not in configuration
        assert (
            PublicId.from_str(component_override["public_id"]) == component_id.public_id
        )

    def test_no_configuration_provided_for_agent_x(
        self,
    ) -> None:
        """Test process metadata."""

        service = Service(name="service", author="author", agent="valory/agent")
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Overrides not provided for agent 1; component=(skill, valory/skill:latest)"
            ),
        ):
            service.process_component_overrides(
                1, {"type": "skill", "public_id": "valory/skill"}
            )

    def test_env_vars(
        self,
    ) -> None:
        """Test if env vars are properly loaded."""

        env_placeholder = "${NUMBER_OF_AGENTS:int:1}"
        dummy_service = get_dummy_service_config()
        dummy_service[0]["number_of_agents"] = env_placeholder

        self._write_service(dummy_service)

        service = load_service_config(self.t, substitute_env_vars=True)
        assert service.number_of_agents == 1

    def teardown(
        self,
    ) -> None:
        """Teardown test."""
        os.chdir(self.cwd)
        shutil.rmtree(self.t)


@pytest.mark.parametrize(
    "service_file",
    Path(
        ROOT_DIR,
        "tests",
        "data",
        "dummy_service_config_files",
    ).iterdir(),
)
def test_load_service(service_file: Path) -> None:
    """Test loading and processing service component."""

    with open_file(service_file, "r", encoding="utf-8") as fp:
        data = yaml_load_all(fp)

    service_config, *overrides = data
    Service.validate_config_data(service_config)
    service_config["license_"] = service_config.pop("license")

    service = Service(**service_config)
    service.overrides = overrides
