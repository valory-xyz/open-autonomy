# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Test the base.py module of the skill."""
import logging  # noqa: F401
from types import MappingProxyType
from typing import Dict, FrozenSet, Optional, Type, cast
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BaseTxPayload,
    ConsensusParams,
)
from packages.valory.skills.agent_registration_abci.rounds import (
    RegistrationStartupRound,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    DeployOraclePayload,
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionHashPayload,
    ValidatePayload,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    CollectSignatureRound,
    DeployOracleRound,
    DeploySafeRound,
    EstimateConsensusRound,
    Event,
    FinalizationRound,
    PeriodState,
    RandomnessRound,
    RegistrationRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    ResetRound as ConsensusReachedRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    SelectKeeperARound,
    SelectKeeperAStartupRound,
    SelectKeeperBRound,
    SelectKeeperBStartupRound,
    SelectKeeperRound,
    TxHashRound,
    ValidateOracleRound,
    ValidateRound,
    ValidateSafeRound,
    ValidateTransactionRound,
    encode_float,
    rotate_list,
)

from tests.test_skills.test_abstract_round_abci.test_base_rounds import (
    BaseCollectDifferentUntilAllRoundTest,
    BaseCollectDifferentUntilThresholdRoundTest,
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
) -> Dict[str, SelectKeeperPayload]:
    """participant_to_selection"""
    return {
        participant: SelectKeeperPayload(sender=participant, keeper="keeper")
        for participant in participants
    }


def get_participant_to_period_count(
    participants: FrozenSet[str], period_count: int
) -> Dict[str, ResetPayload]:
    """participant_to_selection"""
    return {
        participant: ResetPayload(sender=participant, period_count=period_count)
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


def get_participant_to_observations(
    participants: FrozenSet[str],
) -> Dict[str, ObservationPayload]:
    """participant_to_observations"""
    return {
        participant: ObservationPayload(sender=participant, observation=1.0)
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


def get_estimate() -> float:
    """Estimate"""
    return 1.0


def get_most_voted_estimate() -> float:
    """most_voted_estimate"""
    return 1.0


def get_participant_to_tx_hash(
    participants: FrozenSet[str], hash_: Optional[str] = "tx_hash"
) -> Dict[str, TransactionHashPayload]:
    """participant_to_tx_hash"""
    return {
        participant: TransactionHashPayload(sender=participant, tx_hash=hash_)
        for participant in participants
    }


def get_most_voted_tx_hash() -> str:
    """most_voted_tx_hash"""
    return "tx_hash"


def get_participant_to_signature(
    participants: FrozenSet[str],
) -> Dict[str, SignaturePayload]:
    """participant_to_signature"""
    return {
        participant: SignaturePayload(sender=participant, signature="signature")
        for participant in participants
    }


def get_final_tx_hash() -> str:
    """final_tx_hash"""
    return "tx_hash"


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
            state, event = result
            assert event == Event.NO_MAJORITY


class TestRegistrationStartupRound(BaseCollectDifferentUntilAllRoundTest):
    """Test RegistrationStartupRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run_fastforward(
        self,
    ) -> None:
        """Run test."""

        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                period_setup_params={
                    "safe_contract_address": "stub_safe_contract_address",
                    "oracle_contract_address": "stub_oracle_contract_address",
                }
            ),
        )

        test_round = RegistrationStartupRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round, Event.FAST_FORWARD, 1)

    def test_run_default(
        self,
    ) -> None:
        """Run test."""

        test_round = RegistrationStartupRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round, Event.DONE, 1)

    def test_run_default_not_finished(
        self,
    ) -> None:
        """Run test."""

        test_round = RegistrationStartupRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round)

    def _run_with_round(
        self,
        test_round: RegistrationStartupRound,
        expected_event: Optional[Event] = None,
        confirmations: Optional[int] = None,
    ) -> None:
        """Run with given round."""

        test_runner = self._test_round(
            test_round=test_round,
            round_payloads=[
                RegistrationPayload(sender=participant)
                for participant in self.participants
            ],
            state_update_fn=lambda *x: PeriodState(participants=test_round.collection),
            state_attr_checks=[lambda state: state.participants],
            exit_event=expected_event,
        )

        next(test_runner)
        test_round = next(test_runner)
        if confirmations is not None:
            test_round.block_confirmations = confirmations
        prior_confirmations = test_round.block_confirmations

        next(test_runner)
        assert test_round.block_confirmations == prior_confirmations + 1
        next(test_runner)


class TestRegistrationRound(BaseCollectDifferentUntilThresholdRoundTest):
    """Test RegistrationRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run_default(
        self,
    ) -> None:
        """Run test."""
        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )
        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round, Event.DONE, 10)

    def test_run_default_not_finished(
        self,
    ) -> None:
        """Run test."""
        self.period_state = cast(
            PeriodState,
            self.period_state.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )
        test_round = RegistrationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._run_with_round(test_round, finished=False)

    def _run_with_round(
        self,
        test_round: RegistrationRound,
        expected_event: Optional[Event] = None,
        confirmations: Optional[int] = None,
        finished: bool = True,
    ) -> None:
        """Run with given round."""

        test_runner = self._test_round(
            test_round=test_round,
            round_payloads=dict(
                [
                    (participant, RegistrationPayload(sender=participant))
                    for participant in self.participants
                ]
            ),
            state_update_fn=(lambda *x: PeriodState(participants=self.participants)),
            state_attr_checks=[lambda state: state.participants],
            exit_event=expected_event,
        )

        next(test_runner)
        test_round = next(test_runner)
        if confirmations is not None:
            test_round.block_confirmations = confirmations
        prior_confirmations = test_round.block_confirmations

        next(test_runner)
        assert test_round.block_confirmations == prior_confirmations + 1
        if finished:
            next(test_runner)


