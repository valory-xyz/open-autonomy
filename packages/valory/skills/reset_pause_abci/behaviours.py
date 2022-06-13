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

"""This module contains the behaviours for the 'reset_pause_abci' skill."""

from abc import ABC
from typing import Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import BaseSynchronizedData
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.reset_pause_abci.models import Params, SharedState
from packages.valory.skills.reset_pause_abci.payloads import ResetPausePayload
from packages.valory.skills.reset_pause_abci.rounds import (
    ResetAndPauseRound,
    ResetPauseABCIApp,
)


class ResetAndPauseBaseBehaviour(BaseBehaviour, ABC):
    """Reset behaviour."""

    @property
    def synchronized_data(self) -> BaseSynchronizedData:
        """Return the synchronized data."""
        return cast(
            BaseSynchronizedData,
            cast(SharedState, self.context.state).synchronized_data,
        )

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class ResetAndPauseBehaviour(ResetAndPauseBaseBehaviour):
    """Reset and pause behaviour."""

    matching_round = ResetAndPauseRound
    behaviour_id = "reset_and_pause"

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Trivially log the behaviour.
        - Sleep for configured interval.
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """
        # + 1 because `period_count` starts from 0
        n_periods_done = self.synchronized_data.period_count + 1
        reset_tm_nodes = n_periods_done % self.params.reset_tendermint_after == 0
        if reset_tm_nodes:
            tendermint_reset = yield from self.reset_tendermint_with_wait()
            if not tendermint_reset:
                return
        else:
            yield from self.wait_from_last_timestamp(self.params.observation_interval)
        self.context.logger.info("Period end.")
        self.context.benchmark_tool.save(self.synchronized_data.period_count)

        payload = ResetPausePayload(
            self.context.agent_address, self.synchronized_data.period_count
        )
        yield from self.send_a2a_transaction(payload, reset_tm_nodes)
        yield from self.wait_until_round_end()
        self.set_done()


class ResetPauseABCIConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the reset_pause_abci app."""

    initial_behaviour_cls = ResetAndPauseBehaviour
    abci_app_cls = ResetPauseABCIApp  # type: ignore
    behaviours: Set[Type[ResetAndPauseBehaviour]] = {  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }
