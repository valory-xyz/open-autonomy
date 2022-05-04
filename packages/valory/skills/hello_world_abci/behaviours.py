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

"""This module contains the behaviours for the 'hello_world' skill."""

from abc import ABC
from math import floor
from typing import Generator, List, Set, Type, cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.hello_world_abci.models import Params, SharedState
from packages.valory.skills.hello_world_abci.payloads import (
    PrintMessagePayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.hello_world_abci.rounds import (
    HelloWorldAbciApp,
    PeriodState,
    PrintMessageRound,
    RegistrationRound,
    ResetAndPauseRound,
    SelectKeeperRound,
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


class HelloWorldABCIBaseState(BaseState, ABC):
    """Base state behaviour for the Hello World abci skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(SharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class RegistrationBehaviour(HelloWorldABCIBaseState):
    """Register to the next round."""

    state_id = "register"
    matching_round = RegistrationRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Build a registration transaction.
        - Send the transaction and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            payload = RegistrationPayload(self.context.agent_address)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class SelectKeeperBehaviour(HelloWorldABCIBaseState, ABC):
    """Select the keeper agent."""

    state_id = "select_keeper"
    matching_round = SelectKeeperRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Select a keeper randomly.
        - Send the transaction with the keeper and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            keeper_address = random_selection(
                sorted(self.period_state.participants),
                self.period_state.keeper_randomness,
            )

            self.context.logger.info(f"Selected a new keeper: {keeper_address}.")
            payload = SelectKeeperPayload(self.context.agent_address, keeper_address)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PrintMessageBehaviour(HelloWorldABCIBaseState, ABC):
    """Select the keeper agent."""

    state_id = "print_message"
    matching_round = PrintMessageRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Print message
        """

        msg = "Hello World " + str(self.period_state.period_count) + " from " + str(self.context.agent_address)
        print(msg)
        self.context.logger.info(msg)
        payload = PrintMessagePayload(self.context.agent_address, msg)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ResetAndPauseBehaviour(HelloWorldABCIBaseState):
    """Reset state."""

    matching_round = ResetAndPauseRound
    state_id = "reset_and_pause"
    pause = True

    pause = True

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
        if self.pause:
            self.context.logger.info("Period end.")
            self.context.benchmark_tool.save()
            yield from self.sleep(self.params.observation_interval)
        else:
            self.context.logger.info(
                f"Period {self.period_state.period_count} was not finished. Resetting!"
            )

        payload = ResetPayload(
            self.context.agent_address, self.period_state.period_count + 1
        )

        yield from self.send_a2a_transaction(payload)
        yield from self.wait_until_round_end()
        self.set_done()


class HelloWorldRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the simple abci app."""

    initial_state_cls = RegistrationBehaviour
    abci_app_cls = HelloWorldAbciApp  # type: ignore
    behaviour_states: Set[Type[HelloWorldABCIBaseState]] = {  # type: ignore
        RegistrationBehaviour,  # type: ignore
        SelectKeeperBehaviour,  # type: ignore
        PrintMessageBehaviour,  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }
