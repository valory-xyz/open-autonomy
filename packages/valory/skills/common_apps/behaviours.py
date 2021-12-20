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
import json
from abc import ABC
from typing import Generator, Optional, cast

from packages.valory.skills.abstract_round_abci.behaviours import BaseState
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool, VerifyDrand
from packages.valory.skills.common_apps.models import Params
from packages.valory.skills.common_apps.payloads import (
    RandomnessPayload,
    RegistrationPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.common_apps.rounds import (
    PeriodState,
    RandomnessAStartupRound,
    RandomnessBStartupRound,
    RandomnessRound,
    RegistrationRound,
    RegistrationStartupRound,
    SelectKeeperARound,
    SelectKeeperAStartupRound,
    SelectKeeperBRound,
    SelectKeeperBStartupRound,
)
from packages.valory.skills.price_estimation_abci.tools import random_selection


benchmark_tool = BenchmarkTool()
drand_check = VerifyDrand()


class CommonAppsBaseState(BaseState, ABC):
    """Base state behaviour for the common apps skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(BaseSharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class TendermintHealthcheckBehaviour(CommonAppsBaseState):
    """Check whether Tendermint nodes are running."""

    state_id = "tendermint_healthcheck"
    matching_round = None

    _check_started: Optional[datetime.datetime] = None
    _timeout: float
    _is_healthy: bool

    def start(self) -> None:
        """Set up the behaviour."""
        if self._check_started is None:
            self._check_started = datetime.datetime.now()
            self._timeout = self.params.max_healthcheck
            self._is_healthy = False

    def _is_timeout_expired(self) -> bool:
        """Check if the timeout expired."""
        if self._check_started is None or self._is_healthy:
            return False  # pragma: no cover
        return datetime.datetime.now() > self._check_started + datetime.timedelta(
            0, self._timeout
        )

    def async_act(self) -> Generator:
        """Do the action."""

        self.start()
        if self._is_timeout_expired():
            # if the Tendermint node cannot update the app then the app cannot work
            raise RuntimeError("Tendermint node did not come live!")
        if not self._is_healthy:
            health = yield from self._get_health()
            try:
                json_body = json.loads(health.body.decode())
            except json.JSONDecodeError:
                self.context.logger.error("Tendermint not running yet, trying again!")
                yield from self.sleep(self.params.sleep_time)
                return
            self._is_healthy = True
        status = yield from self._get_status()
        try:
            json_body = json.loads(status.body.decode())
        except json.JSONDecodeError:
            self.context.logger.error(
                "Tendermint not accepting transactions yet, trying again!"
            )
            yield from self.sleep(self.params.sleep_time)
            return

        remote_height = int(json_body["result"]["sync_info"]["latest_block_height"])
        local_height = self.context.state.period.height
        self.context.logger.info(
            "local-height = %s, remote-height=%s", local_height, remote_height
        )
        if local_height != remote_height:
            self.context.logger.info("local height != remote height; retrying...")
            yield from self.sleep(self.params.sleep_time)
            return
        self.context.logger.info("local height == remote height; done")
        self.set_done()


class RegistrationBaseBehaviour(CommonAppsBaseState):
    """Register to the next periods."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            payload = RegistrationPayload(self.context.agent_address)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class RegistrationStartupBehaviour(RegistrationBaseBehaviour):
    """Register to the next periods."""

    state_id = "register_startup"
    matching_round = RegistrationStartupRound


class RegistrationBehaviour(RegistrationBaseBehaviour):
    """Register to the next periods."""

    state_id = "register"
    matching_round = RegistrationRound


class RandomnessBehaviour(CommonAppsBaseState):
    """Check whether Tendermint nodes are running."""

    def async_act(self) -> Generator:
        """
        Check whether tendermint is running or not.

        Steps:
        - Do a http request to the tendermint health check endpoint
        - Retry until healthcheck passes or timeout is hit.
        - If healthcheck passes set done event.
        """
        if self.context.randomness_api.is_retries_exceeded():
            # now we need to wait and see if the other agents progress the round
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        with benchmark_tool.measure(
            self,
        ).local():
            api_specs = self.context.randomness_api.get_spec()
            response = yield from self.get_http_response(
                method=api_specs["method"],
                url=api_specs["url"],
            )
            observation = self.context.randomness_api.process_response(response)

        if observation:
            self.context.logger.info(f"Retrieved DRAND values: {observation}.")
            self.context.logger.info("Verifying DRAND values.")
            check, error = drand_check.verify(observation, self.params.drand_public_key)
            if check:
                self.context.logger.info("DRAND check successful.")
            else:
                self.context.logger.info(f"DRAND check failed, {error}.")
                observation["randomness"] = ""
                observation["round"] = ""

            payload = RandomnessPayload(
                self.context.agent_address,
                observation["round"],
                observation["randomness"],
            )
            with benchmark_tool.measure(
                self,
            ).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()
        else:
            self.context.logger.error(
                f"Could not get randomness from {self.context.randomness_api.api_id}"
            )
            yield from self.sleep(self.params.sleep_time)
            self.context.randomness_api.increment_retries()

    def clean_up(self) -> None:
        """
        Clean up the resources due to a 'stop' event.

        It can be optionally implemented by the concrete classes.
        """
        self.context.randomness_api.reset_retries()


class RandomnessAtStartupABehaviour(RandomnessBehaviour):
    """Retrive randomness at startup."""

    state_id = "retrieve_randomness_at_startup_a"
    matching_round = RandomnessAStartupRound


class RandomnessAtStartupBBehaviour(RandomnessBehaviour):
    """Retrive randomness at startup."""

    state_id = "retrieve_randomness_at_startup_b"
    matching_round = RandomnessBStartupRound


class RandomnessInOperationBehaviour(RandomnessBehaviour):
    """Retrive randomness during operation."""

    state_id = "retrieve_randomness"
    matching_round = RandomnessRound


class SelectKeeperBehaviour(CommonAppsBaseState, ABC):
    """Select the keeper agent."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Select a keeper randomly.
        - Send the transaction with the keeper and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with benchmark_tool.measure(
            self,
        ).local():
            if (
                self.period_state.is_keeper_set
                and len(self.period_state.participants) > 1
            ):
                # if a keeper is already set we remove it from the potential selection.
                potential_keepers = list(self.period_state.participants)
                potential_keepers.remove(self.period_state.most_voted_keeper_address)
                relevant_set = sorted(potential_keepers)
            else:
                relevant_set = sorted(self.period_state.participants)
            keeper_address = random_selection(
                relevant_set,
                self.period_state.keeper_randomness,
            )

            self.context.logger.info(f"Selected a new keeper: {keeper_address}.")
            payload = SelectKeeperPayload(self.context.agent_address, keeper_address)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SelectKeeperAAtStartupBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent at startup."""

    state_id = "select_keeper_a_at_startup"
    matching_round = SelectKeeperAStartupRound


class SelectKeeperBAtStartupBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent at startup."""

    state_id = "select_keeper_b_at_startup"
    matching_round = SelectKeeperBStartupRound


class SelectKeeperABehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_a"
    matching_round = SelectKeeperARound


class SelectKeeperBBehaviour(SelectKeeperBehaviour):
    """Select the keeper agent."""

    state_id = "select_keeper_b"
    matching_round = SelectKeeperBRound
