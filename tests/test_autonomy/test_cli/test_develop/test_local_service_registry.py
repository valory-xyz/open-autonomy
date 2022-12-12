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
from typing import Tuple, cast

import docker
import pytest
import requests
from _pytest.capture import CaptureFixture  # type: ignore

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

    def setup(self) -> None:
        """Setup test."""
        super().setup()
        os.chdir(self.t)

    def test_run_service_locally(
        self,
    ) -> None:
        """Run test."""

        self.running_process = self._invoke_command()
        max_retries = 30
        timeout = 5
        expected = (
            "Deploying contracts with the account: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "Account balance: 10000000000000000000000",
            "Owner of created components and agents: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "ComponentRegistry deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3",
            "AgentRegistry deployed to: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
            "RegistriesManager deployed to: 0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0",
            "ServiceRegistry deployed to: 0x998abeb3E57409262aE5b751f60747921B33613E",
            "ServiceManager deployed to: 0x70e0bA845a1A0F2DA3359C97E0285013525FFC49",
            "Gnosis Safe master copy deployed to: 0x4826533B4897376654Bb4d4AD88B7faFD0C98528",
            "Gnosis Safe proxy factory deployed to: 0x99bbA657f2BbC93c02D617f8bA121cB8Fc104Acf",
            "Gnosis Safe Multisig deployed to: 0x0E801D84Fa97b50751Dbf25036d067dCf18858bF",
            "Gnosis Safe Multisig with same address deployed to: 0x8f86403A4DE0BB5791fa46B8e795C547942fE4Cf",
            "Gnosis Safe Multisend deployed to: 0x9d4454B023096f34B160D6B654540c56A1F81688",
        )

        for _ in range(max_retries):
            try:
                res = requests.get(self.expected_network_address)
                assert res.status_code == 200, "bad response from the network"
                # we return in this case
                self._stop_cli_process()
                captured = cast(CaptureFixture, self.cli_runner.capfd).readouterr()
                missing = set(expected).difference(captured.out.split("\n"))
                assert not missing, missing
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
