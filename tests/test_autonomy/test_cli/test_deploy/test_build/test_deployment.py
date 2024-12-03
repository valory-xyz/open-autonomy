# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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

import json
import os
import shutil
from itertools import cycle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from unittest import mock

import yaml
from aea.cli.registry.settings import REGISTRY_LOCAL
from aea.cli.utils.config import get_default_author_from_cli_config
from aea.cli.utils.constants import CLI_CONFIG_PATH, DEFAULT_CLI_CONFIG
from aea.configurations.constants import (
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_ENV_DOTFILE,
    PACKAGES,
    PROTOCOL,
    SKILL,
)
from aea_test_autonomy.configurations import (
    ETHEREUM_ENCRYPTED_KEYS,
    ETHEREUM_ENCRYPTION_PASSWORD,
)

from autonomy.constants import (
    DEFAULT_BUILD_FOLDER,
    DEFAULT_DOCKER_IMAGE_AUTHOR,
    DOCKER_COMPOSE_YAML,
    VALORY,
)
from autonomy.deploy.base import (
    DEFAULT_AGENT_CPU_LIMIT,
    DEFAULT_AGENT_CPU_REQUEST,
    DEFAULT_AGENT_MEMORY_LIMIT,
    DEFAULT_AGENT_MEMORY_REQUEST,
    ServiceBuilder,
    build_hash_id,
)
from autonomy.deploy.constants import (
    AGENT_VARS_CONFIG_FILE,
    DEBUG,
    DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA,
    DEPLOYMENT_KEY_DIRECTORY,
    INFO,
    KUBERNETES_AGENT_KEY_NAME,
    PERSISTENT_DATA_DIR,
    TENDERMINT_VARS_CONFIG_FILE,
    TM_ENV_CREATE_EMPTY_BLOCKS,
    TM_ENV_P2P_LADDR,
    TM_ENV_PROXY_APP,
    TM_ENV_RPC_LADDR,
    TM_ENV_TMHOME,
    TM_ENV_TMSTATE,
    TM_ENV_USE_GRPC,
    TM_STATE_DIR,
)
from autonomy.deploy.generators.docker_compose.base import DockerComposeGenerator
from autonomy.deploy.generators.localhost.utils import _run_aea_cmd
from autonomy.replay.agent import ETHEREUM_PRIVATE_KEY_FILE

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.base import get_dummy_service_config
from tests.test_autonomy.test_cli.base import BaseCliTest


OS_ENV_PATCH = mock.patch.dict(
    os.environ, values={**os.environ, "ALL_PARTICIPANTS": "[]"}, clear=True
)


