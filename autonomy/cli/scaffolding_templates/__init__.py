
FILE_HEADER = """\
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
"""


# Rounds
ROUNDS_FILE_HEADER = """\
\"\"\"This package contains the rounds of {AbciApp}.\"\"\"

from enum import Enum
from typing import List, Optional, Set, Tuple

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    DegenerateRound,
    EventToTimeout,
    TransactionType
)

from {author}.skills.{skill_name}.payloads import (
    {payloads},
)

"""

EVENT_SECTION = """\
class Event(Enum):
    \"\"\"{AbciApp} Events\"\"\"

    {events}

"""

SYNCHRONIZED_DATA_SECTION = """\
class SynchronizedData(BaseSynchronizedData):
    \"\"\"
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    \"\"\"

"""

ROUND_CLS_TEMPLATE = """\
class {RoundCls}({ABCRoundCls}):
    \"\"\"{RoundCls}\"\"\"

    {todo_abstract_round_cls}
    # TODO: set the following class attributes
    round_id: str = "{round_id}"
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str = {PayloadCls}.transaction_type

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        \"\"\"Process the end of the block.\"\"\"
        raise NotImplementedError

    def check_payload(self, payload: {PayloadCls}) -> None:
        \"\"\"Check payload.\"\"\"
        raise NotImplementedError

    def process_payload(self, payload: {PayloadCls}) -> None:
        \"\"\"Process payload.\"\"\"
        raise NotImplementedError

"""

DEGENERATE_ROUND_CLS_TEMPLATE = """\
class {RoundCls}({ABCRoundCls}):
    \"\"\"{RoundCls}\"\"\"

    round_id: str = "{round_id}"

"""

ABCI_APP_CLS_TEMPLATE = """\
class {AbciApp}(AbciApp[Event]):
    \"\"\"{AbciApp}\"\"\"

    initial_round_cls: AppState = {initial_round_cls}
    initial_states: Set[AppState] = {initial_states}
    transition_function: AbciAppTransitionFunction = {transition_function}
    final_states: Set[AppState] = {final_states}
    event_to_timeout: EventToTimeout = {{}}
    cross_period_persisted_keys: List[str] = []
"""


# Behaviours
BEHAVIOUR_FILE_HEADER = """\
\"\"\"This package contains round behaviours of {AbciApp}.\"\"\"

from abc import abstractmethod
from typing import Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)

from {author}.skills.{skill_name}.models import Params
from {author}.skills.{skill_name}.rounds import (
    SynchronizedData,
    {AbciApp},
    {rounds},
)

"""

BASE_BEHAVIOUR_CLS_TEMPLATE = """\
class {BaseBehaviourCls}(BaseBehaviour):
    \"\"\"Base behaviour for the common apps' skill.\"\"\"

    @property
    def synchronized_data(self) -> SynchronizedData:
        \"\"\"Return the synchronized data.\"\"\"
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> Params:
        \"\"\"Return the params.\"\"\"
        return cast(Params, super().params)

"""

BEHAVIOUR_CLS_TEMPLATE = """\
class {BehaviourCls}({BaseBehaviourCls}):
    \"\"\"{BehaviourCls}\"\"\"

    # TODO: set the following class attributes
    state_id: str
    behaviour_id: str = "{behaviour_id}"
    matching_round: Type[AbstractRound] = {matching_round}

    @abstractmethod
    def async_act(self) -> Generator:
        \"\"\"Do the act, supporting asynchronous execution.\"\"\"

"""

ROUND_BEHAVIOUR_CLS_TEMPLATE = """\
class {RoundBehaviourCls}(AbstractRoundBehaviour):
    \"\"\"{RoundBehaviourCls}\"\"\"

    initial_behaviour_cls = {InitialBehaviourCls}
    abci_app_cls = {AbciApp}  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = {round_behaviours}
"""


# Payloads
PAYLOADS_FILE = """\
    \"\"\"This module contains the transaction payloads of the {AbciApp}.\"\"\"

    from abc import ABC
    from enum import Enum
    from typing import Any, Dict, Hashable, Optional

    from packages.valory.skills.abstract_round_abci.base import BaseTxPayload

"""

TRANSACTION_TYPE_SECTION = """\
class TransactionType(Enum):
    \"\"\"Enumeration of transaction types.\"\"\"

    # TODO: define transaction types: e.g. TX_HASH: "tx_hash"
    {tx_types}

    def __str__(self) -> str:
        \"\"\"Get the string value of the transaction type.\"\"\"
        return self.value

"""

BASE_PAYLOAD_CLS = """\
class Base{FSMName}Payload(BaseTxPayload, ABC):
    \"\"\"Base payload for {AbciApp}.\"\"\"

    def __init__(self, sender: str, content: Hashable, **kwargs: Any) -> None:
        \"\"\"Initialize a 'select_keeper' transaction payload.\"\"\"

        super().__init__(sender, **kwargs)
        setattr(self, f"_{{self.transaction_type}}", content)
        p = property(lambda s: getattr(self, f"_{{self.transaction_type}}"))
        setattr(self.__class__, f"{{self.transaction_type}}", p)

    @property
    def data(self) -> Dict[str, Hashable]:
        \"\"\"Get the data.\"\"\"
        return {{str(self.transaction_type): getattr(self, str(self.transaction_type))}}

"""

