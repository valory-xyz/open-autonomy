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

from abc import ABC
from typing import AbstractSet, Dict, Optional, Set, Tuple, Type, cast

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
    Event,
    FinishedRound,
    SelectKeeperRound,
    TransactionType,
    ValidateRound,
)
from packages.valory.skills.oracle_deployment_abci.payloads import DeployOraclePayload


class PeriodState(BasePeriodState):
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        participants: Optional[AbstractSet[str]] = None,
        period_count: Optional[int] = None,
        period_setup_params: Optional[Dict] = None,
        most_voted_keeper_address: Optional[str] = None,
        safe_contract_address: Optional[str] = None,
        oracle_contract_address: Optional[str] = None,
    ) -> None:
        """Initialize a period state."""
        super().__init__(
            participants=participants,
            period_count=period_count,
            period_setup_params=period_setup_params,
            most_voted_keeper_address=most_voted_keeper_address,
            safe_contract_address=safe_contract_address,
            oracle_contract_address=oracle_contract_address,
        )

    @property
    def most_voted_keeper_address(self) -> str:
        """Get the most_voted_keeper_address."""
        return cast(str, self.get("most_voted_keeper_address"))

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.get("safe_contract_address"))

    @property
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
        return cast(str, self.get("oracle_contract_address"))


class OracleDeploymentAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the agent registration skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[PeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state, Event.NO_MAJORITY


class RandomnessOracleRound(BaseRandomnessRound):
    """Randomness round for startup."""

    round_id = "randomness_oracle"


class SelectKeeperOracleRound(SelectKeeperRound):
    """SelectKeeperOracleRound round for startup."""

    round_id = "select_keeper_oracle"


class DeployOracleRound(OnlyKeeperSendsRound, OracleDeploymentAbstractRound):
    """
    This class represents the deploy Oracle round.

    Input: a set of participants (addresses) and a keeper
    Output: a period state with the set of participants, the keeper and the Oracle contract address.

    It schedules the ValidateOracleRound.
    """

    round_id = "deploy_oracle"
    allowed_tx_type = DeployOraclePayload.transaction_type
    payload_attribute = "oracle_contract_address"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        # if reached participant threshold, set the result
        if self.has_keeper_sent_payload:
            state = self.period_state.update(
                oracle_contract_address=self.keeper_payload
            )
            return state, Event.DONE
        return None


class ValidateOracleRound(ValidateRound):
    """
    This class represents the validate Oracle round.

    Input: a period state with the prior round data
    Output: a new period state with the prior round data and the validation of the contract address

    It schedules the CollectObservationRound or SelectKeeperARound.
    """

    round_id = "validate_oracle"
    negative_event = Event.NEGATIVE
    none_event = Event.NONE


class FinishedOracleRound(FinishedRound):
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
