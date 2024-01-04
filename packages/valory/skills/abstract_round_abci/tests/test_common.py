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

"""Test the common.py module of the skill."""

import random
import re
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Generator,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.common import (
    RandomnessBehaviour,
    SelectKeeperBehaviour,
    random_selection,
)
from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.tests.conftest import irrelevant_config
from packages.valory.skills.abstract_round_abci.utils import VerifyDrand


ReturnValueType = TypeVar("ReturnValueType")


def test_random_selection() -> None:
    """Test 'random_selection'"""
    assert random_selection(elements=[0, 1, 2], randomness=0.25) == 0
    assert random_selection(elements=[0, 1, 2], randomness=0.5) == 1
    assert random_selection(elements=[0, 1, 2], randomness=0.75) == 2

    with pytest.raises(
        ValueError, match=re.escape("Randomness should lie in the [0,1) interval")
    ):
        random_selection(elements=[0, 1], randomness=-1)

    with pytest.raises(
        ValueError, match=re.escape("Randomness should lie in the [0,1) interval")
    ):
        random_selection(elements=[0, 1], randomness=1)

    with pytest.raises(
        ValueError, match=re.escape("Randomness should lie in the [0,1) interval")
    ):
        random_selection(elements=[0, 1], randomness=2)

    with pytest.raises(ValueError, match="No elements to randomly select among"):
        random_selection(elements=[], randomness=0.5)


class DummyRandomnessBehaviour(RandomnessBehaviour):
    """Dummy randomness behaviour."""

    behaviour_id = "dummy_randomness"
    payload_class = MagicMock()
    matching_round = MagicMock()


class DummySelectKeeperBehaviour(SelectKeeperBehaviour):
    """Dummy select keeper behaviour."""

    behaviour_id = "dummy_select_keeper"
    payload_class = MagicMock()
    matching_round = MagicMock()


DummyBehaviourType = Union[DummyRandomnessBehaviour, DummySelectKeeperBehaviour]


class BaseDummyBehaviour:  # pylint: disable=too-few-public-methods
    """A Base dummy behaviour class."""

    behaviour: DummyBehaviourType
    dummy_behaviour_cls: Type[DummyBehaviourType]

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test class."""
        cls.behaviour = cls.dummy_behaviour_cls(
            name="test",
            skill_context=MagicMock(
                params=BaseParams(
                    name="test",
                    skill_context=MagicMock(),
                    service_id="test_id",
                    consensus=dict(max_participants=1),
                    **irrelevant_config,
                ),
            ),
        )


def dummy_generator(
    return_value: ReturnValueType,
) -> Callable[[Any, Any], Generator[None, None, ReturnValueType]]:
    """A method that returns a dummy generator which yields nothing once and then returns the given `return_value`."""

    def dummy_generator_wrapped(
        *_: Any, **__: Any
    ) -> Generator[None, None, ReturnValueType]:
        """A wrapped method which yields nothing once and then returns the given `return_value`."""
        yield
        return return_value

    return dummy_generator_wrapped


def last_iteration(gen: Generator) -> None:
    """Perform a generator iteration and ensure that it is the last one."""
    with pytest.raises(StopIteration):
        next(gen)


class TestRandomnessBehaviour(BaseDummyBehaviour):
    """Test `RandomnessBehaviour`."""

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test class."""
        cls.dummy_behaviour_cls = DummyRandomnessBehaviour
        super().setup_class()

    @pytest.mark.parametrize(
        "return_value, expected_hash",
        (
            (MagicMock(performative=LedgerApiMessage.Performative.ERROR), None),
            (MagicMock(state=MagicMock(body={"hash_key_is_not_in_body": ""})), None),
            (
                MagicMock(state=MagicMock(body={"hash": "test_randomness"})),
                {
                    "randomness": "d067b86fa5235e7e5225e8328e8faac5c279cbf57131d647e4da0a70df6d3d7b",
                    "round": 0,
                },
            ),
        ),
    )
    def test_failsafe_randomness(
        self, return_value: MagicMock, expected_hash: Optional[str]
    ) -> None:
        """Test `failsafe_randomness`."""
        gen = self.behaviour.failsafe_randomness()

        with mock.patch.object(
            DummyRandomnessBehaviour,
            "get_ledger_api_response",
            dummy_generator(return_value),
        ):
            next(gen)
            try:
                next(gen)
            except StopIteration as e:
                assert e.value == expected_hash
            else:
                raise AssertionError(
                    "`get_ledger_api_response`'s generator should have been exhausted."
                )

    @pytest.mark.parametrize("randomness_response", ("test", None))
    @pytest.mark.parametrize("verified", (True, False))
    def test_get_randomness_from_api(
        self, randomness_response: Optional[str], verified: bool
    ) -> None:
        """Test `get_randomness_from_api`."""
        # create a dummy `process_response` for `MagicMock`ed `randomness_api`
        self.behaviour.context.randomness_api.process_response = (
            lambda res: res + "_processed" if res is not None else None
        )
        gen = self.behaviour.get_randomness_from_api()

        with mock.patch.object(
            DummyRandomnessBehaviour,
            "get_http_response",
            dummy_generator(randomness_response),
        ), mock.patch.object(
            VerifyDrand,
            "verify",
            return_value=(verified, "Error message."),
        ):
            next(gen)
            try:
                next(gen)
            except StopIteration as e:
                if randomness_response is None or not verified:
                    assert e.value is None
                else:
                    assert e.value == randomness_response + "_processed"
            else:
                raise AssertionError(
                    "`get_randomness_from_api`'s generator should have been exhausted."
                )

    @pytest.mark.parametrize(
        "retries_exceeded, failsafe_succeeds",
        # (False, False) is not tested, because it does not make sense
        ((True, False), (True, True), (False, True)),
    )
    @pytest.mark.parametrize(
        "observation",
        (
            None,
            {},
            {
                "randomness": "d067b86fa5235e7e5225e8328e8faac5c279cbf57131d647e4da0a70df6d3d7b",
                "round": 0,
            },
        ),
    )
    def test_async_act(
        self,
        retries_exceeded: bool,
        failsafe_succeeds: bool,
        observation: Optional[Dict[str, Union[str, int]]],
    ) -> None:
        """Test `async_act`."""
        # create a dummy `is_retries_exceeded` for `MagicMock`ed `randomness_api`
        self.behaviour.context.randomness_api.is_retries_exceeded = (
            lambda: retries_exceeded
        )
        gen = self.behaviour.async_act()

        with mock.patch.object(
            self.behaviour,
            "failsafe_randomness",
            dummy_generator(observation),
        ), mock.patch.object(
            self.behaviour,
            "get_randomness_from_api",
            dummy_generator(observation),
        ), mock.patch.object(
            self.behaviour,
            "send_a2a_transaction",
        ) as send_a2a_transaction_mocked, mock.patch.object(
            self.behaviour,
            "wait_until_round_end",
        ) as wait_until_round_end_mocked, mock.patch.object(
            self.behaviour,
            "set_done",
        ) as set_done_mocked, mock.patch.object(
            self.behaviour,
            "sleep",
        ) as sleep_mocked:
            next(gen)
            last_iteration(gen)

            if not failsafe_succeeds or failsafe_succeeds and observation is None:
                return

            # here, the observation is retrieved from either `failsafe_randomness` or `get_randomness_from_api`
            # depending on the test's parametrization
            if not observation:
                sleep_mocked.assert_called_once_with(
                    self.behaviour.context.randomness_api.retries_info.suggested_sleep_time
                )
                self.behaviour.context.randomness_api.increment_retries.assert_called_once()
                return

            send_a2a_transaction_mocked.assert_called_once()
            wait_until_round_end_mocked.assert_called_once()
            set_done_mocked.assert_called_once()

    def test_clean_up(self) -> None:
        """Test `clean_up`."""
        self.behaviour.clean_up()
        self.behaviour.context.randomness_api.reset_retries.assert_called_once()

    def teardown(self) -> None:
        """Teardown run after each test method."""
        self.behaviour.context.randomness_api.increment_retries.reset_mock()