PAYLOAD_CLS_TEMPLATE = """\
class {PayloadCls}(Base{FSMName}Payload):
    \"\"\"Represent a transaction payload for the {RoundCls}.\"\"\"

    # TODO: specify the transaction type
    transaction_type = TransactionType.{tx_type}

"""


# Models
MODEL_FILE_TEMPLATE = """\
\"\"\"This module contains the shared state for the abci skill of {AbciApp}.\"\"\"

from typing import Any

from packages.valory.skills.abstract_round_abci.models import BaseParams
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from {author}.skills.{skill_name}.rounds import {AbciApp}


class SharedState(BaseSharedState):
    \"\"\"Keep the current shared state of the skill.\"\"\"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        \"\"\"Initialize the state.\"\"\"
        super().__init__(*args, abci_app_cls={AbciApp}, **kwargs)


Params = BaseParams
Requests = BaseRequests
"""


# Handlers
HANDLERS_FILE = """"\
\"\"\"This module contains the handlers for the skill of {AbciApp}.\"\"\"

from packages.valory.skills.abstract_round_abci.handlers import (
    ABCIRoundHandler as BaseABCIRoundHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    ContractApiHandler as BaseContractApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    HttpHandler as BaseHttpHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    LedgerApiHandler as BaseLedgerApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    SigningHandler as BaseSigningHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    TendermintHandler as BaseTendermintHandler,
)


ABCIRoundHandler = BaseABCIRoundHandler
HttpHandler = BaseHttpHandler
SigningHandler = BaseSigningHandler
LedgerApiHandler = BaseLedgerApiHandler
ContractApiHandler = BaseContractApiHandler
TendermintHandler = BaseTendermintHandler
"""


# Dialogues
DIALOGUES_FILE = """\
\"\"\"This module contains the dialogues of the {AbciApp}.\"\"\"

from packages.valory.skills.abstract_round_abci.dialogues import (
    AbciDialogue as BaseAbciDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    AbciDialogues as BaseAbciDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    ContractApiDialogue as BaseContractApiDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    HttpDialogue as BaseHttpDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    HttpDialogues as BaseHttpDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    SigningDialogue as BaseSigningDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    TendermintDialogue as BaseTendermintDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    TendermintDialogues as BaseTendermintDialogues,
)


AbciDialogue = BaseAbciDialogue
AbciDialogues = BaseAbciDialogues


HttpDialogue = BaseHttpDialogue
HttpDialogues = BaseHttpDialogues


SigningDialogue = BaseSigningDialogue
SigningDialogues = BaseSigningDialogues


LedgerApiDialogue = BaseLedgerApiDialogue
LedgerApiDialogues = BaseLedgerApiDialogues


ContractApiDialogue = BaseContractApiDialogue
ContactApiDialogues = BaseContractApiDialogues


TendermintDialogue = BaseTendermintDialogue
TendermintDialogues = BaseTendermintDialogues
"""


# Tests


# Test rounds
TEST_ROUNDS_FILE_HEADER = """\
\"\"\"This package contains the tests for rounds of {FSMName}.\"\"\"

from typing import Any, Dict, List, Callable, Hashable
from dataclasses import dataclass, field

import pytest

# TODO: define and import specific payloads explicitly by name
from {author}.skills.{skill_name}.payloads import *
from {author}.skills.{skill_name}.rounds import (
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

    initial_data: Dict[str, Hashable]
    payloads: BaseTxPayload
    final_data: Dict[str, Hashable]
    event: Event
    synchronized_data_attr_checks: List[Callable] = field(default_factory=list)


MAX_PARTICIPANTS: int = 4

"""


TEST_ROUNDS_BASE_CLASS = """\
class Base{FSMName}RoundTestClass(BaseRoundTestClass):
    \"\"\"Base test class for {FSMName} rounds.\"\"\"

    synchronized_data: SynchronizedData
    _synchronized_data_class = SynchronizedData
    _event_class = Event

    def run_test(self, test_case: RoundTestCase, **kwargs) -> None:
        \"\"\"Run the test\"\"\"

        self.synchronized_data.update(**test_case.initial_data)

        test_round = self.round_class(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        self._complete_run(
            self._test_round(
                test_round=test_round,
                round_payloads=test_case.payloads,
                synchronized_data_update_fn=lambda sync_data, _: sync_data.update(**test_case.final_data),
                synchronized_data_attr_checks=test_case.synchronized_data_attr_checks,
                exit_event=test_case.event,
                **kwargs,  # varies per BaseRoundTestClass child
            )
        )

"""

