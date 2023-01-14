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

"""Tests package for the 'deployments' functionality."""
import json
import os
import re
import shutil
import tempfile
from abc import ABC
from contextlib import suppress
from glob import glob
from pathlib import Path
from typing import Any, List, Tuple, cast
from unittest import mock

import pytest
import yaml
from aea.configurations.data_types import PublicId
from aea.exceptions import AEAValidationError

from autonomy.configurations.base import Service
from autonomy.configurations.validation import ConfigValidator
from autonomy.constants import (
    AUTONOMY_IMAGE_VERSION,
    HARDHAT_IMAGE_VERSION,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.base import (
    BaseDeploymentGenerator,
    NotValidKeysFile,
    ServiceBuilder,
)
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.kubernetes.base import KubernetesGenerator

from tests.conftest import ROOT_DIR, skip_docker_tests


deployment_generators: List[Any] = [
    DockerComposeGenerator,
    KubernetesGenerator,
]

DEPLOYMENT_SPEC_DIR = ROOT_DIR / "deployments" / "deployment_specifications"
DEFAULT_KEY_PATH = ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json"
PACKAGES_DIR = ROOT_DIR / "packages"

BASE_DEPLOYMENT: str = """name: "deployment_case"
author: "valory"
version: 0.1.0
description: Description
aea_version: ">=1.0.0, <2.0.0"
license: Apache-2.0
agent: valory/oracle:0.1.0:bafybeihurloujnbugvvrv5xegyrdnsgl6z6at5xilq7f5ynjdekijapt6q
number_of_agents: 1
fingerprint: {}
fingerprint_ignore_patterns: []
"""

LIST_SKILL_OVERRIDE: str = """public_id: valory/price_estimation_abci:0.1.0
type: skill
0:
  models:
    price_api:
      args:
        url: 'https://api.coingecko.com/api/v3/simple/price'
        api_id: 'coingecko'
        parameters:
        - - ids
          - bitcoin
        - - vs_currencies
          - usd
        response_key: 'bitcoin:usd'
        headers: ~
1:
  models:
    price_api:
      args:
        url: 'https://api.coingecko.com/api/v3/simple/price'
        api_id: 'coingecko'
        parameters:
        - - ids
          - bitcoin
        - - vs_currencies
          - usd
        response_key: 'bitcoin:usd'
        headers: ~
"""
SKILL_OVERRIDE: str = """public_id: valory/price_estimation_abci:0.1.0
type: skill
models:
  price_api:
    args:
      url: ''
      api_id: ''
      headers: ''
      parameters: ''
      response_key: ''
  randomness_api:
    args:
      url: ""
      api_id: ""
"""
CONNECTION_OVERRIDE: str = """public_id: valory/ledger:0.19.0
type: connection
config:
  ledger_apis:
    ethereum:
      address: 'http://hardhat:8545'
      chain_id: '31337'
"""

TEST_DEPLOYMENT_PATH: str = "service.yaml"
IMAGE_VERSIONS = {
    "agent": AUTONOMY_IMAGE_VERSION,
    "hardhat": HARDHAT_IMAGE_VERSION,
    "tendermint": TENDERMINT_IMAGE_VERSION,
}


def get_specified_deployments() -> List[str]:
    """Returns a list specified deployments."""
    return glob(str(DEPLOYMENT_SPEC_DIR / "*.yaml"))


def get_valid_deployments() -> List[str]:
    """Returns a list of valid deployments as string."""
    return [
        "---\n".join([BASE_DEPLOYMENT]),
        "---\n".join([BASE_DEPLOYMENT, CONNECTION_OVERRIDE]),
        "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE]),
        "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE, CONNECTION_OVERRIDE]),
    ]


class CleanDirectoryClass:
    """
    Loads the default aea into a clean temp directory and cleans up after.

    Used when testing code which leaves artifacts
    """

    working_dir: Path
    deployment_path = Path(ROOT_DIR) / "deployments"
    old_cwd = None

    def setup(self) -> None:
        """Sets up the working directory for the test method."""
        self.old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as path:
            self.working_dir = Path(path)
        shutil.copytree(self.deployment_path, self.working_dir)
        os.chdir(self.working_dir)

    def teardown(self) -> None:
        """Removes the over-ride"""
        shutil.rmtree(str(self.working_dir), ignore_errors=True)
        os.chdir(str(self.old_cwd))


class BaseDeploymentTests(ABC, CleanDirectoryClass):
    """Base pytest class for setting up Docker images."""

    deployment_spec_path: str
    temp_dir: tempfile.TemporaryDirectory
    validator: ConfigValidator

    @classmethod
    def setup_class(cls) -> None:
        """Setup up the test class."""
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.validator = ConfigValidator(Service.schema)

    @classmethod
    def teardown_class(cls) -> None:
        """Setup up the test class."""
        with suppress(FileNotFoundError, OSError, PermissionError):
            cls.temp_dir.cleanup()

    def write_deployment(
        self,
        app: str,
    ) -> str:
        """Write the deployment to the local directory."""
        with open(
            str(self.working_dir / TEST_DEPLOYMENT_PATH), "w", encoding="utf8"
        ) as f:
            f.write(app)

        return str(self.working_dir / TEST_DEPLOYMENT_PATH)

    def load_deployer_and_app(
        self, app: str, deployer: BaseDeploymentGenerator
    ) -> Tuple[BaseDeploymentGenerator, ServiceBuilder]:
        """Handles loading the 2 required instances"""
        app_instance = ServiceBuilder.from_dir(
            path=Path(app).parent,
            keys_file=DEFAULT_KEY_PATH,
        )
        instance = deployer(service_builder=app_instance, build_dir=self.temp_dir.name)  # type: ignore
        return instance, app_instance


class TestDockerComposeDeployment(BaseDeploymentTests):
    """Test class for DOcker-compose Deployment."""

    deployment_generator = DockerComposeGenerator

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""
        for spec in get_valid_deployments():
            if spec.find("ropsten") < 0:
                continue
            spec_path = self.write_deployment(spec)
            instance, app_instance = self.load_deployer_and_app(
                spec_path, self.deployment_generator  # type: ignore
            )
            output = instance.generate(app_instance)  # type: ignore
            containers = yaml.safe_load(output)["services"]
            assert "hardhat" not in containers.keys()


class TestKubernetesDeployment(BaseDeploymentTests):
    """Test class for Kubernetes Deployment."""

    deployment_generator = KubernetesGenerator

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""
        for spec in get_valid_deployments():
            if spec.find("ropsten") < 0:
                continue
            spec_path = self.write_deployment(spec)
            instance, app_instance = self.load_deployer_and_app(
                spec_path, self.deployment_generator  # type: ignore
            )
            output = instance.generate(app_instance)  # type: ignore
            resource_names = []
            for resource_yaml in yaml.safe_load_all(output):
                resource_names.append(resource_yaml["metadata"]["name"])
            assert "hardhat" not in resource_names


class TestDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_read_invalid_keys_file(self) -> None:
        """Test JSONDecodeError on read_keys"""

        side_effect = json.decoder.JSONDecodeError("", "", 0)
        expected = "Error decoding keys file, please check the content of the file"
        with mock.patch.object(json, "loads", side_effect=side_effect):
            with pytest.raises(NotValidKeysFile, match=expected):
                ServiceBuilder.read_keys(mock.Mock(), DEFAULT_KEY_PATH)

    def test_update_agent_number_based_on_keys_file(self) -> None:
        """Test JSONDecodeError on read_keys"""

        public_id = PublicId("george", "hegel")
        service = Service(
            "arthur", "schopenhauer", public_id, number_of_agents=1_000_000
        )
        builder = ServiceBuilder(
            service=service,
            keys=None,
            private_keys_password=None,
            agent_instances=list("abcdefg"),
        )
        assert builder.service.number_of_agents == 1_000_000
        return_value = [dict(address="a", private_key="")]
        with mock.patch.object(json, "loads", return_value=return_value):
            builder.read_keys(mock.Mock())
        assert builder.service.number_of_agents == 1

    def test_generates_agent_for_all_valory_apps(self) -> None:
        """Test generator functions with all agent services."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = app_instance.generate_agent(0)
                assert len(res) >= 1

    def test_generates_agents_for_all_valory_apps(self) -> None:
        """Test functionality of the deployment generators."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = app_instance.generate_agents()
                assert len(res) >= 1, "failed to generate agents"


@skip_docker_tests
class TestTendermintDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_all_tendermint_configs(self) -> None:
        """Test functionality of the tendermint deployment generators."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                deployer_instance, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = deployer_instance.generate_config_tendermint()  # type: ignore
                assert (
                    len(cast(str, res.tendermint_job_config)) >= 1
                ), "Failed to generate Tendermint Config"


class TestCliTool(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_deploy_safe_contract(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                app_instance.generate_agent(0)

    def test_generates_deploy_oracle_contract(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                app_instance.generate_agent(0)

    def test_fails_to_generate_with_to_many_overrides(self) -> None:
        """Use a configuration with no overrides."""
        for deployment_generator in deployment_generators:
            spec_path = self.write_deployment(
                "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE, SKILL_OVERRIDE])
            )
            with pytest.raises(
                AEAValidationError,
                match=re.escape(
                    "Overrides for component (skill, valory/price_estimation_abci:0.1.0) are defined more than once"
                ),
            ):
                self.load_deployer_and_app(spec_path, deployment_generator)

    def test_generates_all_specified_apps(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec_path in get_specified_deployments():
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                app_instance.generate_agent(0)

    def test_generates_all_specified_deployments(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec_path in get_specified_deployments():
                deployment_instance, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                deployment_instance.generate(app_instance)  # type: ignore


class TestOverrideTypes(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_validates_with_singular_override(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            spec_path = self.write_deployment(
                "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE])
            )
            _, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            app_instance.service.check_overrides_valid(app_instance.service.overrides)

    def test_validates_with_list_override(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            deployment = yaml.safe_load(BASE_DEPLOYMENT)
            deployment["number_of_agents"] = 2
            spec_path = self.write_deployment(
                "---\n".join([yaml.safe_dump(deployment), LIST_SKILL_OVERRIDE])
            )
            _, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            app_instance.service.check_overrides_valid(app_instance.service.overrides)

    def test_validates_with_10_agents(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            deployment = yaml.safe_load(BASE_DEPLOYMENT)
            deployment["number_of_agents"] = 10
            spec_path = self.write_deployment(
                "---\n".join([yaml.safe_dump(deployment)])
            )
            deployment_instance, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            app_instance.service.check_overrides_valid(app_instance.service.overrides)
            app_instance.generate_agents()
            deployment_instance.generate()

    def test_validates_with_20_agents(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            deployment = yaml.safe_load(BASE_DEPLOYMENT)
            deployment["number_of_agents"] = 20
            spec_path = self.write_deployment(
                "---\n".join([yaml.safe_dump(deployment)])
            )
            deployment_instance, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            app_instance.service.check_overrides_valid(app_instance.service.overrides)
            app_instance.generate_agents()
            deployment_instance.generate()
