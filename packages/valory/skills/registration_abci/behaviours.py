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
from typing import Dict, Generator, Iterable, List, Optional, Set, Type, Union, cast

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


TendermintParams = Dict[
    str,
    Union[
        str,  # proxy_app, p2p_laddr, rpc_laddr
        List[str],  # p2p_seeds
        bool,  # consensus_create_empty_blocks
        Optional[str],  # home
    ],
]


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
    local_tendermint_params: Optional[TendermintParams] = None
    cooldown = 10  # testing purposes only

    @property
    def registered_addresses(self) -> Dict[str, str]:
        """Agent addresses registered on-chain for the service"""
        return self.period_state.db.initial_data.get("registered_addresses", {})

    @property
    def not_yet_collected(self) -> List[str]:
        """Agent addresses for which no Tendermint information has been retrieved"""
        if "registered_addresses" not in self.period_state.db.initial_data:
            raise RuntimeError("Must collect addresses from service registry first")
        return [k for k, v in self.registered_addresses.items() if not v]

    @property
    def missing_response_confirmations(self) -> Set[str]:
        """Agent addresses for which no Tendermint information has been retrieved"""
        if "response_confirmations" not in self.period_state.db.initial_data:
            raise RuntimeError("Must collect addresses from service registry first")
        confirmations = self.period_state.db.initial_data.get("response_confirmations")
        return set(self.registered_addresses).difference(confirmations)

    @property
    def tendermint_parameter_url(self) -> str:
        """Tendermint URL for obtaining and updating parameters"""
        return f"{self.params.tendermint_com_url}/params"

    @property
    def tendermint_start_url(self) -> str:
        """Tendermint URL for obtaining and updating parameters"""
        return f"{self.params.tendermint_com_url}/start"

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
        info: Dict[str, str] = dict.fromkeys(registered_addresses)
        info[self.context.agent_address] = self.context.params.tendermint_url

        self.period_state.db.initial_data.update(dict(registered_addresses=info))
        # self.period_state.db.initial_data.update(dict(response_confirmations=set()))
        log_msg = "Registered addresses retrieved from service registry contract"
        self.context.logger.info(f"{log_msg}: {info}")

    def get_tendermint_configuration(self) -> Generator[None, None, bool]:
        """Make HTTP GET request to obtain agent's local Tendermint node parameters"""

        url = self.tendermint_parameter_url
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
        self.context.logger.debug(f"current collection: {self.registered_addresses}")

    def update_tendermint(self) -> Generator[None, None, bool]:
        """Make HTTP POST request to update agent's local Tendermint node"""

        url = self.tendermint_parameter_url
        params = cast(TendermintParams, self.local_tendermint_params)
        params["p2p_seeds"] = list(self.registered_addresses.values())
        content = json.dumps(params).encode(self.ENCODING)
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

    def start_tendermint(self) -> Generator[None, None, bool]:
        """Start up local Tendermint node"""

        url = self.tendermint_start_url
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

        # # collect personal Tendermint configuration
        # if not self.local_tendermint_params:
        #     successful = yield from self.get_tendermint_configuration()
        #     if not successful:
        #         yield from self.sleep(self.params.sleep_time)
        #         return  # noqa: E800

        # make service registry contract call
        while not self.registered_addresses:
            yield from self.get_addresses()
            yield from self.sleep(self.params.sleep_time)

        # collect Tendermint config information from other agents
        while any(self.not_yet_collected):
            consume(map(self.request_tendermint_info, self.not_yet_collected))
            yield from self.sleep(self.params.sleep_time)

        log_msg = "Completed collecting Tendermint responses"
        self.context.logger.info(f"{log_msg}: {self.registered_addresses}")

        # while any(self.missing_response_confirmations):
        #     yield from self.sleep(self.params.sleep_time)
        # self.context._get_agent_context()

        # # update Tendermint configuration
        # successful = yield from self.update_tendermint()
        # if not successful:
        #     yield from self.sleep(self.params.sleep_time)
        #     return  # noqa: E800
        #
        # # restart Tendermint with updated configuration
        # successful = yield from self.start_tendermint()
        # if not successful:
        #     yield from self.sleep(self.params.sleep_time)
        #     return  # noqa: E800

        # TEST: artificial delay to allow catch up of other agents
        while self.cooldown:
            self.cooldown -= 1
            yield from self.sleep(self.params.sleep_time)

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
