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

"""This module contains the behaviours for the 'abstract_round_abci' skill."""
from typing import List, Type

from aea.exceptions import enforce
from aea.skills.behaviours import FSMBehaviour

from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    DONE_EVENT,
)


class AbstractRoundBehaviour(FSMBehaviour):
    """This behaviour implements an abstract round."""

    all_ordered_states: List[Type[BaseState]] = []

    def setup(self) -> None:
        """Set up the behaviour."""
        self._register_states(self.all_ordered_states)

    def teardown(self) -> None:
        """Tear down the behaviour"""

    def _register_states(self, state_classes: List[Type[BaseState]]) -> None:
        """Register a list of states."""
        enforce(
            len(state_classes) != 0,
            "empty list of state classes",
            exception_class=ValueError,
        )
        self._register_state(state_classes[0], initial=True)
        for state_cls in state_classes[1:]:
            self._register_state(state_cls)

        for index in range(len(state_classes) - 1):
            before, after = state_classes[index], state_classes[index + 1]
            self.register_transition(before.state_id, after.state_id, DONE_EVENT)

    def _register_state(
        self, state_cls: Type[BaseState], initial: bool = False
    ) -> None:
        """Register state."""
        name = state_cls.state_id
        return super().register_state(
            name,
            state_cls(name=name, skill_context=self.context),
            initial=initial,
        )
