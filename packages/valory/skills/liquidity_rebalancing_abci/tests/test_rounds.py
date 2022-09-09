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

"""Tests for rounds.py file in valory/liquidity_rebalancing_abci."""

# pylint: skip-file

import json
from types import MappingProxyType
from typing import Dict, FrozenSet, Mapping, Optional  # noqa : F401
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilThresholdRoundTest,
)
from packages.valory.skills.liquidity_rebalancing_abci.payloads import (
    SleepPayload,
    StrategyEvaluationPayload,
    TransactionHashPayload,
)
from packages.valory.skills.liquidity_rebalancing_abci.rounds import (  # noqa: F401
    Event,
    SleepRound,
    StrategyEvaluationRound,
    SynchronizedData,
    TransactionHashBaseRound,
)
from packages.valory.skills.transaction_settlement_abci.payloads import (
    SignaturePayload,
    ValidatePayload,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Returns test value for participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_strategy(
    participants: FrozenSet[str],
) -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_strategy"""
    return dict(
        [
            (participant, StrategyEvaluationPayload(sender=participant, strategy="{}"))
            for participant in participants
        ]
    )


def get_participant_to_transfers_result(
    participants: FrozenSet[str],
) -> Dict[str, ValidatePayload]:
    """Get participant_to_lp_result"""
    return {
        participant: ValidatePayload(sender=participant) for participant in participants
    }


def get_participant_to_tx_hash(
    participants: FrozenSet[str],
    hash_: Optional[str] = "tx_hash",
    data_: Optional[str] = "tx_data",
) -> Mapping[str, TransactionHashPayload]:
    """participant_to_tx_hash"""
    return {
        participant: TransactionHashPayload(
            sender=participant, tx_hash=json.dumps({"tx_hash": hash_, "tx_data": data_})
        )
        for participant in participants
    }


def get_participant_to_sleep(
    participants: FrozenSet[str],
) -> Mapping[str, SleepPayload]:
    """Returns test value for participant_to_sleep"""
    return dict(
        [
            (participant, SleepPayload(sender=participant))
            for participant in participants
        ]
    )


def get_participant_to_signature(
    participants: FrozenSet[str],
) -> Dict[str, SignaturePayload]:
    """participant_to_signature"""
    return {
        participant: SignaturePayload(sender=participant, signature="signature")
        for participant in participants
    }


class TestTransactionHashBaseRound(BaseCollectSameUntilThresholdRoundTest):
    """Test TransactionHashBaseRound"""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = TransactionHashBaseRound(
            self.synchronized_data, self.consensus_params
        )
        payloads = get_participant_to_tx_hash(self.participants)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=payloads,
                synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                    participant_to_tx_hash=MappingProxyType(payloads),
                    most_voted_tx_hash=json.loads(_test_round.most_voted_payload)[
                        "tx_hash"
                    ],
                ),
                synchronized_data_attr_checks=[
                    lambda _synchronized_data: _synchronized_data.participant_to_tx_hash.keys(),
                ],
                most_voted_payload=payloads["agent_1"].tx_hash,
                exit_event=Event.DONE,
            )
        )


class TestStrategyEvaluationRound(BaseCollectSameUntilThresholdRoundTest):
    """Test StrategyEvaluationRound"""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_run_wait(
        self,
    ) -> None:
        """Run tests."""
        test_round = StrategyEvaluationRound(
            self.synchronized_data, self.consensus_params
        )

        strategy_mock = mock.PropertyMock(return_value=json.dumps(dict(action="wait")))

        with mock.patch.object(
            StrategyEvaluationPayload,
            "strategy",
            strategy_mock,
        ):
            self._complete_run(
                self._test_round(
                    test_round=test_round,
                    round_payloads=get_participant_to_strategy(self.participants),
                    synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                        participant_to_strategy=get_participant_to_strategy(
                            self.participants
                        ),
                        most_voted_strategy=test_round.most_voted_payload,
                    ),
                    synchronized_data_attr_checks=[
                        lambda _synchronized_data: _synchronized_data.participant_to_strategy.keys(),
                    ],
                    most_voted_payload=StrategyEvaluationPayload.strategy,
                    exit_event=Event.DONE,
                )
            )

    def test_run_enter(
        self,
    ) -> None:
        """Run tests."""
        test_round = StrategyEvaluationRound(
            self.synchronized_data, self.consensus_params
        )

        strategy_mock = mock.PropertyMock(return_value=json.dumps(dict(action="enter")))

        with mock.patch.object(
            StrategyEvaluationPayload,
            "strategy",
            strategy_mock,
        ):
            self._complete_run(
                self._test_round(
                    test_round=test_round,
                    round_payloads=get_participant_to_strategy(self.participants),
                    synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                        participant_to_strategy=get_participant_to_strategy(
                            self.participants
                        ),
                        most_voted_strategy=test_round.most_voted_payload,
                    ),
                    synchronized_data_attr_checks=[
                        lambda _synchronized_data: _synchronized_data.participant_to_strategy.keys(),
                    ],
                    most_voted_payload=StrategyEvaluationPayload.strategy,
                    exit_event=Event.DONE_ENTER,
                )
            )

    def test_run_exit(
        self,
    ) -> None:
        """Run tests."""
        test_round = StrategyEvaluationRound(
            self.synchronized_data, self.consensus_params
        )

        strategy_mock = mock.PropertyMock(return_value=json.dumps(dict(action="exit")))

        with mock.patch.object(
            StrategyEvaluationPayload,
            "strategy",
            strategy_mock,
        ):
            self._complete_run(
                self._test_round(
                    test_round=test_round,
                    round_payloads=get_participant_to_strategy(self.participants),
                    synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                        participant_to_strategy=get_participant_to_strategy(
                            self.participants
                        ),
                        most_voted_strategy=test_round.most_voted_payload,
                    ),
                    synchronized_data_attr_checks=[
                        lambda _synchronized_data: _synchronized_data.participant_to_strategy.keys(),
                    ],
                    most_voted_payload=StrategyEvaluationPayload.strategy,
                    exit_event=Event.DONE_EXIT,
                )
            )

    def test_run_swap_back(
        self,
    ) -> None:
        """Run tests."""
        test_round = StrategyEvaluationRound(
            self.synchronized_data, self.consensus_params
        )

        strategy_mock = mock.PropertyMock(
            return_value=json.dumps(dict(action="swap_back"))
        )

        with mock.patch.object(
            StrategyEvaluationPayload,
            "strategy",
            strategy_mock,
        ):
            self._complete_run(
                self._test_round(
                    test_round=test_round,
                    round_payloads=get_participant_to_strategy(self.participants),
                    synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(
                        participant_to_strategy=get_participant_to_strategy(
                            self.participants
                        ),
                        most_voted_strategy=test_round.most_voted_payload,
                    ),
                    synchronized_data_attr_checks=[
                        lambda _synchronized_data: _synchronized_data.participant_to_strategy.keys(),
                    ],
                    most_voted_payload=StrategyEvaluationPayload.strategy,
                    exit_event=Event.DONE_SWAP_BACK,
                )
            )


class TestSleepRound(BaseCollectSameUntilThresholdRoundTest):
    """Test StrategyEvaluationRound"""

    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""
        test_round = SleepRound(self.synchronized_data, self.consensus_params)
        with mock.patch.object(SleepPayload, "sleep", return_value="sleep"):
            self._complete_run(
                self._test_round(
                    test_round=test_round,
                    round_payloads=get_participant_to_sleep(self.participants),
                    synchronized_data_update_fn=lambda _synchronized_data, _test_round: _synchronized_data.update(),
                    synchronized_data_attr_checks=[],
                    most_voted_payload=SleepPayload.sleep,
                    exit_event=Event.DONE,
                )
            )


def test_synchronized_data() -> None:
    """Test SynchronizedData."""

    participants = get_participants()
    period_count = 0
    setup_params: Dict = {}
    most_voted_strategy: Dict = {}
    most_voted_keeper_address = "0x_keeper"
    safe_contract_address = "0x_contract"
    multisend_contract_address = "0x_multisend"
    most_voted_tx_hash = "tx_hash"
    final_tx_hash = "tx_hash"
    participant_to_lp_result = get_participant_to_transfers_result(participants)
    participant_to_tx_hash = get_participant_to_tx_hash(participants)
    participant_to_signature = get_participant_to_signature(participants)
    participant_to_strategy = get_participant_to_strategy(participants)

    synchronized_data = SynchronizedData(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    participants=participants,
                    setup_params=setup_params,
                    most_voted_strategy=most_voted_strategy,
                    most_voted_keeper_address=most_voted_keeper_address,
                    safe_contract_address=safe_contract_address,
                    multisend_contract_address=multisend_contract_address,
                    most_voted_tx_hash=most_voted_tx_hash,
                    final_tx_hash=final_tx_hash,
                    participant_to_lp_result=participant_to_lp_result,
                    participant_to_tx_hash=participant_to_tx_hash,
                    participant_to_signature=participant_to_signature,
                    participant_to_strategy=participant_to_strategy,
                )
            ),
        )
    )

    assert synchronized_data.participants == participants
    assert synchronized_data.period_count == period_count
    assert synchronized_data.most_voted_strategy == most_voted_strategy
    assert synchronized_data.most_voted_keeper_address == most_voted_keeper_address
    assert synchronized_data.safe_contract_address == safe_contract_address
    assert synchronized_data.multisend_contract_address == multisend_contract_address
    assert synchronized_data.most_voted_tx_hash == most_voted_tx_hash
    assert synchronized_data.final_tx_hash == final_tx_hash
    assert synchronized_data.participant_to_tx_hash == participant_to_tx_hash
    assert synchronized_data.participant_to_signature == participant_to_signature
    assert synchronized_data.participant_to_strategy == participant_to_strategy