class TestSelectKeeperBehaviour(BaseDummyBehaviour):
    """Tests for `SelectKeeperBehaviour`."""

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test class."""
        cls.dummy_behaviour_cls = DummySelectKeeperBehaviour
        super().setup_class()

    @mock.patch.object(random, "shuffle", lambda do_not_shuffle: do_not_shuffle)
    @pytest.mark.parametrize(
        "participants, blacklisted_keepers, most_voted_keeper_address, expected_keeper",
        (
            (
                frozenset((f"test_p{i}" for i in range(4))),
                set(),
                "test_p0",
                "test_p1",
            ),
            (
                frozenset((f"test_p{i}" for i in range(4))),
                set(),
                "test_p1",
                "test_p2",
            ),
            (
                frozenset((f"test_p{i}" for i in range(4))),
                set(),
                "test_p2",
                "test_p3",
            ),
            (
                frozenset((f"test_p{i}" for i in range(4))),
                set(),
                "test_p3",
                "test_p0",
            ),
            (
                frozenset((f"test_p{i}" for i in range(4))),
                {f"test_p{i}" for i in range(1)},
                "test_p1",
                "test_p2",
            ),
            (
                frozenset((f"test_p{i}" for i in range(4))),
                {f"test_p{i}" for i in range(4)},
                "",
                "",
            ),
        ),
    )
    def test_select_keeper(
        self,
        participants: FrozenSet[str],
        blacklisted_keepers: Set[str],
        most_voted_keeper_address: str,  # pylint: disable=unused-argument
        expected_keeper: str,
    ) -> None:
        """Test `_select_keeper`."""
        for sync_data_name in (
            "participants",
            "blacklisted_keepers",
            "most_voted_keeper_address",
        ):
            setattr(
                self.behaviour.context.state.synchronized_data,
                sync_data_name,
                locals()[sync_data_name],
            )

        select_keeper_method = (
            self.behaviour._select_keeper  # pylint: disable=protected-access
        )

        if not participants - blacklisted_keepers:
            with pytest.raises(
                RuntimeError,
                match="Cannot continue if all the keepers have been blacklisted!",
            ):
                select_keeper_method()
            return

        with mock.patch("random.seed"):
            actual_keeper = select_keeper_method()
        assert actual_keeper == expected_keeper

    def test_async_act(self) -> None:
        """Test `async_act`."""
        gen = self.behaviour.async_act()

        with mock.patch.object(
            self.behaviour,
            "_select_keeper",
            return_value="test_keeper",
        ), mock.patch.object(
            self.behaviour,
            "send_a2a_transaction",
        ) as send_a2a_transaction_mocked, mock.patch.object(
            self.behaviour,
            "wait_until_round_end",
        ) as wait_until_round_end_mocked, mock.patch.object(
            self.behaviour,
            "set_done",
        ) as set_done_mocked:
            last_iteration(gen)
            send_a2a_transaction_mocked.assert_called_once()
            wait_until_round_end_mocked.assert_called_once()
            set_done_mocked.assert_called_once()
