# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Tests for valory/offend_abci skill's behaviours."""

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    BaseSynchronizedData,
    OffenceStatus,
)
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.offend_abci.behaviours import OffendBehaviour
from packages.valory.skills.offend_abci.rounds import Event, FinishedOffendRound


PACKAGE_DIR = Path(__file__).parents[1]


FIRST_PARTICIPANT = "a"
OTHER_PARTICIPANTS = ("c", "b", "d")
ALL_PARTICIPANTS = OTHER_PARTICIPANTS + (FIRST_PARTICIPANT,)
LIGHT_OFFENCE_UNIT_AMOUNT = 1
SERIOUS_OFFENCE_UNIT_AMOUNT = 2
INITIAL_OFFENCE_STATUS = {
    participant: OffenceStatus() for participant in ALL_PARTICIPANTS
}


class TestOffendBehaviour(FSMBehaviourBaseCase):
    """Test the `OffendBehaviour`."""

    path_to_skill = PACKAGE_DIR
    synchronized_data: BaseSynchronizedData

    @property
    def current_behaviour(self) -> OffendBehaviour:
        """Get the current behaviour."""
        return cast(OffendBehaviour, self.behaviour.current_behaviour)

    def setup(self, **kwargs: Any) -> None:
        """
        Set up the test method.

        Called each time before a test method is called.

        :param kwargs: the keyword arguments passed to _prepare_skill
        """
        super().setup(**kwargs)
        self.synchronized_data = BaseSynchronizedData(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    {"all_participants": ALL_PARTICIPANTS}
                )
            )
        )
        self.fast_forward_to_behaviour(
            self.behaviour,
            OffendBehaviour.auto_behaviour_id(),
            self.synchronized_data,
        )
        assert self.current_behaviour is not None
        assert (
            self.current_behaviour.behaviour_id == OffendBehaviour.auto_behaviour_id()
        )

        self.current_behaviour.context.state.round_sequence.offence_status = deepcopy(
            INITIAL_OFFENCE_STATUS
        )

        self.current_behaviour.params.__dict__["_frozen"] = False
        self.current_behaviour.params.suspected = True
        self.current_behaviour.params.__dict__["_frozen"] = True

    @pytest.mark.parametrize(
        (
            "suspected",
            "validator_downtime",
            "invalid_payload",
            "blacklisted",
            "num_unknown",
            "num_double_signed",
            "num_light_client_attack",
            "expected_slash_amount",
        ),
        (
            (False, False, False, False, 0, 0, 0, 0),
            (True, False, False, False, 0, 0, 0, 1),
            (False, True, False, False, 0, 0, 0, 1),
            (False, False, True, False, 0, 0, 0, 1),
            (False, False, False, True, 0, 0, 0, 1),
            (False, False, False, False, 1, 0, 0, 2),
            (False, False, False, False, 0, 1, 0, 2),
            (False, False, False, False, 0, 0, 1, 2),
            (False, False, False, False, 0, 2, 1, 6),
            (False, True, False, True, 5, 2, 1, 18),
            (True, True, True, True, 5, 2, 1, 20),
        ),
    )
    def test_updated_status(  # pylint: disable=too-many-arguments
        self,
        suspected: bool,
        validator_downtime: bool,
        invalid_payload: bool,
        blacklisted: bool,
        num_unknown: int,
        num_double_signed: int,
        num_light_client_attack: int,
        expected_slash_amount: str,
    ) -> None:
        """Test the `_updated_status` method."""
        self.current_behaviour.params.__dict__["_frozen"] = False
        self.current_behaviour.params.suspected = suspected
        self.current_behaviour.params.validator_downtime = validator_downtime
        self.current_behaviour.params.invalid_payload = invalid_payload
        self.current_behaviour.params.blacklisted = blacklisted
        self.current_behaviour.params.num_unknown = num_unknown
        self.current_behaviour.params.num_double_signed = num_double_signed
        self.current_behaviour.params.num_light_client_attack = num_light_client_attack
        self.current_behaviour.params.__dict__["_frozen"] = True

        status = (
            self.current_behaviour._updated_status()  # pylint: disable=protected-access
        )

        actual_slash_amount = status[FIRST_PARTICIPANT].slash_amount(
            LIGHT_OFFENCE_UNIT_AMOUNT, SERIOUS_OFFENCE_UNIT_AMOUNT
        )
        assert actual_slash_amount == expected_slash_amount

        for participant in OTHER_PARTICIPANTS:
            actual_slash_amount = status[participant].slash_amount(
                LIGHT_OFFENCE_UNIT_AMOUNT, SERIOUS_OFFENCE_UNIT_AMOUNT
            )
            assert actual_slash_amount == 0

    def test_offend_act(self) -> None:
        """Test offend behaviour's `async_act` method."""
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        status = self.current_behaviour.shared_state.round_sequence.offence_status
        assert status == INITIAL_OFFENCE_STATUS
        self._test_done_flag_set()
        self.end_round(Event.DONE)
        expected_id = f"degenerate_behaviour_{FinishedOffendRound.auto_round_id()}"
        assert self.current_behaviour.behaviour_id == expected_id
