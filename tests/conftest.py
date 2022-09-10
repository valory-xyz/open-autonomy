# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
import inspect
import os
import platform
from pathlib import Path
from typing import Generator

import docker
import pytest
from aea_test_autonomy.docker.base import launch_image
from aea_test_autonomy.docker.registries import RegistriesDockerImage


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = Path(CUR_PATH, "..").resolve().absolute()
THIRD_PARTY_CONTRACTS = ROOT_DIR / "third_party"


skip_docker_tests = pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Docker daemon is not available in Windows and macOS CI containers.",
)


@pytest.fixture(scope="class")
def registries_scope_class() -> Generator:
    """Launch the Registry contracts image. This fixture is scoped to a class which means it will destroyed after running every test in a class."""
    client = docker.from_env()
    image = RegistriesDockerImage(
        client, third_party_contract_dir=THIRD_PARTY_CONTRACTS
    )
    yield from launch_image(image, timeout=2, max_attempts=20)
