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

"""This module contains the behaviours for the 'simple_abci' skill."""

from abc import ABC
from math import floor
from typing import Generator, List, Set, Type, cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.simple_abci.models import Params, SharedState
from packages.valory.skills.simple_abci.payloads import (
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.simple_abci.rounds import (
    RandomnessStartupRound,
    RegistrationRound,
    ResetAndPauseRound,
    SelectKeeperAtStartupRound,
    SimpleAbciApp,
    SynchronizedData,
)


def random_selection(elements: List[str], randomness: float) -> str:
    """
    Select a random element from a list.

    :param: elements: a list of elements to choose among
    :param: randomness: a random number in the [0,1) interval
    :return: a randomly chosen element
    """
    random_position = floor(randomness * len(elements))
    return elements[random_position]


class SimpleABCIBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the simple abci skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(
            SynchronizedData, cast(SharedState, self.context.state).synchronized_data
        )

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class RegistrationBehaviour(SimpleABCIBaseBehaviour):
    """Register to the next round."""

    behaviour_id = "register"
    matching_round = RegistrationRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            payload = RegistrationPayload(self.context.agent_address)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class RandomnessBehaviour(SimpleABCIBaseBehaviour):
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
            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.wait_until_round_end()
            self.set_done()
            return

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            api_specs = self.context.randomness_api.get_spec()
            http_message, http_dialogue = self._build_http_request_message(
                method=api_specs["method"],
                url=api_specs["url"],
            )
            response = yield from self._do_request(http_message, http_dialogue)
            observation = self.context.randomness_api.process_response(response)

        if observation:
            self.context.logger.info(f"Retrieved DRAND values: {observation}.")
            payload = RandomnessPayload(
                self.context.agent_address,
                observation["round"],
                observation["randomness"],
            )
            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
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


class RandomnessAtStartupBehaviour(  # pylint: disable=too-many-ancestors
    RandomnessBehaviour
):
    """Retrieve randomness at startup."""

    behaviour_id = "retrieve_randomness_at_startup"
    matching_round = RandomnessStartupRound


class SelectKeeperBehaviour(SimpleABCIBaseBehaviour, ABC):
    """Select the keeper agent."""

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Select a keeper randomly.
        - Send the transaction with the keeper and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            keeper_address = random_selection(
                sorted(self.synchronized_data.participants),
                self.synchronized_data.keeper_randomness,
            )

            self.context.logger.info(f"Selected a new keeper: {keeper_address}.")
            payload = SelectKeeperPayload(self.context.agent_address, keeper_address)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SelectKeeperAtStartupBehaviour(  # pylint: disable=too-many-ancestors
    SelectKeeperBehaviour
):
    """Select the keeper agent at startup."""

    behaviour_id = "select_keeper_at_startup"
    matching_round = SelectKeeperAtStartupRound


class BaseResetBehaviour(SimpleABCIBaseBehaviour):
    """Reset behaviour."""

    pause = True

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
        if self.pause:
            self.context.logger.info("Period end.")
            self.context.benchmark_tool.save()
            yield from self.sleep(self.params.observation_interval)
        else:
            self.context.logger.info(
                f"Period {self.synchronized_data.period_count} was not finished. Resetting!"
            )

        payload = ResetPayload(
            self.context.agent_address, self.synchronized_data.period_count
        )

        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class ResetAndPauseBehaviour(BaseResetBehaviour):  # pylint: disable=too-many-ancestors
    """Reset behaviour."""

    matching_round = ResetAndPauseRound
    behaviour_id = "reset_and_pause"
    pause = True


class SimpleAbciConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the simple abci app."""

    initial_behaviour_cls = RegistrationBehaviour
    abci_app_cls = SimpleAbciApp  # type: ignore
    behaviours: Set[Type[SimpleABCIBaseBehaviour]] = {  # type: ignore
        RegistrationBehaviour,  # type: ignore
        RandomnessAtStartupBehaviour,  # type: ignore
        SelectKeeperAtStartupBehaviour,  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }
