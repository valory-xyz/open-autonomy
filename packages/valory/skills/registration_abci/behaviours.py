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

from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
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
        self.context.logger.info("Service info could not be retrieved")
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.info("`verify_contract` call unsuccessful!")
            return False
        return cast(bool, contract_api_response.state.body["verified"])

    def get_service_info(self) -> Generator[None, None, dict]:
        """Get service info available on-chain"""

        performative = ContractApiMessage.Performative.GET_STATE
        contract_api_response = yield from self.get_contract_api_response(
            performative=performative,  # type: ignore
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_service_info",
            service_id=self.params.on_chain_service_id,
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.info("get_service_info unsuccessful!")
            return {}
        return cast(dict, contract_api_response.state.body["info"])

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
        if not registered_addresses:
            log_msg = f"No agent instances registered:\n{service_info}"
            self.context.logger.info(log_msg)
            return False

        my_address = self.context.agent_address
        if my_address not in registered_addresses:
            log_msg = f"You are not registered:\n{service_info}"
            self.context.logger.info(log_msg)
            return False

        # setup storage for collected tendermint configuration info
        info: Dict[str, str] = dict.fromkeys(registered_addresses)
        info[self.context.agent_address] = self.context.params.tendermint_url

        self.period_state.db.initial_data.update(dict(registered_addresses=info))
        log_msg = "Registered addresses retrieved from service registry contract"
        self.context.logger.info(log_msg)
        return True

    def get_tendermint_configuration(self) -> Generator[None, None, bool]:
        """Make HTTP GET request to obtain agent's local Tendermint node parameters"""

        url = self.tendermint_parameter_url
        result = yield from self.get_http_response(method="GET", url=url)
        try:
            response = json.loads(result.body.decode())
            self.local_tendermint_params = response['params']
            self.context.logger.info(f"Local Tendermint configuration obtained: {response}")
            return True
        except json.JSONDecodeError:
            self.context.logger.error(
                "Error communicating with Tendermint server on get_tendermint_configuration"
            )
            return False

    def get_tendermint_response(self, address: str) -> Generator[None, None, bool]:
        """Get Tendermint response"""

        dialogues = cast(TendermintDialogues, self.context.tendermint_dialogues)
        performative = TendermintMessage.Performative.REQUEST
        message, dialogue = dialogues.create(
            counterparty=address, performative=performative
        )
        message = cast(TendermintMessage, message)
        dialogue = cast(TendermintDialogue, dialogue)
        self.context.outbox.put_message(message=message)
        nonce = self._get_request_nonce_from_dialogue(dialogue)
        requests = cast(Requests, self.context.requests)
        requests.request_id_to_callback[nonce] = self.get_callback_request()
        try:
            timeout = TENDERMINT_CALLBACK_RESPONSE_TIMEOUT
            yield from self.wait_for_message(timeout=timeout)
            return True
        except TimeoutException:
            return False

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
            self.context.logger.info(f"Tendermint node started: {response}")
            return True
        except json.JSONDecodeError:
            self.context.logger.error(
                "Error communicating with Tendermint server on start_tendermint"
            )
            return False

    def async_act(self) -> Generator:
        """Act asynchronously"""

        # collect personal Tendermint configuration
        if not self.local_tendermint_params:
            successful = yield from self.get_tendermint_configuration()
            if not successful:
                yield from self.sleep(self.params.sleep_time)
                return

        # make service registry contract call
        if not self.registered_addresses:
            successful = yield from self.get_addresses()
            if not successful:
                yield from self.sleep(self.params.sleep_time)
                return

        # collect Tendermint config information
        for address in self.not_yet_collected:
            yield from self.get_tendermint_response(address)

        if not any(self.not_yet_collected):
            self.context.logger.info("Completed collecting Tendermint responses")
        else:
            missing = sorted(self.not_yet_collected)
            self.context.logger.info(f"Still missing info on: {missing}")
            yield from self.sleep(self.params.sleep_time)
            return

        # update Tendermint configuration
        successful = yield from self.update_tendermint()
        if not successful:
            yield from self.sleep(self.params.sleep_time)
            return

        # restart Tendermint with updated configuration
        successful = yield from self.start_tendermint()
        if not successful:
            yield from self.sleep(self.params.sleep_time)
            return

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
