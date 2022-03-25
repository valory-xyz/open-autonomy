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

import datetime
import json
from abc import ABC
from typing import Generator, Optional, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import BasePeriodState
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.reset_pause_abci.models import Params, SharedState
from packages.valory.skills.reset_pause_abci.payloads import ResetPausePayload
from packages.valory.skills.reset_pause_abci.rounds import (
    ResetAndPauseRound,
    ResetPauseABCIApp,
)


class ResetAndPauseBaseState(BaseState, ABC):
    """Reset state."""

    @property
    def period_state(self) -> BasePeriodState:
        """Return the period state."""
        return cast(BasePeriodState, cast(SharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class ResetAndPauseBehaviour(ResetAndPauseBaseState):
    """Reset and pause state."""

    matching_round = ResetAndPauseRound
    state_id = "reset_and_pause"

    _check_started: Optional[datetime.datetime] = None
    _timeout: float
    _is_healthy: bool = False

    def start_reset(self) -> Generator:
        """Start tendermint reset."""
        if self._check_started is None and not self._is_healthy:
            # we do the reset in the middle of the pause as there are no immediate transactions on either side of the reset
            yield from self.wait_from_last_timestamp(
                self.params.observation_interval / 2
            )
            self._check_started = datetime.datetime.now()
            self._timeout = self.params.max_healthcheck
            self._is_healthy = False
        yield

    def end_reset(
        self,
    ) -> None:
        """End tendermint reset."""
        self._check_started = None
        self._timeout = -1.0
        self._is_healthy = True

    def _is_timeout_expired(self) -> bool:
        """Check if the timeout expired."""
        if self._check_started is None or self._is_healthy:
            return False  # pragma: no cover
        return datetime.datetime.now() > self._check_started + datetime.timedelta(
            0, self._timeout
        )

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Trivially log the state.
        - Sleep for configured interval.
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        if (
            self.period_state.period_count != 0
            and self.period_state.period_count % self.params.reset_tendermint_after == 0
        ):
            yield from self.start_reset()
            if self._is_timeout_expired():
                # if the Tendermint node cannot update the app then the app cannot work
                raise RuntimeError(  # pragma: no cover
                    "Error resetting tendermint node."
                )

            if not self._is_healthy:
                self.context.logger.info(
                    f"Resetting tendermint node at end of period={self.period_state.period_count}."
                )
                request_message, http_dialogue = self._build_http_request_message(
                    "GET",
                    self.params.tendermint_com_url + "/hard_reset",
                )
                result = yield from self._do_request(request_message, http_dialogue)
                try:
                    response = json.loads(result.body.decode())
                    if response.get("status"):
                        self.context.logger.info(response.get("message"))
                        self.context.logger.info(
                            "Resetting tendermint node successful! Resetting local blockchain."
                        )
                        self.context.state.period.reset_blockchain(
                            response.get("is_replay", False)
                        )
                        self.context.state.period.abci_app.cleanup(
                            self.params.cleanup_history_depth
                        )
                        self.end_reset()
                    else:
                        msg = response.get("message")
                        self.context.logger.error(f"Error resetting: {msg}")
                        yield from self.sleep(self.params.sleep_time)
                        return  # pragma: no cover
                except json.JSONDecodeError:
                    self.context.logger.error(
                        "Error communicating with tendermint com server."
                    )
                    yield from self.sleep(self.params.sleep_time)
                    return  # pragma: no cover

            status = yield from self._get_status()
            try:
                json_body = json.loads(status.body.decode())
            except json.JSONDecodeError:
                self.context.logger.error(
                    "Tendermint not accepting transactions yet, trying again!"
                )
                yield from self.sleep(self.params.sleep_time)
                return  # pragma: nocover

            remote_height = int(json_body["result"]["sync_info"]["latest_block_height"])
            local_height = self.context.state.period.height
            self.context.logger.info(
                "local-height = %s, remote-height=%s", local_height, remote_height
            )
            if local_height != remote_height:
                self.context.logger.info("local height != remote height; retrying...")
                yield from self.sleep(self.params.sleep_time)
                return  # pragma: nocover

            self.context.logger.info(
                "local height == remote height; continuing execution..."
            )
        yield from self.wait_from_last_timestamp(self.params.observation_interval / 2)
        self.context.logger.info("Period end.")
        self.context.benchmark_tool.save(self.period_state.period_count)

        payload = ResetPausePayload(
            self.context.agent_address, self.period_state.period_count + 1
        )
        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class ResetPauseABCIConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the reset_pause_abci app."""

    initial_state_cls = ResetAndPauseBehaviour
    abci_app_cls = ResetPauseABCIApp  # type: ignore
    behaviour_states: Set[Type[ResetAndPauseBehaviour]] = {  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }
