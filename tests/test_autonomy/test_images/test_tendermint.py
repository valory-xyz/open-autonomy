# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Test `valory/open-autonomy-tendermint` image."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import docker
from aea_test_autonomy.docker.tendermint import DEFAULT_ABCI_HOST
from aea_test_autonomy.helpers.async_utils import wait_for_condition
from docker.models.containers import Container

from autonomy.constants import TENDERMINT_IMAGE_NAME, TENDERMINT_IMAGE_VERSION
from autonomy.deploy.constants import DOCKERFILES

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_images.base import BaseImageBuildTest


@skip_docker_tests
class TestTendermintImage(BaseImageBuildTest):
    """Test image build and run."""

    client: docker.DockerClient
    path: Path = ROOT_DIR / "deployments" / DOCKERFILES / "tendermint"
    tag: str = f"{TENDERMINT_IMAGE_NAME}:{TENDERMINT_IMAGE_VERSION}"

    def test_image(self) -> None:
        """Test image build."""

        # check build
        success, output = self.build_image(
            path=self.path,
            tag=self.tag,
        )

        assert success, output
        assert f"Successfully tagged {self.tag}" in output

        # check runtime

        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir, "logs.txt")
            log_file.touch()

            tm_container = cast(
                Container,
                self.client.containers.run(
                    image=self.tag,
                    detach=True,
                    network="host",
                    extra_hosts={
                        DEFAULT_ABCI_HOST: "host-gateway",
                    },
                    environment={
                        "TMHOME": "~/.tendermint",
                        "ID": "3",
                        "PROXY_APP": "tcp://localhost:26658",
                        "CREATE_EMPTY_BLOCKS": "false",
                        "LOG_FILE": "/logs/logs.txt",
                    },
                    volumes={
                        temp_dir: {"bind": "/logs", "mode": "rw"},
                    },
                ),
            )

            self.running_containers = [
                tm_container,
            ]

            def _check_for_outputs() -> bool:
                """Check for required outputs."""
                return (
                    "abci.socketClient failed to connect"
                    in tm_container.logs().decode()
                )

            try:
                wait_for_condition(
                    condition_checker=_check_for_outputs,
                    timeout=10,
                    period=1,
                )
                successful = True
            except TimeoutError:
                successful = False

            assert successful, f"Tendermint runtime failed with {log_file.read_text()}"