class TestRandomnessRound(BaseCollectSameUntilThresholdRoundTest):
    """Test RandomnessRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = RandomnessRound(self.period_state, self.consensus_params)
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_randomness(self.participants, 1),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_randomness=MappingProxyType(
                        dict(get_participant_to_randomness(self.participants, 1))
                    )
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_randomness.keys()
                ],
                most_voted_payload=RANDOMNESS,
                exit_event=Event.DONE,
            )
        )


class TestSelectKeeperRound(BaseCollectSameUntilThresholdRoundTest):
    """Test SelectKeeperRound"""

    _period_state_class = PeriodState
    _event_class = Event

    @classmethod
    def setup(cls) -> None:
        """Set up the test."""
        super().setup()
        SelectKeeperRound.round_id = "round_id"

    def teardown(self) -> None:
        """Tear down the test."""
        delattr(SelectKeeperRound, "round_id")

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = SelectKeeperRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_selection(self.participants),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_selection=MappingProxyType(
                        dict(get_participant_to_selection(self.participants))
                    ),
                ),
                state_attr_checks=[lambda state: state.participant_to_selection.keys()],
                most_voted_payload="keeper",
                exit_event=Event.DONE,
            )
        )


class BaseDeployTestClass(BaseOnlyKeeperSendsRoundTest):
    """Test DeploySafeRound."""

    round_class: Type[AbstractRound]
    payload_class: Type[BaseTxPayload]
    update_keyword: str

    _period_state_class = PeriodState
    _event_class = Event

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
                exit_event=Event.DONE,
            )
        )


class TestDeploySafeRound(BaseDeployTestClass):
    """Test DeploySafeRound."""

    round_class = DeploySafeRound
    payload_class = DeploySafePayload
    update_keyword = "safe_contract_address"


class TestDeployOracleRound(BaseDeployTestClass):
    """Test DeployOracleRound."""

    round_class = DeployOracleRound
    payload_class = DeployOraclePayload
    update_keyword = "oracle_contract_address"


class TestCollectObservationRound(BaseCollectDifferentUntilThresholdRoundTest):
    """Test CollectObservationRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run_a(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectObservationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_observations(self.participants),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    participant_to_observations=get_participant_to_observations(
                        self.participants
                    )
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_observations.keys()
                ],
                exit_event=Event.DONE,
            )
        )

    def test_run_b(
        self,
    ) -> None:
        """Runs tests with one less observation."""

        test_round = CollectObservationRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_observations(
                    frozenset(list(self.participants)[:-1])
                ),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    participant_to_observations=get_participant_to_observations(
                        frozenset(list(self.participants)[:-1])
                    )
                ),
                state_attr_checks=[
                    lambda state: state.participant_to_observations.keys()
                ],
                exit_event=Event.DONE,
            )
        )


