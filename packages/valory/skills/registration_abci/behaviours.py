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

from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.connections.p2p_libp2p_client.connection import PUBLIC_ID
from packages.valory.protocols.tendermint import TendermintMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import TimeoutException
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.models import Requests
from packages.valory.skills.registration_abci.dialogues import (
    TendermintDialogue,
    TendermintDialogues,
)
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

TENDERMINT_CALLBACK_RESPONSE_TIMEOUT = 1


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

    state_id = "registration_startup"
    matching_round = RegistrationStartupRound
    local_tendermint_params: Optional[TendermintParams] = None
    ENCODING: str = "utf-8"

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
        self.context.logger.info(f"verify_contract response: {contract_api_response}")
        if contract_api_response.performative is not ContractApiMessage.Performative.STATE:
            self.context.logger.info("verify_contract call unsuccessful!")
            return False
        self.context.logger.info(f"VALID response: {contract_api_response}")
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
        log_msg = f"ServiceRegistryContract.getServiceInfo response"
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        return cast(dict, contract_api_response.state.body)

    def get_addresses(self) -> Generator[None, None, bool]:
        """Get addresses of agents registered for the service"""

        if self.params.service_registry_address is None:
            raise RuntimeError("Service registry contract address not provided")

        correctly_deployed = yield from self.is_correct_contract()
        if not correctly_deployed:
            log_message = "Service registry contract not correctly deployed"
            self.context.logger.info(log_message)
            return False

        # checks if service exists
        service_info = yield from self.get_service_info()
        if not service_info:
            self.context.logger.info("Service info could not be retrieved")
            return False

        # put service info in the shared state for p2p message handler
        registered_addresses = set(service_info["agent_instances"])
        self.context.logger.info(f"on-chain addresses: {registered_addresses}")
        # TEMP: replace for test debugging
        registered_addresses.remove("0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65")
        registered_addresses.add("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")

        self.context.logger.info(f"addresses after replacement: {registered_addresses}")
        if not registered_addresses:
            log_msg = f"No agent instances registered: {service_info}"
            self.context.logger.info(log_msg)
            return False

        my_address = self.context.agent_address
        if my_address not in registered_addresses:
            log_msg = f"You are not registered, your address: {my_address}"
            self.context.logger.info(f"{log_msg}:\n{registered_addresses}")
            return False

        # setup storage for collected tendermint configuration info
        info: Dict[str, str] = dict.fromkeys(registered_addresses)
        info[self.context.agent_address] = self.context.params.tendermint_url

        self.period_state.db.initial_data.update(dict(registered_addresses=info))
        log_msg = "Registered addresses retrieved from service registry contract"
        self.context.logger.info(f"{log_msg}:\n{info}")
        return True

    # def get_tendermint_configuration(self) -> Generator[None, None, bool]:
    #     """Make HTTP GET request to obtain agent's local Tendermint node parameters"""
    #
    #     url = self.tendermint_parameter_url
    #     result = yield from self.get_http_response(method="GET", url=url)
    #     try:
    #         response = json.loads(result.body.decode())
    #         self.local_tendermint_params = response['params']
    #         self.context.logger.info(f"Local Tendermint configuration obtained: {response}")
    #         return True
    #     except json.JSONDecodeError:
    #         self.context.logger.error(
    #             "Error communicating with Tendermint server on get_tendermint_configuration"
    #         )
    #         return False

    def request_tendermint_info(self, address: str) -> Generator[None, None, bool]:
        """Request Tendermint info from other agents"""
        self.context.logger.info(f"Trying to request_tendermint_info from {address}")

        dialogues = cast(TendermintDialogues, self.context.tendermint_dialogues)
        performative = TendermintMessage.Performative.REQUEST
        message, dialogue = dialogues.create(
            counterparty=address, performative=performative
        )
        message = cast(TendermintMessage, message)
        dialogue = cast(TendermintDialogue, dialogue)
        context = EnvelopeContext(connection_id=PUBLIC_ID)
        self.context.outbox.put_message(message=message, context=context)
        nonce = self._get_request_nonce_from_dialogue(dialogue)
        requests = cast(Requests, self.context.requests)
        requests.request_id_to_callback[nonce] = self.get_callback_request()
        try:
            self.context.logger.info("Waiting for tendermint_response message")
            # timeout = TENDERMINT_CALLBACK_RESPONSE_TIMEOUT + 9
            msg = yield from self.wait_for_message(timeout=1)  # TODO: error response not returned here
            self.context.logger.info(f"Tendermint response msg: {msg}")
            return True
        except TimeoutException:
            log_msg = "Timeout in request_tendermint_info waiting for"
            self.context.logger.info(f"{log_msg}: {address}")
            return False

    # def update_tendermint(self) -> Generator[None, None, bool]:
    #     """Make HTTP POST request to update agent's local Tendermint node"""
    #
    #     url = self.tendermint_parameter_url
    #     params = cast(TendermintParams, self.local_tendermint_params)
    #     params["p2p_seeds"] = list(self.registered_addresses.values())
    #     content = json.dumps(params).encode(self.ENCODING)
    #     result = yield from self.get_http_response(
    #         method="POST", url=url, content=content
    #     )
    #     try:
    #         response = json.loads(result.body.decode())
    #         self.context.logger.info(f"Local TendermintNode updated: {response}")
    #         return True
    #     except json.JSONDecodeError:
    #         self.context.logger.info(
    #             "Error communicating with Tendermint server on update_tendermint"
    #         )
    #         return False
    #
    # def start_tendermint(self) -> Generator[None, None, bool]:
    #     """Start up local Tendermint node"""
    #
    #     url = self.tendermint_start_url
    #     result = yield from self.get_http_response(method="GET", url=url)
    #     try:
    #         response = json.loads(result.body.decode())
    #         self.context.logger.info(f"Tendermint node restarted: {response}")
    #         return True
    #     except json.JSONDecodeError:
    #         self.context.logger.error(
    #             "Error communicating with Tendermint server on start_tendermint"
    #         )
    #         return False

    def async_act(self) -> Generator:
        """Act asynchronously"""

        self.context.logger.info("Time to async_act")

        # # collect personal Tendermint configuration
        # if not self.local_tendermint_params:
        #     successful = yield from self.get_tendermint_configuration()
        #     if not successful:
        #         yield from self.sleep(self.params.sleep_time)
        #         return

        self.context.logger.info(f"My address: {self.context.agent_address}")
        # incoming = self.context.outbox._multiplexer.in_queue.qsize()
        # outgoing = self.context.outbox._multiplexer.out_queue.qsize()
        # self.context.logger.info(f"Outbox: in = {incoming}, out = {outgoing}")
        # message_in_queue = self.context.message_in_queue.qsize()
        # self.context.logger.info(f"Messages in queue: {message_in_queue}")

        # make service registry contract call
        # if not self.registered_addresses:
        #     successful = yield from self.get_addresses()
        #     yield from self.sleep(3)  # wait for other agents
        #     if not successful:
        #         yield from self.sleep(self.params.sleep_time)
        #         return

        # TEMP: because `requests.exceptions.HTTPError: 503 Server Error: Service Temporarily Unavailable for url: https://staging.chain.autonolas.tech/`
        if not self.registered_addresses:
            registered_addresses = [
                "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
                "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
                "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            ]
            info: Dict[str, str] = dict.fromkeys(registered_addresses)
            info[self.context.agent_address] = self.context.params.tendermint_url
            self.period_state.db.initial_data.update(dict(registered_addresses=info))
            self.context.logger.info(f"Registered addresses: {registered_addresses}")
            i = registered_addresses.index(self.context.agent_address) + 1
            yield from self.sleep(i)  # wait for other agents

        self.context.logger.info(f"not yet collected: {self.not_yet_collected}")
        log_msg = f"Current collection behaviour: {self.registered_addresses}"
        self.context.logger.info(f"{log_msg}")

        # collect Tendermint config information
        # for address in self.not_yet_collected:
        while self.not_yet_collected:
            address = next(iter(self.not_yet_collected))
            yield from self.request_tendermint_info(address)
        # for address in self.not_yet_collected:
        #     self.context.logger.info(f"requesting from: {address}")
        #     self.request_tendermint_info(address)

        # yield from self.sleep(5)
        # self.context.logger.info(f"slept a bit")
        # if any(self.not_yet_collected):
        #     msg = yield from self.wait_for_message(timeout=3)
        #     self.context.logger.info(f"waited for msg: {msg}")

        if not any(self.not_yet_collected):
            log_msg = "Completed collecting Tendermint responses"
            self.context.logger.info(f"{log_msg}: {self.registered_addresses}")
        else:
            missing = sorted(self.not_yet_collected)
            self.context.logger.info(f"Still missing info on: {missing}")
            yield from self.sleep(self.params.sleep_time)
            return

        # # update Tendermint configuration
        # successful = yield from self.update_tendermint()
        # if not successful:
        #     yield from self.sleep(self.params.sleep_time)
        #     return
        #
        # # restart Tendermint with updated configuration
        # successful = yield from self.start_tendermint()
        # if not successful:
        #     yield from self.sleep(self.params.sleep_time)
        #     return

        self.context.logger.info(f"{self.__class__.__name__}.async_act executed")
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
