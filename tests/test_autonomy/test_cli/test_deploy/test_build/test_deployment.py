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

"""Test deployment command."""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from unittest import mock

import yaml
from aea.configurations.constants import PACKAGES
from aea_test_autonomy.configurations import (
    ETHEREUM_ENCRYPTED_KEYS,
    ETHEREUM_ENCRYPTION_PASSWORD,
)

from autonomy.constants import DEFAULT_BUILD_FOLDER
from autonomy.deploy.constants import (
    DEBUG,
    DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA,
    DEPLOYMENT_KEY_DIRECTORY,
    KUBERNETES_AGENT_KEY_NAME,
)
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_cli.base import BaseCliTest


@skip_docker_tests
class BaseDeployBuildTest(BaseCliTest):
    """Test `autonomy deply build deployment` command."""

    cli_options: Tuple[str, ...] = ("deploy", "build")
    service_id: str = "valory/oracle_hardhat"

    keys_file: Path

    def setup(self) -> None:
        """Setup test method."""
        super().setup()

        self.keys_file = self.t / "keys.json"
        shutil.copytree(ROOT_DIR / PACKAGES, self.t / PACKAGES)
        shutil.copy(
            ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json", self.keys_file
        )

        shutil.copytree(
            self.t / PACKAGES / "valory" / "services" / "hello_world",
            self.t / "hello_world",
        )
        os.chdir(self.t / "hello_world")


class TestDockerComposeBuilds(BaseDeployBuildTest):
    """Test docker-compose build."""

    @staticmethod
    def load_and_check_docker_compose_file(
        path: Path,
    ) -> Dict:
        """Load docker compose config."""
        with open(path, "r", encoding="utf-8") as fp:
            docker_compose = yaml.safe_load(fp)

        assert any(
            [key in docker_compose for key in ["version", "services", "networks"]]
        )

        assert any(
            [
                service in docker_compose["services"]
                for service in [
                    *map(lambda i: f"abci{i}", range(4)),
                    *map(lambda i: f"node0{i}", range(4)),
                ]
            ]
        )

        return docker_compose

    @staticmethod
    def check_docker_compose_build(
        build_dir: Path,
    ) -> None:
        """Check docker compose build directory."""
        build_tree = list(map(lambda x: x.name, build_dir.iterdir()))
        assert any(
            [
                child in build_tree
                for child in [
                    "persistent_storage",
                    "nodes",
                    DockerComposeGenerator.output_name,
                ]
            ]
        )

    def test_docker_compose_build(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER
        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--force",
                    "--local",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_docker_compose_build(
            build_dir=build_dir,
        )
        self.load_and_check_docker_compose_file(
            path=build_dir / DockerComposeGenerator.output_name
        )

    def test_docker_compose_build_log_level(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER
        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--force",
                    "--local",
                    "--log-level",
                    DEBUG,
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_docker_compose_build(
            build_dir=build_dir,
        )

        docker_compose = self.load_and_check_docker_compose_file(
            path=build_dir / DockerComposeGenerator.output_name
        )

        assert (
            f"LOG_LEVEL={DEBUG}" in docker_compose["services"]["abci0"]["environment"]
        )
        assert (
            f"LOG_LEVEL={DEBUG}" in docker_compose["services"]["node0"]["environment"]
        )

    def test_docker_compose_build_dev(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER
        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--force",
                    "--dev",
                    "--local",
                    "--packages-dir",
                    str(ROOT_DIR),
                    "--open-aea-dir",
                    str(ROOT_DIR),
                    "--open-autonomy-dir",
                    str(ROOT_DIR),
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_docker_compose_build(
            build_dir=build_dir,
        )

        docker_compose = self.load_and_check_docker_compose_file(
            path=build_dir / DockerComposeGenerator.output_name
        )

        assert (
            f"{ROOT_DIR}:/home/ubuntu/packages:rw"
            in docker_compose["services"]["abci0"]["volumes"]
        )
        assert f"{ROOT_DIR}:/open-aea" in docker_compose["services"]["abci0"]["volumes"]
        assert (
            f"{ROOT_DIR}:/open-autonomy"
            in docker_compose["services"]["abci0"]["volumes"]
        )

    def test_docker_compose_password(
        self,
    ) -> None:
        """Run tests."""
        keys_file = Path(ETHEREUM_ENCRYPTED_KEYS)

        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--force",
                    "--password",
                    ETHEREUM_ENCRYPTION_PASSWORD,
                    "--local",
                )
            )

        build_dir = self.t / DEFAULT_BUILD_FOLDER

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        build_dir = self.t / DEFAULT_BUILD_FOLDER

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        docker_compose_file = build_dir / DockerComposeGenerator.output_name
        with open(docker_compose_file, "r", encoding="utf-8") as fp:
            docker_compose = yaml.safe_load(fp)

        agents = int(len(docker_compose["services"]) / 2)

        def _file_check(n: int) -> bool:
            return (
                build_dir
                / DEPLOYMENT_KEY_DIRECTORY
                / DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA.format(agent_n=n)
            ).exists()

        assert all(_file_check(i) for i in range(agents))
        for x in range(agents):
            env = dict(
                [
                    f.split("=")
                    for f in docker_compose["services"][f"abci{x}"]["environment"]
                ]
            )
            assert "AEA_PASSWORD" in env.keys()
            assert env["AEA_PASSWORD"] == ETHEREUM_ENCRYPTION_PASSWORD

    def test_include_acn_and_hardhat_nodes(
        self,
    ) -> None:
        """Run tests."""

        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--force",
                    "--dev",
                    "--local",
                    "--packages-dir",
                    str(ROOT_DIR),
                    "--open-aea-dir",
                    str(ROOT_DIR),
                    "--open-autonomy-dir",
                    str(ROOT_DIR),
                    "--use-hardhat",
                    "--use-acn",
                )
            )

        build_dir = self.t / DEFAULT_BUILD_FOLDER

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        docker_compose = self.load_and_check_docker_compose_file(
            path=build_dir / DockerComposeGenerator.output_name,
        )
        assert "acn" in docker_compose["services"]
        assert "hardhat" in docker_compose["services"]

    def test_build_dev_failures(
        self,
    ) -> None:
        """Run tests."""

        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--force",
                    "--dev",
                    "--local",
                )
            )

        assert result.exit_code == 1, result.output
        assert "Please provide proper value for --packages-dir" in result.output

    def test_non_existent_keys_file_raises(self) -> None:
        """Test non-existent keys file"""

        keys_file = "non_existent_keys.json"
        result = self.run_cli((keys_file,))
        expected = f"No such file or directory: {Path.cwd() / keys_file}. Please provide valid path for keys file."
        assert result.exit_code == 1
        assert expected in result.stdout

    def test_remove_build_dir_on_exception(self) -> None:
        """Test non-existent keys file"""

        target = "autonomy.cli.deploy.build_deployment"
        side_effect = FileNotFoundError("Mocked file not found")
        with mock.patch(target, side_effect=side_effect) as m:
            with mock.patch("shutil.rmtree") as rmtree_mock:
                result = self.run_cli((str(self.keys_file),))
                m.assert_called_once()
                rmtree_mock.assert_called_once()
                assert str(side_effect) in result.stdout