class TestEstimateConsensusRound(BaseCollectSameUntilThresholdRoundTest):
    """Test EstimateConsensusRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = EstimateConsensusRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_estimate(self.participants),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_estimate=dict(
                        get_participant_to_estimate(self.participants)
                    ),
                    most_voted_estimate=_test_round.most_voted_payload,
                ),
                state_attr_checks=[lambda state: state.participant_to_estimate.keys()],
                most_voted_payload=1.0,
                exit_event=Event.DONE,
            )
        )


class TestTxHashRound(BaseCollectSameUntilThresholdRoundTest):
    """Test TxHashRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        hash_ = "tx_hash"
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_tx_hash(self.participants, hash_),
                state_update_fn=lambda _period_state, _test_round: _period_state,
                state_attr_checks=[],
                most_voted_payload=hash_,
                exit_event=Event.DONE,
            )
        )

    def test_run_none(
        self,
    ) -> None:
        """Runs test."""

        test_round = TxHashRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        hash_ = None
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_tx_hash(self.participants, hash_),
                state_update_fn=lambda _period_state, _test_round: _period_state,
                state_attr_checks=[],
                most_voted_payload=hash_,
                exit_event=Event.NONE,
            )
        )


class TestCollectSignatureRound(BaseCollectDifferentUntilThresholdRoundTest):
    """Test CollectSignatureRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Runs tests."""

        test_round = CollectSignatureRound(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_signature(self.participants),
                state_update_fn=lambda _period_state, _: _period_state,
                state_attr_checks=[],
                exit_event=Event.DONE,
            )
        )

    def test_no_majority_event(self) -> None:
        """Test the no-majority event."""
        test_round = CollectSignatureRound(self.period_state, self.consensus_params)
        self._test_no_majority_event(test_round)


class TestFinalizationRound(BaseOnlyKeeperSendsRoundTest):
    """Test FinalizationRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_run_success(
        self,
    ) -> None:
        """Runs tests."""

        keeper = sorted(list(self.participants))[0]
        self.period_state = cast(
            PeriodState,
            self.period_state.update(most_voted_keeper_address=keeper),
        )

        test_round = FinalizationRound(
            state=self.period_state,
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                keeper_payloads=FinalizationTxPayload(sender=keeper, tx_hash="tx_hash"),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    final_tx_hash=get_final_tx_hash()
                ),
                state_attr_checks=[lambda state: state.final_tx_hash],
                exit_event=Event.DONE,
            )
        )

    def test_run_failure(
        self,
    ) -> None:
        """Runs tests."""

        keeper = sorted(list(self.participants))[0]
        self.period_state = cast(
            PeriodState,
            self.period_state.update(most_voted_keeper_address=keeper),
        )

        test_round = FinalizationRound(
            state=self.period_state,
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                keeper_payloads=FinalizationTxPayload(sender=keeper, tx_hash=None),
                state_update_fn=lambda _period_state, _: _period_state.update(
                    final_tx_hash=get_final_tx_hash()
                ),
                state_attr_checks=[],
                exit_event=Event.FAILED,
            )
        )


class BaseSelectKeeperRoundTest(BaseCollectSameUntilThresholdRoundTest):
    """Test SelectKeeperARound"""

    test_class: Type[SelectKeeperRound]
    test_payload: Type[SelectKeeperPayload]

    _period_state_class = PeriodState
    _event_class = Event

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = self.test_class(
            state=self.period_state, consensus_params=self.consensus_params
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_selection(self.participants),
                state_update_fn=lambda _period_state, _test_round: _period_state.update(
                    participant_to_selection=MappingProxyType(
                        dict(get_participant_to_selection(self.participants))
                    )
                ),
                state_attr_checks=[lambda state: state.participant_to_selection.keys()],
                most_voted_payload="keeper",
                exit_event=Event.DONE,
            )
        )


class TestSelectKeeperARound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperARound"""

    test_class = SelectKeeperARound
    test_payload = SelectKeeperPayload


class TestSelectKeeperBRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperBRound."""

    test_class = SelectKeeperBRound
    test_payload = SelectKeeperPayload


class TestSelectKeeperAStartupRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperBRound."""

    test_class = SelectKeeperAStartupRound
    test_payload = SelectKeeperPayload


class TestSelectKeeperBStartupRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperBRound."""

    test_class = SelectKeeperBStartupRound
    test_payload = SelectKeeperPayload


class TestConsensusReachedRound(BaseCollectSameUntilThresholdRoundTest):
    """Test ConsensusReachedRound."""

    _period_state_class = PeriodState
    _event_class = Event

    def test_runs(
        self,
    ) -> None:
        """Runs tests."""

        test_round = ConsensusReachedRound(
            state=self.period_state, consensus_params=self.consensus_params
        )
        next_period_count = 2
        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=get_participant_to_period_count(
                    self.participants, next_period_count
                ),
                state_update_fn=lambda *_: PeriodState(
                    participants=self.participants,
                    period_count=test_round.most_voted_payload,
                ),
                state_attr_checks=[lambda state: state.participants],
                most_voted_payload=next_period_count,
                exit_event=Event.DONE,
            )
        )


class BaseValidateRoundTest(BaseVotingRoundTest):
    """Test BaseValidateRound."""

    test_class: Type[ValidateRound]
    test_payload: Type[ValidatePayload]

    _period_state_class = PeriodState
    _event_class = Event

    def test_positive_votes(
        self,
    ) -> None:
        """Test ValidateRound."""

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
                exit_event=Event.DONE,
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
                exit_event=Event.NEGATIVE,
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
                exit_event=Event.NONE,
            )
        )


class TestValidateSafeRound(BaseValidateRoundTest):
    """Test ValidateSafeRound."""

    test_class = ValidateSafeRound
    test_payload = ValidatePayload


class TestValidateOracleRound(BaseValidateRoundTest):
    """Test ValidateSafeRound."""

    test_class = ValidateOracleRound
    test_payload = ValidatePayload


class TestValidateTransactionRound(BaseValidateRoundTest):
    """Test ValidateRound."""

    test_class = ValidateTransactionRound
    test_payload = ValidatePayload


def test_rotate_list_method() -> None:
    """Test `rotate_list` method."""

    ex_list = [1, 2, 3, 4, 5]
    assert rotate_list(ex_list, 2) == [3, 4, 5, 1, 2]


def test_period_state() -> None:
    """Test PeriodState."""

    participants = get_participants()
    participant_to_randomness = get_participant_to_randomness(participants, 1)
    most_voted_randomness = get_most_voted_randomness()
    participant_to_selection = get_participant_to_selection(participants)
    most_voted_keeper_address = get_most_voted_keeper_address()
    safe_contract_address = get_safe_contract_address()
    oracle_contract_address = get_safe_contract_address()
    participant_to_votes = get_participant_to_votes(participants)
    participant_to_observations = get_participant_to_observations(participants)
    participant_to_estimate = get_participant_to_estimate(participants)
    estimate = get_estimate()
    most_voted_estimate = get_most_voted_estimate()
    participant_to_tx_hash = get_participant_to_tx_hash(participants)
    most_voted_tx_hash = get_most_voted_tx_hash()
    participant_to_signature = get_participant_to_signature(participants)
    final_tx_hash = get_final_tx_hash()

    period_state = PeriodState(
        participants=participants,
        participant_to_randomness=participant_to_randomness,
        most_voted_randomness=most_voted_randomness,
        participant_to_selection=participant_to_selection,
        most_voted_keeper_address=most_voted_keeper_address,
        safe_contract_address=safe_contract_address,
        oracle_contract_address=oracle_contract_address,
        participant_to_votes=participant_to_votes,
        participant_to_observations=participant_to_observations,
        participant_to_estimate=participant_to_estimate,
        estimate=estimate,
        most_voted_estimate=most_voted_estimate,
        participant_to_tx_hash=participant_to_tx_hash,
        most_voted_tx_hash=most_voted_tx_hash,
        participant_to_signature=participant_to_signature,
        final_tx_hash=final_tx_hash,
    )

    actual_keeper_randomness = float(
        (int(most_voted_randomness, base=16) // 10 ** 0 % 10) / 10
    )
    assert period_state.keeper_randomness == actual_keeper_randomness
    assert period_state.participant_to_randomness == participant_to_randomness
    assert period_state.most_voted_randomness == most_voted_randomness
    assert period_state.participant_to_selection == participant_to_selection
    assert period_state.most_voted_keeper_address == most_voted_keeper_address
    assert period_state.safe_contract_address == safe_contract_address
    assert period_state.oracle_contract_address == oracle_contract_address
    assert period_state.participant_to_votes == participant_to_votes
    assert period_state.participant_to_observations == participant_to_observations
    assert period_state.participant_to_estimate == participant_to_estimate
    assert period_state.estimate == estimate
    assert period_state.most_voted_estimate == most_voted_estimate
    assert period_state.is_most_voted_estimate_set is True
    assert period_state.most_voted_tx_hash == most_voted_tx_hash
    assert period_state.participant_to_signature == participant_to_signature
    assert period_state.final_tx_hash == final_tx_hash
    assert period_state.is_final_tx_hash_set is True

    assert period_state.encoded_most_voted_estimate == encode_float(most_voted_estimate)
