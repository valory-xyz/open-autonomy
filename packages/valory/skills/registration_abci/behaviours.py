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
from typing import Dict, Generator, Set, Type, cast

from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.tendermint import TendermintMessage
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


TENDERMINT_CALLBACK_REQUEST_TIMEOUT = 1


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
    collected: Dict[str, str] = dict()

    @property
    def registered_addresses(self) -> Set[str]:
        """Agent addresses registered on-chain for the service"""
        return self.period_state.db.initial_data.get("agent_addresses", set())

    def is_correct_contract(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""

        performative = ContractApiMessage.Performative.GET_STATE
        contract_api_response = yield from self.get_contract_api_response(
            performative=performative,  # type: ignore
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="verify_contract",
        )
        if contract_api_response.performative != performative:
            self.context.logger.warning("`verify_contract` call unsuccessful!")
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
        if contract_api_response.performative != performative:
            self.context.logger.warning("get_service_info unsuccessful!")
            return {}
        return cast(dict, contract_api_response.state.body["verified"])

    def get_addresses(self) -> Generator[None, None, bool]:
        """Get addresses of agents registered for the service"""

        if (
            self.params.service_registry_address is None
        ):  # 0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0
            raise ValueError("Service registry contract address not provided")

        is_deployed = yield from self.is_correct_contract()
        if not is_deployed:
            self.context.logger.info("Service registry contract not deployed")
            return False

        # checks if service exists as prerequisite condition
        service_info = yield from self.get_service_info()
        if not service_info:
            self.context.logger.info("Service info could not be retrieved")
            return False

        # put service info in the shared state for p2p message handler
        registered_addresses = set(service_info["agent_instances"])
        if not registered_addresses:
            self.context.logger.info(f"No agent instances registered:\n{service_info}")
            return False

        my_address = self.context.agent_address
        if my_address not in registered_addresses:
            self.context.logger.info(
                f"You ({my_address}) are not registered:\n{service_info}"
            )

        self.period_state.db.initial_data.update(
            dict(registered_addresses=registered_addresses)
        )
        return True

    def make_tendermint_request(self, address: str) -> None:
        """Make Tendermint callback request"""

        dialogues = cast(TendermintDialogues, self.context.http_dialogues)
        performative = TendermintMessage.Performative.REQUEST
        message, dialogue = dialogues.create(
            counterparty=address, performative=performative
        )
        self.context.outbox.put_message(message=cast(TendermintMessage, message))
        nonce = self._get_request_nonce_from_dialogue(
            cast(TendermintDialogue, dialogue)
        )
        cast(Requests, self.context.requests).request_id_to_callback[
            nonce
        ] = self.get_callback_request()

    def process_response(self, message: TendermintMessage) -> None:
        """Process tendermint response messages"""

        if message.sender not in self.registered_addresses:
            self.context.logger.warning(
                f"Request from agent not registered on-chain:\n{message}"
            )
        elif message.performative == TendermintMessage.Performative.RESPONSE:
            self.collected[message.sender] = message.info
            self.context.logger.info(f"Collected {message.sender}: {message.info}")
        else:
            self.context.logger.info(f"Error: \n{message}")

    def async_act(self) -> Generator:
        """Act asynchronously"""

        # make service registry calls (only once)
        if not self.registered_addresses:
            successful = self.get_addresses()
            if not successful:
                return  # try again next async_act call
            self.context.logger.info(
                "Registered addresses retrieved from service registry contract"
            )

        # request tendermint config information from all agents
        not_yet_collected = self.registered_addresses.difference(self.collected)
        any(map(self.make_tendermint_request, not_yet_collected))  # consume

        # collect responses one-by-one
        timeout = TENDERMINT_CALLBACK_REQUEST_TIMEOUT
        for address in not_yet_collected:
            response = yield from self.wait_for_message(timeout=timeout)
            try:
                self.process_response(cast(TendermintMessage, response))
            except json.JSONDecodeError:
                self.context.logger.error(
                    f"Failed processing tendermint response from {address}"
                )

        # when all information is collected, update and restart tendermint
        if not self.registered_addresses.difference(self.collected):
            # TODO: update tendermint config here
            #  use ABCI connection to send info to tendermint server
            #  - implement `update_validators` endpoint on server
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
