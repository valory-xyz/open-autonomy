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
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest
import yaml

from autonomy.configurations.loader import load_service_config


DUMMY_SERVICE = [
    {
        "name": "oracle_hardhat",
        "author": "valory",
        "version": "0.1.0",
        "description": "A set of agents implementing a price oracle",
        "aea_version": ">=1.0.0, <2.0.0",
        "license": "Apache-2.0",
        "fingerprint": {"README.md": "QmY4bupJmk4BKkFefNCWNEkj3kUtgmraSDNbWFDx4qgbZf"},
        "fingerprint_ignore_patterns": [],
        "agent": "valory/oracle:0.1.0:QmXuaeUagpuJ4cRiBHTX9ydSnibPyEbdL23zmGyUuWwMYr",
        "network": "hardhat",
        "number_of_agents": 1,
    },
    {
        "public_id": "valory/oracle_abci:0.1.0",
        "type": "skill",
        "models": {
            0: [
                {
                    "price_api": {
                        "args": {
                            "url": "url",
                            "api_id": "api_id",
                            "parameters": None,
                            "response_key": None,
                            "headers": None,
                        }
                    }
                },
                {
                    "randomness_api": {
                        "args": {
                            "url": "https://drand.cloudflare.com/public/latest",
                            "api_id": "cloudflare",
                        }
                    }
                },
                {
                    "params": {
                        "args": {
                            "observation_interval": 30,
                            "broadcast_to_server": False,
                            "service_registry_address": "address",
                            "on_chain_service_id": 1,
                        }
                    }
                },
                {"server_api": {"args": {"url": "url"}}},
                {"benchmark_tool": {"args": {"log_dir": "/benchmarks"}}},
            ]
        },
    },
]


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
        dummy_service = DUMMY_SERVICE.copy()
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

        dummy_service = DUMMY_SERVICE.copy()
        dummy_service[0]["number_of_agents"] = 4
        self._write_service(dummy_service)

        with pytest.raises(ValueError, match="Not enough items in override"):
            load_service_config(self.t)

        dummy_service = DUMMY_SERVICE.copy()
        dummy_service[1]["models"]["1"] = []  # type: ignore
        self._write_service(dummy_service)

        with pytest.raises(
            ValueError, match="All keys of list like override should be of type int."
        ):
            load_service_config(self.t)

    @classmethod
    def teardown(
        cls,
    ) -> None:
        """Teardown class."""

        os.chdir(cls.cwd)
        shutil.rmtree(cls.t)
