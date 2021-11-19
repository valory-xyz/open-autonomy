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

"""This module contains the behaviours for the APY estimation skill."""
from typing import Generator, Set, Type

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool
from packages.valory.skills.apy_estimation.rounds import (
    APYEstimationAbciApp,
    CollectObservationRound,
    TransformRound,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    RandomnessInOperationBehaviour,
    ResetBehaviour,
    SelectKeeperABehaviour,
)
from packages.valory.skills.price_estimation_abci.payloads import EstimatePayload
from packages.valory.skills.price_estimation_abci.rounds import EstimateConsensusRound
from packages.valory.skills.simple_abci.behaviours import (
    RegistrationBehaviour,
    ResetAndPauseBehaviour,
    TendermintHealthcheckBehaviour,
)


benchmark_tool = BenchmarkTool()


class ObserveBehaviour(BaseState):
    """Observe historical data."""

    state_id = "observe"
    matching_round = CollectObservationRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Ask the configured API the historical data until now, for the configured duration.
        - If the request fails, retry until max retries are exceeded.
        - Send an observation transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """
        raise NotImplementedError()


class TransformBehaviour(BaseState):
    """Transform historical data, i.e., convert them to a dataframe and calculate useful metrics, such as the APY."""

    state_id = "transform"
    matching_round = TransformRound

    def async_act(self) -> Generator:
        """Do the action."""
        raise NotImplementedError()


class EstimateBehaviour(BaseState):
    """Estimate APY."""

    state_id = "estimate"
    matching_round = EstimateConsensusRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Run the script to compute the estimate starting from the shared observations.
        - Build an estimate transaction and send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(self).local():
            self.context.logger.info(
                "Got estimate of APY for %s: %s",
                # TODO pool_name param,
                self.context.state.period_state.estimate,
            )
            payload = EstimatePayload(
                self.context.agent_address, self.context.state.period_state.estimate
            )

        with benchmark_tool.measure(self).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class APYEstimationConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the APY estimation."""

    initial_state_cls = TendermintHealthcheckBehaviour
    abci_app_cls = APYEstimationAbciApp
    behaviour_states: Set[Type[BaseState]] = {
        TendermintHealthcheckBehaviour,
        RegistrationBehaviour,
        RandomnessInOperationBehaviour,
        SelectKeeperABehaviour,
        ObserveBehaviour,
        TransformBehaviour,
        EstimateBehaviour,
        ResetBehaviour,
        ResetAndPauseBehaviour,
    }

    def setup(self) -> None:
        """Set up the behaviour."""
        super().setup()
        benchmark_tool.logger = self.context.logger
