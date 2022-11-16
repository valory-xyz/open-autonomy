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

"""Templates for FSM components"""

from dataclasses import dataclass


@dataclass
class ROUNDS:
    """Template for rounds.py"""

    FILENAME = "rounds.py"

    HEADER = """\
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

    from packages.{author}.skills.{skill_name}.payloads import (
        {payloads},
    )


    class Event(Enum):
        \"\"\"{AbciApp} Events\"\"\"

        {events}


    class SynchronizedData(BaseSynchronizedData):
        \"\"\"
        Class to represent the synchronized data.

        This data is replicated by the tendermint application.
        \"\"\"

    """

    ROUND_CLS = """\
    class {RoundCls}({ABCRoundCls}):
        \"\"\"{RoundCls}\"\"\"

        {todo_abstract_round_cls}
        round_id: str = "{round_id}"
        allowed_tx_type: Optional[TransactionType] = {PayloadCls}.transaction_type
        payload_attribute: str = "{round_id}"

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

    DEGENERATE_ROUND_CLS = """\
    class {RoundCls}({ABCRoundCls}):
        \"\"\"{RoundCls}\"\"\"

        round_id: str = "{round_id}"

    """

    ABCI_APP_CLS = """\
    class {AbciApp}(AbciApp[Event]):
        \"\"\"{AbciApp}\"\"\"

        initial_round_cls: AppState = {initial_round_cls}
        initial_states: Set[AppState] = {initial_states}
        transition_function: AbciAppTransitionFunction = {transition_function}
        final_states: Set[AppState] = {final_states}
        event_to_timeout: EventToTimeout = {{}}
        cross_period_persisted_keys: List[str] = []
    """


@dataclass
class BEHAVIOURS:
    """Template for behaviours.py"""

    FILENAME = "behaviours.py"

    HEADER = """\
    \"\"\"This package contains round behaviours of {AbciApp}.\"\"\"

    from typing import Generator, Set, Type, cast

    from packages.valory.skills.abstract_round_abci.base import AbstractRound
    from packages.valory.skills.abstract_round_abci.behaviours import (
        AbstractRoundBehaviour,
        BaseBehaviour,
    )

    from packages.{author}.skills.{skill_name}.models import Params
    from packages.{author}.skills.{skill_name}.rounds import (
        SynchronizedData,
        {AbciApp},
        {rounds},
    )
    from packages.{author}.skills.{skill_name}.rounds import (
        {payloads},
    )

    """

    BASE_BEHAVIOUR_CLS = """\
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

    BEHAVIOUR_CLS = """\
    class {BehaviourCls}({BaseBehaviourCls}):
        \"\"\"{BehaviourCls}\"\"\"

        # TODO: set the following class attributes
        state_id: str
        behaviour_id: str = "{behaviour_id}"
        matching_round: Type[AbstractRound] = {matching_round}

        # TODO: implement logic required to set payload content (e.g. synchronized_data)
        def async_act(self) -> Generator:
            \"\"\"Do the act, supporting asynchronous execution.\"\"\"

            with self.context.benchmark_tool.measure(self.behaviour_id).local():
                sender = self.context.agent_address
                payload = {PayloadCls}(sender=sender, content=...)

            with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
                yield from self.send_a2a_transaction(payload)
                yield from self.wait_until_round_end()

            self.set_done()

    """

    ROUND_BEHAVIOUR_CLS = """\
    class {RoundBehaviourCls}(AbstractRoundBehaviour):
        \"\"\"{RoundBehaviourCls}\"\"\"

        initial_behaviour_cls = {InitialBehaviourCls}
        abci_app_cls = {AbciApp}  # type: ignore
        behaviours: Set[Type[BaseBehaviour]] = {round_behaviours}
    """


@dataclass
class PAYLOADS:
    """Template for payloads.py"""

    FILENAME = "payloads.py"

    HEADER = """\
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
            \"\"\"Initialize a transaction payload.\"\"\"

            super().__init__(sender, **kwargs)
            setattr(self, f"_{{self.transaction_type}}", content)
            p = property(lambda s: getattr(self, f"_{{self.transaction_type}}"))
            setattr(self.__class__, f"{{self.transaction_type}}", p)

        @property
        def data(self) -> Dict[str, Hashable]:
            \"\"\"Get the data.\"\"\"
            return dict(content=getattr(self, str(self.transaction_type)))

    """

    PAYLOAD_CLS = """\
    class {PayloadCls}(Base{FSMName}Payload):
        \"\"\"Represent a transaction payload for the {RoundCls}.\"\"\"

        transaction_type = TransactionType.{tx_type}

    """


@dataclass
class MODELS:
    """Template for models.py"""

    FILENAME = "models.py"

    HEADER = """\
    \"\"\"This module contains the shared state for the abci skill of {AbciApp}.\"\"\"

    from typing import Any

    from packages.valory.skills.abstract_round_abci.models import BaseParams
    from packages.valory.skills.abstract_round_abci.models import (
        BenchmarkTool as BaseBenchmarkTool,
    )
    from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
    from packages.valory.skills.abstract_round_abci.models import (
        SharedState as BaseSharedState,
    )
    from packages.{author}.skills.{skill_name}.rounds import {AbciApp}


    class SharedState(BaseSharedState):
        \"\"\"Keep the current shared state of the skill.\"\"\"

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            \"\"\"Initialize the state.\"\"\"
            super().__init__(*args, abci_app_cls={AbciApp}, **kwargs)


    Params = BaseParams
    Requests = BaseRequests
    BenchmarkTool = BaseBenchmarkTool
    """


@dataclass
class HANDLERS:
    """Template for handlers.py"""

    FILENAME = "handlers.py"

    HEADER = """\
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


@dataclass
class DIALOGUES:
    """Template for dialogues.py"""

    FILENAME = "dialogues.py"

    HEADER = """\
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
    ContractApiDialogues = BaseContractApiDialogues


    TendermintDialogue = BaseTendermintDialogue
    TendermintDialogues = BaseTendermintDialogues
    """
