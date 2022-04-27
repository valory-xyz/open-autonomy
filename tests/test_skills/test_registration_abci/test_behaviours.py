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
import time
from pathlib import Path
from typing import cast
from unittest import mock
import pytest
from _pytest.logging import LogCaptureFixture
from contextlib import contextmanager, ExitStack
from aea.exceptions import AEAActException

from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
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

    other_agents = ["0xAlice", "0xBob"]

    @property
    def agent_instances(self):
        return *self.other_agents, self.state.context.agent_address

    @property
    def state(self) -> RegistrationStartupBehaviour:
        return cast(RegistrationStartupBehaviour, self.behaviour.current_state)

    @property
    def logger(self) -> str:
        return "aea.test_agent_name.packages.valory.skills.registration_abci"

    @property
    def tendermint_mock_params(self):
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

    def mocked_registered_addresses(self, *agent_instances) -> mock._patch:
        address = self.state.context.params.tendermint_url
        data = {agent: address for agent in agent_instances}
        return_value = dict(registered_addresses=data)
        return mock.patch.object(
            StateDB,
            "initial_data",
            new_callable=mock.PropertyMock,
            return_value=return_value,
        )

    # mock contract calls
    def mock_is_correct_contract(self) -> None:
        """Mock service registry contract call to for contract verification"""
        request_kwargs = dict(performative=ContractApiMessage.Performative.GET_STATE)
        state = ContractApiMessage.State(ledger_id="ethereum", body={"verified": True})
        response_kwargs = dict(
            performative=ContractApiMessage.Performative.STATE,
            callable="verify_contract",
            state=state,
        )
        self.mock_contract_api_request(
            contract_id="valory/service_registry:0.1.0",
            request_kwargs=request_kwargs,
            response_kwargs=response_kwargs,
        )

    def mock_get_service_info(self, *agent_instances: str) -> None:
        """Mock get service info"""
        request_kwargs = dict(performative=ContractApiMessage.Performative.GET_STATE)
        body = {"info": {"agent_instances": list(agent_instances)}}
        state = ContractApiMessage.State(ledger_id="ethereum", body=body)
        response_kwargs = dict(
            performative=ContractApiMessage.Performative.STATE,
            callable="get_service_info",
            state=state,
        )
        self.mock_contract_api_request(
            contract_id="valory/service_registry:0.1.0",
            request_kwargs=request_kwargs,
            response_kwargs=response_kwargs,
        )

    # mock HTTP requests
    def mock_tendermint_get_local_params(self) -> None:
        """Mock Tendermint get local params"""
        request_kwargs = dict(method="GET", url=self.state.tendermint_parameter_url)
        response_kwargs = dict(
            status_code=200,
            body=json.dumps(self.tendermint_mock_params).encode(self.state.ENCODING),
        )
        self.mock_http_request(
            request_kwargs,
            response_kwargs,
        )

    def mock_tendermint_update(self) -> None:
        """Mock Tendermint update"""
        params = self.state.local_tendermint_params
        body = json.dumps(params).encode(self.state.ENCODING)
        request_kwargs = dict(
            method="POST",
            url=self.state.tendermint_parameter_url,
            body=body,
        )
        response_kwargs = dict(status_code=200, body=b"{}")
        self.mock_http_request(
            request_kwargs,
            response_kwargs,
        )

    def mock_tendermint_start(self) -> None:
        """Mock tendermint start"""
        request_kwargs = dict(method="GET", url=self.state.tendermint_start_url)
        response_kwargs = dict(
                status_code=200,
                body=json.dumps({}).encode(self.state.ENCODING),
            )
        self.mock_http_request(request_kwargs, response_kwargs)

    # tests
    def test_init(self):
        """Empty init"""
        assert self.state.registered_addresses == {}
        assert self.state.local_tendermint_params is None

    def test_service_registry_contract_address_not_provided(self):
        """Test service registry contract address not provided"""

        with pytest.raises(AEAActException):
            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()

    def test_must_collect_addresses_first(self, caplog):
        """Test service registry contract address not provided"""

        with pytest.raises(RuntimeError):
            self.state.not_yet_collected

    def test_get_tendermint_configuration_failure(self, caplog: LogCaptureFixture):
        """Test get tendermint configuration """

        with caplog.at_level(logging.ERROR, logger=self.logger):
            self.behaviour.act_wrapper()
            request_kwargs = dict(method="GET", url=self.state.tendermint_parameter_url)
            response_kwargs = dict(body=b"")
            self.mock_http_request(request_kwargs, response_kwargs)
            assert "Error communicating with Tendermint server on get_tendermint_configuration" in caplog.text

    def test_get_tendermint_configuration(self, caplog: LogCaptureFixture):
        """Test get tendermint configuration"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
        ):
            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()
            assert "Local Tendermint configuration obtained" in caplog.text
            assert "Service registry contract not deployed" not in caplog.text

    def test_service_registry_contract_not_deployed(self, caplog: LogCaptureFixture):
        """Test service registry contract not deployed"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
        ):
            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()
            self.mock_contract_api_request(
                contract_id="valory/service_registry:0.1.0",
                request_kwargs=dict(performative=ContractApiMessage.Performative.GET_STATE),
                response_kwargs=dict(
                    performative=ContractApiMessage.Performative.ERROR,
                    callable="verify_contract",
                ),
            )
            assert "`verify_contract` call unsuccessful!" in caplog.text
            assert "Service registry contract not deployed" in caplog.text

    def test_service_info_could_not_be_retrieved(self, caplog: LogCaptureFixture):
        """Test service registry contract not deployed"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
        ):
            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()
            self.mock_is_correct_contract()
            assert "Service info could not be retrieved" in caplog.text

    def test_no_agent_instances_registered(self, caplog: LogCaptureFixture):
        """Test no agent instances registered"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info()
            assert "No agent instances registered:" in caplog.text

    def test_node_operator_agent_not_registered(self, caplog: LogCaptureFixture):
        """Test node operator agent not registered"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()
            self.mock_is_correct_contract()
            self.mock_get_service_info(*self.other_agents)
            assert "You are not registered:" in caplog.text

    def test_addresses_retrieved_and_request_sent(self, caplog: LogCaptureFixture):
        """Test registered addresses retrieved and tendermint request sent"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()
            self.behaviour.act_wrapper()
            self.mock_is_correct_contract()
            self.behaviour.act_wrapper()
            self.mock_get_service_info(*self.agent_instances)
            assert "Registered addresses retrieved from service registry contract" in caplog.text
            assert set(self.state.registered_addresses) == set(self.agent_instances)
            my_address = self.state.registered_addresses[self.state.context.agent_address]
            assert my_address == "http://localhost:26657"
            assert "Tendermint request sent to: " in caplog.text
            assert f"Still missing info on: {self.other_agents}" in caplog.text

    def test_tendermint_information_collected(self, caplog: LogCaptureFixture):
        """Test Tendermint information collected"""

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.state.params.sleep_time = 0  # sleep to zero

            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()

            self.behaviour.act_wrapper()
            self.mock_is_correct_contract()

            self.behaviour.act_wrapper()
            self.mock_get_service_info(*self.agent_instances)

            with self.mocked_registered_addresses(*self.agent_instances):
                # sanity check for skipping message mocks on second `act_wrapper` call
                assert self.state.local_tendermint_params
                assert self.state.registered_addresses
                assert not any(self.state.not_yet_collected)

                self.behaviour.act_wrapper()
                assert "All tendermint information collected" in caplog.text

    def test_(self, caplog):

        with as_context(
            caplog.at_level(logging.INFO, logger=self.logger),
            self.mocked_service_registry_address,
            self.mocked_on_chain_service_id,
        ):
            self.behaviour.act_wrapper()
            self.mock_tendermint_get_local_params()
            self.behaviour.act_wrapper()
            self.mock_is_correct_contract()

            other_agents = []  # ["0xAlice", "0xBob"]
            agent_instances = *other_agents, self.state.context.agent_address
            self.behaviour.act_wrapper()
            self.mock_get_service_info(*agent_instances)

            with self.mocked_registered_addresses(*self.agent_instances):
                self.behaviour.act_wrapper()

                self.mock_tendermint_update()
                self.behaviour.act_wrapper()
                # assert "Error communicating with Tendermint server" in caplog.text

                assert "Local TendermintNode started: " in caplog.text

                self.mock_tendermint_start()
                self.behaviour.act_wrapper()

                # assert "Error starting Tendermint: " in caplog.text
                assert "Local TendermintNode started:" in caplog.text
                # assert "Error communicating with Tendermint server on start_tendermint" in caplog.text


class TestRegistrationBehaviour(BaseRegistrationTestBehaviour):
    """Test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBehaviour
    next_behaviour_class = make_degenerate_state(FinishedRegistrationFFWRound.round_id)