@skip_docker_tests
class BaseDeployBuildTest(BaseCliTest):
    """Test `autonomy deply build deployment` command."""

    cli_options: Tuple[str, ...] = ("deploy", "build")
    keys_file: Path
    spec: ServiceBuilder

    def setup(self) -> None:
        """Setup test method."""
        super().setup()

        self.keys_file = self.t / "keys.json"
        shutil.copytree(ROOT_DIR / PACKAGES, self.t / PACKAGES)
        shutil.copy(
            ROOT_DIR / "deployments" / "keys" / "hardhat_keys.json", self.keys_file
        )

        shutil.copytree(
            self.t / PACKAGES / "valory" / "services" / "register_reset",
            self.t / "register_reset",
        )
        with OS_ENV_PATCH:
            self.spec = ServiceBuilder.from_dir(
                self.t / "register_reset", self.keys_file, service_hash_id="test"
            )
        os.chdir(self.t / "register_reset")

    @staticmethod
    def load_kubernetes_config(
        path: Path,
    ) -> List[Dict]:
        """Load kubernetes config."""

        with open(path / "build.yaml", "r") as fp:
            return list(yaml.safe_load_all(fp))

    @classmethod
    def check_kubernetes_build(cls, build_dir: Path) -> None:
        """Check kubernetes build dir."""

        build_tree = list(map(lambda x: x.name, build_dir.iterdir()))
        assert any(
            child in build_tree for child in ["persistent_storage", "build.yaml"]
        )

    def load_and_check_docker_compose_file(
        self,
        path: Path,
        service_hash_id: Optional[str] = None,
    ) -> Dict:
        """Load docker compose config."""
        with open(path, "r", encoding="utf-8") as fp:
            docker_compose = yaml.safe_load(fp)

        if service_hash_id is not None:
            with OS_ENV_PATCH:
                self.spec = ServiceBuilder.from_dir(
                    self.t / "register_reset",
                    self.keys_file,
                    service_hash_id=service_hash_id,
                )

        assert any(
            [key in docker_compose for key in ["version", "services", "networks"]]
        )

        assert any(
            [
                service in docker_compose["services"]
                for service in [
                    *map(lambda i: self.spec.get_abci_container_name(i), range(4)),
                    *map(lambda i: self.spec.get_tm_container_name(i), range(4)),
                ]
            ]
        )

        return docker_compose

    @staticmethod
    def check_localhost_build(build_dir: Path) -> None:
        """Check localhost build directory."""
        build_tree = list(map(lambda x: x.name, build_dir.iterdir()))
        assert all(
            [
                child in build_tree
                for child in {
                    ".certs",
                    DEFAULT_AEA_CONFIG_FILE,
                    DEPLOYMENT_KEY_DIRECTORY,
                    ETHEREUM_PRIVATE_KEY_FILE,
                    PERSISTENT_DATA_DIR,
                    AGENT_VARS_CONFIG_FILE,
                    "data",
                    "node",
                    TENDERMINT_VARS_CONFIG_FILE,
                }
            ]
        )

    def load_and_check_localhost_build(self, path: Path) -> None:
        """Load localhost build config."""
        with open(path / TENDERMINT_VARS_CONFIG_FILE, "r", encoding="utf-8") as fp:
            assert json.load(fp) == {
                TM_ENV_TMHOME: (
                    self.t / "register_reset" / DEFAULT_BUILD_FOLDER / "node"
                ).as_posix(),
                TM_ENV_TMSTATE: (
                    self.t / "register_reset" / DEFAULT_BUILD_FOLDER / TM_STATE_DIR
                ).as_posix(),
                TM_ENV_P2P_LADDR: "tcp://localhost:26656",
                TM_ENV_RPC_LADDR: "tcp://localhost:26657",
                TM_ENV_PROXY_APP: "tcp://localhost:26658",
                TM_ENV_CREATE_EMPTY_BLOCKS: "true",
                TM_ENV_USE_GRPC: "false",
            }
        with open(path / AGENT_VARS_CONFIG_FILE, "r", encoding="utf-8") as fp:
            assert json.load(fp) == {
                "ID": "0",
                "AEA_AGENT": "valory/register_reset:0.1.0:bafybeia4pxlphcvco3ttlv3tytklriwvuwxxxr5m2tdry32yc5vogxtm7u",
                "LOG_LEVEL": INFO,
                "AEA_PASSWORD": "",
                "CONNECTION_LEDGER_CONFIG_LEDGER_APIS_ETHEREUM_ADDRESS": "http://host.docker.internal:8545",
                "CONNECTION_LEDGER_CONFIG_LEDGER_APIS_ETHEREUM_CHAIN_ID": "31337",
                "CONNECTION_LEDGER_CONFIG_LEDGER_APIS_ETHEREUM_POA_CHAIN": "False",
                "CONNECTION_LEDGER_CONFIG_LEDGER_APIS_ETHEREUM_DEFAULT_GAS_PRICE_STRATEGY": "eip1559",
                "CONNECTION_ABCI_CONFIG_HOST": "localhost",
                "CONNECTION_ABCI_CONFIG_PORT": "26658",
            }

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


