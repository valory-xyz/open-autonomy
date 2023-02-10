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

"""Templates for FSM tests"""

from dataclasses import dataclass


@dataclass
class TEST_ROUNDS:
    """Template for test_rounds.py"""

    FILENAME = "test_rounds.py"

    HEADER = """\
    \"\"\"This package contains the tests for rounds of {FSMName}.\"\"\"

    from typing import Any, Type, Dict, List, Callable, Hashable, Mapping
    from dataclasses import dataclass, field

    import pytest

    from packages.{author}.skills.{skill_name}.payloads import (
        {payloads},
    )
    from packages.{author}.skills.{skill_name}.rounds import (
        AbstractRound,
        Event,
        SynchronizedData,
        {rounds},
    )
    from packages.valory.skills.abstract_round_abci.base import (
        BaseTxPayload,
    )
    from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
        BaseRoundTestClass,
        BaseOnlyKeeperSendsRoundTest,
        BaseCollectDifferentUntilThresholdRoundTest,
        BaseCollectSameUntilThresholdRoundTest,
     )


    @dataclass
    class RoundTestCase:
        \"\"\"RoundTestCase\"\"\"

        name: str
        initial_data: Dict[str, Hashable]
        payloads: Mapping[str, BaseTxPayload]
        final_data: Dict[str, Hashable]
        event: Event
        synchronized_data_attr_checks: List[Callable] = field(default_factory=list)
        kwargs: Dict[str, Any] = field(default_factory=dict)


    MAX_PARTICIPANTS: int = 4

    """

    BASE_ROUND_TEST_CLS = """\
    class Base{FSMName}RoundTest(BaseRoundTestClass):
        \"\"\"Base test class for {FSMName} rounds.\"\"\"

        round_cls: Type[AbstractRound]
        synchronized_data: SynchronizedData
        _synchronized_data_class = SynchronizedData
        _event_class = Event

        def run_test(self, test_case: RoundTestCase) -> None:
            \"\"\"Run the test\"\"\"

            self.synchronized_data.update(**test_case.initial_data)

            test_round = self.round_cls(
                synchronized_data=self.synchronized_data,
            )

            self._complete_run(
                self._test_round(
                    test_round=test_round,
                    round_payloads=test_case.payloads,
                    synchronized_data_update_fn=lambda sync_data, _: sync_data.update(**test_case.final_data),
                    synchronized_data_attr_checks=test_case.synchronized_data_attr_checks,
                    exit_event=test_case.event,
                    **test_case.kwargs,  # varies per BaseRoundTestClass child
                )
            )

    """

    TEST_ROUND_CLS = """\
    class Test{RoundCls}(Base{FSMName}RoundTest):
        \"\"\"Tests for {RoundCls}.\"\"\"

        round_class = {RoundCls}

        # TODO: provide test cases
        @pytest.mark.parametrize("test_case", [])
        def test_run(self, test_case: RoundTestCase) -> None:
            \"\"\"Run tests.\"\"\"

            self.run_test(test_case)

    """


