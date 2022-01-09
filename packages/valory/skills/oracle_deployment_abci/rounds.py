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
    FAILED = "failed"
    DEPLOY_TIMEOUT = "deploy_timeout"
    VALIDATE_TIMEOUT = "validate_timeout"


class PeriodState(BasePeriodState):
    """Class to represent a period state.

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
    """A round in which a random number is retrieved

    This number is obtained from a distributed randomness beacon. The agents
    need to reach consensus on this number and subsequently use it to seed
    any random number generators.
    """

    round_id = "randomness_oracle"
    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = "randomness"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_randomness"
    selection_key = "most_voted_randomness"


class SelectKeeperOracleRound(CollectSameUntilThresholdRound):
    """A round in which a single agent is chosen to be the oracle keeper"""

    round_id = "select_keeper_oracle"
    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = "keeper"
    period_state_class = PeriodState
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_selection"
    selection_key = "most_voted_keeper_address"


class DeployOracleRound(OnlyKeeperSendsRound):
    """A round in which the chosen agent deploys the oracle"""

    round_id = "deploy_oracle"
    allowed_tx_type = DeployOraclePayload.transaction_type
    payload_attribute = "oracle_contract_address"
    period_state_class = PeriodState
    done_event = Event.DONE
    fail_event = Event.FAILED
    payload_key = "oracle_contract_address"


class ValidateOracleRound(VotingRound):
    """A round in which the agents validate the oracle contract address"""

    round_id = "validate_oracle"
    allowed_tx_type = ValidateOraclePayload.transaction_type
    payload_attribute = "vote"
    period_state_class = PeriodState
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_votes"


class FinishedOracleRound(DegenerateRound):
    """A round that signals that oracle deployment has finished"""

    round_id = "finished_oracle"


class OracleDeploymentAbciApp(AbciApp[Event]):
    """OracleDeploymentAbciApp

    Initial round: RandomnessOracleRound

    Initial states:

    Transition states:
    0. RandomnessOracleRound
        - done: 1.
        - round timeout: 0.
        - no majority: 0.
    1. SelectKeeperOracleRound
        - done: 2.
        - round timeout: 0.
        - no majority: 0.
    2. DeployOracleRound
        - done: 3.
        - deploy timeout: 1.
        - failed: 1.
    3. ValidateOracleRound
        - done: 4.
        - negative: 0.
        - none: 0.
        - validate timeout: 0.
        - no majority: 0.
    4. FinishedOracleRound

    Final states: FinishedOracleRound

    Timeouts:
        round timeout: 30.0
        validate timeout: 30.0
        deploy timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = RandomnessOracleRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessOracleRound: {
            Event.DONE: SelectKeeperOracleRound,
            Event.ROUND_TIMEOUT: RandomnessOracleRound,
            Event.NO_MAJORITY: RandomnessOracleRound,
        },
        SelectKeeperOracleRound: {
            Event.DONE: DeployOracleRound,
            Event.ROUND_TIMEOUT: RandomnessOracleRound,
            Event.NO_MAJORITY: RandomnessOracleRound,
        },
        DeployOracleRound: {
            Event.DONE: ValidateOracleRound,
            Event.DEPLOY_TIMEOUT: SelectKeeperOracleRound,  # TODO: what if the keeper does send the tx but doesn't share the hash? need to check for this! simple round timeout won't do here, need an intermediate step.
            Event.FAILED: SelectKeeperOracleRound,
        },
        ValidateOracleRound: {
            Event.DONE: FinishedOracleRound,
            Event.NEGATIVE: RandomnessOracleRound,
            Event.NONE: RandomnessOracleRound,  # NOTE: unreachable
            Event.VALIDATE_TIMEOUT: RandomnessOracleRound,
            Event.NO_MAJORITY: RandomnessOracleRound,
        },
        FinishedOracleRound: {},
    }
    final_states: Set[AppState] = {FinishedOracleRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.DEPLOY_TIMEOUT: 30.0,
    }
