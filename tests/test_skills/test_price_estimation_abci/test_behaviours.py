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

"""Tests for valory/price_estimation_abci skill's behaviours."""
import copy
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Union, cast
from unittest import mock

import atheris  # type: ignore
import pytest
from aea.exceptions import AEAEnforceError
from aea.helpers.transaction.base import RawTransaction, SignedMessage

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.contracts.offchain_aggregator.contract import (
    PUBLIC_ID as ORACLE_CONTRACT_ID,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    make_degenerate_state,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    EstimateBehaviour,
    ObserveBehaviour,
    TransactionHashBehaviour,
    pack_for_server,
)
from packages.valory.skills.price_estimation_abci.payloads import ObservationPayload
from packages.valory.skills.price_estimation_abci.rounds import (
    Event,
    FinishedPriceAggregationRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    PeriodState as PriceEstimationPeriodState,
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


def mock_to_server_message_flow(
    self: "TestTransactionHashBehaviour",
    this_period_count: int,
    prev_tx_hash: str,
) -> None:
    """Mock to server message flow"""

    self.behaviour.context.logger.info("Mocking to server message flow")
    # note that although this is a dict, order matters for the test
    data = {
        "period_count": this_period_count,
        "agent_address": "test_agent_address",
        "estimate": 1.0,
        "prev_tx_hash": prev_tx_hash,
        "observations": {"agent1": 0.0},
        "data_source": "coinbase",
        "unit": "BTC:USD",
    }
    state = self.behaviour.current_state  # type: ignore
    participants = state.period_state.sorted_participants  # type: ignore
    decimals = state.params.oracle_params["decimals"]  # type: ignore
    data["package"] = pack_for_server(participants, decimals, **data).hex()  # type: ignore
    data["signature"] = "stub_signature"

    request_kwargs: Dict[str, Union[str, bytes]] = dict(
        method="POST",
        url="http://192.168.2.17:9999/deposit",
        headers="",
        version="",
        body=str(data).encode("utf-8"),
    )

    response_kwargs = dict(
        version="",
        status_code=201,
        status_text="",
        headers="",
        body=b"",
    )

    # mock signature acquisition
    self.behaviour.act_wrapper()
    self.mock_signing_request(
        request_kwargs=dict(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
        ),
        response_kwargs=dict(
            performative=SigningMessage.Performative.SIGNED_MESSAGE,
            signed_message=SignedMessage(ledger_id="ethereum", body="stub_signature"),
        ),
    )

    self.behaviour.act_wrapper()
    self.mock_http_request(request_kwargs, response_kwargs)
    self.behaviour.act_wrapper()


def get_valid_server_data() -> Dict[str, Any]:
    """Get valid server data"""

    participants = [
        "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    ]
    period_count = 123456789
    estimate = 43974.960019901744
    observations = {
        "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC": 44251.11,
        "0x70997970C51812dc3A010C7d01b50e0d17dc79C8": 43964.3900398035,
        "0x90F79bf6EB2c4f870365E785982E1f101E93b906": 43985.53,
        "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266": 43949.0,
    }
    data_source = "coinbase"
    unit = "BTC:USD"
    return dict(
        participants=participants,
        period_count=period_count,
        estimate=estimate,
        observations=observations,
        data_source=data_source,
        unit=unit,
    )


@pytest.mark.parametrize(
    "broadcast_to_server, this_period_count", ((True, 0), (False, 0), (True, 1))
)
class TestTransactionHashBehaviour(PriceEstimationFSMBehaviourBaseCase):
    """Test TransactionHashBehaviour."""

    def test_estimate(
        self,
        broadcast_to_server: bool,
        this_period_count: int,
    ) -> None:
        """Test estimate behaviour."""

        # change setting, mock message flow with and without broadcast to server
        state_params = self.behaviour.current_state.params  # type: ignore
        state_params.is_broadcasting_to_server = broadcast_to_server  # type: ignore

        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=TransactionHashBehaviour.state_id,
            period_state=PriceEstimationPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_estimate=1.0,
                        safe_contract_address="safe_contract_address",
                        oracle_contract_address="0x77E9b2EF921253A171Fa0CB9ba80558648Ff7215",
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
                    ledger_id="ethereum", body={"data": b"data"}  # type: ignore
                ),
            ),
        )

        tx_hashes = ["", "0x_prev_cycle_tx_hash"]
        period_state = self.behaviour.current_state.period_state  # type: ignore
        period_data = period_state.db.get_all()
        period_data.update(
            {
                "participants": {"agent1"},
                "participant_to_observations": {"agent1": 1.0},
                "most_voted_estimate": 1.0,
                "final_tx_hash": tx_hashes[1],
            }
        )

        # add new cycle, and dummy period data
        period_state.db._current_period_count = this_period_count  # type: ignore
        next_period_data = copy.deepcopy(period_data)
        next_period_data["final_tx_hash"] = tx_hashes[0]
        period_state.db.add_new_period(
            this_period_count,
            **period_data,
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

        if broadcast_to_server:
            tx_hash = tx_hashes[this_period_count]
            mock_to_server_message_flow(self, this_period_count, tx_hash)

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(Event.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert (
            state.state_id
            == make_degenerate_state(FinishedPriceAggregationRound.round_id).state_id
        )


class TestPackForServer(PriceEstimationFSMBehaviourBaseCase):
    """Test packaging of data for signing by agents"""

    @pytest.mark.parametrize(
        "mutation, remains_valid",
        (
            ({}, True),  # do nothing
            ({"participants": ("",) * 4}, True),
            ({"period_count": (1 << 256) - 1}, True),
            ({"period_count": 1 << 256}, False),
            ({"estimate": f"{'9'*30}.{'9'*1}"}, True),
            ({"estimate": f"{'9'*30}.{'9'*2}"}, False),
            ({"data_source": "a" * 32}, True),
            ({"data_source": "a" * 33}, False),
            ({"unit": "a" * 32}, True),
            ({"unit": "a" * 33}, False),
        ),
    )
    def test_pack_for_server(
        self,
        mutation: Dict[str, Any],
        remains_valid: bool,
    ) -> None:
        """Test packaging valid and invalid data"""

        decimals = self.behaviour.current_state.params.oracle_params["decimals"]  # type: ignore
        kwargs = get_valid_server_data()
        kwargs.update({"decimals": decimals})
        kwargs.update(mutation)

        if remains_valid:
            package = pack_for_server(**kwargs)
            assert isinstance(package, bytes) and len(package) == 256
        else:
            with pytest.raises((OverflowError, AEAEnforceError)):
                pack_for_server(**kwargs)


@pytest.mark.skip
def test_fuzz_pack_for_server() -> None:
    """Test fuzz pack_for_server."""

    @atheris.instrument_func
    def fuzz_pack_for_server(input_bytes: bytes) -> None:
        """Fuzz pack_for_server."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        participants = [fdp.ConsumeStr(12) for _ in range(4)]
        decimals = fdp.ConsumeInt(4)
        period_count = fdp.ConsumeInt(4)
        estimate = fdp.ConsumeFloat()
        observations = {p: fdp.ConsumeFloat() for p in participants}
        data_source = fdp.ConsumeStr(12)
        unit = fdp.ConsumeStr(12)
        pack_for_server(
            participants,
            decimals,
            period_count,
            estimate,
            observations,
            data_source,
            unit,
        )

    atheris.instrument_all()
    atheris.Setup(sys.argv, fuzz_pack_for_server)
    atheris.Fuzz()
