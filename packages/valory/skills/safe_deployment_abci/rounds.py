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

"""This module contains the data classes for the safe deployment ABCI application."""

from typing import Dict, Optional, Set, Tuple, Type

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BasePeriodState,
    OnlyKeeperSendsRound,
)
from packages.valory.skills.common_apps.rounds import (
    BaseRandomnessRound,
    CommonAppsAbstractRound,
    Event,
    FinishedRound,
    SelectKeeperRound,
    ValidateRound,
)
from packages.valory.skills.safe_deployment_abci.payloads import DeploySafePayload


class RandomnessSafeRound(BaseRandomnessRound):
    """Randomness round for startup."""

    round_id = "randomness_safe"


class SelectKeeperSafeRound(SelectKeeperRound):
    """SelectKeeperSafeRound round for startup."""

    round_id = "select_keeper_safe"


class DeploySafeRound(OnlyKeeperSendsRound, CommonAppsAbstractRound):
    """
    This class represents the deploy Safe round.

    Input: a set of participants (addresses) and a keeper
    Output: a period state with the set of participants, the keeper and the Safe contract address.

    It schedules the ValidateSafeRound.
    """

    round_id = "deploy_safe"
    allowed_tx_type = DeploySafePayload.transaction_type
    payload_attribute = "safe_contract_address"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.has_keeper_sent_payload:
            state = self.period_state.update(safe_contract_address=self.keeper_payload)
            return state, Event.DONE
        return None


class ValidateSafeRound(ValidateRound):
    """
    This class represents the validate Safe round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the contract address

    It schedules the CollectObservationRound or SelectKeeperARound.
    """

    round_id = "validate_safe"
    negative_event = Event.NEGATIVE
    none_event = Event.NONE


class FinishedSafeRound(FinishedRound):
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
            Event.DEPLOY_TIMEOUT: SelectKeeperSafeRound,  # if the round times out we try with a new keeper; TODO: what if the keeper does send the tx but doesn't share the hash? need to check for this! simple round timeout won't do here, need an intermediate step.
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
