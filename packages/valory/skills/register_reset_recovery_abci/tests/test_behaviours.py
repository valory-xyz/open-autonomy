# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Tests for valory/register_reset_recovery skill's behaviours."""
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Type
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    BaseSynchronizedData,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.register_reset_recovery_abci.behaviours import (
    RegisterResetRecoveryAbciAppConsensusBehaviour,
    ShareRoundCountBehaviour,
)
from packages.valory.skills.register_reset_recovery_abci.rounds import Event


class BaseTerminationTest(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(__file__).parents[1]

    behaviour: RegisterResetRecoveryAbciAppConsensusBehaviour
    behaviour_class: Type[BaseBehaviour]
    synchronized_data: BaseSynchronizedData
    next_behaviour_class = ShareRoundCountBehaviour
    done_event = Event.DONE

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Fast-forward on initialization"""

        data = data if data is not None else {}
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.auto_behaviour_id(),
            BaseSynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert (
            self.behaviour.current_behaviour is not None
            and self.behaviour.current_behaviour.auto_behaviour_id()
            == self.behaviour_class.auto_behaviour_id()
        )

    def complete(self) -> None:
        """Complete test"""
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=self.done_event)
        assert (
            self.behaviour.current_behaviour is not None
            and self.behaviour.current_behaviour.auto_behaviour_id()
            == self.next_behaviour_class.auto_behaviour_id()
        )


class TestShareRoundCountBehaviour(BaseTerminationTest):
    """Tests the ShareRoundCountBehaviour."""

    behaviour_class = ShareRoundCountBehaviour

    def test_run(self) -> None:
        """Run the behaviour."""

        def mock_sleep() -> Generator:
            """Mocks BaseBehaviour.sleep()"""
            return
            yield

        self.fast_forward()
        with mock.patch.object(
            self.behaviour.current_behaviour, "sleep", side_effects=mock_sleep()
        ):
            self.behaviour.act_wrapper()
            self.complete()
