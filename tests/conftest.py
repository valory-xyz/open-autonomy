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

"""Conftest module for Pytest."""
import docker
import pytest

from tests.helpers.docker.base import launch_image
from tests.helpers.docker.tendermint import (
    DEFAULT_PROXY_APP,
    DEFAULT_TENDERMINT_PORT,
    TendermintDockerImage,
)


DEFAULT_ASYNC_TIMEOUT = 5.0
HTTP_LOCALHOST = "http://localhost"


@pytest.fixture()
def tendermint_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_TENDERMINT_PORT


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="function")
def tendermint(
    tendermint_port,
    proxy_app: str = DEFAULT_PROXY_APP,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the Ganache image."""
    client = docker.from_env()
    image = TendermintDockerImage(client, tendermint_port, proxy_app)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.mark.integration
class UseTendermint:
    """Inherit from this class to use Tendermint."""

    @pytest.fixture(autouse=True)
    def _start_tendermint(self, tendermint, tendermint_port):
        """Start a Tendermint image."""
        self.tendermint_port = tendermint_port