class TestKubernetesBuild(BaseDeployBuildTest):
    """Test kubernetes builds."""

    @staticmethod
    def load_kubernetes_config(
        path: Path,
    ) -> List[Dict]:
        """Load kubernetes config."""

        with open(path / "build.yaml", "r") as fp:
            return list(yaml.safe_load_all(fp))

    @staticmethod
    def check_kubernetes_build(build_dir: Path) -> None:
        """Check kubernetes build dir."""

        build_tree = list(map(lambda x: x.name, build_dir.iterdir()))
        assert any(
            child in build_tree for child in ["persistent_storage", "build.yaml"]
        )

    def test_kubernetes_build(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER
        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--kubernetes",
                    "--force",
                    "--local",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        build_tree = list(map(lambda x: x.name, build_dir.iterdir()))
        assert any(
            child in build_tree for child in ["persistent_storage", "build.yaml"]
        )

    def test_kubernetes_build_log_level(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER
        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--kubernetes",
                    "--force",
                    "--local",
                    "--log-level",
                    DEBUG,
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(build_dir=build_dir)

        build_config = self.load_kubernetes_config(build_dir)
        assert {"name": "LOG_LEVEL", "value": DEBUG} in build_config[1]["spec"][
            "template"
        ]["spec"]["containers"][0]["env"]

    def test_kubernetes_build_dev(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER
        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--kubernetes",
                    "--force",
                    "--dev",
                    "--local",
                    "--packages-dir",
                    str(ROOT_DIR),
                    "--open-aea-dir",
                    str(ROOT_DIR),
                    "--open-autonomy-dir",
                    str(ROOT_DIR),
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(
            build_dir=build_dir,
        )

    def test_kubernetes_build_password(
        self,
    ) -> None:
        """Run tests."""
        keys_file = Path(ETHEREUM_ENCRYPTED_KEYS)
        build_dir = self.t / DEFAULT_BUILD_FOLDER

        with mock.patch("os.chown"):
            result = self.run_cli(
                (
                    str(keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER),
                    "--force",
                    "--kubernetes",
                    "--password",
                    ETHEREUM_ENCRYPTION_PASSWORD,
                    "--local",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        kubernetes_config = self.load_kubernetes_config(
            path=build_dir,
        )
        for resource in kubernetes_config:
            try:
                container = resource["spec"]["template"]["spec"]["containers"]
                agent_vars = {f["name"]: f["value"] for f in container[1]["env"]}
            except (KeyError, IndexError):
                continue

            assert agent_vars["AEA_PASSWORD"] == ETHEREUM_ENCRYPTION_PASSWORD

        assert all(
            (
                build_dir
                / DEPLOYMENT_KEY_DIRECTORY
                / KUBERNETES_AGENT_KEY_NAME.format(agent_n=i)
            ).exists()
            for i in range(4)
        )
