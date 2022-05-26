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
from typing import Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
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
    PrintMessageRound,
    RegistrationRound,
    ResetAndPauseRound,
    SelectKeeperRound,
    SynchronizedData,
)


class HelloWorldABCIBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour behaviour for the Hello World abci skill."""

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


class RegistrationBehaviour(HelloWorldABCIBaseBehaviour):
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


class SelectKeeperBehaviour(HelloWorldABCIBaseBehaviour, ABC):
    """Select the keeper agent."""

    behaviour_id = "select_keeper"
    matching_round = SelectKeeperRound

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
            keeper_address = sorted(self.synchronized_data.participants)[
                self.synchronized_data.period_count
                % self.synchronized_data.nb_participants
            ]

            self.context.logger.info(f"Selected a new keeper: {keeper_address}.")
            payload = SelectKeeperPayload(self.context.agent_address, keeper_address)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PrintMessageBehaviour(HelloWorldABCIBaseBehaviour, ABC):
    """Prints the celebrated 'HELLO WORLD!' message."""

    behaviour_id = "print_message"
    matching_round = PrintMessageRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Determine if this agent is the current keeper agent.
        - Print the appropriate to the local console.
        - Send the transaction with the printed message and wait for it to be mined.
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour (set done event).
        """

        printed_message = f"Agent {self.context.agent_name} (address {self.context.agent_address}) in period {self.synchronized_data.period_count} says: "
        if (
            self.context.agent_address
            == self.synchronized_data.most_voted_keeper_address
        ):
            printed_message += "HELLO WORLD!"
        else:
            printed_message += ":|"

        print(printed_message)
        self.context.logger.info(f"printed_message={printed_message}")

        payload = PrintMessagePayload(self.context.agent_address, printed_message)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ResetAndPauseBehaviour(HelloWorldABCIBaseBehaviour):
    """Reset behaviour."""

    matching_round = ResetAndPauseRound
    behaviour_id = "reset_and_pause"
    pause = True

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


class HelloWorldRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the Hello World abci app."""

    initial_behaviour_cls = RegistrationBehaviour
    abci_app_cls = HelloWorldAbciApp  # type: ignore
    behaviours: Set[Type[HelloWorldABCIBaseBehaviour]] = {  # type: ignore
        RegistrationBehaviour,  # type: ignore
        SelectKeeperBehaviour,  # type: ignore
        PrintMessageBehaviour,  # type: ignore
        ResetAndPauseBehaviour,  # type: ignore
    }
