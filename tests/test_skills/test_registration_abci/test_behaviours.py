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
import logging
import json
from pathlib import Path
from typing import cast, Dict, Tuple, Any, List
from unittest import mock
import pytest
from _pytest.logging import LogCaptureFixture
from contextlib import contextmanager, ExitStack
from aea.exceptions import AEAActException

from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    BaseParams,
    make_degenerate_state,
)
from packages.valory.skills.registration_abci.behaviours import (
    RegistrationBaseBehaviour,
    RegistrationBehaviour,
    RegistrationStartupBehaviour,
    consume,
)
from packages.valory.skills.registration_abci.rounds import (
    BasePeriodState as RegistrationPeriodState,
)
from packages.valory.skills.registration_abci.rounds import (
    Event,
    FinishedRegistrationFFWRound,
    FinishedRegistrationRound,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.tendermint.message import TendermintMessage

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


SERVICE_REGISTRY_ADDRESS = "0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0"
CONTRACT_ID = str(ServiceRegistryContract.contract_id)
ON_CHAIN_SERVICE_ID = 42
DUMMY_ADDRESS = "http://0.0.0.0:25567"


@contextmanager
def as_context(*contexts):
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
    next_behaviour_class = BaseState

    def test_registration(self) -> None:
        """Test registration."""
        self.fast_forward_to_state(
            self.behaviour,
            self.behaviour_class.state_id,
            RegistrationPeriodState(StateDB(initial_period=0, initial_data={})),
        )
        assert (
                cast(BaseState, self.behaviour.current_state).state_id
                == self.behaviour_class.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round(Event.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id


class TestRegistrationStartupBehaviour(RegistrationAbciBaseCase):
    """Test case to test RegistrationStartupBehaviour."""

    behaviour_class = RegistrationStartupBehaviour
    next_behaviour_class = make_degenerate_state(FinishedRegistrationRound.round_id)

    other_agents: List[str] = ["0xAlice", "0xBob", "0xCharlie"]

    @property
    def agent_instances(self) -> Tuple[Any, str]:
        return *self.other_agents, self.state.context.agent_address

    @property
    def state(self) -> RegistrationStartupBehaviour:
        return cast(RegistrationStartupBehaviour, self.behaviour.current_state)

    @property
    def logger(self) -> str:
        return "aea.test_agent_name.packages.valory.skills.registration_abci"

    @property
    def tendermint_mock_params(self) -> Dict[str, Any]:
        return dict(
            proxy_app="",
            p2p_seeds=[],
            consensus_create_empty_blocks=True,
            p2p_laddr="tcp://0.0.0.0:26656",
            rpc_laddr="tcp://0.0.0.0:26657",
            home=None,
        )

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

    # mock contract calls
    def mock_is_correct_contract(self, error_response=False) -> None:
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
            contract_id="valory/service_registry:0.1.0",
            request_kwargs=request_kwargs,
            response_kwargs=response_kwargs,
        )

    def mock_get_service_info(self, *agent_instances: str, error_response=False) -> None:
        """Mock get service info"""
        request_kwargs = dict(performative=ContractApiMessage.Performative.GET_STATE)
        performative = ContractApiMessage.Performative.STATE
        if error_response:
            performative = ContractApiMessage.Performative.ERROR
        body = {"info": {"agent_instances": list(agent_instances)}}
        state = ContractApiMessage.State(ledger_id="ethereum", body=body)
        response_kwargs = dict(
            performative=performative,
            callable="get_service_info",
            state=state,
        )
        self.mock_contract_api_request(
            contract_id="valory/service_registry:0.1.0",
            request_kwargs=request_kwargs,
            response_kwargs=response_kwargs,
        )

    # mock Tendermint config request
    def mock_tendermint_request(self, request_kwargs: Dict, response_kwargs: Dict) -> None:
        """Mock Tendermint request."""

        self.assert_quantity_in_outbox(1)
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
        self.behaviour.act_wrapper()
        self.assert_quantity_in_outbox(0)
        incoming_message = self.build_incoming_message(
            message_type=TendermintMessage,
            dialogue_reference=(actual_tendermint_message.dialogue_reference[0], "stub"),
            performative=TendermintMessage.Performative.RESPONSE,
            target=actual_tendermint_message.message_id,
            message_id=-1,
            to=self.state.context.agent_address,
            sender=actual_tendermint_message.to,
            **response_kwargs,
        )
        self.tendermint_handler.handle(cast(TendermintMessage, incoming_message))
        self.behaviour.act_wrapper()

    def mock_get_tendermint_info(self, *addresses: str) -> None:
        """Mock get Tendermint info"""
        for _ in addresses:
            request_kwargs = dict()
            response_kwargs = dict(info=DUMMY_ADDRESS)
            self.mock_tendermint_request(request_kwargs, response_kwargs)

    # mock HTTP requests
    def mock_get_local_tendermint_params(self, valid_response=True) -> None:
        """Mock Tendermint get local params"""
        request_kwargs = dict(method="GET", url=self.state.tendermint_parameter_url)
        body = b""
        if valid_response:
            params = self.tendermint_mock_params
            body = json.dumps(params).encode(self.state.ENCODING)
        response_kwargs = dict(
            status_code=200,
            body=body,
        )
        self.mock_http_request(request_kwargs, response_kwargs)

    def mock_tendermint_update(self, valid_response=True) -> None:
        """Mock Tendermint update"""
        params = self.state.local_tendermint_params
        body = json.dumps(params).encode(self.state.ENCODING)
        request_kwargs = dict(
            method="POST",
            url=self.state.tendermint_parameter_url,
            body=body,
        )
        body = b"{}" if valid_response else b""
        response_kwargs = dict(status_code=200, body=body)
        self.mock_http_request(request_kwargs, response_kwargs)

    def mock_tendermint_start(self, valid_response=True) -> None:
        """Mock tendermint start"""
        request_kwargs = dict(method="GET", url=self.state.tendermint_start_url)
        body = b"{}" if valid_response else b""
        response_kwargs = dict(status_code=200, body=body)
        self.mock_http_request(request_kwargs, response_kwargs)

    # tests
    def test_init(self) -> None:
        """Empty init"""
        assert self.state.registered_addresses == {}
        assert self.state.local_tendermint_params is None

    def test_service_registry_contract_address_not_provided(self) -> None:
        """Test service registry contract address not provided"""

        with pytest.raises(AEAActException):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()

    def test_must_collect_addresses_first(self) -> None:
        """Test service registry contract address not provided"""

        with pytest.raises(RuntimeError):
            any(self.state.not_yet_collected)

    @pytest.mark.parametrize(
        "valid_response, log_message",
        [
            (True, "Local Tendermint configuration obtained"),
            (False, "Error communicating with Tendermint server on get_tendermint_configuration")
        ]
    )
    def test_get_tendermint_configuration(self, valid_response, log_message, caplog: LogCaptureFixture) -> None:
        """Test get tendermint configuration"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params(valid_response=valid_response)
            assert log_message in caplog.text

    def test_service_registry_contract_not_deployed(self, caplog: LogCaptureFixture) -> None:
        """Test service registry contract not deployed"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract(error_response=True)
            assert "`verify_contract` call unsuccessful!" in caplog.text
            assert "Service registry contract not deployed or incorrect" in caplog.text

    def test_get_service_info_failure(self, caplog: LogCaptureFixture) -> None:
        """Test get service info failure"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(error_response=True)
            assert "get_service_info unsuccessful!" in caplog.text
            assert "Service info could not be retrieved" in caplog.text

    def test_no_agent_instances_registered(self, caplog: LogCaptureFixture) -> None:
        """Test no agent instances registered"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info()
            assert "No agent instances registered:" in caplog.text

    def test_node_operator_agent_not_registered(self, caplog: LogCaptureFixture) -> None:
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
            assert "You are not registered:" in caplog.text

    def test_service_info_retrieved(self, caplog: LogCaptureFixture) -> None:
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
            my_address = self.state.registered_addresses[self.state.context.agent_address]
            assert my_address == self.state.context.params.tendermint_url
            assert set(self.state.not_yet_collected) == set(self.other_agents)
            assert "Registered addresses retrieved from service registry contract" in caplog.text

    def test_tendermint_info_retrieved(self, caplog: LogCaptureFixture) -> None:
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
            self.mock_get_tendermint_info(*self.other_agents)

            assert not any(self.state.not_yet_collected)
            assert "Completed collecting Tendermint responses" in caplog.text
            # assert any(self.state.not_yet_collected)
            # assert "Still missing info on: " in caplog.text

    @pytest.mark.parametrize(
        "valid_response, log_message",
        [
            (True, "Local TendermintNode updated: "),
            (False, "Error communicating with Tendermint server on update_tendermint_configuration")
        ]
    )
    def test_tendermint_config_update(self, valid_response, log_message, caplog) -> None:
        """Test Tendermint config update"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(*self.agent_instances)
            self.mock_get_tendermint_info(*self.other_agents)
            self.mock_tendermint_update(valid_response=valid_response)
            assert log_message in caplog.text

    @pytest.mark.parametrize(
        "valid_response, log_message",
        [
            (True, "Tendermint node started: "),
            (False, "Error communicating with Tendermint server on start_tendermint")
        ]
    )
    def test_tendermint_start(self, valid_response, log_message, caplog) -> None:
        """Test Tendermint start"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_get_local_tendermint_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(*self.agent_instances)
            self.mock_get_tendermint_info(*self.other_agents)
            self.mock_tendermint_update()
            self.mock_tendermint_start(valid_response=valid_response)
            assert log_message in caplog.text


class TestRegistrationBehaviour(BaseRegistrationTestBehaviour):
    """Test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBehaviour
    next_behaviour_class = make_degenerate_state(FinishedRegistrationFFWRound.round_id)
