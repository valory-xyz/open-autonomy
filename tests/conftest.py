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
from typing import List, Tuple

import docker
import pytest

from tests.helpers.constants import KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.docker.base import launch_image
from tests.helpers.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)
from tests.helpers.docker.tendermint import (
    DEFAULT_PROXY_APP,
    DEFAULT_TENDERMINT_PORT,
    TendermintDockerImage,
)


ROOT_DIR = _ROOT_DIR


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


@pytest.fixture()
def hardhat_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_HARDHAT_PORT


@pytest.fixture()
def key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for hardhat."""
    return KEY_PAIRS


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="function")
def gnosis_safe_hardhat(
    hardhat_port,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the HardHat node with Gnosis Safe contracts deployed."""
    client = docker.from_env()
    image = GnosisSafeNetDockerImage(client, hardhat_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)
