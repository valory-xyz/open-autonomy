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

"""Test `service-registry-network` command."""

import multiprocessing
import os
import time
from typing import Tuple

import docker
import pytest
import requests

from autonomy.constants import (
    SERVICE_REGISTRY_CONTRACT_CONTAINER_NAME as CONTAINER_NAME,
)

from tests.conftest import skip_docker_tests
from tests.test_autonomy.test_cli.base import BaseCliTest


@pytest.mark.integration
@skip_docker_tests
class TestRunServiceLocally(BaseCliTest):
    """Test `service-registry-network` command."""

    cli_options: Tuple[str, ...] = (
        "develop",
        "service-registry-network",
    )
    expected_network_address = "http://localhost:8545"
    running_process: multiprocessing.Process

    @classmethod
    def setup(cls) -> None:
        """Setup test."""
        super().setup()
        os.chdir(cls.t)

    def test_run_service_locally(
        self,
    ) -> None:
        """Run test."""
        self.running_process = self._invoke_command()
        max_retries = 30
        timeout = 5

        for _ in range(max_retries):
            try:
                res = requests.get(self.expected_network_address)
                assert res.status_code == 200, "bad response from the network"
                # we return in this case
                self._stop_cli_process()
                return
            except requests.ConnectionError:
                # the container is not yet available
                time.sleep(timeout)

        self._stop_cli_process()

        raise AssertionError(f"failed to start network after {max_retries} tries")

    def _stop_cli_process(
        self,
    ) -> None:
        """Kill the process running the CLI."""
        if self.running_process is not None:
            self.running_process.terminate()
            client = docker.from_env()
            client.containers.get(CONTAINER_NAME).kill()
            client.containers.get(CONTAINER_NAME).remove()

    def _invoke_command(self) -> multiprocessing.Process:
        """Run the command on a different process, as it blocks."""
        process = multiprocessing.Process(target=self.run_cli)
        process.start()
        return process
