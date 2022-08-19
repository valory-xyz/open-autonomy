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

"""Tests for service specification."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest
import yaml

from autonomy.deploy.base import ServiceSpecification

from tests.test_autonomy.base import get_dummy_service_config


def get_keys() -> List[Dict]:
    """Get service keys."""

    return [
        {
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "private_key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        },
        {
            "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "private_key": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
        },
    ]


class TestServiceSpecification:
    """Test `ServiceSpecification` class."""

    t: Path
    cwd: Path
    keys_path: Path
    service_path: Path

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup test."""
        cls.cwd = Path.cwd()

        cls.t = Path(tempfile.TemporaryDirectory().name)
        cls.t.mkdir()

        cls.service_path = cls.t / "dummy_service"
        cls.service_path.mkdir()

        cls.keys_path = cls.t / "keys.json"
        cls.keys_path.write_text(json.dumps(get_keys()[0:1]))

    def _write_service(self, data: List[Dict]) -> None:
        """Write service config to a file."""
        with open(self.service_path / "service.yaml", "w+") as fp:
            yaml.dump_all(data, fp)

    def test_initialize(
        self,
    ) -> None:
        """Test service spec initialization."""

        self._write_service(get_dummy_service_config())
        spec = ServiceSpecification(
            self.service_path,
            self.keys_path,
        )

        agents = spec.generate_agents()
        assert len(agents) == 1, agents

        agent = spec.generate_agent(0)
        assert len(agent.keys()) == 20, agent

        spec.service.overrides = []
        agent = spec.generate_agent(0)
        assert len(agent.keys()) == 7, agent

    def test_set_number_of_agents(
        self,
    ) -> None:
        """Test service spec initialization."""

        self._write_service(get_dummy_service_config())

        with pytest.raises(
            ValueError, match="Number of agents cannot be greater than available keys"
        ):
            ServiceSpecification(
                self.service_path,
                self.keys_path,
                number_of_agents=2,
            )

    def test_key_load_failure(
        self,
    ) -> None:
        """Test service spec initialization."""

        self._write_service(get_dummy_service_config())

        self.keys_path.write_text(
            json.dumps(
                [
                    {
                        "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                    }
                ]
            )
        )

        with pytest.raises(ValueError, match="Key file incorrectly formatted"):

            ServiceSpecification(
                self.service_path,
                self.keys_path,
                number_of_agents=2,
            )

    def test_agent_instances(
        self,
    ) -> None:
        """Test agent_instance initialization."""

        agent_instances = [
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        ]

        self._write_service(get_dummy_service_config())
        spec = ServiceSpecification(
            self.service_path, self.keys_path, agent_instances=agent_instances
        )
        agents = spec.generate_agents()
        assert len(agents) == 1

        with pytest.raises(
            ValueError,
            match="Cannot find the provided keys in the list of the agent instances",
        ):
            ServiceSpecification(self.service_path, self.keys_path, agent_instances=[])

    @classmethod
    def teardown(
        cls,
    ) -> None:
        """Teardown test."""

        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)
