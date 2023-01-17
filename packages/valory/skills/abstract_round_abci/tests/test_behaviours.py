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

"""Test the behaviours.py module of the skill."""

# pylint: skip-file

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Tuple
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci import PUBLIC_ID
from packages.valory.skills.abstract_round_abci.base import (
    ABCIAppInternalError,
    AbciApp,
    AbstractRound,
    BaseSynchronizedData,
    BaseTxPayload,
    DegenerateRound,
    EventType,
    RoundSequence,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseBehaviour,
    DegenerateBehaviour,
    TmManager,
)
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    _MetaRoundBehaviour,
)
from packages.valory.skills.abstract_round_abci.models import TendermintRecoveryParams


BEHAVIOUR_A_ID = "behaviour_a"
BEHAVIOUR_B_ID = "behaviour_b"
BEHAVIOUR_C_ID = "behaviour_c"
CONCRETE_BACKGROUND_BEHAVIOUR_ID = "background_behaviour"
ROUND_A_ID = "round_a"
ROUND_B_ID = "round_b"
CONCRETE_BACKGROUND_ROUND_ID = "background_round"


def test_skill_public_id() -> None:
    """Test skill module public ID"""

    assert PUBLIC_ID.name == Path(__file__).parents[1].name
    assert PUBLIC_ID.author == Path(__file__).parents[3].name


class RoundA(AbstractRound):
    """Round A."""

    round_id = ROUND_A_ID
    payload_class = BaseTxPayload
    payload_attribute = ""
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, EventType]]:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


class RoundB(AbstractRound):
    """Round B."""

    round_id = ROUND_B_ID
    payload_class = BaseTxPayload
    payload_attribute = ""
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, EventType]]:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


class ConcreteBackgroundRound(AbstractRound):
    """Concrete Background Round."""

    round_id = ROUND_B_ID
    payload_class = BaseTxPayload
    payload_attribute = ""
    synchronized_data_class = BaseSynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, EventType]]:
        """End block."""

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""


