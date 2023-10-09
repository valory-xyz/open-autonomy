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

"""Templates for FSM components"""

from dataclasses import dataclass


@dataclass
class ROUNDS:
    """Template for rounds.py"""

    FILENAME = "rounds.py"

    HEADER = """\
    \"\"\"This package contains the rounds of {AbciApp}.\"\"\"

    from enum import Enum
    from typing import Dict, FrozenSet, List, Optional, Set, Tuple

    from packages.valory.skills.abstract_round_abci.base import (
        AbciApp,
        AbciAppTransitionFunction,
        AbstractRound,
        AppState,
        BaseSynchronizedData,
        DegenerateRound,
        EventToTimeout,
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

        payload_class = {PayloadCls}
        payload_attribute = ""  # TODO: update
        synchronized_data_class = SynchronizedData

        {todo_abstract_round_cls}

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

    """

    ABCI_APP_CLS = """\
    class {AbciApp}(AbciApp[Event]):
        \"\"\"{AbciApp}\"\"\"

        initial_round_cls: AppState = {initial_round_cls}
        initial_states: Set[AppState] = {initial_states}
        transition_function: AbciAppTransitionFunction = {transition_function}
        final_states: Set[AppState] = {final_states}
        event_to_timeout: EventToTimeout = {{}}
        cross_period_persisted_keys: FrozenSet[str] = frozenset()
        db_pre_conditions: Dict[AppState, Set[str]] = {{
            {db_pre_conditions}
        }}
        db_post_conditions: Dict[AppState, Set[str]] = {{
            {db_post_conditions}
        }}
    """


@dataclass
class BEHAVIOURS:
    """Template for behaviours.py"""

    FILENAME = "behaviours.py"

    HEADER = """\
    \"\"\"This package contains round behaviours of {AbciApp}.\"\"\"

    from abc import ABC
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
    class {BaseBehaviourCls}(BaseBehaviour, ABC):
        \"\"\"Base behaviour for the {skill_name} skill.\"\"\"

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

        matching_round: Type[AbstractRound] = {matching_round}

        # TODO: implement logic required to set payload content for synchronization
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

    from dataclasses import dataclass

    from packages.valory.skills.abstract_round_abci.base import BaseTxPayload

    """

    PAYLOAD_CLS = """\
    @dataclass(frozen=True)
    class {PayloadCls}(BaseTxPayload):
        \"\"\"Represent a transaction payload for the {RoundCls}.\"\"\"

        # TODO: define your attributes

    """


@dataclass
class MODELS:
    """Template for models.py"""

    FILENAME = "models.py"

    HEADER = """\
    \"\"\"This module contains the shared state for the abci skill of {AbciApp}.\"\"\"

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

        abci_app_cls = {AbciApp}


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
        IpfsHandler as BaseIpfsHandler,
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


    ABCIHandler = BaseABCIRoundHandler
    HttpHandler = BaseHttpHandler
    SigningHandler = BaseSigningHandler
    LedgerApiHandler = BaseLedgerApiHandler
    ContractApiHandler = BaseContractApiHandler
    TendermintHandler = BaseTendermintHandler
    IpfsHandler = BaseIpfsHandler
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
        IpfsDialogue as BaseIpfsDialogue,
    )
    from packages.valory.skills.abstract_round_abci.dialogues import (
        IpfsDialogues as BaseIpfsDialogues,
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


    IpfsDialogue = BaseIpfsDialogue
    IpfsDialogues = BaseIpfsDialogues
    """
