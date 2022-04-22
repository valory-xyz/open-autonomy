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
from typing import cast
from unittest import mock
import pytest

from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    make_degenerate_state,
)
from packages.valory.skills.registration_abci.behaviours import (
    RegistrationBaseBehaviour,
    RegistrationBehaviour,
    RegistrationStartupBehaviour,
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

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


SERVICE_REGISTRY_ADDRESS = "0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0"
CONTRACT_ID = str(ServiceRegistryContract.contract_id)
ON_CHAIN_SERVICE_ID = 42


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

    @property
    def state(self) -> RegistrationStartupBehaviour:
        return cast(RegistrationStartupBehaviour, self.behaviour.current_state)

    # @pytest.mark.parametrize(
    #     "request_performative, response_performative, expected",
    #     [
    #         (
    #             ContractApiMessage.Performative.GET_STATE,
    #             ContractApiMessage.Performative.GET_STATE,
    #             True,
    #         ),
    #         (
    #             ContractApiMessage.Performative.GET_STATE,
    #             ContractApiMessage.Performative.ERROR,
    #             False,
    #         ),
    #     ]
    # )
    # def test_is_correct_contract(
    #     self,
    #     request_performative: ContractApiMessage.Performative,
    #     response_performative: ContractApiMessage.Performative,
    #     expected: bool,
    # ):
    #     request_kwargs = dict(
    #         performative=request_performative
    #     )
    #     response_kwargs = dict(
    #         performative=response_performative
    #     )
    #
    #     self.mock_contract_api_request(
    #         contract_id=CONTRACT_ID,
    #         request_kwargs=request_kwargs,
    #         response_kwargs=response_kwargs,
    #     )
    #     x = self.state.is_correct_contract()
    #     logging.error(str(x))

    def test_registration(self):
        """Sequentially stepping through the execution"""

        assert self.state.registered_addresses == {}

        self.behaviour.act_wrapper()
        assert self.state.registered_addresses == {}

        # 1. collect personal tendermint configuration
        url = self.state.tendermint_start_url
        request_kwargs = dict(method="GET", url=url)

        mock_params = dict(
            proxy_app="",
            p2p_seeds=[],
            consensus_create_empty_blocks=True,
            p2p_laddr="tcp://0.0.0.0:26656",
            rpc_laddr="tcp://0.0.0.0:26657",
            home=None,
        )

        response_kwargs = dict(
            version="",
            status_code=200,
            body=json.dumps(mock_params).encode(self.state.ENCODING),
        )

        # mock service registry address (else RuntimeError)
        with mock.patch.object(
            self.state.params,
            "service_registry_address",
            return_value="0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0"
        ):
            self.mock_http_request(request_kwargs, response_kwargs)

        # 2. make service registry calls
        self.state.params.service_registry_address = SERVICE_REGISTRY_ADDRESS

        # mock is_correct_contract
        performative = ContractApiMessage.Performative.GET_STATE
        request_kwargs = dict(
            performative=performative,
        )
        response_kwargs = dict(
            performative=performative,
        )
        self.mock_contract_api_request(
            contract_id=CONTRACT_ID,
            request_kwargs=request_kwargs,
            response_kwargs=response_kwargs,
        )

        # mock get_service_info
        request_kwargs = dict(
            performative=performative,
            contract_address=SERVICE_REGISTRY_ADDRESS,
            contract_id=str(ServiceRegistryContract.contract_id),
            contract_callable="get_service_info",
            service_id=ON_CHAIN_SERVICE_ID,
        )
        response_kwargs = dict(
            performative=performative,
        )
        self.mock_contract_api_request(
            contract_id=CONTRACT_ID,
            request_kwargs=request_kwargs,
            response_kwargs=response_kwargs,
        )



        # mock the super().async_act() call

        # self.mock_a2a_transaction()
        # self._test_done_flag_set()
        #
        # self.end_round(Event.DONE)
        # state = cast(BaseState, self.behaviour.current_state)
        # assert state.state_id == self.next_behaviour_class.state_id


        # my_address = self.state.context.agent_address
        # [my_address, "http://0.0.0.0:26657"]

class TestRegistrationBehaviour(BaseRegistrationTestBehaviour):
    """Test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBehaviour
    next_behaviour_class = make_degenerate_state(FinishedRegistrationFFWRound.round_id)
