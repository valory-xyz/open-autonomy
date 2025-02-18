# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2025 Valory AG
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
import re
import shutil
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple
from unittest import mock

import pytest
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
from dotenv import load_dotenv

from autonomy.constants import (
    DEFAULT_BUILD_FOLDER,
    DEFAULT_DOCKER_IMAGE_AUTHOR,
    DOCKER_COMPOSE_YAML,
    VALORY,
)
from autonomy.deploy import base
from autonomy.deploy.base import (
    AUTONOMY_PKEY_PASSWORD,
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
from autonomy.deploy.generators.docker_compose.base import (
    AGENT_ENV_TEMPLATE,
    DockerComposeGenerator,
)
from autonomy.deploy.generators.localhost.utils import _run_aea_cmd
from autonomy.replay.agent import ETHEREUM_PRIVATE_KEY_FILE

from tests.conftest import PACKAGES_DIR, ROOT_DIR, skip_docker_tests
from tests.test_autonomy.base import get_dummy_service_config
from tests.test_autonomy.test_cli.base import BaseCliTest


OS_ENV_PATCH = mock.patch.dict(
    os.environ, values={**os.environ, "ALL_PARTICIPANTS": "[]"}, clear=True
)
MOCK_SERVICE_HASH_ID = "test"
HASH_BUILDER_PATCH = mock.patch.object(
    base, "build_hash_id", return_value=MOCK_SERVICE_HASH_ID
)
SERVICE_HASH_ID_REGEX = r".*?([\w-]{4})(?:_abci|_tm)_(\d+)"
SERVICE_HASH_ID_MATCH_GROUP = 1
N_AGENTS = 4
AGENT_DIRECTORY = "agent"
NODE_DIRECTORY = "node"
REGISTER_RESET_COMPONENT = "register_reset"
PACKAGES_CONFIG = "packages.json"


def iterdir(directory: Path) -> FrozenSet[str]:
    """Iterate the given directory and return its contents."""
    return frozenset(map(lambda x: x.name, directory.iterdir()))


def find_hash(component_name: str) -> str:
    """Find the hash for a component."""
    packages_dir = PACKAGES_DIR / PACKAGES_CONFIG
    assert packages_dir.exists(), f"{packages_dir!r} does not exist!"

    with open(packages_dir, "r", encoding="utf-8") as configuration:
        try:
            packages = json.load(configuration)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            raise AssertionError(
                f"{packages_dir!r} is not properly formatted!"
            ) from exc

        for component_id, hash_ in packages.get("dev", {}).items():
            if f"{component_name}/" in component_id:
                return hash_

    raise AssertionError(
        f"No hash found in dev packages of {PACKAGES_CONFIG} for {component_name=}!"
    )


def check_agent_env(build_dir: Path, env_var_name: str, expected_value: str) -> None:
    """Check env."""
    for node_id in range(N_AGENTS):
        env_file = AGENT_ENV_TEMPLATE.substitute(node_id=node_id)
        assert load_dotenv(
            build_dir / env_file, override=True
        ), "Environment was not changed!"
        env_var_value = os.getenv(env_var_name)
        assert (
            env_var_value is not None
        ), f"{env_var_name!r} not in {os.environ.keys()!r}!"
        assert (
            env_var_value == expected_value
        ), f"{env_var_value!r} != {expected_value!r}!"


def get_service_hash_id(path: Path) -> str:
    """Get the service hash id from the docker compose file."""
    with open(path, "r", encoding="utf-8") as fp:
        docker_compose = yaml.safe_load(fp)
        first_service = next(iter(docker_compose.get("services", {})))
        match = re.search(SERVICE_HASH_ID_REGEX, first_service)
        assert match is not None, "No service found in docker compose file!"
        return match.group(SERVICE_HASH_ID_MATCH_GROUP)


@skip_docker_tests
@HASH_BUILDER_PATCH
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
            self.t / PACKAGES / "valory" / "services" / REGISTER_RESET_COMPONENT,
            self.t / REGISTER_RESET_COMPONENT,
        )
        with OS_ENV_PATCH:
            self.spec = ServiceBuilder.from_dir(
                self.t / REGISTER_RESET_COMPONENT,
                self.keys_file,
                service_hash_id="test",
            )
        os.chdir(self.t / REGISTER_RESET_COMPONENT)

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
                    self.t / REGISTER_RESET_COMPONENT,
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
                    *map(
                        lambda i: self.spec.get_abci_container_name(i), range(N_AGENTS)
                    ),
                    *map(lambda i: self.spec.get_tm_container_name(i), range(N_AGENTS)),
                ]
            ]
        )

        return docker_compose

    @staticmethod
    def check_localhost_build(build_dir: Path) -> None:
        """Check localhost build directory."""
        build_tree = iterdir(build_dir)
        assert all(
            [
                child in build_tree
                for child in {
                    AGENT_DIRECTORY,
                    DEPLOYMENT_KEY_DIRECTORY,
                    ETHEREUM_PRIVATE_KEY_FILE,
                    PERSISTENT_DATA_DIR,
                    AGENT_VARS_CONFIG_FILE,
                    "data",
                    NODE_DIRECTORY,
                    TENDERMINT_VARS_CONFIG_FILE,
                }
            ]
        )

        agent_tree = iterdir(build_dir / AGENT_DIRECTORY)
        assert all(
            [
                child in agent_tree
                for child in [
                    ".certs",
                    DEFAULT_AEA_CONFIG_FILE,
                    "vendor",
                    ETHEREUM_PRIVATE_KEY_FILE,
                ]
            ]
        )

        node_tree = iterdir(build_dir / NODE_DIRECTORY)
        assert all([child in node_tree for child in ["config", "data"]])

    def load_and_check_localhost_build(self, path: Path) -> None:
        """Load localhost build config."""
        with open(path / TENDERMINT_VARS_CONFIG_FILE, "r", encoding="utf-8") as fp:
            assert json.load(fp) == {
                TM_ENV_TMHOME: (
                    self.t / REGISTER_RESET_COMPONENT / path.name / "node"
                ).as_posix(),
                TM_ENV_TMSTATE: (
                    self.t / REGISTER_RESET_COMPONENT / path.name / TM_STATE_DIR
                ).as_posix(),
                TM_ENV_P2P_LADDR: "tcp://localhost:26656",
                TM_ENV_RPC_LADDR: "tcp://localhost:26657",
                TM_ENV_PROXY_APP: "tcp://localhost:26658",
                TM_ENV_CREATE_EMPTY_BLOCKS: "true",
                TM_ENV_USE_GRPC: "false",
            }

        hash_ = find_hash(REGISTER_RESET_COMPONENT)
        with open(path / AGENT_VARS_CONFIG_FILE, "r", encoding="utf-8") as fp:
            assert json.load(fp) == {
                "ID": "0",
                "AEA_AGENT": f"valory/register_reset:0.1.0:{hash_}",
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
            / REGISTER_RESET_COMPONENT
            / DEFAULT_AEA_CONFIG_FILE,
            self.t / REGISTER_RESET_COMPONENT,
        )
        DEFAULT_CLI_CONFIG["registry_config"]["settings"][REGISTRY_LOCAL][
            "default_packages_path"
        ] = (ROOT_DIR / PACKAGES).as_posix()
        Path(CLI_CONFIG_PATH).write_text(yaml.dump(DEFAULT_CLI_CONFIG))

        with open(
            self.t / REGISTER_RESET_COMPONENT / DEFAULT_AEA_CONFIG_FILE, "r"
        ) as fp:
            agent_config = next(yaml.safe_load_all(fp))
        agent_config["private_key_paths"]["ethereum"] = ETHEREUM_PRIVATE_KEY_FILE
        with open(
            self.t / REGISTER_RESET_COMPONENT / DEFAULT_AEA_CONFIG_FILE, "w"
        ) as fp:
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
                    cwd=self.t / REGISTER_RESET_COMPONENT,
                    ignore_error="already exists",
                )

        # prepare ethereum private key
        with open(
            self.t / REGISTER_RESET_COMPONENT / ETHEREUM_PRIVATE_KEY_FILE, "w"
        ) as fp:
            fp.write(  # mock private key
                "0x0000000000000000000000000000000000000000000000000000000000000001"
            )

    def teardown(self) -> None:
        """Teardown method."""
        super().teardown()
        DEFAULT_CLI_CONFIG["registry_config"]["settings"][REGISTRY_LOCAL][
            "default_packages_path"
        ] = None
        Path(CLI_CONFIG_PATH).write_text(yaml.dump(DEFAULT_CLI_CONFIG))

    def test_localhost_build(
        self,
    ) -> None:
        """Test that the build command works."""

        build_dir = (
            self.t
            / REGISTER_RESET_COMPONENT
            / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        )
        result = self.run_cli(
            (
                str(self.keys_file),
                "--o",
                str(build_dir),
                "--localhost",
                "--mkdir",
                "data",
            )
        )

        assert result.exit_code == 0, result.output
        assert build_dir.exists()
        assert (build_dir / "data").exists()

        self.check_localhost_build(build_dir)
        self.load_and_check_localhost_build(build_dir)

    @pytest.mark.skip("Test is not implemented yet.")
    def test_dev_mode(self) -> None:
        """Test that the dev mode works."""


