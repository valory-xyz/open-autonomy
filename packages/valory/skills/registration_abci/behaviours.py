# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
import datetime
import json
from abc import ABC
from enum import Enum
from typing import Any, Dict, Generator, Optional, Set, Type, cast

from aea.mail.base import EnvelopeContext

from packages.valory.connections.p2p_libp2p_client.connection import (
    PUBLIC_ID as P2P_LIBP2P_CLIENT_PUBLIC_ID,
)
from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.tendermint import TendermintMessage
from packages.valory.skills.abstract_round_abci.base import ABCIAppInternalError
from packages.valory.skills.abstract_round_abci.behaviour_utils import TimeoutException
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.utils import parse_tendermint_p2p_url
from packages.valory.skills.registration_abci.dialogues import TendermintDialogues
from packages.valory.skills.registration_abci.models import SharedState
from packages.valory.skills.registration_abci.payloads import RegistrationPayload
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    RegistrationRound,
    RegistrationStartupRound,
)


NODE = "node_{address}"
WAIT_FOR_BLOCK_TIMEOUT = 60.0  # 1 minute


class RegistrationBaseBehaviour(BaseBehaviour, ABC):
    """Agent registration to the FSM App."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            initialisation = json.dumps(
                self.synchronized_data.db.setup_data, sort_keys=True
            )
            payload = RegistrationPayload(
                self.context.agent_address, initialisation=initialisation
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class RegistrationStartupBehaviour(RegistrationBaseBehaviour):
    """Agent registration to the FSM App."""

    ENCODING: str = "utf-8"
    matching_round = RegistrationStartupRound
    local_tendermint_params: Dict[str, Any] = {}
    updated_genesis_data: Dict[str, Any] = {}
    collection_complete: bool = False

    class LogMessages(Enum):
        """Log messages used in RegistrationStartupBehaviour"""

        config_sharing = "Sharing Tendermint config on start-up?"
        # request personal tendermint configuration
        request_personal = "Request validator config from personal Tendermint node"
        response_personal = "Response validator config from personal Tendermint node"
        failed_personal = "Failed validator config from personal Tendermint node"
        # verify deployment on-chain contract
        request_verification = "Request service registry contract verification"
        response_verification = "Response service registry contract verification"
        failed_verification = "Failed service registry contract verification"
        # request service info from on-chain contract
        request_service_info = "Request on-chain service info"
        response_service_info = "Response on-chain service info"
        failed_service_info = "Failed on-chain service info"
        # request tendermint configuration other agents
        request_others = "Request Tendermint config info from other agents"
        collection_complete = "Completed collecting Tendermint configuration responses"
        # update personal tendermint node config
        request_update = "Request update Tendermint node configuration"
        response_update = "Response update Tendermint node configuration"
        failed_update = "Failed update Tendermint node configuration"
        # exceptions
        no_contract_address = "Service registry contract address not provided"
        no_on_chain_service_id = "On-chain service id not provided"
        contract_incorrect = "Service registry contract not correctly deployed"
        no_agents_registered = "No agents registered on-chain"
        self_not_registered = "This agent is not registered on-chain"

        def __str__(self) -> str:
            """For ease of use in formatted string literals"""
            return self.value

    @property
    def registered_addresses(self) -> Dict[str, Dict[str, Any]]:
        """Agent addresses registered on-chain for the service"""
        return cast(
            Dict[str, Dict[str, Any]],
            self.synchronized_data.db.get("registered_addresses", {}),
        )

    @property
    def tendermint_parameter_url(self) -> str:
        """Tendermint URL for obtaining and updating parameters"""
        return f"{self.params.tendermint_com_url}/params"

    def _decode_result(
        self, message: HttpMessage, error_log: LogMessages
    ) -> Optional[Dict[str, Any]]:
        """Decode a http message's body.

        :param message: the http message.
        :param error_log: a log to prefix potential errors with.
        :return: the message's body, as a dictionary
        """
        try:
            response = json.loads(message.body.decode())
        except json.JSONDecodeError as error:
            self.context.logger.error(f"{error_log}: {error}")
            return None

        if not response["status"]:  # pragma: no cover
            self.context.logger.error(f"{error_log}: {response['error']}")
            return None

        return response

    def is_correct_contract(
        self, service_registry_address: str
    ) -> Generator[None, None, bool]:
        """Contract deployment verification."""

        log_message = self.LogMessages.request_verification
        self.context.logger.info(f"{log_message}")

        performative = ContractApiMessage.Performative.GET_STATE
        contract_api_response = yield from self.get_contract_api_response(
            performative=performative,  # type: ignore
            contract_address=service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="verify_contract",
        )
        if (
            contract_api_response.performative
            is not ContractApiMessage.Performative.STATE
        ):
            log_message = self.LogMessages.failed_verification
            self.context.logger.info(f"{log_message}")
            return False
        log_message = self.LogMessages.response_verification
        self.context.logger.info(f"{log_message}: {contract_api_response}")
        return cast(bool, contract_api_response.state.body["verified"])

    def get_agent_instances(
        self, service_registry_address: str, on_chain_service_id: int
    ) -> Generator[None, None, Dict[str, Any]]:
        """Get service info available on-chain"""

        log_message = self.LogMessages.request_service_info
        self.context.logger.info(f"{log_message}")

        performative = ContractApiMessage.Performative.GET_STATE
        kwargs = dict(
            performative=performative,
            contract_address=service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_agent_instances",
            service_id=on_chain_service_id,
        )
        contract_api_response = yield from self.get_contract_api_response(**kwargs)  # type: ignore
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            log_message = self.LogMessages.failed_service_info
            self.context.logger.info(
                f"{log_message} ({kwargs}): {contract_api_response}"
            )
            self.context.logger.info(log_message)
            return {}

        log_message = self.LogMessages.response_service_info
        self.context.logger.info(f"{log_message}: {contract_api_response}")
        return cast(dict, contract_api_response.state.body)

    def get_addresses(self) -> Generator:  # pylint: disable=too-many-return-statements
        """Get addresses of agents registered for the service"""

        service_registry_address = self.params.service_registry_address
        if service_registry_address is None:
            log_message = self.LogMessages.no_contract_address.value
            self.context.logger.info(log_message)
            return False

        correctly_deployed = yield from self.is_correct_contract(
            service_registry_address
        )
        if not correctly_deployed:
            return False

        on_chain_service_id = self.params.on_chain_service_id
        if on_chain_service_id is None:
            log_message = self.LogMessages.no_on_chain_service_id.value
            self.context.logger.info(log_message)
            return False

        service_info = yield from self.get_agent_instances(
            service_registry_address, on_chain_service_id
        )
        if not service_info:
            return False

        registered_addresses = set(service_info["agentInstances"])
        if not registered_addresses:
            log_message = self.LogMessages.no_agents_registered.value
            self.context.logger.info(f"{log_message}: {service_info}")
            return False

        my_address = self.context.agent_address
        if my_address not in registered_addresses:
            log_message = f"{self.LogMessages.self_not_registered} ({my_address})"
            self.context.logger.info(f"{log_message}: {registered_addresses}")
            return False

        # put service info in the shared state for p2p message handler
        info: Dict[str, Dict[str, str]] = dict.fromkeys(registered_addresses)
        tm_host, tm_port = parse_tendermint_p2p_url(url=self.params.tendermint_p2p_url)
        validator_config = dict(
            hostname=tm_host,
            p2p_port=tm_port,
            address=self.local_tendermint_params["address"],
            pub_key=self.local_tendermint_params["pub_key"],
            peer_id=self.local_tendermint_params["peer_id"],
        )
        info[self.context.agent_address] = validator_config
        self.synchronized_data.db.update(registered_addresses=info)
        log_message = self.LogMessages.response_service_info.value
        self.context.logger.info(f"{log_message}: {info}")
        return True

    def get_tendermint_configuration(self) -> Generator[None, None, bool]:
        """Make HTTP GET request to obtain agent's local Tendermint node parameters"""

        url = self.tendermint_parameter_url
        log_message = self.LogMessages.request_personal
        self.context.logger.info(f"{log_message}: {url}")

        result = yield from self.get_http_response(method="GET", url=url)
        response = self._decode_result(result, self.LogMessages.failed_personal)
        if response is None:
            return False

        self.local_tendermint_params = response["params"]
        log_message = self.LogMessages.response_personal
        self.context.logger.info(f"{log_message}: {response}")
        return True

    def request_tendermint_info(self) -> Generator[None, None, bool]:
        """Request Tendermint info from other agents"""

        still_missing = {k for k, v in self.registered_addresses.items() if not v}
        log_message = self.LogMessages.request_others
        self.context.logger.info(f"{log_message}: {still_missing}")

        for address in still_missing:
            dialogues = cast(TendermintDialogues, self.context.tendermint_dialogues)
            performative = TendermintMessage.Performative.GET_GENESIS_INFO
            message, _ = dialogues.create(
                counterparty=address, performative=performative
            )
            message = cast(TendermintMessage, message)
            context = EnvelopeContext(connection_id=P2P_LIBP2P_CLIENT_PUBLIC_ID)
            self.context.outbox.put_message(message=message, context=context)
        # we wait for the messages that were put in the outbox.
        yield from self.sleep(self.params.sleep_time)

        if all(self.registered_addresses.values()):
            log_message = self.LogMessages.collection_complete
            self.context.logger.info(f"{log_message}: {self.registered_addresses}")
            self.collection_complete = True
        return self.collection_complete

    def format_genesis_data(
        self,
        collected_agent_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format collected agent info for genesis update"""

        validators = []
        for address, validator_config in collected_agent_info.items():
            validator = dict(
                hostname=validator_config["hostname"],
                p2p_port=validator_config["p2p_port"],
                address=validator_config["address"],
                pub_key=validator_config["pub_key"],
                peer_id=validator_config["peer_id"],
                power=self.params.genesis_config.voting_power,
                name=NODE.format(address=address[2:]),  # skip 0x part
            )
            validators.append(validator)

        genesis_data = dict(
            validators=validators,
            genesis_config=self.params.genesis_config.to_json(),
        )
        return genesis_data

    def request_update(self) -> Generator[None, None, bool]:
        """Make HTTP POST request to update agent's local Tendermint node"""

        url = self.tendermint_parameter_url
        genesis_data = self.format_genesis_data(self.registered_addresses)
        log_message = self.LogMessages.request_update
        self.context.logger.info(f"{log_message}: {genesis_data}")

        content = json.dumps(genesis_data).encode(self.ENCODING)
        result = yield from self.get_http_response(
            method="POST", url=url, content=content
        )
        response = self._decode_result(result, self.LogMessages.failed_update)
        if response is None:
            return False

        log_message = self.LogMessages.response_update
        self.context.logger.info(f"{log_message}: {response}")
        self.updated_genesis_data.update(genesis_data)
        return True

    def wait_for_block(self, timeout: float) -> Generator[None, None, bool]:
        """Wait for a block to be received in the specified timeout."""
        # every agent will finish with the reset at a different time
        # hence the following will be different for all agents
        start_time = datetime.datetime.now()

        def received_block() -> bool:
            """Check whether we have received a block after "start_time"."""
            try:
                shared_state = cast(SharedState, self.context.state)
                last_timestamp = shared_state.round_sequence.last_timestamp
                if last_timestamp > start_time:
                    return True
                return False
            except ABCIAppInternalError:
                # this can happen if we haven't received a block yet
                return False

        try:
            yield from self.wait_for_condition(
                condition=received_block, timeout=timeout
            )
            # if the `wait_for_condition` finish without an exception,
            # it means that the condition has been satisfied on time
            return True
        except TimeoutException:
            # the agent wasn't able to receive blocks in the given amount of time (timeout)
            return False

    def async_act(self) -> Generator:  # pylint: disable=too-many-return-statements
        """
        Do the action.

        Steps:
        1. Collect personal Tendermint configuration
        2. Make Service Registry contract call to retrieve addresses
           of the other agents registered on-chain for the service.
        3. Request Tendermint configuration from registered agents.
           This is done over the Agent Communication Network using
           the p2p_libp2p_client connection.
        4. Update Tendermint configuration via genesis.json with the
           information of the other validators (agents).
        5. Restart Tendermint to establish the validator network.
        """

        exchange_config = self.params.share_tm_config_on_startup
        log_message = self.LogMessages.config_sharing.value
        self.context.logger.info(f"{log_message}: {exchange_config}")

        if not exchange_config:
            yield from super().async_act()
            return

        self.context.logger.info(f"My address: {self.context.agent_address}")

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

        # collect Tendermint config information from other agents
        if not self.collection_complete:
            successful = yield from self.request_tendermint_info()
            if not successful:
                yield from self.sleep(self.params.sleep_time)
                return

        # update Tendermint configuration
        if not self.updated_genesis_data:
            successful = yield from self.request_update()
            if not successful:
                yield from self.sleep(self.params.sleep_time)
                return

        # restart Tendermint with updated configuration
        successful = yield from self.reset_tendermint_with_wait(on_startup=True)
        if not successful:
            yield from self.sleep(self.params.sleep_time)
            return

        # the reset has gone through, and at this point tendermint should start
        # sending blocks to the agent. However, that might take a while, since
        # we rely on 2/3 of the voting power to be active in order for block production
        # to begin. In other words, we wait for >=2/3 of the agents to become active.
        successful = yield from self.wait_for_block(timeout=WAIT_FOR_BLOCK_TIMEOUT)
        if not successful:
            yield from self.sleep(self.params.sleep_time)
            return

        yield from super().async_act()


class RegistrationBehaviour(RegistrationBaseBehaviour):
    """Agent registration to the FSM App."""

    matching_round = RegistrationRound


class AgentRegistrationRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the registration."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = AgentRegistrationAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        RegistrationBehaviour,  # type: ignore
        RegistrationStartupBehaviour,  # type: ignore
    }