TEST_ROUND_CLS_TEMPLATE = """\
class Test{RoundCls}(Base{FSMName}RoundTestClass):
    \"\"\"Tests for {RoundCls}.\"\"\"

    round_class = {RoundCls}

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: RoundTestCase, **kwargs: Any) -> None:
        \"\"\"Run tests.\"\"\"

        self.run_test(test_case, **kwargs)

"""


# Test behaviours
TEST_BEHAVIOUR_FILE_HEADER = """\
\"\"\"This package contains round behaviours of {AbciApp}.\"\"\"

from pathlib import Path
from typing import Any, Dict, Hashable, Optional, Type
from dataclasses import dataclass

import pytest

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
    make_degenerate_behaviour,
)
from {author}.skills.{skill_name}.behaviours import (
    {FSMName}BaseBehaviour,
    {FSMName}RoundBehaviour,
    {behaviours},
)
from {author}.skills.{skill_name}.rounds import (
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

    initial_data: Dict[str, Hashable]
    event: Event

"""


TEST_BEHAVIOUR_BASE_CLASS = """\
class Base{FSMName}Test(FSMBehaviourBaseCase):
    \"\"\"Base test case.\"\"\"

    path_to_skill = Path(__file__).parent.parent

    behaviour: {FSMName}RoundBehaviour
    behaviour_class: Type[{FSMName}BaseBehaviour]
    next_behaviour_class: Type[{FSMName}BaseBehaviour]
    synchronized_data: SynchronizedData
    done_event = Event.DONE

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        \"\"\"Fast-forward on initialization\"\"\"

        data = data if data is not None else {{}}
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert self.behaviour.behaviour_id == self.behaviour_class.behaviour_id

    def complete(self, event: Event) -> None:
        \"\"\"Complete test\"\"\"

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=event)
        assert self.behaviour.behaviour_id == self.next_behaviour_class.behaviour_id

"""


TEST_BEHAVIOUR_CLS_TEMPLATE = """\
class Test{BehaviourCls}(Base{FSMName}Test):
    \"\"\"Tests {BehaviourCls}\"\"\"

    # TODO: set next_behaviour_class
    behaviour_class: Type[BaseBehaviour] = {BehaviourCls}
    next_behaviour_class: Type[BaseBehaviour] = ...

    # TODO: provide test cases
    @pytest.mark.parametrize("test_case, kwargs", [])
    def test_run(self, test_case: BehaviourTestCase, **kwargs: Any) -> None:
        \"\"\"Run tests.\"\"\"

        self.fast_forward(test_case.initial_data)
        # TODO: mock the necessary calls
        # self.mock_ ...
        self.complete(test_case.event)

"""


# Test payloads
TEST_PAYLOAD_FILE_HEADER = """\
\"\"\"This package contains payload tests for the {AbciApp}.\"\"\"

from typing import Hashable
from dataclasses import dataclass

import pytest

from {author}.skills.{skill_name}.payloads import (
    TransactionType,
    Base{FSMName}Payload,
    {payloads},
)


@dataclass
class PayloadTestCase:
    \"\"\"PayloadTestCase\"\"\"

    payload_cls: Base{FSMName}Payload
    content: Hashable
    transaction_type: TransactionType

"""


TEST_PAYLOAD_CLS_TEMPLATE = """\
# TODO: provide test cases
@pytest.mark.parametrize("test_case", [])
def test_payloads(test_case: PayloadTestCase) -> None:
    \"\"\"Tests for {AbciApp} payloads\"\"\"

    payload = test_case.payload_cls(sender="sender", content=test_case.content)
    assert payload.sender == "sender"
    assert getattr(payload, f"{{payload.transaction_type}}") == test_case.content
    assert payload.transaction_type == test_case.transaction_type
    assert payload.from_json(payload.json) == payload

"""


TEST_MODELS_FILE = """\
\"\"\"Test the models.py module of the {FSMName}.\"\"\"

from packages.valory.skills.abstract_round_abci.test_tools.base import DummyContext
from {author}.skills.{skill_name}.models import SharedState


class TestSharedState:
    \"\"\"Test SharedState of {FSMName}.\"\"\"

    def test_initialization(self) -> None:
        \"\"\"Test initialization.\"\"\"
        SharedState(name="", skill_context=DummyContext())

"""


TEST_HANDLERS_FILE = """\
\"\"\"Test the handlers.py module of the {FSMName}.\"\"\"

import packages.{author}.skills.{skill_name}.handlers  # noqa


def test_import() -> None:
    \"\"\"Test that the 'handlers.py' of the {FSMName} can be imported.\"\"\"

"""


TEST_DIALOGUES_FILE = """\
\"\"\"Test the dialogues.py module of the {FSMName}.\"\"\"

import packages.{author}.skills.{skill_name}.dialogues  # noqa


def test_import() -> None:
    \"\"\"Test that the 'dialogues.py' of the {FSMName} can be imported.\"\"\"
"""
