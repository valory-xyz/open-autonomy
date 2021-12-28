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

"""This module contains the data classes for the oracle deployment ABCI application."""

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
from packages.valory.skills.oracle_deployment_abci.payloads import (
    DeployOraclePayload,
    RandomnessPayload,
    SelectKeeperPayload,
    ValidateOraclePayload,
)


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    NEGATIVE = "negative"
    NONE = "none"
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

    @property
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
        return cast(str, self.db.get("oracle_contract_address"))


class RandomnessOracleRound(CollectSameUntilThresholdRound):
    """RandomnessOracleRound round for startup."""

    round_id = "randomness_oracle"
    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_randomness"
    selection_key = "most_voted_randomness"


class SelectKeeperOracleRound(CollectSameUntilThresholdRound):
    """SelectKeeperOracleRound round for startup."""

    round_id = "select_keeper_oracle"
    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_selection"
    selection_key = "most_voted_keeper_address"


class DeployOracleRound(OnlyKeeperSendsRound):
    """
    This class represents the deploy Oracle round.

    Input: a set of participants (addresses) and a keeper
    Output: a period state with the set of participants, the keeper and the Oracle contract address.

    It schedules the ValidateOracleRound.
    """

    round_id = "deploy_oracle"
    allowed_tx_type = DeployOraclePayload.transaction_type
    payload_attribute = "oracle_contract_address"
    payload_key = "oracle_contract_address"
    done_event = Event.DONE


class ValidateOracleRound(VotingRound):
    """
    This class represents the validate Oracle round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the contract address

    It schedules the CollectObservationRound or SelectKeeperARound.
    """

    round_id = "validate_oracle"
    allowed_tx_type = ValidateOraclePayload.transaction_type
    state_key = "participant_to_votes"
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY


class FinishedOracleRound(DegenerateRound):
    """This class represents the finished round of the oracle deployment."""

    round_id = "finished_oracle"


class OracleDeploymentAbciApp(AbciApp[Event]):
    """Oracle deployment ABCI application."""

    initial_round_cls: Type[AbstractRound] = RandomnessOracleRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessOracleRound: {
            Event.DONE: SelectKeeperOracleRound,
            Event.ROUND_TIMEOUT: RandomnessOracleRound,  # if the round times out we restart
            Event.NO_MAJORITY: RandomnessOracleRound,  # we can have some agents on either side of an epoch, so we retry
        },
        SelectKeeperOracleRound: {
            Event.DONE: DeployOracleRound,
            Event.ROUND_TIMEOUT: RandomnessOracleRound,  # if the round times out we restart
            Event.NO_MAJORITY: RandomnessOracleRound,  # if the round has no majority we restart
        },
        DeployOracleRound: {
            Event.DONE: ValidateOracleRound,
            Event.DEPLOY_TIMEOUT: SelectKeeperOracleRound,  # if the round times out we try with a new keeper; TODO: what if the keeper does send the tx but doesn't share the hash? need to check for this! simple round timeout won't do here, need an intermediate step.
        },
        ValidateOracleRound: {
            Event.DONE: FinishedOracleRound,
            Event.NEGATIVE: RandomnessOracleRound,  # if the round does not reach a positive vote we restart
            Event.NONE: RandomnessOracleRound,  # NOTE: unreachable
            Event.VALIDATE_TIMEOUT: RandomnessOracleRound,  # the tx validation logic has its own timeout, this is just a safety check
            Event.NO_MAJORITY: RandomnessOracleRound,  # if the round has no majority we restart
        },
        FinishedOracleRound: {},
    }
    final_states: Set[AppState] = {FinishedOracleRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.DEPLOY_TIMEOUT: 30.0,
    }
