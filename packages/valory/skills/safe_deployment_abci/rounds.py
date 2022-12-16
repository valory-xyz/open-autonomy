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
from typing import Dict, List, Set, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    OnlyKeeperSendsRound,
    VotingRound,
    get_name,
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


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))


class RandomnessSafeRound(CollectSameUntilThresholdRound):
    """A round for generating randomness"""

    allowed_tx_type = RandomnessPayload.transaction_type
    payload_attribute = get_name(RandomnessPayload.randomness)
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_randomness)
    selection_key = get_name(SynchronizedData.most_voted_randomness)


class SelectKeeperSafeRound(CollectSameUntilThresholdRound):
    """A round in a which keeper is selected"""

    allowed_tx_type = SelectKeeperPayload.transaction_type
    payload_attribute = get_name(SelectKeeperPayload.keeper)
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_selection)
    selection_key = get_name(SynchronizedData.most_voted_keeper_address)


class DeploySafeRound(OnlyKeeperSendsRound):
    """A round in a which the safe is deployed"""

    allowed_tx_type = DeploySafePayload.transaction_type
    payload_attribute = get_name(DeploySafePayload.safe_contract_address)
    synchronized_data_class = SynchronizedData
    done_event = Event.DONE
    fail_event = Event.FAILED
    payload_key = get_name(SynchronizedData.safe_contract_address)


class ValidateSafeRound(VotingRound):
    """A round in a which the safe address is validated"""

    allowed_tx_type = ValidatePayload.transaction_type
    payload_attribute = get_name(ValidatePayload.vote)
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_votes)
    synchronized_data_class = SynchronizedData


class FinishedSafeRound(DegenerateRound):
    """A round that represents that the safe has been deployed"""


class SafeDeploymentAbciApp(AbciApp[Event]):
    """SafeDeploymentAbciApp

    Initial round: RandomnessSafeRound

    Initial states: {RandomnessSafeRound}

    Transition states:
        0. RandomnessSafeRound
            - done: 1.
            - round timeout: 0.
            - no majority: 0.
        1. SelectKeeperSafeRound
            - done: 2.
            - round timeout: 0.
            - no majority: 0.
        2. DeploySafeRound
            - done: 3.
            - deploy timeout: 1.
            - failed: 1.
        3. ValidateSafeRound
            - done: 4.
            - negative: 0.
            - none: 0.
            - validate timeout: 0.
            - no majority: 0.
        4. FinishedSafeRound

    Final states: {FinishedSafeRound}

    Timeouts:
        round timeout: 30.0
        validate timeout: 30.0
        deploy timeout: 30.0
    """

    initial_round_cls: AppState = RandomnessSafeRound
    transition_function: AbciAppTransitionFunction = {
        RandomnessSafeRound: {
            Event.DONE: SelectKeeperSafeRound,
            Event.ROUND_TIMEOUT: RandomnessSafeRound,
            Event.NO_MAJORITY: RandomnessSafeRound,
        },
        SelectKeeperSafeRound: {
            Event.DONE: DeploySafeRound,
            Event.ROUND_TIMEOUT: RandomnessSafeRound,
            Event.NO_MAJORITY: RandomnessSafeRound,
        },
        DeploySafeRound: {
            Event.DONE: ValidateSafeRound,
            Event.DEPLOY_TIMEOUT: SelectKeeperSafeRound,
            # NOTE: Consider the case where the keeper does send the tx but doesn't share the hash.
            # We do not need to check for this! A simple round timeout will do here as the safe is
            # either unusable by the keeper (requiring the other agent's to sign) or simply has signers which are
            # different to the other agents and therefore they don't care about this safe instance.
            Event.FAILED: SelectKeeperSafeRound,
        },
        ValidateSafeRound: {
            Event.DONE: FinishedSafeRound,
            Event.NEGATIVE: RandomnessSafeRound,
            Event.NONE: RandomnessSafeRound,  # NOTE: unreachable
            Event.VALIDATE_TIMEOUT: RandomnessSafeRound,
            Event.NO_MAJORITY: RandomnessSafeRound,
        },
        FinishedSafeRound: {},
    }
    final_states: Set[AppState] = {FinishedSafeRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.VALIDATE_TIMEOUT: 30.0,
        Event.DEPLOY_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys: List[str] = [
        get_name(SynchronizedData.safe_contract_address)
    ]
    db_pre_conditions: Dict[AppState, List[str]] = {
        RandomnessSafeRound: [get_name(BaseSynchronizedData.participants)]
    }
    db_post_conditions: Dict[AppState, List[str]] = {
        FinishedSafeRound: [get_name(SynchronizedData.safe_contract_address)]
    }
