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
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.registration_abci.dialogues import TendermintDialogues
from packages.valory.skills.registration_abci.payloads import RegistrationPayload
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    RegistrationRound,
    RegistrationStartupRound,
)


CONSENSUS_PARAMS = {
    "block": {"max_bytes": "22020096", "max_gas": "-1", "time_iota_ms": "1000"},
    "evidence": {
        "max_age_num_blocks": "100000",
        "max_age_duration": "172800000000000",
        "max_bytes": "1048576",
    },
    "validator": {"pub_key_types": ["ed25519"]},
    "version": {},
}


GENESIS_CONFIG = dict(  # type: ignore
    genesis_time="2022-05-20T16:00:21.735122717Z",
    chain_id="chain-c4daS1",
    consensus_params=CONSENSUS_PARAMS,
)

DEFAULT_VOTING_POWER = str(10)


def format_genesis_data(
    collected_agent_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Format collected agent info for genesis update"""

    validators = []
    for i, validator_config in enumerate(collected_agent_info.values()):
        validator = dict(
            address=validator_config["address"],
            pub_key=validator_config["pub_key"],
            power=DEFAULT_VOTING_POWER,
            name=f"node{i}",
        )
        validators.append(validator)

    genesis_data = dict(
        validators=validators,
        genesis_config=GENESIS_CONFIG,
    )
    return genesis_data


class RegistrationBaseBehaviour(BaseBehaviour):
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
            initialisation = (
                json.dumps(self.synchronized_data.db.setup_data, sort_keys=True)
                if self.synchronized_data.db.setup_data != {}
                else None
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
    state_id = "registration_startup"
    behaviour_id = "registration_startup"
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

    def is_correct_contract(self) -> Generator[None, None, bool]:
        """Contract deployment verification."""

        log_message = self.LogMessages.request_verification
        self.context.logger.info(f"{log_message}")

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
            log_message = self.LogMessages.failed_verification
            self.context.logger.info(f"{log_message}")
            return False
        log_message = self.LogMessages.response_verification
        self.context.logger.info(f"{log_message}: {contract_api_response}")
        return cast(bool, contract_api_response.state.body["verified"])

    def get_agent_instances(self) -> Generator[None, None, Dict[str, Any]]:
        """Get service info available on-chain"""

        log_message = self.LogMessages.request_service_info
        self.context.logger.info(f"{log_message}")

        performative = ContractApiMessage.Performative.GET_STATE
        service_id = int(self.params.on_chain_service_id)
        kwargs = dict(
            performative=performative,  # type: ignore
            contract_address=self.params.service_registry_address,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_agent_instances",
            service_id=service_id,
        )
        contract_api_response = yield from self.get_contract_api_response(**kwargs)
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

    def get_addresses(self) -> Generator:
        """Get addresses of agents registered for the service"""

        if self.context.params.service_registry_address is None:
            log_message = self.LogMessages.no_contract_address.value
            self.context.logger.info(log_message)
            return False

        correctly_deployed = yield from self.is_correct_contract()
        if not correctly_deployed:
            return False

        service_info = yield from self.get_agent_instances()
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
        validator_config = dict(
            tendermint_url=self.context.params.tendermint_url,
            address=self.local_tendermint_params["address"],
            pub_key=self.local_tendermint_params["pub_key"],
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
            performative = TendermintMessage.Performative.REQUEST
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

    def request_update(self) -> Generator[None, None, bool]:
        """Make HTTP POST request to update agent's local Tendermint node"""

        url = self.tendermint_parameter_url
        genesis_data = format_genesis_data(self.registered_addresses)
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

    def async_act(self) -> Generator:
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

        yield from super().async_act()


class RegistrationBehaviour(RegistrationBaseBehaviour):
    """Agent registration to the FSM App."""

    behaviour_id = "registration"
    matching_round = RegistrationRound


class AgentRegistrationRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the registration."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = AgentRegistrationAbciApp  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = {  # type: ignore
        RegistrationBehaviour,  # type: ignore
        RegistrationStartupBehaviour,  # type: ignore
    }
