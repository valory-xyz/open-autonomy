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

"""This module contains the data classes for the safe deployment ABCI application."""

from enum import Enum
from typing import Dict, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    OnlyKeeperSendsRound,
    VotingRound,
)
from packages.valory.skills.safe_deployment_abci.payloads import (
    DeploySafePayload,
    RandomnessPayload,
    SelectKeeperPayload,
    ValidatePayload,
)


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    NEGATIVE = "negative"
    NONE = "none"
    FAILED = "failed"
    DEPLOY_TIMEOUT = "deploy_timeout"
    VALIDATE_TIMEOUT = "validate_timeout"


class PeriodState(BasePeriodState):
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))


class RandomnessSafeRound(CollectSameUntilThresholdRound):
    """Randomness round for startup."""

    round_id = "randomness_safe"
    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_randomness"
    selection_key = "most_voted_randomness"


class SelectKeeperSafeRound(CollectSameUntilThresholdRound):
    """SelectKeeperSafeRound round for startup."""

    round_id = "select_keeper_safe"
    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_selection"
    selection_key = "most_voted_keeper_address"


class DeploySafeRound(OnlyKeeperSendsRound):
    """
    This class represents the deploy Safe round.

    Input: a set of participants (addresses) and a keeper
    Output: a period state with the set of participants, the keeper and the Safe contract address.

    It schedules the ValidateSafeRound.
    """

    round_id = "deploy_safe"
    allowed_tx_type = DeploySafePayload.transaction_type
    payload_attribute = "safe_contract_address"
    period_state_class = PeriodState
    done_event = Event.DONE
    fail_event = Event.FAILED
    payload_key = "safe_contract_address"


class ValidateSafeRound(VotingRound):
    """
    This class represents the validate Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the contract address

    It schedules the CollectObservationRound or SelectKeeperARound.
    """

    round_id = "validate_safe"
    allowed_tx_type = ValidatePayload.transaction_type
    payload_attribute = "vote"
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_votes"


class FinishedSafeRound(DegenerateRound):
    """This class represents the finished round of the safe deployment."""

    round_id = "finished_safe"


class SafeDeploymentAbciApp(AbciApp[Event]):
    """Safe deployment ABCI application."""

    initial_round_cls: Type[AbstractRound] = RandomnessSafeRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessSafeRound: {
            Event.DONE: SelectKeeperSafeRound,
            Event.ROUND_TIMEOUT: RandomnessSafeRound,  # if the round times out we restart
            Event.NO_MAJORITY: RandomnessSafeRound,  # we can have some agents on either side of an epoch, so we retry
        },
        SelectKeeperSafeRound: {
            Event.DONE: DeploySafeRound,
            Event.ROUND_TIMEOUT: RandomnessSafeRound,  # if the round times out we restart
            Event.NO_MAJORITY: RandomnessSafeRound,  # if the round has no majority we restart
        },
        DeploySafeRound: {
            Event.DONE: ValidateSafeRound,
            Event.DEPLOY_TIMEOUT: SelectKeeperSafeRound,  # if the round times out we try with a new keeper;
            # NOTE: Consider the case where the keeper does send the tx but doesn't share the hash.
            # We do not need to check for this! A simple round timeout will do here as the safe is
            # either unusable by the keeper (requiring the other agent's to sign) or simply has signers which are
            # different to the other agents and therefore they don't care about this safe instance.
            Event.FAILED: SelectKeeperSafeRound,  # the keeper was unsuccessful;
        },
        ValidateSafeRound: {
            Event.DONE: FinishedSafeRound,
            Event.NEGATIVE: RandomnessSafeRound,  # if the round does not reach a positive vote we restart
            Event.NONE: RandomnessSafeRound,  # NOTE: unreachable
            Event.VALIDATE_TIMEOUT: RandomnessSafeRound,  # the tx validation logic has its own timeout, this is just a safety check
            Event.NO_MAJORITY: RandomnessSafeRound,  # if the round has no majority we restart
        },
        FinishedSafeRound: {},
    }
    final_states: Set[AppState] = {FinishedSafeRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.DEPLOY_TIMEOUT: 30.0,
    }
