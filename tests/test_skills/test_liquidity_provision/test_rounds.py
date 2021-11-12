# -*- def get_coding() -> utf-8 -*-
# """Returns test value for coding"""--------
# ----------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       def get_http() ->//www.apache.org/licenses/LICENSE-2.0
"""Returns test value for http"""

#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Tests for rounds.py file in valory/liquidity_provision."""

import logging  # noqa : F401
import re
from types import MappingProxyType
from typing import AbstractSet, Dict, FrozenSet, Mapping, Type, cast
from unittest import mock
from packages.valory.skills.abstract_round_abci.base import ABCIAppInternalError, AbstractRound, ConsensusParams

import pytest
from aea.exceptions import AEAEnforceError

from packages.valory.skills.liquidity_provision.payloads import (
    StrategyEvaluationPayload,
)
from packages.valory.skills.price_estimation_abci.payloads import SignaturePayload
from packages.valory.skills.liquidity_provision.rounds import (
    Event,
    PeriodState,
    Event,
    PeriodState,
    TransactionHashBaseRound,
    TransactionSignatureBaseRound,
    TransactionSendBaseRound,
    TransactionValidationBaseRound,
    SelectKeeperMainRound,
    DeploySelectKeeperRound,
    StrategyEvaluationRound,
    WaitRound,
    SwapSelectKeeperRound,
    SwapTransactionHashRound,
    SwapSignatureRound,
    SwapSendRound,
    SwapValidationRound,
    AllowanceCheckRound,
    AddAllowanceSelectKeeperRound,
    AddAllowanceTransactionHashRound,
    AddAllowanceSignatureRound,
    AddAllowanceSendRound,
    AddAllowanceValidationRound,
    AddLiquiditySelectKeeperRound,
    AddLiquidityTransactionHashRound,
    AddLiquiditySignatureRound,
    AddLiquiditySendRound,
    AddLiquidityValidationRound,
    RemoveLiquiditySelectKeeperRound,
    RemoveLiquidityTransactionHashRound,
    RemoveLiquiditySignatureRound,
    RemoveLiquiditySendRound,
    RemoveLiquidityValidationRound,
    RemoveAllowanceSelectKeeperRound,
    RemoveAllowanceTransactionHashRound,
    RemoveAllowanceSignatureRound,
    RemoveAllowanceSendRound,
    RemoveAllowanceValidationRound,
    SwapBackSelectKeeperRound,
    SwapBackTransactionHashRound,
    SwapBackSignatureRound,
    SwapBackSendRound,
    SwapBackValidationRound
)
from tests.test_skills.test_price_estimation_abci.test_rounds import get_participant_to_tx_hash

MAX_PARTICIPANTS: int = 4


