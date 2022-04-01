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

"""Tests for valory/registration_abci skill's rounds."""

import logging  # noqa: F401
from collections import deque
from types import MappingProxyType
from typing import Any, Deque, Dict, FrozenSet, Optional, Type, cast

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.base import (
    BasePeriodState as PeriodState,
)
from packages.valory.skills.abstract_round_abci.base import (
    BaseTxPayload,
    CollectSameUntilThresholdRound,
    StateDB,
    VotingRound,
)
from packages.valory.skills.oracle_deployment_abci.payloads import (
    DeployOraclePayload,
    RandomnessPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.oracle_deployment_abci.rounds import DeployOracleRound
from packages.valory.skills.oracle_deployment_abci.rounds import (
    Event as OracleDeploymentEvent,
)
from packages.valory.skills.oracle_deployment_abci.rounds import (
    PeriodState as OracleDeploymentPeriodState,
)
from packages.valory.skills.oracle_deployment_abci.rounds import (
    SelectKeeperOracleRound,
    ValidateOracleRound,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    EstimatePayload,
    TransactionHashPayload,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
)
from packages.valory.skills.transaction_settlement_abci.payloads import ValidatePayload

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectSameUntilThresholdRoundTest,
    BaseOnlyKeeperSendsRoundTest,
    BaseVotingRoundTest,
)


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_randomness(
    participants: FrozenSet[str], round_id: int
) -> Dict[str, RandomnessPayload]:
    """participant_to_randomness"""
    return {
        participant: RandomnessPayload(
            sender=participant,
            round_id=round_id,
            randomness=RANDOMNESS,
        )
        for participant in participants
    }


def get_most_voted_randomness() -> str:
    """most_voted_randomness"""
    return RANDOMNESS


def get_participant_to_selection(
    participants: FrozenSet[str],
    keeper: str = "keeper",
) -> Dict[str, SelectKeeperPayload]:
    """participant_to_selection"""
    return {
        participant: SelectKeeperPayload(sender=participant, keeper=keeper)
        for participant in participants
    }


def get_most_voted_keeper_address() -> str:
    """most_voted_keeper_address"""
    return "keeper"


def get_safe_contract_address() -> str:
    """safe_contract_address"""
    return "0x6f6ab56aca12"


def get_participant_to_votes(
    participants: FrozenSet[str], vote: Optional[bool] = True
) -> Dict[str, ValidatePayload]:
    """participant_to_votes"""
    return {
        participant: ValidatePayload(sender=participant, vote=vote)
        for participant in participants
    }


def get_participant_to_estimate(
    participants: FrozenSet[str],
) -> Dict[str, EstimatePayload]:
    """participant_to_estimate"""
    return {
        participant: EstimatePayload(sender=participant, estimate=1.0)
        for participant in participants
    }


def get_participant_to_tx_hash(
    participants: FrozenSet[str], hash_: Optional[str] = "tx_hash"
) -> Dict[str, TransactionHashPayload]:
    """participant_to_tx_hash"""
    return {
        participant: TransactionHashPayload(sender=participant, tx_hash=hash_)
        for participant in participants
    }


class BaseDeployTestClass(BaseOnlyKeeperSendsRoundTest):
    """Test DeploySafeRound."""

    round_class: Type[AbstractRound]
    payload_class: Type[BaseTxPayload]
    update_keyword: str

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        keeper = sorted(list(self.participants))[0]
        self.period_state = cast(
            PeriodState,
            self.period_state.update(most_voted_keeper_address=keeper),
        )

        test_round = self.round_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,  # type: ignore
                keeper_payloads=self.payload_class(keeper, get_safe_contract_address()),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    **{self.update_keyword: get_safe_contract_address()}
                ),
                state_attr_checks=[lambda state: getattr(state, self.update_keyword)],
                exit_event=self._event_class.DONE,
            )
        )


class TestDeployOracleRound(BaseDeployTestClass):
    """Test DeployOracleRound."""

    round_class = DeployOracleRound
    payload_class = DeployOraclePayload
    update_keyword = "oracle_contract_address"
    _event_class = OracleDeploymentEvent
    _period_state_class = OracleDeploymentPeriodState


