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
from pathlib import Path
from typing import Dict, List, Tuple, Any

import yaml

from deployments.base_deployments import BaseDeployment, BaseDeploymentGenerator
from deployments.generators.docker_compose.docker_compose import DockerComposeGenerator
from deployments.generators.kubernetes.kubernetes import KubernetesGenerator

from tests.helpers.constants import ROOT_DIR


deployment_generators: List[Any] = [
    DockerComposeGenerator,
    KubernetesGenerator,
]

test_deployment_spec_paths: Dict[str, str] = {
    "case_hardhat": "./deployments/deployment_specifications/price_estimation_hardhat.yaml",
    "case_ropsten": "./deployments/deployment_specifications/price_estimation_ropsten.yaml",
}

os.chdir(ROOT_DIR)


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

    deployment_spec_path: str

    @classmethod
    def setup_class(cls) -> None:
        """Setup up the test class."""

    @classmethod
    def teardown_class(cls) -> None:
        """Setup up the test class."""

    @staticmethod
    def load_deployer_and_app(
        app: str, deployer: BaseDeploymentGenerator
    ) -> Tuple[BaseDeploymentGenerator, BaseDeployment]:
        """Handles loading the 2 required instances"""
        app_instance = BaseDeployment(path_to_deployment_spec=app)
        instance = deployer(deployment_spec=app_instance)  # type: ignore
        return instance, app_instance


class TestDockerComposeDeployment(BaseDeploymentTests):
    """Test class for DOcker-compose Deployment."""

    deployment_generator = DockerComposeGenerator

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""
        for (
            test_case_name,
            spec_path,
        ) in test_deployment_spec_paths.items():
            if test_case_name.find("ropsten") < 0:
                continue
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
        for (
            test_case_name,
            spec_path,
        ) in test_deployment_spec_paths.items():
            if test_case_name.find("ropsten") < 0:
                continue
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

    def test_creates_hardhat_deploy(self) -> None:
        """Required for deployment of hardhat."""

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""

    def test_generates_agent_for_all_valory_apps(self) -> None:
        """Test generator functions with all valory apps."""
        for deployment_generator in deployment_generators:
            for _, spec_path in test_deployment_spec_paths.items():
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = app_instance.generate_agent(0)
                assert len(res) >= 1

    def test_generates_agents_for_all_valory_apps(self) -> None:
        """Test functionality of the valory deployment generators."""
        for deployment_generator in deployment_generators:
            for _, spec_path in test_deployment_spec_paths.items():
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = app_instance.generate_agents()
                assert len(res) >= 1
            res = app_instance.generate_agents()
            assert len(res) > 1, "failed to generate agents"


class TestTendermintDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_all_tendermint_configs(self) -> None:
        """Test functionality of the tendermint deployment generators."""
        for deployment_generator in deployment_generators:
            for _, spec_path in test_deployment_spec_paths.items():
                deployer_instance, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = deployer_instance.generate_config_tendermint(app_instance)  # type: ignore
                assert len(res) > 1, "Failed to generate Tendermint Config"


class TestDeploymentLoadsAgent(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_loads_agent_config(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for _, spec_path in test_deployment_spec_paths.items():
                deployer_instance, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                agent_json = app_instance.load_agent()
                assert agent_json != {}


class TestCliTool(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_deploy_safe_contract(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for _, spec_path in test_deployment_spec_paths.items():
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                app_instance.generate_agent(0)

    def test_generates_deploy_oracle_contract(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for (
                _,
                spec_path,
            ) in test_deployment_spec_paths.items():
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                if app_instance.network != "ropsten":
                    continue
                app_instance.generate_agent(0)