class TestLocalhostBuilds(BaseDeployBuildTest):
    """Test localhost builds."""

    def setup(self) -> None:
        """Setup test for localhost deployment."""
        super().setup()
        shutil.copy(
            ROOT_DIR
            / PACKAGES
            / VALORY
            / "agents"
            / "register_reset"
            / DEFAULT_AEA_CONFIG_FILE,
            self.t / "register_reset",
        )
        aea_cli_config = DEFAULT_CLI_CONFIG
        aea_cli_config["registry_config"]["settings"][REGISTRY_LOCAL][
            "default_packages_path"
        ] = (ROOT_DIR / PACKAGES).as_posix()
        Path(CLI_CONFIG_PATH).write_text(yaml.dump(aea_cli_config))

        with open(self.t / "register_reset" / DEFAULT_AEA_CONFIG_FILE, "r") as fp:
            agent_config = next(yaml.safe_load_all(fp))
        agent_config["private_key_paths"]["ethereum"] = ETHEREUM_PRIVATE_KEY_FILE
        with open(self.t / "register_reset" / DEFAULT_AEA_CONFIG_FILE, "w") as fp:
            yaml.dump(agent_config, fp)

        # add all the components
        for component_type in (CONNECTION, CONTRACT, SKILL, PROTOCOL):
            for component_name in agent_config[component_type + "s"]:
                _run_aea_cmd(
                    [
                        "--skip-consistency-check",
                        "add",
                        component_type,
                        component_name,
                        "--mixed",
                    ],
                    cwd=self.t / "register_reset",
                    ignore_error="already exists",
                )

        # prepare ethereum private key
        with open(self.t / "register_reset" / ETHEREUM_PRIVATE_KEY_FILE, "w") as fp:
            fp.write(  # mock private key
                "0x0000000000000000000000000000000000000000000000000000000000000001"
            )

    def test_localhost_build(
        self,
    ) -> None:
        """Test that the build command works."""

        build_dir = self.t / "register_reset" / DEFAULT_BUILD_FOLDER
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (str(self.keys_file), "--localhost", "--mkdir", "data")
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()
        assert (build_dir / "data").exists()

        self.check_localhost_build(build_dir=build_dir)
        self.load_and_check_localhost_build(path=build_dir)


class TestDockerComposeBuilds(BaseDeployBuildTest):
    """Test docker-compose build."""

    def test_docker_compose_build(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--local",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        assert not (build_dir / "nodes").exists()

        self.check_docker_compose_build(
            build_dir=build_dir,
        )
        self.load_and_check_docker_compose_file(
            path=build_dir / DockerComposeGenerator.output_name
        )

    def test_docker_compose_build_with_testnet(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--local",
                    "--local-tm-setup",
                )
            )

        assert result.exit_code == 0, result.output
        assert (build_dir / "nodes").exists(), result.stderr

    def test_docker_compose_build_log_level(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
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
            f"LOG_LEVEL={DEBUG}"
            in docker_compose["services"][self.spec.get_abci_container_name(0)][
                "environment"
            ]
        )
        assert (
            f"LOG_LEVEL={DEBUG}"
            in docker_compose["services"][self.spec.get_tm_container_name(0)][
                "environment"
            ]
        )

    def test_docker_compose_build_dev(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--dev",
                    "--local",
                    "--packages-dir",
                    str(ROOT_DIR),
                    "--open-aea-dir",
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
            in docker_compose["services"][self.spec.get_abci_container_name(index=0)][
                "volumes"
            ]
        )
        assert (
            f"{ROOT_DIR}:/open-aea"
            in docker_compose["services"][self.spec.get_abci_container_name(index=0)][
                "volumes"
            ]
        )
        assert (
            f"{ROOT_DIR}:/open-autonomy"
            in docker_compose["services"][self.spec.get_abci_container_name(index=0)][
                "volumes"
            ]
        )

    def test_docker_compose_password(
        self,
    ) -> None:
        """Run tests."""
        keys_file = Path(ETHEREUM_ENCRYPTED_KEYS)
        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())

        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(keys_file),
                    "--o",
                    str(build_dir),
                    "--password",
                    ETHEREUM_ENCRYPTION_PASSWORD,
                    "--local",
                )
            )

        assert result.exit_code == 0, result.stderr
        assert (
            "WARNING: `--password` flag has been deprecated, use `OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD` to export the password value"
            in result.stdout
        )
        assert build_dir.exists()
        assert result.exit_code == 0, result.output

        docker_compose_file = build_dir / DockerComposeGenerator.output_name
        with open(docker_compose_file, "r", encoding="utf-8") as fp:
            docker_compose = yaml.safe_load(fp)

        def _file_check(n: int) -> bool:
            return (
                build_dir
                / DEPLOYMENT_KEY_DIRECTORY
                / DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA.format(agent_n=n)
            ).exists()

        agents = int(len(docker_compose["services"]) / 2)
        assert all(_file_check(i) for i in range(agents))
        for x in range(agents):
            env = dict(
                [
                    f.split("=")
                    for f in docker_compose["services"][
                        self.spec.get_abci_container_name(x)
                    ]["environment"]
                ]
            )
            assert "AEA_PASSWORD" in env.keys()
            assert env["AEA_PASSWORD"] == "$OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD"

    def test_include_acn_and_hardhat_nodes(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--dev",
                    "--local",
                    "--packages-dir",
                    str(ROOT_DIR),
                    "--open-aea-dir",
                    str(ROOT_DIR),
                    "--use-hardhat",
                    "--use-acn",
                )
            )

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

        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())),
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

    def test_docker_compose_build_image_author_flag_default(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
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
            docker_compose["services"][self.spec.get_abci_container_name(0)][
                "image"
            ].split("/")[0]
            == get_default_author_from_cli_config()
            or DEFAULT_DOCKER_IMAGE_AUTHOR
        )

    def test_docker_compose_build_image_author_flag_custom(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        image_author = "some_author"
        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", return_value="test"
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--local",
                    "--log-level",
                    DEBUG,
                    "--image-author",
                    image_author,
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
            docker_compose["services"][self.spec.get_abci_container_name(0)][
                "image"
            ].split("/")[0]
            == image_author
        )

    def test_docker_compose_build_multiple(
        self,
    ) -> None:
        """Run tests."""

        mock_build_hash_id_cycle = cycle(["test", "test2"])

        def mock_build_hash_id() -> str:
            """Mock build hash id."""
            return next(mock_build_hash_id_cycle)

        with mock.patch("os.chown"), OS_ENV_PATCH, mock.patch(
            "autonomy.cli.deploy.build_hash_id", new=mock_build_hash_id
        ):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--number-of-services",
                    "2",
                )
            )

        assert result.exit_code == 0, result.output

        builds_count = 0
        for build_dir in Path.cwd().glob("abci_build_*"):
            if not (build_dir / DOCKER_COMPOSE_YAML).exists():
                continue

            builds_count += 1

            self.check_docker_compose_build(
                build_dir=build_dir,
            )
            self.load_and_check_docker_compose_file(
                path=build_dir / DockerComposeGenerator.output_name,
                service_hash_id=mock_build_hash_id(),
            )

        assert builds_count == 2