class TestDockerComposeBuilds(BaseDeployBuildTest):
    """Test docker-compose build."""

    def teardown(self) -> None:
        """Teardown method."""
        super().teardown()
        os.environ.pop(AUTONOMY_PKEY_PASSWORD, None)

    def test_docker_compose_build(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("autonomy.cli.deploy.build_hash_id", return_value="test"):
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
        with mock.patch("autonomy.cli.deploy.build_hash_id", return_value="test"):
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
        with mock.patch("autonomy.cli.deploy.build_hash_id", return_value="test"):
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
        check_agent_env(build_dir, "LOG_LEVEL", DEBUG)
        assert (
            f"LOG_LEVEL={DEBUG}"
            in docker_compose["services"][self.spec.get_tm_container_name(0)][
                "environment"
            ]
        )

    def test_docker_compose_build_dev_unavailable(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("autonomy.cli.deploy.build_hash_id", return_value="test"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
                    "--dev",
                    "--packages-dir",
                    PACKAGES_DIR,
                    "--open-aea-dir",
                    str(ROOT_DIR.parent / "open-aea"),
                )
            )

        assert result.exit_code == 1
        assert result.exception
        assert result.exception.args
        assert result.exception.args[0] in (
            1,
            "Development mode can only be used with localhost deployments",
        )

    @pytest.mark.parametrize("deprecated_password", [True, False])
    def test_docker_compose_password(
        self,
        deprecated_password: bool,
    ) -> None:
        """Run tests."""
        keys_file = Path(ETHEREUM_ENCRYPTED_KEYS)
        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        cmd: Tuple[str, ...] = (
            str(keys_file),
            "--o",
            str(build_dir),
            "--local",
        )
        if deprecated_password:
            cmd += ("--password", ETHEREUM_ENCRYPTION_PASSWORD)
            os.environ.pop(AUTONOMY_PKEY_PASSWORD, None)
        else:
            os.environ[AUTONOMY_PKEY_PASSWORD] = ETHEREUM_ENCRYPTION_PASSWORD

        result = self.run_cli(cmd)

        assert result.exit_code == 0, result.stderr
        if deprecated_password:
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
        password = "" if deprecated_password else ETHEREUM_ENCRYPTION_PASSWORD
        check_agent_env(build_dir, "AEA_PASSWORD", password)

    def test_include_acn_and_hardhat_nodes(
        self,
    ) -> None:
        """Run tests."""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("autonomy.cli.deploy.build_hash_id", return_value="test"):
            result = self.run_cli(
                (
                    str(self.keys_file),
                    "--o",
                    str(build_dir),
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

        result = self.run_cli(
            (
                str(self.keys_file),
                "--o",
                str(self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())),
                "--dev",
            )
        )
        assert result.exit_code == 1, result.output
        assert (
            "Please provide a valid path to the `packages` directory for development mode."
            in result.output
        )

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
        with mock.patch("autonomy.cli.deploy.build_hash_id", return_value="test"):
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
        with mock.patch("autonomy.cli.deploy.build_hash_id", return_value="test"):
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
            path = build_dir / DockerComposeGenerator.output_name
            service_hash_id = get_service_hash_id(path)
            self.load_and_check_docker_compose_file(path, service_hash_id)

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

    def test_kubernetes_build_dev_unavailable(
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
                    "--packages-dir",
                    PACKAGES_DIR,
                    "--open-aea-dir",
                    str(ROOT_DIR.parent / "open-aea"),
                )
            )

        assert result.exit_code == 1
        assert result.exception
        assert result.exception.args
        assert result.exception.args[0] in (
            1,
            "Development mode can only be used with localhost deployments",
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
            for i in range(N_AGENTS)
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
                self.t / REGISTER_RESET_COMPONENT,
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

        self.check_docker_compose_build(build_dir)
        path = build_dir / DockerComposeGenerator.output_name
        service_hash_id = get_service_hash_id(path)
        docker_compose = self.load_and_check_docker_compose_file(path, service_hash_id)

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
                self.t / REGISTER_RESET_COMPONENT,
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

        self.check_docker_compose_build(build_dir)
        path = build_dir / DockerComposeGenerator.output_name
        service_hash_id = get_service_hash_id(path)
        docker_compose = self.load_and_check_docker_compose_file(path, service_hash_id)

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

    def _run_test(self) -> None:
        """Run test."""
        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(MOCK_SERVICE_HASH_ID)
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

        self.check_docker_compose_build(build_dir=build_dir)
        path = build_dir / DockerComposeGenerator.output_name
        service_hash_id = get_service_hash_id(path)
        self.load_and_check_docker_compose_file(path, service_hash_id)
        check_agent_env(build_dir, self.env_var_path, self.env_var_value)

    def test_load_dot_env(self) -> None:
        """Test load `.env` file"""

        (self.t / REGISTER_RESET_COMPONENT / DEFAULT_ENV_DOTFILE).write_text(
            f"{self.env_var}={self.env_var_value}"
        )
        self._run_test()

    def test_load_json(self) -> None:
        """Test load `.json` file"""

        env_var_value = "ENV_VAR_VALUE"
        env_file = self.t / REGISTER_RESET_COMPONENT / "env.json"
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
                self.t / REGISTER_RESET_COMPONENT,
                self.keys_file,
            )

    def test_default_resources_docker_compose(self) -> None:
        """Test default resources"""

        build_dir = self.t / DEFAULT_BUILD_FOLDER.format(build_hash_id())
        with mock.patch("os.chown"), OS_ENV_PATCH:
            result = self.run_cli((str(self.keys_file), "--o", str(build_dir)))

        assert result.exit_code == 0, result.output
        assert build_dir.exists()

        self.check_docker_compose_build(
            build_dir=build_dir,
        )
        path = build_dir / DockerComposeGenerator.output_name
        service_hash_id = get_service_hash_id(path)
        docker_compose = self.load_and_check_docker_compose_file(path, service_hash_id)
        abci_0_name = self.spec.get_abci_container_name(0)
        abci_0 = docker_compose["services"][abci_0_name]
        assert abci_0["mem_reservation"] == f"{DEFAULT_AGENT_MEMORY_REQUEST}M"
        assert abci_0["mem_limit"] == f"{DEFAULT_AGENT_MEMORY_LIMIT}M"
        assert abci_0["cpus"] == DEFAULT_AGENT_CPU_LIMIT

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
        path = build_dir / DockerComposeGenerator.output_name
        service_hash_id = get_service_hash_id(path)
        docker_compose = self.load_and_check_docker_compose_file(path, service_hash_id)
        abci_0_name = self.spec.get_abci_container_name(0)
        abci_0 = docker_compose["services"][abci_0_name]
        assert abci_0["mem_reservation"] == "2048M"
        assert abci_0["mem_limit"] == "4096M"
        assert abci_0["cpus"] == 2.0

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
