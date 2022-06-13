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

"""Tests for valory/registration_abci skill's behaviours."""
from pathlib import Path
from typing import Dict, Optional
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseBehaviour,
    make_degenerate_behaviour,
)
from packages.valory.skills.registration_abci.behaviours import (
    RegistrationBaseBehaviour,
    RegistrationBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.registration_abci.rounds import (
    BaseSynchronizedData as RegistrationSynchronizedData,
)
from packages.valory.skills.registration_abci.rounds import (
    Event,
    FinishedRegistrationFFWRound,
    FinishedRegistrationRound,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase


class RegistrationAbciBaseCase(FSMBehaviourBaseCase):
    """Base case for testing RegistrationAbci FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "registration_abci")


class BaseRegistrationTestBehaviour(RegistrationAbciBaseCase):
    """Base test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBaseBehaviour
    next_behaviour_class = BaseBehaviour

    @pytest.mark.parametrize(
        "setup_data, expected_initialisation",
        (
            ({}, None),
            ({"test": []}, None),
            ({"test": [], "valid": [1, 2]}, '{"valid": [1, 2]}'),
        ),
    )
    def test_registration(
        self, setup_data: Dict, expected_initialisation: Optional[str]
    ) -> None:
        """Test registration."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            RegistrationSynchronizedData(AbciAppDB(setup_data=setup_data)),
        )
        assert isinstance(self.behaviour.current_behaviour, BaseBehaviour)
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == self.behaviour_class.behaviour_id
        )
        with mock.patch.object(
            self.behaviour.current_behaviour,
            "send_a2a_transaction",
            side_effect=self.behaviour.current_behaviour.send_a2a_transaction,
        ):
            self.behaviour.act_wrapper()
            assert isinstance(
                self.behaviour.current_behaviour.send_a2a_transaction, MagicMock
            )
            assert (
                self.behaviour.current_behaviour.send_a2a_transaction.call_args[0][
                    0
                ].initialisation
                == expected_initialisation
            )
            self.mock_a2a_transaction()

        self._test_done_flag_set()
        self.end_round(Event.DONE)
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == self.next_behaviour_class.behaviour_id
        )


class TestRegistrationStartupBehaviour(BaseRegistrationTestBehaviour):
    """Test case to test RegistrationStartupBehaviour."""

    behaviour_class = RegistrationStartupBehaviour
    next_behaviour_class = make_degenerate_behaviour(FinishedRegistrationRound.round_id)


class TestRegistrationBehaviour(BaseRegistrationTestBehaviour):
    """Test case to test RegistrationBehaviour."""

    behaviour_class = RegistrationBehaviour
    next_behaviour_class = make_degenerate_behaviour(
        FinishedRegistrationFFWRound.round_id
    )