class BaseValidateRoundTest(BaseVotingRoundTest):
    """Test BaseValidateRound."""

    test_class: Type[VotingRound]
    test_payload: Type[ValidatePayload]

    def test_positive_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        self.period_state.update(tx_hashes_history=["test"])

        test_round = self.test_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_voting_round_positive(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    participant_to_votes=MappingProxyType(
                        dict(get_participant_to_votes(self.participants))
                    )
                ),
                state_attr_checks=[lambda state: state.participant_to_votes.keys()],
                exit_event=self._event_class.DONE,
            )
        )

    def test_negative_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_voting_round_negative(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants, vote=False),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    participant_to_votes=MappingProxyType(
                        dict(get_participant_to_votes(self.participants, vote=False))
                    )
                ),
                state_attr_checks=[],
                exit_event=self._event_class.NEGATIVE,
            )
        )

    def test_none_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

        test_round = self.test_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_voting_round_none(
                test_round=test_round,
                round_payloads=get_participant_to_votes(self.participants, vote=None),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    participant_to_votes=MappingProxyType(
                        dict(get_participant_to_votes(self.participants, vote=None))
                    )
                ),
                state_attr_checks=[],
                exit_event=self._event_class.NONE,
            )
        )


class TestValidateOracleRound(BaseValidateRoundTest):
    """Test ValidateSafeRound."""

    test_class = ValidateOracleRound
    test_payload = ValidatePayload
    _event_class = OracleDeploymentEvent
    _period_state_class = OracleDeploymentPeriodState


class BaseSelectKeeperRoundTest(BaseCollectSameUntilThresholdRoundTest):
    """Test SelectKeeperTransactionSubmissionRoundA"""

    test_class: Type[CollectSameUntilThresholdRound]
    test_payload: Type[SelectKeeperPayload]

    _period_state_class = PeriodState
    _exit_event: Optional[Any] = None
    _most_voted_payload = "keeper"

    def test_run(
        self,
        keepers: Optional[Deque[str]] = None,
        keeper_retries: int = 1,
        blacklisted: bool = False,
    ) -> None:
        """Run tests."""
        if keepers is None:
            keepers = deque()

        test_round = self.test_class(
            state=self.period_state.update(
                keepers=deque(keepers),
                keeper_retries=keeper_retries,
                final_verification_status=VerificationStatus.PENDING,
                blacklisted_keepers={self._most_voted_payload} if blacklisted else {},
            ),
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_selection(
                    self.participants, self._most_voted_payload
                ),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_selection=MappingProxyType(
                        dict(
                            get_participant_to_selection(
                                self.participants, self._most_voted_payload
                            )
                        )
                    )
                ),
                state_attr_checks=[lambda state: state.participant_to_selection.keys()],
                most_voted_payload=self._most_voted_payload,
                exit_event=self._event_class.DONE
                if self._exit_event is None
                else self._exit_event,
            )
        )


class TestSelectKeeperOracleRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperTransactionSubmissionRoundB."""

    test_class = SelectKeeperOracleRound
    test_payload = SelectKeeperPayload
    _event_class = OracleDeploymentEvent


def test_period_states() -> None:
    """Test PeriodState."""

    participants = get_participants()
    participant_to_randomness = get_participant_to_randomness(participants, 1)
    most_voted_randomness = get_most_voted_randomness()
    participant_to_selection = get_participant_to_selection(participants)
    most_voted_keeper_address = get_most_voted_keeper_address()
    safe_contract_address = get_safe_contract_address()
    oracle_contract_address = get_safe_contract_address()
    participant_to_votes = get_participant_to_votes(participants)
    actual_keeper_randomness = float(
        (int(most_voted_randomness, base=16) // 10 ** 0 % 10) / 10
    )

    period_state__ = OracleDeploymentPeriodState(
        StateDB(
            initial_period=0,
            initial_data=dict(
                participants=participants,
                participant_to_randomness=participant_to_randomness,
                most_voted_randomness=most_voted_randomness,
                participant_to_selection=participant_to_selection,
                participant_to_votes=participant_to_votes,
                most_voted_keeper_address=most_voted_keeper_address,
                safe_contract_address=safe_contract_address,
                oracle_contract_address=oracle_contract_address,
            ),
        )
    )
    assert period_state__.keeper_randomness == actual_keeper_randomness
    assert period_state__.most_voted_randomness == most_voted_randomness
    assert period_state__.most_voted_keeper_address == most_voted_keeper_address
    assert period_state__.safe_contract_address == safe_contract_address
    assert period_state__.oracle_contract_address == oracle_contract_address
