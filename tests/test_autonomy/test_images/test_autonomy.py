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

"""Test `valory/open-autonomy` image."""

from pathlib import Path
from typing import cast

import docker
from docker.models.containers import Container

from autonomy.constants import AUTONOMY_IMAGE_NAME
from autonomy.deploy.constants import DOCKERFILES

from tests.conftest import ROOT_DIR, skip_docker_tests
from tests.test_autonomy.test_images.base import BaseImageBuildTest


@skip_docker_tests
class TestOpenAutonomyBaseImage(BaseImageBuildTest):
    """Test image build and run."""

    client: docker.DockerClient
    path: Path = ROOT_DIR / "deployments" / DOCKERFILES / "autonomy"
    tag: str = f"{AUTONOMY_IMAGE_NAME}:latest"

    def test_image(self) -> None:
        """Test image build."""

        success, output = self.build_image(
            path=self.path,
            tag=self.tag,
        )

        assert success, output
        assert "Successfully built" in output

        container = cast(
            Container,
            self.client.containers.run(
                image=self.tag,
                command=["-c", "ls"],
                detach=True,
            ),
        )

        container.wait()

        assert b"scripts" in container.logs()