class BehaviourA(BaseBehaviour):
    """Dummy behaviour."""

    behaviour_id = BEHAVIOUR_A_ID
    matching_round = RoundA

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize behaviour."""
        super().__init__(*args, **kwargs)
        self.count = 0

    def setup(self) -> None:
        """Setup behaviour."""
        self.count += 1

    def async_act(self) -> Generator:
        """Dummy act method."""
        yield


class BehaviourB(BaseBehaviour):
    """Dummy behaviour."""

    behaviour_id = BEHAVIOUR_B_ID
    matching_round = RoundB

    def async_act(self) -> Generator:
        """Dummy act method."""
        yield


class BehaviourC(BaseBehaviour):
    """Dummy behaviour."""

    matching_round = RoundB

    def async_act(self) -> Generator:
        """Dummy act method."""
        yield


def test_auto_behaviour_id() -> None:
    """Test that the 'auto_behaviour_id()' method works as expected."""

    assert BehaviourB.auto_behaviour_id() == BEHAVIOUR_B_ID
    assert BehaviourB.behaviour_id == BEHAVIOUR_B_ID
    assert BehaviourC.auto_behaviour_id() == "behaviour_c"
    assert isinstance(BehaviourC.behaviour_id, property)


class ConcreteBackgroundBehaviour(BaseBehaviour):
    """Dummy behaviour."""

    behaviour_id = CONCRETE_BACKGROUND_BEHAVIOUR_ID
    matching_round = ConcreteBackgroundRound

    def async_act(self) -> Generator:
        """Dummy act method."""
        yield


class ConcreteAbciApp(AbciApp):
    """Concrete ABCI App."""

    initial_round_cls = RoundA
    transition_function = {RoundA: {MagicMock(): RoundB}}
    event_to_timeout: Dict = {}


class ConcreteRoundBehaviour(AbstractRoundBehaviour):
    """Concrete round behaviour."""

    abci_app_cls = ConcreteAbciApp
    behaviours = {BehaviourA, BehaviourB}  # type: ignore
    initial_behaviour_cls = BehaviourA
    background_behaviour_cls = ConcreteBackgroundBehaviour


class TestAbstractRoundBehaviour:
    """Test 'AbstractRoundBehaviour' class."""

    def setup(self) -> None:
        """Set up the tests."""
        self.round_sequence_mock = MagicMock()
        context_mock = MagicMock()
        context_mock.state.round_sequence = self.round_sequence_mock
        context_mock.state.round_sequence.syncing_up = False
        self.round_sequence_mock.block_stall_deadline_expired = False
        self.behaviour = ConcreteRoundBehaviour(name="", skill_context=context_mock)
        self.behaviour.tm_manager = self.behaviour.instantiate_behaviour_cls(TmManager)  # type: ignore

    def test_setup(self) -> None:
        """Test 'setup' method."""
        self.behaviour.setup()

    def test_teardown(self) -> None:
        """Test 'teardown' method."""
        self.behaviour.teardown()

    def test_current_behaviour_return_none(self) -> None:
        """Test 'current_behaviour' property return None."""
        assert self.behaviour.current_behaviour is None

    def test_act_current_behaviour_name_is_none(self) -> None:
        """Test 'act' with current behaviour None."""
        self.behaviour.current_behaviour = None
        with mock.patch.object(self.behaviour, "_process_current_round"):
            self.behaviour.act()

    def test_check_matching_round_consistency(self) -> None:
        """Test classmethod '_get_behaviour_id_to_behaviour_mapping', negative case."""
        rounds = [
            MagicMock(**{"auto_round_id.return_value": f"round_{i}"}) for i in range(3)
        ]
        mock_behaviours = [
            MagicMock(matching_round=round, behaviour_id=f"behaviour_{i}")
            for i, round in enumerate(rounds)
        ]

        with mock.patch.object(
            _MetaRoundBehaviour, "_check_all_required_classattributes_are_set"
        ), mock.patch.object(
            _MetaRoundBehaviour, "_check_behaviour_id_uniqueness"
        ), mock.patch.object(
            _MetaRoundBehaviour, "_check_initial_behaviour_in_set_of_behaviours"
        ), pytest.raises(
            ABCIAppInternalError,
            match="internal error: round round_0 is a final round it shouldn't have any matching behaviours",
        ):

            class MyRoundBehaviour(AbstractRoundBehaviour):
                abci_app_cls = MagicMock(
                    get_all_round_classes=lambda include_termination_rounds: rounds,
                    final_states={
                        rounds[0],
                    },
                )
                behaviours = mock_behaviours  # type: ignore
                initial_behaviour_cls = MagicMock()

            MyRoundBehaviour(name=MagicMock(), skill_context=MagicMock())

    def test_get_behaviour_id_to_behaviour_mapping_negative(self) -> None:
        """Test classmethod '_get_behaviour_id_to_behaviour_mapping', negative case."""
        behaviour_id = "behaviour_id"
        behaviour_1 = MagicMock(**{"auto_behaviour_id.return_value": behaviour_id})
        behaviour_2 = MagicMock(**{"auto_behaviour_id.return_value": behaviour_id})

        with pytest.raises(
            ValueError,
            match=f"cannot have two behaviours with the same id; got {behaviour_2} and {behaviour_1} both with id '{behaviour_id}'",
        ):
            with mock.patch.object(_MetaRoundBehaviour, "_check_consistency"):

                class MyRoundBehaviour(AbstractRoundBehaviour):
                    abci_app_cls = MagicMock
                    behaviours = [behaviour_1, behaviour_2]  # type: ignore
                    initial_behaviour_cls = MagicMock()

                MyRoundBehaviour(name=MagicMock(), skill_context=MagicMock())

    def test_get_round_to_behaviour_mapping_two_behaviours_same_round(self) -> None:
        """Test classmethod '_get_round_to_behaviour_mapping' when two different behaviours point to the same round."""
        behaviour_id_1 = "behaviour_id_1"
        behaviour_id_2 = "behaviour_id_2"
        round_cls = RoundA
        round_id = round_cls.auto_round_id()
        behaviour_1 = MagicMock(
            matching_round=round_cls,
            **{"auto_behaviour_id.return_value": behaviour_id_1},
        )
        behaviour_2 = MagicMock(
            matching_round=round_cls,
            **{"auto_behaviour_id.return_value": behaviour_id_2},
        )

        with pytest.raises(
            ValueError,
            match=f"the behaviours '{behaviour_2.auto_behaviour_id()}' and '{behaviour_1.auto_behaviour_id()}' point to the same matching round '{round_id}'",
        ):
            with mock.patch.object(_MetaRoundBehaviour, "_check_consistency"):

                class MyRoundBehaviour(AbstractRoundBehaviour):
                    abci_app_cls = ConcreteAbciApp
                    behaviours = [behaviour_1, behaviour_2]  # type: ignore
                    initial_behaviour_cls = behaviour_1

                MyRoundBehaviour(name=MagicMock(), skill_context=MagicMock())

    def test_get_round_to_behaviour_mapping_with_final_rounds(self) -> None:
        """Test classmethod '_get_round_to_behaviour_mapping' with final rounds."""

        class FinalRound(DegenerateRound):
            """A final round for testing."""

            synchronized_data_class = BaseSynchronizedData

            def check_payload(self, payload: BaseTxPayload) -> None:
                pass

            def process_payload(self, payload: BaseTxPayload) -> None:
                pass

            def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
                pass

        behaviour_id_1 = "behaviour_id_1"
        behaviour_1 = MagicMock(behaviour_id=behaviour_id_1, matching_round=RoundA)

        class AbciAppTest(AbciApp):
            """Abci App for testing."""

            initial_round_cls = RoundA
            transition_function = {RoundA: {MagicMock(): FinalRound}, FinalRound: {}}
            event_to_timeout: Dict = {}
            final_states = {FinalRound}

        class MyRoundBehaviour(AbstractRoundBehaviour):
            abci_app_cls = AbciAppTest
            behaviours = {behaviour_1}
            initial_behaviour_cls = behaviour_1
            matching_round = FinalRound

        behaviour = MyRoundBehaviour(name=MagicMock(), skill_context=MagicMock())
        final_behaviour = behaviour._round_to_behaviour[FinalRound]
        assert issubclass(final_behaviour, DegenerateBehaviour)
        assert (
            final_behaviour.auto_behaviour_id()
            == f"degenerate_behaviour_{FinalRound.auto_round_id()}"
        )

    def test_check_behaviour_id_uniqueness_negative(self) -> None:
        """Test metaclass method '_check_consistency', negative case."""
        behaviour_id = "behaviour_id"
        behaviour_1_cls_name = "Behaviour1"
        behaviour_2_cls_name = "Behaviour2"
        behaviour_1 = MagicMock(
            __name__=behaviour_1_cls_name,
            **{"auto_behaviour_id.return_value": behaviour_id},
        )
        behaviour_2 = MagicMock(
            __name__=behaviour_2_cls_name,
            **{"auto_behaviour_id.return_value": behaviour_id},
        )

        with pytest.raises(
            ABCIAppInternalError,
            match=rf"behaviours \['{behaviour_1_cls_name}', '{behaviour_2_cls_name}'\] have the same behaviour id '{behaviour_id}'",
        ):

            class MyRoundBehaviour(AbstractRoundBehaviour):
                abci_app_cls = MagicMock
                behaviours = [behaviour_1, behaviour_2]  # type: ignore
                initial_behaviour_cls = MagicMock()

    def test_check_consistency_two_behaviours_same_round(self) -> None:
        """Test metaclass method '_check_consistency' when two different behaviours point to the same round."""
        behaviour_id_1 = "behaviour_id_1"
        behaviour_id_2 = "behaviour_id_2"
        round_cls = RoundA
        round_id = round_cls.auto_round_id()
        behaviour_1 = MagicMock(
            matching_round=round_cls,
            **{"auto_behaviour_id.return_value": "behaviour_id_1"},
        )
        behaviour_2 = MagicMock(
            matching_round=round_cls,
            **{"auto_behaviour_id.return_value": "behaviour_id_2"},
        )

        with pytest.raises(
            ABCIAppInternalError,
            match=rf"internal error: behaviours \['{behaviour_id_1}', '{behaviour_id_2}'\] have the same matching round '{round_id}'",
        ):

            class MyRoundBehaviour(AbstractRoundBehaviour):
                abci_app_cls = ConcreteAbciApp
                behaviours = [behaviour_1, behaviour_2]  # type: ignore
                initial_behaviour_cls = behaviour_1

    def test_check_initial_behaviour_in_set_of_behaviours_negative_case(self) -> None:
        """Test classmethod '_check_initial_behaviour_in_set_of_behaviours' when initial behaviour is NOT in the set."""
        behaviour_1 = MagicMock(
            matching_round=MagicMock(),
            **{"auto_behaviour_id.return_value": "behaviour_id_1"},
        )
        behaviour_2 = MagicMock(
            matching_round=MagicMock(),
            **{"auto_behaviour_id.return_value": "behaviour_id_2"},
        )

        with pytest.raises(
            ABCIAppInternalError,
            match=f"initial behaviour {behaviour_2.auto_behaviour_id()} is not in the set of behaviours",
        ):

            class MyRoundBehaviour(AbstractRoundBehaviour):
                abci_app_cls = ConcreteAbciApp
                behaviours = {behaviour_1}
                initial_behaviour_cls = behaviour_2

    def test_act_no_round_change(self) -> None:
        """Test the 'act' method of the behaviour, with no round change."""
        self.round_sequence_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.round_sequence_mock.current_round_height = 0

        # check that after setup(), current behaviour is initial behaviour
        self.behaviour.setup()
        assert isinstance(self.behaviour.current_behaviour, BehaviourA)

        with mock.patch.object(
            self.behaviour.current_behaviour, "clean_up"
        ) as clean_up_mock:
            # check that after act(), current behaviour is initial behaviour and `clean_up()` has not been called
            self.behaviour.act()
            assert isinstance(self.behaviour.current_behaviour, BehaviourA)
            clean_up_mock.assert_not_called()

            # check that once the flag done is set, the `clean_up()` has been called
            # and `current_behaviour` is set to `None`.
            self.behaviour.current_behaviour.set_done()
            self.behaviour.act()
            assert self.behaviour.current_behaviour is None
            clean_up_mock.assert_called_once()

    def test_act_behaviour_setup(self) -> None:
        """Test the 'act' method of the FSM behaviour triggers setup() of the behaviour."""
        self.round_sequence_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.round_sequence_mock.current_round_height = 0

        # check that after setup(), current behaviour is initial behaviour
        self.behaviour.setup()
        assert isinstance(self.behaviour.current_behaviour, BehaviourA)

        assert self.behaviour.current_behaviour.count == 0

        with mock.patch.object(
            self.behaviour.current_behaviour, "clean_up"
        ) as clean_up_mock:
            # check that after act() first time, a call to setup has been made
            self.behaviour.act()
            assert isinstance(self.behaviour.current_behaviour, BehaviourA)
            assert self.behaviour.current_behaviour.count == 1

            # check that after act() second time, no further call to setup
            self.behaviour.act()
            assert self.behaviour.current_behaviour.count == 1

            # check that the `clean_up()` has not been called
            clean_up_mock.assert_not_called()

    def test_act_with_round_change(self) -> None:
        """Test the 'act' method of the behaviour, with round change."""
        self.round_sequence_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.round_sequence_mock.current_round_height = 0

        # check that after setup(), current behaviour is initial behaviour
        self.behaviour.setup()
        assert isinstance(self.behaviour.current_behaviour, BehaviourA)

        # check that after act(), current behaviour is initial behaviour
        with mock.patch.object(
            self.behaviour.current_behaviour, "clean_up"
        ) as clean_up_mock:
            self.behaviour.act()
            assert isinstance(self.behaviour.current_behaviour, BehaviourA)
            clean_up_mock.assert_not_called()

            # change the round
            self.round_sequence_mock.current_round = RoundB(MagicMock(), MagicMock())
            self.round_sequence_mock.current_round_height = (
                self.round_sequence_mock.current_round_height + 1
            )

            # check that if the round is changed, the behaviour transition is performed and the clean-up is called
            self.behaviour.act()
            assert isinstance(self.behaviour.current_behaviour, BehaviourB)
            clean_up_mock.assert_called_once()

    def test_act_with_round_change_after_current_behaviour_is_none(self) -> None:
        """Test the 'act' method of the behaviour, with round change, after cur behaviour is none."""
        self.round_sequence_mock.current_round = RoundA(MagicMock(), MagicMock())
        self.round_sequence_mock.current_round_height = 0

        # instantiate behaviour
        self.behaviour.current_behaviour = self.behaviour.instantiate_behaviour_cls(BehaviourA)  # type: ignore
        self.behaviour.background_behaviour = self.behaviour.instantiate_behaviour_cls(ConcreteBackgroundBehaviour)  # type: ignore

        with mock.patch.object(
            self.behaviour.current_behaviour, "clean_up"
        ) as clean_up_mock:
            # check that after act(), current behaviour is same behaviour
            self.behaviour.act()
            assert isinstance(self.behaviour.current_behaviour, BehaviourA)
            clean_up_mock.assert_not_called()

            # check that after the behaviour is done, current behaviour is None
            self.behaviour.current_behaviour.set_done()
            self.behaviour.act()
            assert self.behaviour.current_behaviour is None
            clean_up_mock.assert_called_once()

            # change the round
            self.round_sequence_mock.current_round = RoundB(MagicMock(), MagicMock())
            self.round_sequence_mock.current_round_height = (
                self.round_sequence_mock.current_round_height + 1
            )

            # check that if the round is changed, the behaviour transition is taken
            self.behaviour.act()
            assert isinstance(self.behaviour.current_behaviour, BehaviourB)
            clean_up_mock.assert_called_once()

    @mock.patch.object(
        AbstractRoundBehaviour,
        "_process_current_round",
    )
    @pytest.mark.parametrize(
        ("mock_tm_communication_unhealthy", "mock_is_acting", "expected_fix"),
        [
            (True, True, True),
            (False, True, True),
            (True, False, True),
            (False, False, False),
        ],
    )
    def test_try_fix_call(
        self,
        _: mock._patch,
        mock_tm_communication_unhealthy: bool,
        mock_is_acting: bool,
        expected_fix: bool,
    ) -> None:
        """Test that `try_fix` is called when necessary."""
        with mock.patch.object(
            TmManager,
            "tm_communication_unhealthy",
            new_callable=mock.PropertyMock,
            return_value=mock_tm_communication_unhealthy,
        ), mock.patch.object(
            TmManager,
            "is_acting",
            new_callable=mock.PropertyMock,
            return_value=mock_is_acting,
        ), mock.patch.object(
            TmManager,
            "try_fix",
        ) as mock_try_fix:
            self.behaviour.act()
            if expected_fix:
                mock_try_fix.assert_called()
            else:
                mock_try_fix.assert_not_called()


def test_meta_round_behaviour_when_instance_not_subclass_of_abstract_round_behaviour() -> None:
    """Test instantiation of meta class when instance not a subclass of abstract round behaviour."""

    class MyRoundBehaviour(metaclass=_MetaRoundBehaviour):
        pass


def test_abstract_round_behaviour_instantiation_without_attributes_raises_error() -> None:
    """Test that definition of concrete subclass of AbstractRoundBehavior without attributes raises error."""
    with pytest.raises(ABCIAppInternalError):

        class MyRoundBehaviour(AbstractRoundBehaviour):
            pass


def test_abstract_round_behaviour_matching_rounds_not_covered() -> None:
    """Test that definition of concrete subclass of AbstractRoundBehavior when matching round not covered."""
    with pytest.raises(ABCIAppInternalError):

        class MyRoundBehaviour(AbstractRoundBehaviour):
            abci_app_cls = ConcreteAbciApp
            behaviours = {BehaviourA}
            initial_behaviour_cls = BehaviourA


@mock.patch.object(
    BaseBehaviour,
    "tm_communication_unhealthy",
    new_callable=mock.PropertyMock,
    return_value=False,
)
def test_self_loops_in_abci_app_reinstantiate_behaviour(_: mock._patch) -> None:
    """Test that a self-loop transition in the AbciApp will trigger a transition in the round behaviour."""
    event = MagicMock()

    class AbciAppTest(AbciApp):
        initial_round_cls = RoundA
        transition_function = {RoundA: {event: RoundA}}

    class RoundBehaviour(AbstractRoundBehaviour):
        abci_app_cls = AbciAppTest
        behaviours = {BehaviourA}
        initial_behaviour_cls = BehaviourA

    round_sequence = RoundSequence(AbciAppTest)
    round_sequence.end_sync()
    round_sequence.setup(MagicMock(), MagicMock(), MagicMock())
    context_mock = MagicMock()
    context_mock.state.round_sequence = round_sequence
    behaviour = RoundBehaviour(name="", skill_context=context_mock)
    behaviour.setup()

    behaviour_1 = behaviour.current_behaviour
    assert isinstance(behaviour_1, BehaviourA)

    round_sequence.abci_app.process_event(event)

    behaviour.act()
    behaviour_2 = behaviour.current_behaviour
    assert isinstance(behaviour_2, BehaviourA)
    assert id(behaviour_1) != id(behaviour_2)
    assert behaviour_1 != behaviour_2


class LongRunningBehaviour(BaseBehaviour):
    """A behaviour that runs forevever."""

    behaviour_id = "long_running_behaviour"
    matching_round = RoundA

    def async_act(self) -> Generator:
        """An act method that simply cycles forever."""
        while True:
            # cycle forever
            yield


def test_reset_should_be_performed_when_tm_unhealthy() -> None:
    """Test that hard reset is performed while a behaviour is running, and tendermint communication is unhealthy."""
    event = MagicMock()

    class AbciAppTest(AbciApp):
        initial_round_cls = RoundA
        transition_function = {RoundA: {event: RoundA}}

    class RoundBehaviour(AbstractRoundBehaviour):
        abci_app_cls = AbciAppTest
        behaviours = {LongRunningBehaviour}  # type: ignore
        initial_behaviour_cls = LongRunningBehaviour

    round_sequence = RoundSequence(AbciAppTest)
    round_sequence.end_sync()
    round_sequence.setup(MagicMock(), MagicMock(), MagicMock())
    context_mock = MagicMock()
    context_mock.state.round_sequence = round_sequence
    tm_recovery_params = TendermintRecoveryParams(
        reset_from_round=RoundA.auto_round_id()
    )
    context_mock.state.get_acn_result = MagicMock(return_value=tm_recovery_params)
    context_mock.params.ipfs_domain_name = None
    behaviour = RoundBehaviour(name="", skill_context=context_mock)
    behaviour.setup()

    current_behaviour = behaviour.current_behaviour
    assert isinstance(current_behaviour, LongRunningBehaviour)

    # upon entering the behaviour, the tendermint node communication is working well
    with mock.patch.object(
        RoundSequence,
        "block_stall_deadline_expired",
        new_callable=mock.PropertyMock,
        return_value=False,
    ):
        behaviour.act()

    def dummy_num_peers(
        timeout: Optional[float] = None,
    ) -> Generator[None, None, Optional[int]]:
        """A dummy method for num_active_peers."""
        # a None response is acceptable here, because tendermint is not healthy
        return None
        yield

    def dummy_reset_tendermint_with_wait(
        is_recovery: bool = False,
    ) -> Generator[None, None, bool]:
        """A dummy method for reset_tendermint_with_wait."""
        # we assume the reset goes through successfully
        return True
        yield

    # at this point LongRunningBehaviour is running
    # while the behaviour is running, the tendermint node
    # becomes unhealthy, we expect the node to be reset
    with mock.patch.object(
        RoundSequence,
        "block_stall_deadline_expired",
        new_callable=mock.PropertyMock,
        return_value=True,
    ), mock.patch.object(
        BaseBehaviour,
        "num_active_peers",
        side_effect=dummy_num_peers,
    ), mock.patch.object(
        BaseBehaviour,
        "reset_tendermint_with_wait",
        side_effect=dummy_reset_tendermint_with_wait,
    ) as mock_reset_tendermint:
        behaviour.act()
        mock_reset_tendermint.assert_called()
