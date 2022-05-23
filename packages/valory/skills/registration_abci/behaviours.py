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

"""This module contains the behaviours for the 'abci' skill."""
import collections
import json
from typing import Any, Dict, Generator, Iterable, List, Set, Type, cast

from aea.mail.base import EnvelopeContext

from packages.valory.connections.p2p_libp2p_client.connection import (
    PUBLIC_ID as P2P_LIBP2P_CLIENT_PUBLIC_ID,
)
from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.tendermint import TendermintMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.registration_abci.dialogues import TendermintDialogues
from packages.valory.skills.registration_abci.payloads import RegistrationPayload
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    RegistrationRound,
    RegistrationStartupRound,
)


consensus_params = (
    {
        "block": {"max_bytes": "22020096", "max_gas": "-1", "time_iota_ms": "1000"},
        "evidence": {
            "max_age_num_blocks": "100000",
            "max_age_duration": "172800000000000",
            "max_bytes": "1048576",
        },
        "validator": {"pub_key_types": ["ed25519"]},
        "version": {},
    },
)


def consume(iterator: Iterable) -> None:
    """Consume the iterator"""
    collections.deque(iterator, maxlen=0)


class RegistrationBaseBehaviour(BaseState):
    """Register to the next periods."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            initialisation = (
                json.dumps(self.period_state.db.initial_data, sort_keys=True)
                if self.period_state.db.initial_data != {}
                else None
            )
            payload = RegistrationPayload(
                self.context.agent_address, initialisation=initialisation
            )

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class RegistrationStartupBehaviour(RegistrationBaseBehaviour):
    """Register to the next periods."""

    ENCODING: str = "utf-8"
    state_id = "registration_startup"
    matching_round = RegistrationStartupRound
    local_tendermint_params: Dict[str, Any] = {}

    @property
    def registered_addresses(self) -> Dict[str, Dict[str, Any]]:
        """Agent addresses registered on-chain for the service"""
        return self.period_state.db.initial_data.get("registered_addresses", {})

    @property
    def _not_yet_collected(self) -> List[str]:
        """Agent addresses for which no Tendermint information has been retrieved"""
        if "registered_addresses" not in self.period_state.db.initial_data:
            raise RuntimeError("Must collect addresses from service registry first")
        return [k for k, v in self.registered_addresses.items() if not v]

    @property
    def tendermint_parameter_url(self) -> str:
        """Tendermint URL for obtaining and updating parameters"""
        return f"{self.params.tendermint_com_url}/params"

    @property
    def tendermint_hard_reset_url(self) -> str:
        """Tendermint URL for obtaining and updating parameters"""
        return f"{self.params.tendermint_com_url}/hard_reset"

    def is_correct_contract(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""

        performative = ContractApiMessage.Performative.GET_STATE
        contract_api_response = yield from self.get_contract_api_response(
            performative=performative,  # type: ignore
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="verify_contract",
        )
        if (
            contract_api_response.performative
            is not ContractApiMessage.Performative.STATE
        ):
            self.context.logger.info("verify_contract call unsuccessful!")
            return False
        log_msg = "ServiceRegistryContract.is_correct_contract response"
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        return cast(bool, contract_api_response.state.body["verified"])

    def get_service_info(self) -> Generator[None, None, dict]:
        """Get service info available on-chain"""

        performative = ContractApiMessage.Performative.GET_STATE
        service_id = int(self.params.on_chain_service_id)
        kwargs = dict(
            performative=performative,  # type: ignore
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_service_info",
            service_id=service_id,
        )
        contract_api_response = yield from self.get_contract_api_response(**kwargs)
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            log_msg = "get_service_info unsuccessful with"
            self.context.logger.info(f"{log_msg}: {kwargs}\n{contract_api_response}")
            return {}
        log_msg = "ServiceRegistryContract.getServiceInfo response"
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        return cast(dict, contract_api_response.state.body)

    def get_addresses(self) -> Generator:
        """Get addresses of agents registered for the service"""

        if self.context.params.service_registry_address is None:
            raise RuntimeError("Service registry contract address not provided")

        correctly_deployed = yield from self.is_correct_contract()
        if not correctly_deployed:
            log_message = "Service registry contract not correctly deployed"
            self.context.logger.info(log_message)
            return

        # checks if service exists
        service_info = yield from self.get_service_info()
        if not service_info:
            self.context.logger.info("Service info could not be retrieved")
            return

        registered_addresses = set(service_info["agent_instances"])
        if not registered_addresses:
            log_msg = f"No agent instances registered: {service_info}"
            self.context.logger.info(log_msg)
            return

        my_address = self.context.agent_address
        if my_address not in registered_addresses:
            log_msg = f"You are not registered, your address: {my_address}"
            self.context.logger.info(f"{log_msg}:\n{registered_addresses}")
            return

        # put service info in the shared state for p2p message handler
        info: Dict[str, Dict[str, str]] = dict.fromkeys(registered_addresses)
        validator_config = dict(
            tendermint_url=self.context.params.tendermint_url,
            address=self.local_tendermint_params["address"],
            pub_key=self.local_tendermint_params["pub_key"],
        )
        info[self.context.agent_address] = validator_config

        self.period_state.db.initial_data.update(dict(registered_addresses=info))
        log_msg = "Registered addresses retrieved from service registry contract"

        self.context.logger.info(f"{log_msg}: {info}")

    def get_tendermint_configuration(self) -> Generator[None, None, bool]:
        """Make HTTP GET request to obtain agent's local Tendermint node parameters"""

        url = self.tendermint_parameter_url
        self.context.logger.info(f"GET request local config at: {url}")

        result = yield from self.get_http_response(method="GET", url=url)
        try:
            response = json.loads(result.body.decode())
            self.local_tendermint_params = response["params"]
            self.context.logger.info(
                f"Local Tendermint configuration obtained: {response}"
            )
            return True
        except json.JSONDecodeError:
            self.context.logger.error(
                "Error communicating with Tendermint server on get_tendermint_configuration"
            )
            return False

    def request_tendermint_info(self, address: str) -> None:
        """Request Tendermint info from other agents"""

        self.context.logger.info(f"Requesting Tendermint info from {address}")
        dialogues = cast(TendermintDialogues, self.context.tendermint_dialogues)
        performative = TendermintMessage.Performative.REQUEST
        message, _ = dialogues.create(counterparty=address, performative=performative)
        message = cast(TendermintMessage, message)
        context = EnvelopeContext(connection_id=P2P_LIBP2P_CLIENT_PUBLIC_ID)
        self.context.outbox.put_message(message=message, context=context)
        self.context.logger.info(f"Requested Tendermint info from {address}")

    def update_tendermint(self) -> Generator[None, None, bool]:
        """Make HTTP POST request to update agent's local Tendermint node"""

        url = self.tendermint_parameter_url

        registered_addresses = [
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
            "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        ]
        validators = []
        for agent_address, validator_config in self.registered_addresses.items():
            i = registered_addresses.index(agent_address)
            validator = dict(
                address=validator_config["address"],
                pub_key=validator_config["pub_key"],
                power="1",
                name=f"node{i}",
            )
            validators.append(validator)

        data = {}
        data["validators"] = validators
        data["genesis_config"] = dict(  # type: ignore
            genesis_time="2022-05-20T16:00:21.735122717Z",
            chain_id="chain-c4daS1",
            consensus_params=consensus_params,
        )
        self.context.logger.info(f"POST request local config at {url}: {data}")

        content = json.dumps(data).encode(self.ENCODING)
        result = yield from self.get_http_response(
            method="POST", url=url, content=content
        )
        try:
            response = json.loads(result.body.decode())
            self.context.logger.info(f"Local TendermintNode updated: {response}")
            return True
        except json.JSONDecodeError:
            self.context.logger.info(
                "Error communicating with Tendermint server on update_tendermint"
            )
            return False

    def restart_tendermint(self) -> Generator[None, None, bool]:
        """Restart up local Tendermint node"""

        self.context.logger.info("Restarting tendermint")
        url = self.tendermint_hard_reset_url
        result = yield from self.get_http_response(method="GET", url=url)
        try:
            response = json.loads(result.body.decode())
            self.context.logger.info(f"Tendermint node restarted: {response}")
            return True
        except json.JSONDecodeError:
            self.context.logger.error(
                "Error communicating with Tendermint server on start_tendermint"
            )
            return False

    def async_act(self) -> Generator:
        """Act asynchronously"""

        self.context.logger.info(f"My address: {self.context.agent_address}")
        # sleep to ensure it crashes here, otherwise possible it completes entire registration
        yield from self.sleep(2)

        # collect personal Tendermint configuration
        if not self.local_tendermint_params:
            successful = yield from self.get_tendermint_configuration()
            if not successful:
                yield from self.sleep(self.params.sleep_time)
                return

        # make service registry contract call
        while not self.registered_addresses:
            yield from self.get_addresses()
            yield from self.sleep(self.params.sleep_time)

        # collect Tendermint config information from other agents
        while any(self._not_yet_collected):
            consume(map(self.request_tendermint_info, self._not_yet_collected))
            yield from self.sleep(self.params.sleep_time + 2)

        log_msg = "Completed collecting Tendermint responses"
        self.context.logger.info(f"{log_msg}: {self.registered_addresses}")

        # update Tendermint configuration
        successful = yield from self.update_tendermint()
        if not successful:
            yield from self.sleep(self.params.sleep_time)
            return

        # restart Tendermint with updated configuration
        successful = yield from self.restart_tendermint()
        if not successful:
            yield from self.sleep(self.params.sleep_time)
            return

        self.context.logger.info("RegistrationStartupBehaviour executed")
        yield from super().async_act()


class RegistrationBehaviour(RegistrationBaseBehaviour):
    """Register to the next periods."""

    state_id = "registration"
    matching_round = RegistrationRound


class AgentRegistrationRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the registration."""

    initial_state_cls = RegistrationStartupBehaviour
    abci_app_cls = AgentRegistrationAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {  # type: ignore
        RegistrationBehaviour,  # type: ignore
        RegistrationStartupBehaviour,  # type: ignore
    }
