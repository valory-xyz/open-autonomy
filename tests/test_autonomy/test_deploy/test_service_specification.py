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
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from autonomy.deploy.base import (
    ABCI_HOST,
    ENV_VAR_ABCI_HOST,
    ENV_VAR_AEA_AGENT,
    ENV_VAR_AEA_PASSWORD,
    ENV_VAR_ID,
    ENV_VAR_LOG_LEVEL,
    ENV_VAR_MAX_PARTICIPANTS,
    ENV_VAR_TENDERMINT_COM_URL,
    ENV_VAR_TENDERMINT_URL,
    NotValidKeysFile,
    ServiceBuilder,
)

from tests.test_autonomy.base import get_dummy_service_config


COMMON_VARS = (
    ENV_VAR_ID,
    ENV_VAR_AEA_AGENT,
    ENV_VAR_ABCI_HOST,
    ENV_VAR_MAX_PARTICIPANTS,
    ENV_VAR_TENDERMINT_URL,
    ENV_VAR_TENDERMINT_COM_URL,
    ENV_VAR_LOG_LEVEL,
    ENV_VAR_AEA_PASSWORD,
)
DUMMY_CONTRACT_ADDRESS = "0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


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


class TestServiceBuilder:
    """Test `ServiceBuilder` class."""

    t: Path
    cwd: Path
    keys_path: Path
    service_path: Path

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

        self.service_path = self.t / "dummy_service"
        self.service_path.mkdir()

        self.keys_path = self.t / "keys.json"
        self.keys_path.write_text(json.dumps(get_keys()[0:1]))

    def _write_service(self, data: List[Dict]) -> None:
        """Write service config to a file."""
        with open(self.service_path / "service.yaml", "w+") as fp:
            yaml.dump_all(data, fp)

    def test_initialize(
        self,
    ) -> None:
        """Test service spec initialization."""

        self._write_service(get_dummy_service_config(file_number=1))
        spec = ServiceBuilder.from_dir(
            self.service_path,
            self.keys_path,
        )

        assert spec.private_keys_password is None
        assert spec.agent_instances is None
        assert len(spec.keys) == 1

    def test_generate_agents(
        self,
    ) -> None:
        """Test service spec initialization."""

        self._write_service(get_dummy_service_config(file_number=1))
        spec = ServiceBuilder.from_dir(
            self.service_path,
            self.keys_path,
        )

        agents = spec.generate_agents()
        assert len(agents) == 1, agents

        agent = spec.generate_agent(0)
        assert len(agent.keys()) == 14, agent

        spec.service.overrides = []
        agent = spec.generate_agent(0)
        assert len(agent.keys()) == 7, agent

    def test_generate_common_vars(
        self,
    ) -> None:
        """Test service spec initialization."""

        self._write_service(get_dummy_service_config(file_number=1))
        spec = ServiceBuilder.from_dir(
            self.service_path,
            self.keys_path,
        )

        common_vars_without_password = spec.generate_common_vars(agent_n=0)
        assert all(var in common_vars_without_password for var in COMMON_VARS[:-1])
        assert common_vars_without_password[ENV_VAR_AEA_AGENT] == spec.service.agent
        assert common_vars_without_password[ENV_VAR_ABCI_HOST] == ABCI_HOST.format(0)

        spec = ServiceBuilder.from_dir(  # nosec
            self.service_path,
            self.keys_path,
            private_keys_password="some_password",
        )
        common_vars_without_password = spec.generate_common_vars(agent_n=0)
        assert all(var in common_vars_without_password for var in COMMON_VARS)

    def test_agent_instance_setter(
        self,
        caplog: Any,
    ) -> None:
        """Test agent instance setter."""

        self._write_service(get_dummy_service_config(file_number=1))
        spec = ServiceBuilder.from_dir(
            self.service_path,
            self.keys_path,
        )

        with pytest.raises(
            NotValidKeysFile,
            match="Key file contains keys which are not registered as instances",
        ):
            spec.agent_instances = []

        with caplog.at_level(logging.WARNING):
            spec.agent_instances = [
                "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                "0xDummyaddress",
            ]
            assert (
                "Key file does not contain key pair for following instances {'0xDummyaddress'}"
                in caplog.text
            )

        with caplog.at_level(logging.INFO):
            spec.agent_instances = [
                "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            ]
            assert (
                "Found following keys with registered instances {'0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'}"
                in caplog.text
            )

    def test_try_update_runtime_params_failure(self, caplog: Any) -> None:
        """Test `try_update_runtime_params` method."""
        multisig_address = "0xMULTISIGADDRESS"
        self._write_service(get_dummy_service_config(file_number=4))
        spec = ServiceBuilder.from_dir(
            self.service_path,
        )

        with caplog.at_level(logging.WARNING):
            spec.try_update_runtime_params(multisig_address=multisig_address)

            assert "Could not update the setup parameter for" in caplog.text

    def test_try_update_runtime_params_singular(
        self,
    ) -> None:
        """Test `try_update_runtime_params` method."""
        multisig_address = "0xMULTISIGADDRESS"
        agent_instances = [f"0xagent{i}" for i in range(4)]

        self._write_service(get_dummy_service_config(file_number=1))
        spec = ServiceBuilder.from_dir(
            self.service_path,
            self.keys_path,
        )

        skill_config, *_ = spec.service.overrides
        assert skill_config["models"]["params"]["args"]["setup"][
            "safe_contract_address"
        ] == [DUMMY_CONTRACT_ADDRESS]

        spec.try_update_runtime_params(
            multisig_address=multisig_address,
            agent_instances=agent_instances,
        )
        skill_config, *_ = spec.service.overrides
        assert skill_config["models"]["params"]["args"]["setup"][
            "safe_contract_address"
        ] == [multisig_address]
        assert skill_config["models"]["params"]["args"]["setup"][
            "all_participants"
        ] == [agent_instances]

    def test_try_update_runtime_params_multiple(
        self,
    ) -> None:
        """Test `try_update_runtime_params` method."""
        multisig_address = "0xMULTISIGADDRESS"
        agent_instances = [f"0xagent{i}" for i in range(4)]

        self._write_service(get_dummy_service_config(file_number=2))
        spec = ServiceBuilder.from_dir(
            self.service_path,
        )

        spec.try_update_runtime_params(
            multisig_address=multisig_address, agent_instances=agent_instances
        )
        skill_config, *_ = spec.service.overrides

        for agent_idx in range(spec.service.number_of_agents):
            assert skill_config[agent_idx]["models"]["params"]["args"]["setup"][
                "safe_contract_address"
            ] == [multisig_address]
            assert skill_config[agent_idx]["models"]["params"]["args"]["setup"][
                "all_participants"
            ] == [agent_instances]

    def test_verify_agent_instances(
        self,
        caplog: Any,
    ) -> None:
        """Test `verify_agent_instances` method."""

        with pytest.raises(
            NotValidKeysFile,
            match=re.escape(
                "Key file contains keys which are not registered as instances; invalid keys={'0xaddress0'}"
            ),
        ):
            ServiceBuilder.verify_agent_instances([{"address": "0xaddress0"}], [])

        with caplog.at_level(logging.WARNING):
            ServiceBuilder.verify_agent_instances(
                [{"address": "0xaddress0"}], ["0xaddress0", "0xaddress1"]
            )
            assert (
                "Key file does not contain key pair for following instances {'0xaddress1'}"
                in caplog.text
            )

        with caplog.at_level(logging.INFO):
            ServiceBuilder.verify_agent_instances(
                [{"address": "0xaddress0"}], ["0xaddress0"]
            )
            assert (
                "Found following keys with registered instances {'0xaddress0'}"
                in caplog.text
            )

    def test_set_number_of_agents(
        self,
    ) -> None:
        """Test service spec initialization."""

        self._write_service(get_dummy_service_config())

        with pytest.raises(
            NotValidKeysFile,
            match="Number of agents cannot be greater than available keys",
        ):
            ServiceBuilder.from_dir(
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

        with pytest.raises(NotValidKeysFile, match="Key file incorrectly formatted"):
            ServiceBuilder.from_dir(
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
        spec = ServiceBuilder.from_dir(
            self.service_path, self.keys_path, agent_instances=agent_instances
        )
        agents = spec.generate_agents()
        assert len(agents) == 1

        with pytest.raises(
            NotValidKeysFile,
            match="Key file contains keys which are not registered as instances",
        ):
            ServiceBuilder.from_dir(
                self.service_path, self.keys_path, agent_instances=[]
            )

    def teardown(
        self,
    ) -> None:
        """Teardown test."""
        os.chdir(self.cwd)
        shutil.rmtree(self.t)
