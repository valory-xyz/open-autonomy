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

"""This module contains the behaviours, round and payloads for the 'abstract_round_abci' skill."""

import hashlib
from math import floor
from typing import Dict, Generator, List, Optional, Type, Union

from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import BaseTxPayload
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.utils import BenchmarkTool, VerifyDrand


RandomnessObservation = Optional[Dict[str, Union[str, int]]]

benchmark_tool = BenchmarkTool()
drand_check = VerifyDrand()


def random_selection(elements: List[str], randomness: float) -> str:
    """
    Select a random element from a list.

    :param: elements: a list of elements to choose among
    :param: randomness: a random number in the [0,1) interval
    :return: a randomly chosen element
    """
    random_position = floor(randomness * len(elements))
    return elements[random_position]


class RandomnessBehaviour(BaseState):
    """Check whether Tendermint nodes are running."""

    payload_class: Type[BaseTxPayload]

    def failsafe_randomness(
        self,
    ) -> Generator[None, None, RandomnessObservation]:
        """
        This methods provides a failsafe for randomeness retrival.

        :return: derived randomness
        :yields: derived randomness
        """
        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,  # type: ignore
            ledger_callable="get_block",
            block_identifier="latest",
        )

        randomness = hashlib.sha256(
            ledger_api_response.state.body.get("hash").encode()
            + str(self.params.service_id).encode()
        ).hexdigest()
        return {"randomness": randomness, "round": "0"}

    def get_randomness_from_api(
        self,
    ) -> Generator[None, None, RandomnessObservation]:
        """Retrieve randomness from given api specs."""
        api_specs = self.context.randomness_api.get_spec()
        response = yield from self.get_http_response(
            method=api_specs["method"],
            url=api_specs["url"],
        )
        observation = self.context.randomness_api.process_response(response)
        if observation is not None:
            self.context.logger.info("Verifying DRAND values.")
            check, error = drand_check.verify(observation, self.params.drand_public_key)
            if check:
                self.context.logger.info("DRAND check successful.")
            else:
                self.context.logger.info(f"DRAND check failed, {error}.")
                return None
        return observation

    def async_act(self) -> Generator:
        """
        Retrieve randomness from API.

        Steps:
        - Do a http request to the API.
        - Retry until reciving valid values for randomness or retries exceed.
        - If retrieved values are valid continue else generate randomness from chain.
        """
        with benchmark_tool.measure(
            self,
        ).local():
            if self.context.randomness_api.is_retries_exceeded():
                self.context.logger.info("Cannot retrieve randomness from api.")
                self.context.logger.info("Generating randomness from chain.")
                observation = yield from self.failsafe_randomness()
            else:
                self.context.logger.info("Retrieving DRAND values from api.")
                observation = yield from self.get_randomness_from_api()
                self.context.logger.info(f"Retrieved DRAND values: {observation}.")

        if observation:
            payload = self.payload_class(  # type: ignore
                self.context.agent_address,
                round_id=observation["round"],
                randomness=observation["randomness"],
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


class SelectKeeperBehaviour(BaseState):
    """Select the keeper agent."""

    payload_class: Type[BaseTxPayload]

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
            payload = self.payload_class(self.context.agent_address, keeper_address)

        with benchmark_tool.measure(
            self,
        ).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()
