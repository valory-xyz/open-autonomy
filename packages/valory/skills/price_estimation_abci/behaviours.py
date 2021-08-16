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

"""This module contains the behaviours for the 'abci' skill."""
import datetime
from functools import partial
from typing import Callable, Generator, cast

from aea.skills.behaviours import FSMBehaviour, State

from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    DONE_EVENT,
    WaitForConditionBehaviour,
)
from packages.valory.skills.price_estimation_abci.models.payloads import (
    EstimatePayload,
    ObservationPayload,
    RegistrationPayload,
)
from packages.valory.skills.price_estimation_abci.models.rounds import (
    CollectObservationRound,
    ConsensusReachedRound,
    EstimateConsensusRound,
    PeriodState,
    RegistrationRound,
)


class PriceEstimationConsensusBehaviour(FSMBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    def setup(self) -> None:
        """Set up the behaviour."""
        # initial delay to wait synchronization with Tendermint
        self.register_state(
            "wait_tendermint",
            WaitForConditionBehaviour(
                condition=self.get_wait_tendermint_rpc_is_ready(),
                name="wait_tendermint",
                skill_context=self.context,
            ),
            initial=True,
        )
        self.register_state(
            "register",
            RegistrationBehaviour(name="register", skill_context=self.context),
        )
        self.register_state(
            "wait_registration_threshold",
            WaitForConditionBehaviour(
                condition=self.wait_observation_round,
                name="wait_registration_threshold",
                skill_context=self.context,
            ),
        )
        self.register_state(
            "observe",
            ObserveBehaviour(name="observe", skill_context=self.context),
        )
        self.register_state(
            "wait_observation_threshold",
            WaitForConditionBehaviour(
                condition=self.wait_estimate_round,
                name="wait_observation_threshold",
                skill_context=self.context,
            ),
        )
        self.register_state(
            "estimate",
            EstimateBehaviour(name="estimate", skill_context=self.context),
        )

        self.register_state(
            "wait_estimate_threshold",
            WaitForConditionBehaviour(
                condition=self.wait_consensus_round,
                name="wait_estimate_threshold",
                skill_context=self.context,
            ),
        )

        self.register_state(
            "end",
            EndBehaviour(name="end", skill_context=self.context),
        )

        self.register_transition("wait_tendermint", "register", DONE_EVENT)
        self.register_transition("register", "wait_registration_threshold", DONE_EVENT)
        self.register_transition("wait_registration_threshold", "observe", DONE_EVENT)
        self.register_transition("observe", "wait_observation_threshold", DONE_EVENT)
        self.register_transition("wait_observation_threshold", "estimate", DONE_EVENT)
        self.register_transition("estimate", "wait_estimate_threshold", DONE_EVENT)
        self.register_transition("wait_estimate_threshold", "end", DONE_EVENT)

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def get_wait_tendermint_rpc_is_ready(self) -> Callable:
        """
        Wait Tendermint RPC server is up.

        This method will return a function that returns
        False until 'initial_delay' seconds (a skill parameter)
        have elapsed since the call of the method.

        :return: the function used to wait.
        """

        def _check_time(expected_time: datetime.datetime) -> bool:
            return datetime.datetime.now() > expected_time

        initial_delay = self.context.params.initial_delay
        date = datetime.datetime.now() + datetime.timedelta(0, initial_delay)
        return partial(_check_time, date)

    def wait_observation_round(self) -> bool:
        """Wait registration threshold is reached."""
        return (
            self.context.state.period.current_round_id
            == CollectObservationRound.round_id
        )

    def wait_estimate_round(self) -> bool:
        """Wait observation threshold is reached."""
        return (
            self.context.state.period.current_round_id
            == EstimateConsensusRound.round_id
        )

    def wait_consensus_round(self) -> bool:
        """Wait estimate threshold is reached."""
        return (
            self.context.state.period.current_round_id == ConsensusReachedRound.round_id
        )


class RegistrationBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Register to the next round."""

    def async_act(self) -> None:  # type: ignore
        """
        Do the action.

        Steps:
        - Build a registration transaction
        - Send the transaction and wait for it to be mined
        - Go to the next state.
        """
        self.context.logger.info("Entered in the 'registration' behaviour state")
        payload = RegistrationPayload(self.context.agent_address)
        stop_condition = self.is_round_ended(RegistrationRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)
        self.context.logger.info("'registration' behaviour state is done")
        self.set_done()


class ObserveBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Observe price estimate."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the price of a currency
        - Build an observation transaction
        - Send the transaction and wait for it to be mined
        - Go to the next state.
        """
        self.context.logger.info("Entered in the 'observation' behaviour state")
        currency_id = self.context.params.currency_id
        convert_id = self.context.params.convert_id
        observation = self.context.price_api.get_price(currency_id, convert_id)
        self.context.logger.info(
            f"Got observation of {currency_id} price in {convert_id} from {self.context.price_api.api_id}: {observation}"
        )
        payload = ObservationPayload(self.context.agent_address, observation)
        stop_condition = self.is_round_ended(CollectObservationRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)
        self.context.logger.info("'observation' behaviour state is done")
        self.set_done()


class EstimateBehaviour(BaseState):  # pylint: disable=too-many-ancestors
    """Estimate price."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Run the script to compute the estimate starting from the shared observations
        - Build an estimate transaction
        - Send the transaction and wait for it to be mined
        - Go to the next state.
        """
        self.context.logger.info("Entered in the 'estimate' behaviour state")
        currency_id = self.context.params.currency_id
        convert_id = self.context.params.convert_id
        observation_payloads = cast(
            PeriodState, self.context.state.period_state
        ).observations
        observations = [obs_payload.observation for obs_payload in observation_payloads]
        self.context.logger.info(
            f"Using observations {observations} to compute the estimate."
        )
        estimate = self.context.estimator.aggregate(observations)
        self.context.logger.info(
            f"Got estimate of {currency_id} price in {convert_id}: {estimate}"
        )
        payload = EstimatePayload(self.context.agent_address, estimate)
        stop_condition = self.is_round_ended(EstimateConsensusRound.round_id)
        yield from self._send_transaction(payload, stop_condition=stop_condition)
        self.context.logger.info("'estimate' behaviour state is done")
        self.set_done()


class EndBehaviour(State):
    """Final state."""

    is_programmatically_defined = True

    def is_done(self) -> bool:
        """Check if the behaviour is done."""
        return True

    def act(self) -> None:
        """Do the act."""
        final_estimate = cast(
            PeriodState, self.context.state.period_state
        ).most_voted_estimate
        self.context.logger.info(f"Consensus reached on estimate: {final_estimate}")
