# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""Tests for valory/hello_world_abci skill's behaviours."""

# pylint: skip-file

import json
import time
from pathlib import Path
from typing import Any, Type, cast
from unittest import mock

from aea.skills.base import SkillContext

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.hello_world_abci import PUBLIC_ID
from packages.valory.skills.hello_world_abci.behaviours import (
    CollectRandomnessBehaviour,
    PrintMessageBehaviour,
    RegistrationBehaviour,
    ResetAndPauseBehaviour,
    SelectKeeperBehaviour,
)
from packages.valory.skills.hello_world_abci.rounds import Event, SynchronizedData


PACKAGE_DIR = Path(__file__).parent.parent


def test_skill_public_id() -> None:
    """Test skill module public ID"""

    assert PUBLIC_ID.name == Path(__file__).parents[1].name
    assert PUBLIC_ID.author == Path(__file__).parents[3].name


class HelloWorldAbciFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = PACKAGE_DIR

    def setup(self, **kwargs: Any) -> None:
        """
        Set up the test method.

        Called each time before a test method is called.

        :param kwargs: the keyword arguments passed to _prepare_skill
        """
        super().setup(**kwargs)
        self.synchronized_data = SynchronizedData(
            AbciAppDB(
                setup_data=dict(
                    most_voted_keeper_address=["most_voted_keeper_address"],
                ),
            )
        )

    def end_round(  # type: ignore
        self,
    ) -> None:
        """Ends round early to cover `wait_for_end` generator."""
        super().end_round(Event.DONE)


class BaseCollectRandomnessBehaviourTest(HelloWorldAbciFSMBehaviourBaseCase):
    """Test CollectRandomnessBehaviour."""

    collect_randomness_behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[BaseBehaviour]

    def test_randomness_behaviour(
        self,
    ) -> None:
        """Test RandomnessBehaviour."""

        self.fast_forward_to_behaviour(
            self.behaviour,
            self.collect_randomness_behaviour_class.auto_behaviour_id(),
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.collect_randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps(
                    {
                        "round": 1283255,
                        "randomness": "04d4866c26e03347d2431caa82ab2d7b7bdbec8b58bca9460c96f5265d878feb",
                    }
                ).encode("utf-8"),
            ),
        )

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.auto_behaviour_id()

    def test_invalid_response(
        self,
    ) -> None:
        """Test invalid json response."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.collect_randomness_behaviour_class.auto_behaviour_id(),
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.collect_randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()

        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="", status_code=200, status_text="", headers="", body=b""
            ),
        )
        self.behaviour.act_wrapper()
        time.sleep(1)
        self.behaviour.act_wrapper()

    def test_max_retries_reached(
        self,
    ) -> None:
        """Test with max retries reached."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.collect_randomness_behaviour_class.auto_behaviour_id(),
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.collect_randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.context.randomness_api.__dict__["_frozen"] = False
        with mock.patch.object(
            self.behaviour.context.randomness_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.behaviour.act_wrapper()
            behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
            assert (
                behaviour.behaviour_id
                == self.collect_randomness_behaviour_class.auto_behaviour_id()
            )
            self._test_done_flag_set()
        self.behaviour.context.randomness_api.__dict__["_frozen"] = True

    def test_clean_up(
        self,
    ) -> None:
        """Test when `observed` value is none."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.collect_randomness_behaviour_class.auto_behaviour_id(),
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.collect_randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.context.randomness_api.retries_info.retries_attempted = 1
        assert self.behaviour.current_behaviour is not None
        self.behaviour.current_behaviour.clean_up()
        assert self.behaviour.context.randomness_api.retries_info.retries_attempted == 0


class BaseSelectKeeperBehaviourTest(HelloWorldAbciFSMBehaviourBaseCase):
    """Test SelectKeeperBehaviour."""

    select_keeper_behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[BaseBehaviour]

    def test_select_keeper(
        self,
    ) -> None:
        """Test select keeper agent."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.select_keeper_behaviour_class.auto_behaviour_id(),
            synchronized_data=SynchronizedData(
                AbciAppDB(
                    setup_data=dict(
                        participants=[participants],
                        most_voted_randomness=[
                            "56cbde9e9bbcbdcaf92f183c678eaa5288581f06b1c9c7f884ce911776727688"
                        ],
                        most_voted_keeper_address=["most_voted_keeper_address"],
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.select_keeper_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.auto_behaviour_id()


class TestRegistrationBehaviour(HelloWorldAbciFSMBehaviourBaseCase):
    """Test case to test RegistrationBehaviour."""

    def test_registration(self) -> None:
        """Test registration."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            RegistrationBehaviour.auto_behaviour_id(),
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == RegistrationBehaviour.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round()
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == CollectRandomnessBehaviour.auto_behaviour_id()


class TestCollectRandomnessBehaviour(BaseCollectRandomnessBehaviourTest):
    """Test CollectRandomnessBehaviour."""

    collect_randomness_behaviour_class = CollectRandomnessBehaviour
    next_behaviour_class = SelectKeeperBehaviour


class TestSelectKeeperBehaviour(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    select_keeper_behaviour_class = SelectKeeperBehaviour
    next_behaviour_class = PrintMessageBehaviour


class TestPrintMessageBehaviour(HelloWorldAbciFSMBehaviourBaseCase):
    """Test case to test PrintMessageBehaviour."""

    def test_print_message_non_keeper(self) -> None:
        """Test print_message."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            PrintMessageBehaviour.auto_behaviour_id(),
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == PrintMessageBehaviour.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round()
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == ResetAndPauseBehaviour.auto_behaviour_id()

    @mock.patch.object(SkillContext, "agent_address", new_callable=mock.PropertyMock)
    def test_print_message_keeper(
        self,
        agent_address_mock: mock.PropertyMock,
    ) -> None:
        """Test print_message."""
        agent_address_mock.return_value = "most_voted_keeper_address"
        self.fast_forward_to_behaviour(
            self.behaviour,
            PrintMessageBehaviour.auto_behaviour_id(),
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == PrintMessageBehaviour.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round()
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == ResetAndPauseBehaviour.auto_behaviour_id()


class TestResetAndPauseBehaviour(HelloWorldAbciFSMBehaviourBaseCase):
    """Test ResetBehaviour."""

    behaviour_class = ResetAndPauseBehaviour
    next_behaviour_class = CollectRandomnessBehaviour

    def test_pause_and_reset_behaviour(
        self,
    ) -> None:
        """Test pause and reset behaviour."""
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.behaviour_class.auto_behaviour_id(),
            synchronized_data=self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.behaviour_class.auto_behaviour_id()
        )
        self.behaviour.context.params.__dict__["observation_interval"] = 0.1
        self.behaviour.act_wrapper()
        time.sleep(0.3)
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.auto_behaviour_id()

    def test_reset_behaviour(
        self,
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.behaviour_class.auto_behaviour_id(),
            synchronized_data=self.synchronized_data,
        )
        assert self.behaviour.current_behaviour is not None
        self.behaviour.current_behaviour.pause = False
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.behaviour_class.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.auto_behaviour_id()