@dataclass
class TEST_BEHAVIOURS:
    """Template for test_behaviours.py"""

    FILENAME = "test_behaviours.py"

    HEADER = """\
    \"\"\"This package contains round behaviours of {AbciApp}.\"\"\"

    from pathlib import Path
    from typing import Any, Dict, Hashable, Optional, Type
    from dataclasses import dataclass, field

    import pytest

    from packages.valory.skills.abstract_round_abci.base import AbciAppDB
    from packages.valory.skills.abstract_round_abci.behaviours import (
        AbstractRoundBehaviour,
        BaseBehaviour,
        make_degenerate_behaviour,
    )
    from packages.{author}.skills.{skill_name}.behaviours import (
        {BaseBehaviourCls},
        {RoundBehaviourCls},
        {behaviours},
    )
    from packages.{author}.skills.{skill_name}.rounds import (
        SynchronizedData,
        DegenerateRound,
        Event,
        {AbciApp},
        {all_rounds},
    )

    from packages.valory.skills.abstract_round_abci.test_tools.base import (
        FSMBehaviourBaseCase,
    )


    @dataclass
    class BehaviourTestCase:
        \"\"\"BehaviourTestCase\"\"\"

        name: str
        initial_data: Dict[str, Hashable]
        event: Event
        kwargs: Dict[str, Any] = field(default_factory=dict)

    """

    BASE_BEHAVIOUR_TEST_CLS = """\
    class Base{FSMName}Test(FSMBehaviourBaseCase):
        \"\"\"Base test case.\"\"\"

        path_to_skill = Path(__file__).parent.parent

        behaviour: {RoundBehaviourCls}
        behaviour_class: Type[{BaseBehaviourCls}]
        next_behaviour_class: Type[{BaseBehaviourCls}]
        synchronized_data: SynchronizedData
        done_event = Event.DONE

        @property
        def current_behaviour_id(self) -> str:
            \"\"\"Current RoundBehaviour's behaviour id\"\"\"

            return self.behaviour.current_behaviour.behaviour_id

        def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
            \"\"\"Fast-forward on initialization\"\"\"

            data = data if data is not None else {{}}
            self.fast_forward_to_behaviour(
                self.behaviour,
                self.behaviour_class.behaviour_id,
                SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
            )
            assert self.current_behaviour_id == self.behaviour_class.behaviour_id

        def complete(self, event: Event) -> None:
            \"\"\"Complete test\"\"\"

            self.behaviour.act_wrapper()
            self.mock_a2a_transaction()
            self._test_done_flag_set()
            self.end_round(done_event=event)
            assert self.current_behaviour_id == self.next_behaviour_class.behaviour_id

    """

    TEST_BEHAVIOUR_CLS = """\
    class Test{BehaviourCls}(Base{FSMName}Test):
        \"\"\"Tests {BehaviourCls}\"\"\"

        # TODO: set next_behaviour_class
        behaviour_class: Type[BaseBehaviour] = {BehaviourCls}
        next_behaviour_class: Type[BaseBehaviour] = ...

        # TODO: provide test cases
        @pytest.mark.parametrize("test_case", [])
        def test_run(self, test_case: BehaviourTestCase) -> None:
            \"\"\"Run tests.\"\"\"

            self.fast_forward(test_case.initial_data)
            # TODO: mock the necessary calls
            # self.mock_ ...
            self.complete(test_case.event)

    """


@dataclass
class TEST_PAYLOADS:
    """Template for test_payloads.py"""

    FILENAME = "test_payloads.py"

    HEADER = """\
    \"\"\"This package contains payload tests for the {AbciApp}.\"\"\"

    from typing import Type, Hashable
    from dataclasses import dataclass

    import pytest

    from packages.{author}.skills.{skill_name}.payloads import (
        BaseTxPayload,
        {payloads},
    )


    @dataclass
    class PayloadTestCase:
        \"\"\"PayloadTestCase\"\"\"

        name: str
        payload_cls: Type[BaseTxPayload]
        content: Hashable

    """

    TEST_PAYLOAD_CLS = """\
    # TODO: provide test cases
    @pytest.mark.parametrize("test_case", [])
    def test_payloads(test_case: PayloadTestCase) -> None:
        \"\"\"Tests for {AbciApp} payloads\"\"\"

        payload = test_case.payload_cls(sender="sender", content=test_case.content)
        assert payload.sender == "sender"
        assert payload.from_json(payload.json) == payload

    """


@dataclass
class TEST_MODELS:
    """Template for test_models.py"""

    FILENAME = "test_models.py"

    HEADER = """\
    \"\"\"Test the models.py module of the {FSMName}.\"\"\"

    from packages.valory.skills.abstract_round_abci.test_tools.base import DummyContext
    from packages.{author}.skills.{skill_name}.models import SharedState


    class TestSharedState:
        \"\"\"Test SharedState of {FSMName}.\"\"\"

        def test_initialization(self) -> None:
            \"\"\"Test initialization.\"\"\"
            SharedState(name="", skill_context=DummyContext())

    """


@dataclass
class TEST_HANDLERS:
    """Template for test_handlers.py"""

    FILENAME = "test_handlers.py"

    HEADER = """\
    \"\"\"Test the handlers.py module of the {FSMName}.\"\"\"

    import packages.{author}.skills.{skill_name}.handlers  # noqa


    def test_import() -> None:
        \"\"\"Test that the 'handlers.py' of the {FSMName} can be imported.\"\"\"

    """


@dataclass
class TEST_DIALOGUES:
    """Template for test_dialogues.py"""

    FILENAME = "test_dialogues.py"

    HEADER = """\
    \"\"\"Test the dialogues.py module of the {FSMName}.\"\"\"

    import packages.{author}.skills.{skill_name}.dialogues  # noqa


    def test_import() -> None:
        \"\"\"Test that the 'dialogues.py' of the {FSMName} can be imported.\"\"\"
    """
