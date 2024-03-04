# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2024 Valory AG
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
# pylint: disable=broad-except,unspecified-encoding,import-error,redefined-outer-name

"""End2End tests base classes for the Termination agent."""
import web3
from aea.configurations.base import PublicId
from aea_test_autonomy.base_test_classes.agents import BaseTestEnd2End
from aea_test_autonomy.configurations import KEY_PAIRS as _HARDHAT_KEY_PAIRS
from aea_test_autonomy.docker.registries import (
    DEFAULT_HARDHAT_ADDR as _DEFAULT_HARDHAT_ADDR,
)
from aea_test_autonomy.docker.registries import (
    DEFAULT_HARDHAT_PORT as _DEFAULT_HARDHAT_PORT,
)
from aea_test_autonomy.docker.registries import (
    GNOSIS_SAFE_MULTISEND as _DEFAULT_MULTISEND_ADDRESS,
)
from aea_test_autonomy.docker.registries import (
    SERVICE_MULTISIG_1 as _DEFAULT_SAFE_CONTRACT_ADDRESS,
)
from aea_test_autonomy.docker.registries import (
    SERVICE_REGISTRY as _DEFAULT_SERVICE_REGISTRY_ADDRESS,
)
from web3.types import Wei


TERMINATION_TIMEOUT = 120


class BaseTestTerminationEnd2End(
    BaseTestEnd2End
):  # pylint: disable=too-few-public-methods
    """
    Extended base class for conducting E2E tests with `termination_abci` activated.

    Test subclasses must set NB_AGENTS, agent_package, wait_to_finish and check_strings.
    """

    skill_package = "valory/register_termination_abci:0.1.0"
    SAFE_CONTRACT_ADDRESS = _DEFAULT_SAFE_CONTRACT_ADDRESS
    SERVICE_REGISTRY_ADDRESS = _DEFAULT_SERVICE_REGISTRY_ADDRESS
    MULTISEND_ADDRESS = _DEFAULT_MULTISEND_ADDRESS
    SERVICE_OWNER_ADDRESS, SERVICE_OWNER_PK = _HARDHAT_KEY_PAIRS[0]
    NETWORK_ENDPOINT = f"{_DEFAULT_HARDHAT_ADDR}:{_DEFAULT_HARDHAT_PORT}"
    CHAIN_ID = 31337
    SERVICE_ID = 1
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.service_registry_address",
            "value": SERVICE_REGISTRY_ADDRESS,
        },
        {
            "dotted_path": f"{__args_prefix}.on_chain_service_id",
            "value": SERVICE_ID,
        },
        {
            "dotted_path": f"{__args_prefix}.multisend_address",
            "value": MULTISEND_ADDRESS,
        },
    ]

    def _send_service_termination_signal(self) -> None:
        """
        Sends a termination signal to the service.

        The termination signal is just a zero transfer to the safe contract by the service.
        """
        instance = web3.Web3(web3.HTTPProvider(self.NETWORK_ENDPOINT))
        zero_eth = Wei(0)
        checksum_sender_address = instance.to_checksum_address(
            self.SERVICE_OWNER_ADDRESS
        )
        checksum_receiver_address = instance.to_checksum_address(
            self.SAFE_CONTRACT_ADDRESS
        )

        raw_tx = {
            "to": checksum_receiver_address,
            "from": checksum_sender_address,
            "value": zero_eth,
            "gas": 100000,
            "chainId": self.CHAIN_ID,
            "gasPrice": instance.eth.gas_price,
            "nonce": instance.eth.get_transaction_count(checksum_sender_address),
        }
        signed_tx = instance.eth.account.sign_transaction(
            raw_tx, private_key=self.SERVICE_OWNER_PK
        )
        instance.eth.send_raw_transaction(signed_tx.rawTransaction)

    def test_run(self, nb_nodes: int) -> None:
        """Run the test."""
        self._send_service_termination_signal()
        self.prepare_and_launch(nb_nodes)
        self.health_check(
            max_retries=self.HEALTH_CHECK_MAX_RETRIES,
            sleep_interval=self.HEALTH_CHECK_SLEEP_INTERVAL,
        )
        self.check_aea_messages()
        self.terminate_agents(timeout=TERMINATION_TIMEOUT)
