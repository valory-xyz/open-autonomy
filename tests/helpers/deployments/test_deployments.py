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

"""Tests package for the 'deployments' functionality."""
import os
import shutil
import tempfile
from abc import ABC
from copy import deepcopy
from pathlib import Path
from typing import List, Tuple, Type

import yaml

from deployments.base_deployments import (
    APYEstimationDeployment,
    BaseDeployment,
    BaseDeploymentGenerator,
    CounterDeployment,
    PriceEstimationDeployment,
)
from deployments.generators.docker_compose.docker_compose import DockerComposeGenerator
from deployments.generators.kubernetes.kubernetes import KubernetesGenerator

from tests.helpers.constants import ROOT_DIR


class CleanDirectoryClass:
    """
    Loads the default aea into a clean temp directory and cleans up after.

    Used when testing code which leaves artifacts
    """

    working_dir = None
    deployment_path = Path(ROOT_DIR) / "deployments"

    def __init__(self) -> None:
        """Initialise the test."""
        self.old_cwd = ""

    def setup(self) -> None:
        """Sets up the working directory for the test method."""
        self.old_cwd = os.getcwd()
        self.working_dir = Path(tempfile.TemporaryDirectory().name)
        shutil.copytree(self.deployment_path, self.working_dir)
        os.chdir(self.working_dir)

    def teardown(self) -> None:
        """Removes the over-ride"""
        shutil.rmtree(str(self.working_dir), ignore_errors=True)
        os.chdir(str(self.old_cwd))


class BaseDeploymentTests(ABC):
    """Base pytest class for setting up Docker images."""

    app_config: dict

    @classmethod
    def setup_class(cls) -> None:
        """Setup up the test class."""
        cls.app_config = deepcopy(test_app_config)

    @classmethod
    def teardown_class(cls) -> None:
        """Setup up the test class."""

    def load_deployer_and_app(
        self, app: Type[BaseDeployment], deployer: Type[BaseDeploymentGenerator]
    ) -> Tuple[BaseDeploymentGenerator, BaseDeployment]:
        """Handles loading the 2 required instances"""
        instance = deployer(
            network=self.app_config["network"],
            number_of_agents=self.app_config["number_of_agents"],
        )  # type: ignore
        app_instance = app(**self.app_config)  # type: ignore
        return instance, app_instance


valory_apps: List[Type[BaseDeployment]] = [
    CounterDeployment,
    PriceEstimationDeployment,
    APYEstimationDeployment,
]

deployment_generators = [DockerComposeGenerator, KubernetesGenerator]

test_app_config = {
    "number_of_agents": 4,
    "network": "hardhat",
    "deploy_safe_contract": False,
    "deploy_oracle_contract": False,
}

test_deploy_config = {
    "number_of_agents": 4,
    "network": "hardhat",
}


class TestDockerComposeDeployment(BaseDeploymentTests):
    """Test class for DOcker-compose Deployment."""

    deployment_generator = DockerComposeGenerator

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""
        self.app_config["network"] = "ropsten"
        for app in valory_apps:
            instance, app_instance = self.load_deployer_and_app(
                app, self.deployment_generator
            )
            output = instance.generate(app_instance)  # type: ignore
            containers = yaml.safe_load(output)["services"]
            assert "hardhat" not in containers.keys()

    def test_creates_hardhat_deploy(self) -> None:
        """Required for deployment of hardhat."""
        self.app_config["network"] = "hardhat"
        for app in valory_apps:
            instance, app_instance = self.load_deployer_and_app(
                app, self.deployment_generator
            )
            output = instance.generate(app_instance)  # type: ignore
            containers = yaml.safe_load(output)["services"]
            assert "hardhat" in containers.keys()


class TestKubernetesDeployment(BaseDeploymentTests):
    """Test class for Kubernetes Deployment."""

    deployment_generator = KubernetesGenerator

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""
        self.app_config["network"] = "ropsten"
        for app in valory_apps:
            instance, app_instance = self.load_deployer_and_app(
                app, self.deployment_generator
            )
            output = instance.generate(app_instance)  # type: ignore
            for resource_yaml in yaml.safe_load_all(output):
                deployment_name = resource_yaml["metadata"]["name"]
                if deployment_name == "hardhat":
                    raise ValueError("Hardhat found in the deployment.")

    def test_creates_hardhat_deploy(self) -> None:
        """Required for deployment of hardhat."""
        self.app_config["network"] = "hardhat"
        for app in valory_apps:
            instance, app_instance = self.load_deployer_and_app(
                app, self.deployment_generator
            )
            output = instance.generate(app_instance)  # type: ignore
            for resource_yaml in yaml.safe_load_all(output):
                deployment_name = resource_yaml["metadata"]["name"]
                if deployment_name == "hardhat":
                    return
        raise ValueError("Hardhat Not found in the deployment.")


class TestDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_creates_hardhat_deploy(self) -> None:
        """Required for deployment of hardhat."""

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""

    def test_generates_agent_for_all_valory_apps(self) -> None:
        """Test generator functions with all valory apps."""
        for generator in valory_apps:
            instance = generator(
                number_of_agents=self.app_config["number_of_agents"],
                network=self.app_config["network"],
                deploy_safe_contract=self.app_config["deploy_safe_contract"],
                deploy_oracle_contract=self.app_config["deploy_oracle_contract"],
            )
            res = instance.generate_agent(0)
            assert len(res) >= 1

    def test_generates_agents_for_all_valory_apps(self) -> None:
        """Test functionality of the valory deployment generators."""
        for generator in valory_apps:
            instance = generator(
                number_of_agents=self.app_config["number_of_agents"],
                network=self.app_config["network"],
                deploy_safe_contract=self.app_config["deploy_safe_contract"],
                deploy_oracle_contract=self.app_config["deploy_oracle_contract"],
            )
            res = instance.generate_agents()
            assert len(res) > 1, "failed to generate agents"


class TestTendermintDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_agents_for_all_tendermint_configs(self) -> None:
        """Test functionality of the tendermint deployment generators."""
        for deployment_generator in deployment_generators:
            for app in valory_apps:
                instance, app_instance = self.load_deployer_and_app(
                    app, deployment_generator  # type: ignore
                )
                res = instance.generate_config_tendermint(app_instance)  # type: ignore
                assert len(res) > 1, "Failed to generate Tendermint Config"


class TestCliTool(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_all_tendermint_configs(self) -> None:
        """Test functionality of the tendermint deployment generators."""

        for deployment_generator in deployment_generators:
            for app in valory_apps:
                instance, app_instance = self.load_deployer_and_app(
                    app, deployment_generator  # type: ignore
                )
                res = instance.generate_config_tendermint(app_instance)  # type: ignore
                assert len(res) > 1, "Failed to generate Tendermint Config"
