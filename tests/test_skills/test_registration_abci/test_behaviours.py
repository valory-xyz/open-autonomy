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

"""Tests for valory/registration_abci skill's behaviours."""
import json
import logging
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, cast
from unittest import mock

import pytest
from _pytest.logging import LogCaptureFixture
from aea.exceptions import AEAActException

from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.tendermint.message import TendermintMessage
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseBehaviour,
    make_degenerate_behaviour,
)
from packages.valory.skills.registration_abci.behaviours import (
    RegistrationBaseBehaviour,
    RegistrationBehaviour,
    RegistrationStartupBehaviour,
    consume,
)
from packages.valory.skills.registration_abci.rounds import (
    BaseSynchronizedData as RegistrationSynchronizedSata,
)
from packages.valory.skills.registration_abci.rounds import (
    Event,
    FinishedRegistrationFFWRound,
    FinishedRegistrationRound,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


SERVICE_REGISTRY_ADDRESS = "0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0"
CONTRACT_ID = str(ServiceRegistryContract.contract_id)
ON_CHAIN_SERVICE_ID = 42
DUMMY_ADDRESS = "http://0.0.0.0:25567"


@contextmanager
def as_context(*contexts: Any) -> Generator[None, None, None]:
    """Set contexts"""
    with ExitStack() as stack:
        consume(map(stack.enter_context, contexts))
        yield


class RegistrationAbciBaseCase(FSMBehaviourBaseCase):
    """Base case for testing RegistrationAbci FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "registration_abci")


class BaseRegistrationTestBehaviour(RegistrationAbciBaseCase):
    """Base test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBaseBehaviour
    next_behaviour_class = BaseBehaviour

    def test_registration(self) -> None:
        """Test registration."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            RegistrationSynchronizedSata(AbciAppDB(initial_data={})),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.behaviour_class.behaviour_id
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round(Event.DONE)
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id


class TestRegistrationStartupBehaviour(RegistrationAbciBaseCase):
    """Test case to test RegistrationStartupBehaviour."""

    behaviour_class = RegistrationStartupBehaviour
    next_behaviour_class = make_degenerate_behaviour(FinishedRegistrationRound.round_id)

    other_agents: List[str] = ["0xAlice", "0xBob", "0xCharlie"]

    @property
    def agent_instances(self) -> List[str]:
        """Agent instance addresses"""
        return [*self.other_agents, self.state.context.agent_address]

    @property
    def state(self) -> RegistrationStartupBehaviour:
        """Current behavioural state"""
        return cast(RegistrationStartupBehaviour, self.behaviour.current_behaviour)

    @property
    def logger(self) -> str:
        """Logger"""
        return "aea.test_agent_name.packages.valory.skills.registration_abci"

    @property
    def tendermint_mock_params(self) -> Dict[str, Any]:
        """Tendermint mock params"""
        info = dict(
            address="3877157BFE637FCD7B9FC4B1CEC231F4CA99FDCA",
            pub_key=dict(
                type="tendermint/PubKeyEd25519",
                value="7y7ycBMMABj5Onf74ITYtUS3uZ6SsCQKZML87mIX+r4=",
            ),
        )
        return dict(params=info, status=True, error=None)

    # mock patches
    @property
    def mocked_service_registry_address(self) -> mock._patch:
        """Mocked service registry address"""
        return mock.patch.object(
            self.state.params,
            "service_registry_address",
            return_value=SERVICE_REGISTRY_ADDRESS,
        )

    @property
    def mocked_on_chain_service_id(self) -> mock._patch:
        """Mocked on chain service id"""
        return mock.patch.object(
            self.state.params,
            "on_chain_service_id",
            return_value=ON_CHAIN_SERVICE_ID,
        )

    # @property
    # def mocked_registered_addresses(self) -> mock._patch:
    #     """Mocked on chain service id"""
    #     return_value = {k: 1 for k in self.agent_instances}.values()
    #
    #     return mock.patch.dict(
    #         RegistrationStartupBehaviour.registered_addresses,
    #         return_value=return_value,
    #     )
    #
    #     # return mock.patch.object(
    #     #     RegistrationStartupBehaviour.registered_addresses,
    #     #     "values",
    #     #     # new_callable=mock.PropertyMock,
    #     #     return_value=return_value,
    #     # )
    #
    #     return mock.patch(
    #         "packages.valory.skills.registration_abci.behaviours.RegistrationStartupBehaviour.registered_addresses.values",
    #         new_callable=mock.PropertyMock,
    #         return_value=return_value,
    #     )

    @property
    def mocked_sleep(self) -> mock._patch:
        """Mocked sleep"""
        return mock.patch.object(self.state.params, "sleep_time", new=0)

    # mock contract calls
    def mock_is_correct_contract(self, error_response: bool = False) -> None:
        """Mock service registry contract call to for contract verification"""
        request_kwargs = dict(performative=ContractApiMessage.Performative.GET_STATE)
        state = ContractApiMessage.State(ledger_id="ethereum", body={"verified": True})
        performative = ContractApiMessage.Performative.STATE
        if error_response:
            performative = ContractApiMessage.Performative.ERROR
        response_kwargs = dict(
            performative=performative,
            callable="verify_contract",
            state=state,
        )
        self.mock_contract_api_request(
            contract_id=CONTRACT_ID,
            request_kwargs=request_kwargs,
            response_kwargs=response_kwargs,
        )

    def mock_get_service_info(
        self, *agent_instances: str, error_response: bool = False
    ) -> None:
        """Mock get service info"""
        request_kwargs = dict(performative=ContractApiMessage.Performative.GET_STATE)
        performative = ContractApiMessage.Performative.STATE
        if error_response:
            performative = ContractApiMessage.Performative.ERROR
        body = {"agent_instances": list(agent_instances)}
        state = ContractApiMessage.State(ledger_id="ethereum", body=body)
        response_kwargs = dict(
            performative=performative,
            callable="get_service_info",
            state=state,
        )
        self.mock_contract_api_request(
            contract_id=CONTRACT_ID,
            request_kwargs=request_kwargs,
            response_kwargs=response_kwargs,
        )

    # mock Tendermint config request
    def mock_tendermint_request(
        self, request_kwargs: Dict, response_kwargs: Dict
    ) -> None:
        """Mock Tendermint request."""

        actual_tendermint_message = self.get_message_from_outbox()
        assert actual_tendermint_message is not None, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_tendermint_message,
            message_type=TendermintMessage,
            performative=TendermintMessage.Performative.REQUEST,
            sender=self.state.context.agent_address,
            to=actual_tendermint_message.to,
            **request_kwargs,
        )
        assert has_attributes, error_str
        incoming_message = self.build_incoming_message(
            message_type=TendermintMessage,
            dialogue_reference=(
                actual_tendermint_message.dialogue_reference[0],
                "stub",
            ),
            performative=TendermintMessage.Performative.RESPONSE,
            target=actual_tendermint_message.message_id,
            message_id=-1,
            to=self.state.context.agent_address,
            sender=actual_tendermint_message.to,
            **response_kwargs,
        )
        self.tendermint_handler.handle(cast(TendermintMessage, incoming_message))

    def mock_get_tendermint_info(self, *addresses: str) -> None:
        """Mock get Tendermint info"""
        for _ in addresses:
            request_kwargs: Dict = dict()
            validator_config = {
                "tendermint_url": "http://0.0.0.0:25567",
                "address": "address",
                "pub_key": "pub_key",
                }

            info = json.dumps(validator_config)
            response_kwargs = dict(info=info)
            self.mock_tendermint_request(request_kwargs, response_kwargs)
        self.behaviour.act_wrapper()

    # mock HTTP requests
    def mock_get_local_tendermint_params(self, valid_response: bool = True) -> None:
        """Mock Tendermint get local params"""
        url = self.state.tendermint_parameter_url
        request_kwargs = dict(method="GET", url=url)
        body = b""
        if valid_response:
            params = self.tendermint_mock_params  # TODO
            body = json.dumps(params).encode(self.state.ENCODING)
        response_kwargs = dict(status_code=200, body=body)
        self.mock_http_request(request_kwargs, response_kwargs)

    def mock_tendermint_update(self, valid_response: bool = True) -> None:
        """Mock Tendermint update"""

        from packages.valory.skills.registration_abci.behaviours import format_genesis_data
        validator_configs = format_genesis_data(self.state.registered_addresses)
        body = json.dumps(validator_configs).encode(self.state.ENCODING)
        url = self.state.tendermint_parameter_url
        request_kwargs = dict(method="POST", url=url, body=body)
        body = b"{}" if valid_response else b""
        response_kwargs = dict(status_code=200, body=body)
        self.mock_http_request(request_kwargs, response_kwargs)

    def mock_tendermint_restart(self, valid_response: bool = True) -> None:
        """Mock tendermint restart"""
        url = self.state.tendermint_hard_reset_url
        request_kwargs = dict(method="GET", url=url)
        body = b"{}" if valid_response else b""
        response_kwargs = dict(status_code=200, body=body)
        self.mock_http_request(request_kwargs, response_kwargs)

    # tests
    def test_init(self) -> None:
        """Empty init"""
        assert self.state.registered_addresses == {}
        assert self.state.local_tendermint_params == {}

    def test_no_contract_address(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test service registry contract address not provided"""
        self.behaviour.act_wrapper()
        self.mock_get_local_tendermint_params()
        log_message = self.state.LogMessages.no_contract_address
        assert log_message.value in caplog.text

    @pytest.mark.parametrize("valid_response", [True, False])
    def test_request_personal(
        self, valid_response: bool, caplog: LogCaptureFixture
    ) -> None:
        """Test get tendermint configuration"""

        failed_message = self.state.LogMessages.failed_personal
        response_message = self.state.LogMessages.response_personal
        log_message = [failed_message, response_message][valid_response]
        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_sleep,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params(valid_response=valid_response)
            assert log_message.value in caplog.text

    def test_failed_verification(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test service registry contract not correctly deployed"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract(error_response=True)
            log_message = self.state.LogMessages.failed_verification
            assert log_message.value in caplog.text

    def test_failed_service_info(self, caplog: LogCaptureFixture) -> None:
        """Test get service info failure"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(error_response=True)
            log_message = self.state.LogMessages.failed_service_info
            assert log_message.value in caplog.text

    def test_no_agents_registered(self, caplog: LogCaptureFixture) -> None:
        """Test no agent instances registered"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
            self.mocked_sleep,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info()
            log_message = self.state.LogMessages.no_agents_registered
            assert log_message.value in caplog.text

    def test_self_not_registered(
        self, caplog: LogCaptureFixture
    ) -> None:
        """Test node operator agent not registered"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(*self.other_agents)
            log_message = self.state.LogMessages.self_not_registered
            assert log_message.value in caplog.text

    def test_response_service_info(self, caplog: LogCaptureFixture) -> None:
        """Test registered addresses retrieved"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(*self.agent_instances)

            assert set(self.state.registered_addresses) == set(self.agent_instances)
            my_info = self.state.registered_addresses[self.state.context.agent_address]
            assert my_info["tendermint_url"] == self.state.context.params.tendermint_url
            assert not any(map(self.state.registered_addresses.get, self.other_agents))
            log_message = self.state.LogMessages.response_service_info
            assert log_message.value in caplog.text

    # @pytest.mark.asyncio
    def test_collection_complete(self, caplog: LogCaptureFixture) -> None:
        """Test registered addresses retrieved"""

        # async def flush_queue():
        #     self.state.context.message_in_queue
        #     await self.state.context.outbox._multiplexer.out_queue.join()
        import asyncio

        @pytest.mark.asyncio
        async def test_sleep(event_loop):
            result = await asyncio.sleep(1, result=3, loop=event_loop)
            assert result == 3

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
            self.mocked_sleep,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(*self.agent_instances)
            self.mock_get_tendermint_info(*self.other_agents)
            logging.error(str(self.state.registered_addresses))
            assert all(map(self.state.registered_addresses.get, self.other_agents))
            log_message = self.state.LogMessages.collection_complete
            assert log_message.value in caplog.text

    @pytest.mark.parametrize("valid_response", [True, False])
    def test_request_update(
        self, valid_response: bool, caplog: LogCaptureFixture
    ) -> None:
        """Test Tendermint config update"""

        failed_message = self.state.LogMessages.failed_update
        response_message = self.state.LogMessages.response_update
        log_message = [failed_message, response_message][valid_response]
        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
            self.mocked_sleep,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(*self.agent_instances)
            self.mock_get_tendermint_info(*self.other_agents)
            self.mock_tendermint_update(valid_response=valid_response)
            assert log_message.value in caplog.text

    @pytest.mark.parametrize("valid_response", [True, False])
    def test_request_restart(
        self, valid_response: bool, caplog: LogCaptureFixture
    ) -> None:
        """Test Tendermint start"""

        failed_message = self.state.LogMessages.failed_restart
        response_message = self.state.LogMessages.response_restart
        log_message = [failed_message, response_message][valid_response]
        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
            self.mocked_sleep,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(*self.agent_instances)
            self.mock_get_tendermint_info(*self.other_agents)
            self.mock_tendermint_update()
            self.mock_tendermint_restart(valid_response=valid_response)
            assert log_message.value in caplog.text


class TestRegistrationBehaviour(BaseRegistrationTestBehaviour):
    """Test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBehaviour
    next_behaviour_class = make_degenerate_behaviour(
        FinishedRegistrationFFWRound.round_id
    )