def get_participants() -> AbstractSet[str]:
    """Returns test value for participants"""
    return set([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_strategy() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_strategy"""
    ...


def get_most_voted_strategy() -> dict:
    """Returns test value for most_voted_strategy"""
    ...


def get_participant_to_allowance_check() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_allowance_check"""
    ...


def get_most_voted_allowance_check() -> int:
    """Returns test value for most_voted_allowance_check"""
    ...


def get_most_voted_keeper_address() -> str:
    """Returns test value for most_voted_keeper_address"""
    ...


def get_participant_to_swap_tx_hash() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_swap_tx_hash"""
    ...


def get_most_voted_swap_tx_hash() -> str:
    """Returns test value for most_voted_swap_tx_hash"""
    ...


def get_participant_to_add_allowance_tx_hash() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_add_allowance_tx_hash"""
    ...


def get_most_voted_add_allowance_tx_hash() -> str:
    """Returns test value for most_voted_add_allowance_tx_hash"""
    ...


def get_participant_to_add_liquidity_tx_hash() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_add_liquidity_tx_hash"""
    ...


def get_most_voted_add_liquidity_tx_hash() -> str:
    """Returns test value for most_voted_add_liquidity_tx_hash"""
    ...


def get_participant_to_remove_liquidity_tx_hash() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_remove_liquidity_tx_hash"""
    ...


def get_most_voted_remove_liquidity_tx_hash() -> str:
    """Returns test value for most_voted_remove_liquidity_tx_hash"""
    ...


def get_participant_to_remove_allowance_tx_hash() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_remove_allowance_tx_hash"""
    ...


def get_most_voted_remove_allowance_tx_hash() -> str:
    """Returns test value for most_voted_remove_allowance_tx_hash"""
    ...


def get_participant_to_swap_back_tx_hash() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_swap_back_tx_hash"""
    ...


def get_most_voted_swap_back_tx_hash() -> str:
    """Returns test value for most_voted_swap_back_tx_hash"""
    ...


def get_participant_to_swap_signature() -> Mapping[str, SignaturePayload]:
    """Returns test value for participant_to_swap_signature"""
    ...


def get_most_voted_swap_signature() -> str:
    """Returns test value for most_voted_swap_signature"""
    ...


def get_participant_to_add_allowance_signature() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_add_allowance_signature"""
    ...


def get_most_voted_add_allowance_signature() -> str:
    """Returns test value for most_voted_add_allowance_signature"""
    ...


def get_participant_to_add_liquidity_signature() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_add_liquidity_signature"""
    ...


def get_most_voted_add_liquidity_signature() -> str:
    """Returns test value for most_voted_add_liquidity_signature"""
    ...


def get_participant_to_remove_liquidity_signature() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_remove_liquidity_signature"""
    ...


def get_most_voted_remove_liquidity_signature() -> str:
    """Returns test value for most_voted_remove_liquidity_signature"""
    ...


def get_participant_to_remove_allowance_signature() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_remove_allowance_signature"""
    ...


def get_most_voted_remove_allowance_signature() -> str:
    """Returns test value for most_voted_remove_allowance_signature"""
    ...


def get_participant_to_swap_back_signature() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_swap_back_signature"""
    ...


def get_most_voted_swap_back_signature() -> str:
    """Returns test value for most_voted_swap_back_signature"""
    ...


def get_participant_to_swap_send() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_swap_send"""
    ...


def get_most_voted_swap_send() -> str:
    """Returns test value for most_voted_swap_send"""
    ...


def get_participant_to_add_allowance_send() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_add_allowance_send"""
    ...


def get_most_voted_add_allowance_send() -> str:
    """Returns test value for most_voted_add_allowance_send"""
    ...


def get_participant_to_add_liquidity_send() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_add_liquidity_send"""
    ...


def get_most_voted_add_liquidity_send() -> str:
    """Returns test value for most_voted_add_liquidity_send"""
    ...


def get_participant_to_remove_liquidity_send() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_remove_liquidity_send"""
    ...


def get_most_voted_remove_liquidity_send() -> str:
    """Returns test value for most_voted_remove_liquidity_send"""
    ...


def get_participant_to_remove_allowance_send() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_remove_allowance_send"""
    ...


def get_most_voted_remove_allowance_send() -> str:
    """Returns test value for most_voted_remove_allowance_send"""
    ...


def get_participant_to_swap_back_send() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_swap_back_send"""
    ...


def get_most_voted_swap_back_send() -> str:
    """Returns test value for most_voted_swap_back_send"""
    ...


def get_participant_to_swap_validation() -> Mapping[str, StrategyEvaluationPayload]:
    """Returns test value for participant_to_swap_validation"""
    ...


def get_most_voted_swap_validation() -> str:
    """Returns test value for most_voted_swap_validation"""
    ...


def get_participant_to_add_allowance_validation() -> Mapping[str, SignaturePayload]:
    """Returns test value for participant_to_add_allowance_validation"""
    ...


def get_most_voted_add_allowance_validation() -> str:
    """Returns test value for most_voted_add_allowance_validation"""
    ...


def get_participant_to_add_liquidity_validation() -> Mapping[str, SignaturePayload]:
    """Returns test value for participant_to_add_liquidity_validation"""
    ...


def get_most_voted_add_liquidity_validation() -> str:
    """Returns test value for most_voted_add_liquidity_validation"""
    ...


def get_participant_to_remove_liquidity_validation() -> Mapping[str, SignaturePayload]:
    """Returns test value for participant_to_remove_liquidity_validation"""
    ...


def get_most_voted_remove_liquidity_validation() -> str:
    """Returns test value for most_voted_remove_liquidity_validation"""
    ...


def get_participant_to_remove_allowance_validation() -> Mapping[str, SignaturePayload]:
    """Returns test value for participant_to_remove_allowance_validation"""
    ...


def get_most_voted_remove_allowance_validation() -> str:
    """Returns test value for most_voted_remove_allowance_validation"""
    ...


def get_participant_to_swap_back_validation() -> Mapping[str, SignaturePayload]:
    """Returns test value for participant_to_swap_back_validation"""
    ...


def get_most_voted_swap_back_validation() -> str:
    """Returns test value for most_voted_swap_back_validation"""
    ...


def get_final_swap_tx_hash() -> str:
    """Returns test value for final_swap_tx_hash"""
    ...


def get_final_add_allowance_tx_hash() -> str:
    """Returns test value for final_add_allowance_tx_hash"""
    ...


def get_final_add_liquidity_tx_hash() -> str:
    """Returns test value for final_add_liquidity_tx_hash"""
    ...


def get_final_remove_liquidity_tx_hash() -> str:
    """Returns test value for final_remove_liquidity_tx_hash"""
    ...


def get_final_remove_allowance_tx_hash() -> str:
    """Returns test value for final_remove_allowance_tx_hash"""
    ...


def get_final_swap_back_tx_hash() -> str:
    """Returns test value for final_swap_back_tx_hash"""
    ...


class BaseRoundTestClass:
    """Base test class for Rounds."""

    period_state: PeriodState
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.period_state = PeriodState(participants=cls.participants)
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    def _test_no_majority_event(self, round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            _, event = result
            assert event == Event.NO_MAJORITY

class TestTransactionHashBaseRound(BaseRoundTestClass):
    """Test TransactionHashBaseRound"""

    def test_run(self,) -> None:
        """Run tests."""

        test_round = TransactionHashBaseRound(self.period_state, self.consensus_params)
        (sender, first_payload), *transaction_hash_payloads = get_participant_to_tx_hash(self.participants).items()

        test_round.process_payload(first_payload)
        assert not test_round.threshold_reached
        with pytest.raises(ABCIAppInternalError, "not enough votes"):
            _ = test_round.most_voted_payload

class TestTransactionSignatureBaseRound(BaseRoundTestClass):
    """Test TransactionSignatureBaseRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestTransactionSendBaseRound(BaseRoundTestClass):
    """Test TransactionSendBaseRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestTransactionValidationBaseRound(BaseRoundTestClass):
    """Test TransactionValidationBaseRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSelectKeeperMainRound(BaseRoundTestClass):
    """Test SelectKeeperMainRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestDeploySelectKeeperRound(BaseRoundTestClass):
    """Test DeploySelectKeeperRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestStrategyEvaluationRound(BaseRoundTestClass):
    """Test StrategyEvaluationRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestWaitRound(BaseRoundTestClass):
    """Test WaitRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapSelectKeeperRound(BaseRoundTestClass):
    """Test SwapSelectKeeperRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapTransactionHashRound(BaseRoundTestClass):
    """Test SwapTransactionHashRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapSignatureRound(BaseRoundTestClass):
    """Test SwapSignatureRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapSendRound(BaseRoundTestClass):
    """Test SwapSendRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapValidationRound(BaseRoundTestClass):
    """Test SwapValidationRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAllowanceCheckRound(BaseRoundTestClass):
    """Test AllowanceCheckRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddAllowanceSelectKeeperRound(BaseRoundTestClass):
    """Test AddAllowanceSelectKeeperRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddAllowanceTransactionHashRound(BaseRoundTestClass):
    """Test AddAllowanceTransactionHashRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddAllowanceSignatureRound(BaseRoundTestClass):
    """Test AddAllowanceSignatureRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddAllowanceSendRound(BaseRoundTestClass):
    """Test AddAllowanceSendRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddAllowanceValidationRound(BaseRoundTestClass):
    """Test AddAllowanceValidationRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddLiquiditySelectKeeperRound(BaseRoundTestClass):
    """Test AddLiquiditySelectKeeperRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddLiquidityTransactionHashRound(BaseRoundTestClass):
    """Test AddLiquidityTransactionHashRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddLiquiditySignatureRound(BaseRoundTestClass):
    """Test AddLiquiditySignatureRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddLiquiditySendRound(BaseRoundTestClass):
    """Test AddLiquiditySendRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestAddLiquidityValidationRound(BaseRoundTestClass):
    """Test AddLiquidityValidationRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveLiquiditySelectKeeperRound(BaseRoundTestClass):
    """Test RemoveLiquiditySelectKeeperRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveLiquidityTransactionHashRound(BaseRoundTestClass):
    """Test RemoveLiquidityTransactionHashRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveLiquiditySignatureRound(BaseRoundTestClass):
    """Test RemoveLiquiditySignatureRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveLiquiditySendRound(BaseRoundTestClass):
    """Test RemoveLiquiditySendRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveLiquidityValidationRound(BaseRoundTestClass):
    """Test RemoveLiquidityValidationRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveAllowanceSelectKeeperRound(BaseRoundTestClass):
    """Test RemoveAllowanceSelectKeeperRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveAllowanceTransactionHashRound(BaseRoundTestClass):
    """Test RemoveAllowanceTransactionHashRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveAllowanceSignatureRound(BaseRoundTestClass):
    """Test RemoveAllowanceSignatureRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveAllowanceSendRound(BaseRoundTestClass):
    """Test RemoveAllowanceSendRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestRemoveAllowanceValidationRound(BaseRoundTestClass):
    """Test RemoveAllowanceValidationRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapBackSelectKeeperRound(BaseRoundTestClass):
    """Test SwapBackSelectKeeperRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapBackTransactionHashRound(BaseRoundTestClass):
    """Test SwapBackTransactionHashRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapBackSignatureRound(BaseRoundTestClass):
    """Test SwapBackSignatureRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapBackSendRound(BaseRoundTestClass):
    """Test SwapBackSendRound"""

    def test_run(self,) -> None:
        """Run tests."""

class TestSwapBackValidationRound(BaseRoundTestClass):
    """Test SwapBackValidationRound"""

    def test_run(self,) -> None:
        """Run tests."""