class TestKubernetesBuild(BaseDeployBuildTest):
    """Test kubernetes builds."""

    def test_kubernetes_build(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                    "--local",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(build_dir=build_dir)

    def test_kubernetes_build_log_level(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
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

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                    "--dev",
                    "--local",
                    "--packages-dir",
                    str(ROOT_DIR),
                    "--open-aea-dir",
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
        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())

        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                    "--password",
                    ETHEREUM_ENCRYPTION_PASSWORD,
                    "--local",
                )
            )

        assert result.exit_code == 0, result.output
        assert (
            "WARNING: `--password` flag has been deprecated, use `OPEN_AUTONOMY_PRIVATE_KEY_PASSWORD` to export the password value"
            in result.stdout
        )
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

            assert agent_vars["AEA_PASSWORD"] == ""

        assert all(
            (
                build_dir
                / DEPLOYMENT_KEY_DIRECTORY
                / KUBERNETES_AGENT_KEY_NAME.format(agent_n=i)
            ).exists()
            for i in range(4)
        )

    def test_kubernetes_build_with_testnet(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())

        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--local",
                    "--kubernetes",
                    "--local-tm-setup",
                )
            )

        assert result.exit_code == 0, result.output

        kubernetes_config = self.load_kubernetes_config(
            path=build_dir,
        )

        assert any(
            [
                resource["metadata"]["name"] == "config-nodes"
                for resource in kubernetes_config
            ]
        )

    def test_kubernetes_build_image_author_default(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                    "--local",
                    "--log-level",
                    DEBUG,
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(build_dir=build_dir)

        build_config = self.load_kubernetes_config(build_dir)
        assert (
            f"'image': '{get_default_author_from_cli_config() or  DEFAULT_DOCKER_IMAGE_AUTHOR}/oar-"
            in str(build_config)
        )

    def test_kubernetes_build_image_author_custom(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        image_author = "some_image_author"
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                    "--local",
                    "--log-level",
                    DEBUG,
                    "--image-author",
                    image_author,
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(build_dir=build_dir)

        build_config = self.load_kubernetes_config(build_dir)
        assert f"'image': '{image_author}/oar-" in str(build_config)
        assert f"'image': '{DEFAULT_DOCKER_IMAGE_AUTHOR}/oar-" not in str(build_config)


class TestExposePorts(BaseDeployBuildTest):
    """Test expose ports from service config."""

    def setup(self) -> None:
        """Setup test."""
        super().setup()

        service_data = get_dummy_service_config(file_number=1)
        service_data[0]["deployment"] = {
            "agent": {"ports": {0: {8080: 8081}}},
            "tendermint": {"ports": {0: {26656: 26666}}},
        }

        with open("./service.yaml", "w+") as fp:
            yaml.dump_all(service_data, fp)

        with OS_ENV_PATCH:
            self.spec = ServiceBuilder.from_dir(
                self.t / "register_reset",
                self.keys_file,
            )

    def test_expose_agent_ports_docker_compose(self) -> None:
        """Test expose agent ports"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
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

        assert docker_compose["services"][self.spec.get_abci_container_name(0)][
            "ports"
        ] == ["8080:8081"]
        assert docker_compose["services"][self.spec.get_tm_container_name(0)][
            "ports"
        ] == ["26656:26666"]

    def test_expose_agent_ports_kubernetes(self) -> None:
        """Test expose agent ports"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(build_dir=build_dir)

        build_config = self.load_kubernetes_config(build_dir)

        assert "ports" in build_config[1]["spec"]["template"]["spec"]["containers"][1]
        assert build_config[1]["spec"]["template"]["spec"]["containers"][1][
            "ports"
        ] == [{"containerPort": 8080}]


class TestExtraVolumes(BaseDeployBuildTest):
    """Test expose ports from service config."""

    volume: Path

    def setup(self) -> None:
        """Setup test."""
        super().setup()

        self.volume = self.t / "extra_volume"
        service_data = get_dummy_service_config(file_number=1)
        service_data[0]["deployment"] = {
            "agent": {"volumes": {f"{self.volume}": "/data"}}
        }

        with open("./service.yaml", "w+") as fp:
            yaml.dump_all(service_data, fp)

        with OS_ENV_PATCH:
            self.spec = ServiceBuilder.from_dir(
                self.t / "register_reset",
                self.keys_file,
            )

    def test_expose_agent_ports_docker_compose(self) -> None:
        """Test expose agent ports"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
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

        assert self.volume.exists()
        assert (
            f"{self.volume}:/data:Z"
            in docker_compose["services"][self.spec.get_abci_container_name(0)][
                "volumes"
            ]
        )

    def test_expose_agent_ports_kubernetes(self) -> None:
        """Test expose agent ports"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(build_dir=build_dir)
        build_config = self.load_kubernetes_config(build_dir)
        assert self.volume.exists()
        assert (
            build_config[1]["spec"]["template"]["spec"]["volumes"][-1]["name"]
            == "extra-volume"
        )
        assert (
            build_config[1]["spec"]["template"]["spec"]["containers"][1][
                "volumeMounts"
            ][-1]["mountPath"]
            == "/data"
        )
        assert (
            build_config[1]["spec"]["template"]["spec"]["containers"][1][
                "volumeMounts"
            ][-1]["name"]
            == "extra-volume"
        )
        assert build_config[-1]["metadata"]["name"] == "extra-volume"


class TestLoadEnvVars(BaseDeployBuildTest):
    """Test expose ports from service config."""

    env_var = "SERVICE_HELLO_WORLD_HELLO_WORLD_STRING"
    env_var_path = "SKILL_DUMMY_SKILL_MODELS_PARAMS_ARGS_HELLO_WORLD_MESSAGE"
    env_var_value = "ENV_VAR_VALUE"

    def setup(self) -> None:
        """Setup test."""
        super().setup()
        service_data = get_dummy_service_config(file_number=4)
        with open("./service.yaml", "w+") as fp:
            yaml.dump_all(service_data, fp)
        with OS_ENV_PATCH:
            self.spec = ServiceBuilder.from_dir(
                self.t / "register_reset",
                self.keys_file,
            )

    def _run_test(self) -> None:
        """Run test."""
        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
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
            f"{self.env_var_path}={self.env_var_value}"
            in docker_compose["services"][self.spec.get_abci_container_name(0)][
                "environment"
            ]
        )

    def test_load_dot_env(self) -> None:
        """Test load `.env` file"""

        (self.t / "register_reset" / DEFAULT_ENV_DOTFILE).write_text(
            f"{self.env_var}={self.env_var_value}"
        )
        self._run_test()

    def test_load_json(self) -> None:
        """Test load `.json` file"""

        env_var_value = "ENV_VAR_VALUE"
        env_file = self.t / "register_reset" / "env.json"
        env_file.write_text(json.dumps({self.env_var: env_var_value}))
        self.cli_options = ("deploy", "--env-file", str(env_file.resolve()), "build")

        self._run_test()


class TestResourceSpecification(BaseDeployBuildTest):
    """Test expose ports from service config."""

    def setup(self) -> None:
        """Setup test."""
        super().setup()
        service_data = get_dummy_service_config(file_number=4)
        with open("./service.yaml", "w+") as fp:
            yaml.dump_all(service_data, fp)
        with OS_ENV_PATCH:
            self.spec = ServiceBuilder.from_dir(
                self.t / "register_reset",
                self.keys_file,
            )

    def test_default_resources_docker_compose(self) -> None:
        """Test custom resources"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli((str(self.keys_file), "--o", str(build_dir)))

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_docker_compose_build(
            build_dir=build_dir,
        )
        docker_compose = self.load_and_check_docker_compose_file(
            path=build_dir / DockerComposeGenerator.output_name
        )

        assert (
            docker_compose["services"]["dummyservice_abci_0"]["mem_reservation"]
            == f"{DEFAULT_AGENT_MEMORY_REQUEST}M"
        )
        assert (
            docker_compose["services"]["dummyservice_abci_0"]["mem_limit"]
            == f"{DEFAULT_AGENT_MEMORY_LIMIT}M"
        )
        assert (
            docker_compose["services"]["dummyservice_abci_0"]["cpus"]
            == DEFAULT_AGENT_CPU_LIMIT
        )

    def test_default_resources_kuberntes(self) -> None:
        """Test custom resources"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(build_dir=build_dir)
        build_config = self.load_kubernetes_config(build_dir)

        assert build_config[1]["spec"]["template"]["spec"]["containers"][1][
            "resources"
        ]["requests"]["cpu"] == str(DEFAULT_AGENT_CPU_REQUEST)

        assert (
            build_config[1]["spec"]["template"]["spec"]["containers"][1]["resources"][
                "requests"
            ]["memory"]
            == f"{DEFAULT_AGENT_MEMORY_REQUEST}Mi"
        )

        assert build_config[1]["spec"]["template"]["spec"]["containers"][1][
            "resources"
        ]["limits"]["cpu"] == str(DEFAULT_AGENT_CPU_LIMIT)

        assert (
            build_config[1]["spec"]["template"]["spec"]["containers"][1]["resources"][
                "limits"
            ]["memory"]
            == f"{DEFAULT_AGENT_MEMORY_LIMIT}Mi"
        )

    def test_custom_resources_docker_compose(self) -> None:
        """Test custom resources"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--agent-cpu-limit",
                    "2.0",
                    "--agent-memory-limit",
                    "4096",
                    "--agent-memory-request",
                    "2048",
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
            docker_compose["services"]["dummyservice_abci_0"]["mem_reservation"]
            == "2048M"
        )
        assert docker_compose["services"]["dummyservice_abci_0"]["mem_limit"] == "4096M"
        assert docker_compose["services"]["dummyservice_abci_0"]["cpus"] == 2.0

    def test_custom_resources_kuberntes(self) -> None:
        """Test custom resources"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--kubernetes",
                    "--agent-cpu-request",
                    "1.0",
                    "--agent-memory-request",
                    "2048",
                    "--agent-cpu-limit",
                    "2.0",
                    "--agent-memory-limit",
                    "4096",
                )
            )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_kubernetes_build(build_dir=build_dir)
        build_config = self.load_kubernetes_config(build_dir)

        assert (
            build_config[1]["spec"]["template"]["spec"]["containers"][1]["resources"][
                "requests"
            ]["cpu"]
            == "1.0"
        )

        assert (
            build_config[1]["spec"]["template"]["spec"]["containers"][1]["resources"][
                "requests"
            ]["memory"]
            == "2048Mi"
        )

        assert (
            build_config[1]["spec"]["template"]["spec"]["containers"][1]["resources"][
                "limits"
            ]["cpu"]
            == "2.0"
        )

        assert (
            build_config[1]["spec"]["template"]["spec"]["containers"][1]["resources"][
                "limits"
            ]["memory"]
            == "4096Mi"
        )
