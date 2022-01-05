# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Tests for valory/price_estimation_abci skill's behaviours."""

import json
import time
from pathlib import Path
from typing import cast
from unittest import mock

from aea.helpers.transaction.base import RawTransaction

from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.contracts.offchain_aggregator.contract import (
    PUBLIC_ID as ORACLE_CONTRACT_ID,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.price_estimation_abci.behaviours import (
    EstimateBehaviour,
    ObserveBehaviour,
    TransactionHashBehaviour,
)
from packages.valory.skills.price_estimation_abci.payloads import ObservationPayload
from packages.valory.skills.price_estimation_abci.rounds import Event
from packages.valory.skills.price_estimation_abci.rounds import (
    PeriodState as PriceEstimationPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    RandomnessTransactionSubmissionBehaviour,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


DRAND_VALUE = {
    "round": 1416669,
    "randomness": "f6be4bf1fa229f22340c1a5b258f809ac4af558200775a67dacb05f0cb258a11",
    "signature": (
        "b44d00516f46da3a503f9559a634869b6dc2e5d839e46ec61a090e3032172954929a5"
        "d9bd7197d7739fe55db770543c71182562bd0ad20922eb4fe6b8a1062ed21df3b68de"
        "44694eb4f20b35262fa9d63aa80ad3f6172dd4d33a663f21179604"
    ),
    "previous_signature": (
        "903c60a4b937a804001032499a855025573040cb86017c38e2b1c3725286756ce8f33"
        "61188789c17336beaf3f9dbf84b0ad3c86add187987a9a0685bc5a303e37b008fba8c"
        "44f02a416480dd117a3ff8b8075b1b7362c58af195573623187463"
    ),
}


class DummyRoundId:
    """Dummy class for setting round_id for exit condition."""

    round_id: str

    def __init__(self, round_id: str) -> None:
        """Dummy class for setting round_id for exit condition."""
        self.round_id = round_id


class PriceEstimationFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "price_estimation_abci"
    )


class TestObserveBehaviour(PriceEstimationFSMBehaviourBaseCase):
    """Test ObserveBehaviour."""

    def test_observer_behaviour(
        self,
    ) -> None:
        """Run tests."""
        self.fast_forward_to_state(
            self.behaviour,
            ObserveBehaviour.state_id,
            PriceEstimationPeriodState(
                StateDB(initial_period=0, initial_data=dict(estimate=1.0)),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == ObserveBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                url="https://api.coinbase.com/v2/prices/BTC-USD/buy",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"data": {"amount": 54566}}).encode("utf-8"),
            ),
        )
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == EstimateBehaviour.state_id

    def test_observer_behaviour_retries_exceeded(
        self,
    ) -> None:
        """Run tests."""
        self.fast_forward_to_state(
            self.behaviour,
            ObserveBehaviour.state_id,
            PriceEstimationPeriodState(
                StateDB(initial_period=0, initial_data=dict(estimate=1.0)),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == ObserveBehaviour.state_id
        )
        with mock.patch.object(
            self.behaviour.context.price_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.behaviour.act_wrapper()
            state = cast(BaseState, self.behaviour.current_state)
            assert state.state_id == ObserveBehaviour.state_id
            self._test_done_flag_set()

    def test_observed_value_none(
        self,
    ) -> None:
        """Test when `observed` value is none."""
        self.fast_forward_to_state(
            self.behaviour,
            ObserveBehaviour.state_id,
            PriceEstimationPeriodState(
                StateDB(initial_period=0, initial_data=dict()),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == ObserveBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                url="https://api.coinbase.com/v2/prices/BTC-USD/buy",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=b"",
            ),
        )
        time.sleep(1)
        self.behaviour.act_wrapper()

    def test_clean_up(
        self,
    ) -> None:
        """Test when `observed` value is none."""
        self.fast_forward_to_state(
            self.behaviour,
            ObserveBehaviour.state_id,
            PriceEstimationPeriodState(
                StateDB(initial_period=0, initial_data=dict()),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == ObserveBehaviour.state_id
        )
        self.behaviour.context.price_api._retries_attempted = 1
        assert self.behaviour.current_state is not None
        self.behaviour.current_state.clean_up()
        assert self.behaviour.context.price_api._retries_attempted == 0


class TestEstimateBehaviour(PriceEstimationFSMBehaviourBaseCase):
    """Test EstimateBehaviour."""

    def test_estimate(
        self,
    ) -> None:
        """Test estimate behaviour."""

        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=EstimateBehaviour.state_id,
            period_state=PriceEstimationPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        participant_to_observations={
                            "a": ObservationPayload(sender="a", observation=1.0)
                        }
                    ),
                ),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == EstimateBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == TransactionHashBehaviour.state_id


class TestTransactionHashBehaviour(PriceEstimationFSMBehaviourBaseCase):
    """Test TransactionHashBehaviour."""

    def test_estimate(
        self,
    ) -> None:
        """Test estimate behaviour."""

        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=TransactionHashBehaviour.state_id,
            period_state=PriceEstimationPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_estimate=1.0,
                        safe_contract_address="safe_contract_address",
                        oracle_contract_address="oracle_contract_address",
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == TransactionHashBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ),
            contract_id=str(ORACLE_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_latest_transmission_details",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum", body={"epoch_": 1, "round_": 1}
                ),
            ),
        )
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ),
            contract_id=str(ORACLE_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_transmit_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum", body={"data": "data"}
                ),
            ),
        )
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ),
            contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_deploy_transaction",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={
                        "tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"
                    },
                ),
            ),
        )
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == RandomnessTransactionSubmissionBehaviour.state_id
