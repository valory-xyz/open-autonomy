# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
from aea.exceptions import AEAValidationError

from autonomy.configurations.loader import load_service_config

from tests.test_autonomy.base import get_dummy_service_config


class TestServiceConfig:
    """Test `Service` component."""

    cwd: Path
    t: Path
    service_file: Path

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup test."""

        cls.cwd = Path.cwd()
        cls.t = Path(tempfile.TemporaryDirectory().name)
        cls.t.mkdir()
        cls.service_file = cls.t / "service.yaml"

        os.chdir(cls.t)

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

    def test_check_overrides_valid(
        self,
    ) -> None:
        """Test check_overrides_valid method."""

        dummy_service = get_dummy_service_config()
        dummy_service[0]["number_of_agents"] = 4
        self._write_service(dummy_service)

        with pytest.raises(ValueError, match="Not enough items in override"):
            load_service_config(self.t)

        dummy_service = get_dummy_service_config()
        dummy_service[1]["models"]["1"] = []  # type: ignore
        self._write_service(dummy_service)

        with pytest.raises(
            ValueError, match="All keys of list like override should be of type int."
        ):
            load_service_config(self.t)

        dummy_service = get_dummy_service_config()
        dummy_service.append(dummy_service[1])
        self._write_service(dummy_service)

        with pytest.raises(
            ValueError,
            match=re.escape(
                "Configuration of component (skill, valory/oracle_abci:0.1.0) occurs more than once."
            ),
        ):
            load_service_config(self.t)

    def test_env_vars(
        self,
    ) -> None:
        """Test if env vars are properly loaded."""

        env_placeholder = "${NUMBER_OF_AGENTS:int:1}"
        dummy_service = get_dummy_service_config()
        dummy_service[0]["number_of_agents"] = env_placeholder

        self._write_service(dummy_service)

        with pytest.raises(
            AEAValidationError,
            match=re.escape("'${NUMBER_OF_AGENTS:int:1}' is not of type 'integer'"),
        ):
            load_service_config(self.t)

        dummy_service = get_dummy_service_config()
        dummy_service[0]["number_of_agents"] = env_placeholder

        self._write_service(dummy_service)

        service = load_service_config(self.t, substitute_env_vars=True)
        assert service.number_of_agents == 1

    @classmethod
    def teardown(
        cls,
    ) -> None:
        """Teardown class."""

        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)
