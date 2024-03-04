# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

"""Test `valory/oar-{agent}` image."""

from pathlib import Path
from typing import cast

import docker
from aea.configurations.data_types import PackageId
from aea_test_autonomy.docker.tendermint import DEFAULT_ABCI_HOST, TendermintDockerImage
from aea_test_autonomy.helpers.async_utils import wait_for_condition
from docker.models.containers import Container

from autonomy.constants import (
    AUTONOMY_IMAGE_NAME,
    AUTONOMY_IMAGE_VERSION,
    DEFAULT_DOCKER_IMAGE_AUTHOR,
    OAR_IMAGE,
    TENDERMINT_IMAGE_NAME,
    TENDERMINT_IMAGE_VERSION,
)
from autonomy.deploy.constants import DOCKERFILES

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_images.base import BaseImageBuildTest


AGENT = PackageId.from_uri_path("agent/valory/offend_slash/0.1.0")
TENDERMINT_IMAGE = f"{TENDERMINT_IMAGE_NAME}:{TENDERMINT_IMAGE_VERSION}"


@skip_docker_tests
class TestOpenAutonomyBaseImage(BaseImageBuildTest):
    """Test image build and run."""

    client: docker.DockerClient
    agent: str
    path: Path = ROOT_DIR / "autonomy" / "data" / DOCKERFILES / "agent"
    tag: str = OAR_IMAGE.format(
        image_author=DEFAULT_DOCKER_IMAGE_AUTHOR, agent=AGENT.name, version="latest"
    )

    @classmethod
    def setup_class(cls) -> None:
        """Setup class."""
        super().setup_class()

        cls.agent = str(
            AGENT.with_hash(
                package_hash="bafybeih7chy5ajfycimrma3iqiu7u6ycoxrjnnlcwcfbgkbrou34m56cr4"
            ).public_id
        )

    def test_image_fail(self) -> None:
        """Test image build fail."""

        success, output = self.build_image(
            path=self.path,
            tag=self.tag,
            buildargs={},
        )

        assert not success
        assert (
            "The command '/bin/sh -c aea init --reset --remote --ipfs --author ${AUTHOR}' returned a non-zero code: 2"
            in output
        )

    def test_image(self) -> None:
        """Test image build."""

        # check build
        success, output = self.build_image(
            path=self.path,
            tag=self.tag,
            buildargs={
                "AUTONOMY_IMAGE_NAME": AUTONOMY_IMAGE_NAME,
                "AUTONOMY_IMAGE_VERSION": AUTONOMY_IMAGE_VERSION,
                "AEA_AGENT": self.agent,
                "AUTHOR": "ci",
            },
        )

        assert success, output
        assert "Successfully built the host dependencies" in output
        assert f"Successfully tagged {self.tag}" in output

        # check runtime
        tm_image = TendermintDockerImage(
            client=self.client,
        )
        tm_container = tm_image.create()

        agent_container = cast(
            Container,
            self.client.containers.run(
                image=self.tag,
                detach=True,
                network="host",
                extra_hosts={
                    DEFAULT_ABCI_HOST: "host-gateway",
                },
            ),
        )

        self.running_containers += [tm_container, agent_container]

        def _check_for_outputs() -> bool:
            """Check for required outputs."""
            return b"Starting AEA 'agent' in 'async' mode..." in agent_container.logs()

        try:
            wait_for_condition(
                condition_checker=_check_for_outputs,
                timeout=30,
                period=1,
            )
            successful = True
        except TimeoutError:
            successful = False

        assert (
            successful
        ), f"Agent runtime failed with error: {agent_container.logs().decode()}"
