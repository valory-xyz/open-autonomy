
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
class {AbciAppCls}(AbciApp[Event]):
    \"\"\"{AbciAppCls}\"\"\"

    initial_round_cls: AppState = {initial_round_cls}
    initial_states: Set[AppState] = {initial_states}
    transition_function: AbciAppTransitionFunction = {transition_function}
    final_states: Set[AppState] = {final_states}
    event_to_timeout: EventToTimeout = {{}}
    cross_period_persisted_keys: List[str] = []
"""

