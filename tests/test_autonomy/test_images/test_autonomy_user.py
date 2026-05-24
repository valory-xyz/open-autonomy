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

"""Test `valory/open-autonomy-user` image."""

from pathlib import Path
from typing import cast

import docker
import pytest
from docker.models.containers import Container

from autonomy import __version__
from autonomy.constants import AUTONOMY_IMAGE_NAME
from autonomy.deploy.constants import DOCKERFILES

from tests.conftest import ROOT_DIR
from tests.test_autonomy.test_images.base import BaseImageBuildTest


@pytest.mark.skip(
    reason=(
        "Temporary skip untile we figure out the volume size issue "
        "https://forums.docker.com/t/error-response-from-daemon-error-creating-overlay-mount-to-var-lib-docker-overlay2-merged-no-such-file-or-directory-error-failed-to-start-containers-mydocker/123365"
    )
)
class TestOpenAutonomyUserImage(BaseImageBuildTest):
    """Test image build and run."""

    client: docker.DockerClient
    path: Path = ROOT_DIR / "deployments" / DOCKERFILES / "autonomy-user"
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
                command=["-c", "autonomy --version"],
                detach=True,
            ),
        )
        container.wait()
        assert __version__.encode() in container.logs()
