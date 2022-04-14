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
import json
import logging
from typing import Generator, Set, Type, Tuple, cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.registration_abci.payloads import RegistrationPayload
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    RegistrationRound,
    RegistrationStartupRound,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.contracts.service_registry.contract import (
    ServiceRegistryContract,
)
from packages.valory.protocols.tendermint import TendermintMessage
from packages.valory.skills.registration_abci.dialogues import (
    TendermintDialogue,
    TendermintDialogues,
)
from packages.valory.skills.abstract_round_abci.models import Requests

TENDERMINT_TIMEOUT = 10


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
    collected: Set[str] = set()

    def has_contract_been_deployed(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""

        performative = ContractApiMessage.Performative.GET_STATE
        contract_api_response = yield from self.get_contract_api_response(
            performative=performative,
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="verify_contract",
        )
        if contract_api_response.performative != performative:
            self.context.logger.warning("`verify_contract` call unsuccessful!")
            return False
        return cast(bool, contract_api_response.state.body["verified"])

    def service_exists(self) -> Generator[None, None, bool]:
        """Service existing on-chain verification."""

        performative = ContractApiMessage.Performative.GET_STATE
        contract_api_response = yield from self.get_contract_api_response(
            performative=performative,
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="exists",
            # service_id=self.params.on_chain_service_id
        )
        if contract_api_response.performative != performative:
            self.context.logger.warning("`exists` call unsuccessful!")
            return False
        return cast(bool, contract_api_response.state.body["verified"])

    def get_service_info(self) -> Generator[None, None, dict]:
        performative = ContractApiMessage.Performative.GET_STATE
        contract_api_response = yield from self.get_contract_api_response(
            performative=performative,
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_service_info",
            # service_id=self.params.on_chain_service_id
        )
        if contract_api_response.performative != performative:
            self.context.logger.warning("get_service_info unsuccessful!")
            return {}
        return cast(dict, contract_api_response.state.body["verified"])

    def get_addresses(self) -> Set[str]:
        """Get addresses of agents registered for the service"""

        if self.params.service_registry_address is None:  # 0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0
            raise ValueError(f"Service registry contract address not provided")

        is_deployed = yield from self.has_contract_been_deployed()
        if not is_deployed:
            raise ValueError(f"Service registry contract not deployed")

        service_exists = yield from self.service_exists()
        if not service_exists:
            raise ValueError(f"Service does not exist on-chain")

        service_info = yield from self.get_service_info()
        if not service_info:
            raise ValueError(f"Service info could not be retrieved")

        # put service info in the shared state for p2p message handler
        self.period_state.db.initial_data.update(dict(service_info=service_info))
        return set(service_info["agent_instances"])

    def build_tendermint_request_message(self, address: str) -> Tuple[TendermintMessage, TendermintDialogue]:
        """Build Tendermint request message"""
        dialogues = cast(TendermintDialogues, self.context.http_dialogues)
        message, dialogue = dialogues.create(
            counterparty=address,
            performative=TendermintMessage.Performative.TENDERMINT_CONFIG_REQUEST,
        )
        return cast(TendermintMessage, message), cast(TendermintDialogue, dialogue)

    def make_tendermint_request(self, message, dialogue) -> Generator[None, None, TendermintMessage]:
        """Make Tendermint request"""
        self.context.outbox.put_message(message=message)
        nonce = self._get_request_nonce_from_dialogue(dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[nonce] = self.get_callback_request()
        response = yield from self.wait_for_message(timeout=TENDERMINT_TIMEOUT)
        return cast(TendermintMessage, response)

    def async_act(self) -> Generator:

        # make service registry calls (only once)
        service_info = self.period_state.db.initial_data.get("service_info")
        if not service_info:
            self.collected = self.get_addresses()

        # collect tendermint config information
        registered_addresses = set(service_info["agent_instances"])
        not_yet_collected = registered_addresses.difference(self.collected)
        for address in not_yet_collected:
            message, dialogue = self.build_tendermint_request_message(address)
            response = yield from self.make_tendermint_request(message, dialogue)
            response = json.loads(response.body.decode())
            # TODO: read response
            #  if it contains the requested info, store it, add address to self.collected

        # when all information present, update and restart tendermint
        if registered_addresses == self.collected:
            # TODO: update tendermint config here
            self.reset_tendermint_with_wait()

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
