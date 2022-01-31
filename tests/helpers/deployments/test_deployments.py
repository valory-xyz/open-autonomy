# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

from deployments.base_deployments import (
    APYEstimationDeployment,
    CounterDeployment,
    PriceEstimationDeployment,
)
from deployments.generators.docker_compose.docker_compose import DockerComposeGenerator

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

    @classmethod
    def setup_class(cls) -> None:
        """Setup up the test class."""

    @classmethod
    def teardown_class(cls) -> None:
        """Setup up the test class."""


class TestDockerComposeDeployment(BaseDeploymentTests):
    """Test class for DOcker-compose Deployment."""

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""

    def test_creates_hardhat_deploy(self) -> None:
        """Required for deployment of hardhat."""


class TestKubernetesDeployment(BaseDeploymentTests):
    """Test class for Kubernetes Deployment."""

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""

    def test_creates_hardhat_deploy(self) -> None:
        """Required for deployment of hardhat."""


valory_apps = [CounterDeployment, PriceEstimationDeployment, APYEstimationDeployment]

deployment_generators = [DockerComposeGenerator]


class TestDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    config = {"number_of_agents": 4, "network": "hardhat"}

    def test_creates_hardhat_deploy(self) -> None:
        """Required for deployment of hardhat."""

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""

    def test_generates_agent_for_all_valory_apps(self) -> None:
        """Test generator functions with all valory apps."""
        for generator in valory_apps:
            instance = generator(
                number_of_agents=self.config["number_of_agents"],
                network=self.config["network"]
            )
            res = instance.generate_agent(0)
            assert len(res) >= 1

    def test_generates_agents_for_all_valory_apps(self) -> None:
        """Test functionality of the valory deployment generators."""
        for generator in valory_apps:
            instance = generator(**self.config)
            res = instance.generate_agents()
            assert len(res) > 1, "failed to generate agents"


class TestTendermintDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    config = {"number_of_agents": 4, "network": "hardhat"}

    def test_generates_agents_for_all_tendermint_configs(self) -> None:
        """Test functionality of the tendermint deployment generators."""
        for generator in deployment_generators:
            instance = generator(**self.config)
            for app in valory_apps:
                res = instance.generate_config_tendermint(app)
                assert len(res) > 1, "Failed to generate Tendermint Config"
