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

"""Fixture helpers."""
import logging
from typing import Generator, cast

import docker
import pytest
from aea_test_autonomy.docker.base import launch_many_containers

from packages.valory.agents.register_reset.tests.helpers.docker.docker import (
    SlowFlaskTendermintDockerImage,
)


@pytest.fixture
def flask_tendermint(
    tendermint_port: int,  # pylint: disable=redefined-outer-name
    nb_nodes: int,  # pylint: disable=redefined-outer-name
    abci_host: str,  # pylint: disable=redefined-outer-name
    abci_port: int,  # pylint: disable=redefined-outer-name
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator[SlowFlaskTendermintDockerImage, None, None]:
    """Launch the Flask server with Tendermint container."""
    client = docker.from_env()
    logging.info(
        f"Launching Tendermint nodes managed by Flask server at ports {[tendermint_port + i * 10 for i in range(nb_nodes)]}"
    )
    image = SlowFlaskTendermintDockerImage(
        client, abci_host, abci_port, tendermint_port
    )
    yield from cast(
        Generator[SlowFlaskTendermintDockerImage, None, None],
        launch_many_containers(image, nb_nodes, timeout, max_attempts),
    )
