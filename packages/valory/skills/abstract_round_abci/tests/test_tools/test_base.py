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

"""Tests for abstract_round_abci/test_tools/base.py"""

from enum import Enum
from typing import Any, Dict, cast

import pytest
from aea.mail.base import Envelope

from packages.valory.connections.ledger.connection import (
    PUBLIC_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviours import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    DummyContext,
    FSMBehaviourBaseCase,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci import PUBLIC_ID
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours import (
    DummyRoundBehaviour,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.models import (
    SharedState,
)
from packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds import (
    Event,
    SynchronizedData,
)
from packages.valory.skills.abstract_round_abci.tests.test_tools.base import (
    FSMBehaviourTestToolSetup,
)


class TestFSMBehaviourBaseCaseSetup(FSMBehaviourTestToolSetup):
    """test TestFSMBehaviourBaseCaseSetup setup"""

    test_cls = FSMBehaviourBaseCase

    @pytest.mark.parametrize("kwargs", [{}])
    def test_setup_fails_without_path(self, kwargs: Dict[str, Dict[str, Any]]) -> None:
        """Test setup"""
        with pytest.raises(ValueError):
            self.test_cls.setup_class(**kwargs)

    @pytest.mark.parametrize("kwargs", [{}, {"param_overrides": {"new_p": None}}])
    def test_setup(self, kwargs: Dict[str, Dict[str, Any]]) -> None:
        """Test setup"""

        self.set_path_to_skill()
        test_instance = self.setup_test_cls(**kwargs)
        assert test_instance
        assert hasattr(test_instance.behaviour.context.params, "new_p") == bool(kwargs)

    @pytest.mark.parametrize("behaviour", DummyRoundBehaviour.behaviours)
    def test_fast_forward_to_behaviour(self, behaviour: BaseBehaviour) -> None:
        """Test fast_forward_to_behaviour"""
        self.set_path_to_skill()
        test_instance = self.setup_test_cls()

        skill = test_instance._skill  # pylint: disable=protected-access
        round_behaviour = skill.skill_context.behaviours.main
        behaviour_id = behaviour.behaviour_id
        synchronized_data = SynchronizedData(
            AbciAppDB(setup_data=dict(participants=[tuple("abcd")]))
        )

        test_instance.fast_forward_to_behaviour(
            behaviour=round_behaviour,
            behaviour_id=behaviour_id,
            synchronized_data=synchronized_data,
        )

        current_behaviour = test_instance.behaviour.current_behaviour
        assert current_behaviour is not None
        assert isinstance(
            current_behaviour.synchronized_data,
            SynchronizedData,
        )
        assert current_behaviour.behaviour_id == behaviour.behaviour_id
        assert (  # pylint: disable=protected-access
            test_instance.skill.skill_context.state.round_sequence.abci_app._current_round_cls
            == current_behaviour.matching_round
            == behaviour.matching_round
        )

    @pytest.mark.parametrize("event", Event)
    @pytest.mark.parametrize("set_none", [False, True])
    def test_end_round(self, event: Enum, set_none: bool) -> None:
        """Test end_round"""

        self.set_path_to_skill()
        test_instance = self.setup_test_cls()
        current_behaviour = cast(
            BaseBehaviour, test_instance.behaviour.current_behaviour
        )
        abci_app = current_behaviour.context.state.round_sequence.abci_app
        if set_none:
            test_instance.behaviour.current_behaviour = None
        assert abci_app.current_round_height == 0
        test_instance.end_round(event)
        assert abci_app.current_round_height == 1 - int(set_none)

    def test_mock_ledger_api_request(self) -> None:
        """Test mock_ledger_api_request"""

        self.set_path_to_skill()
        test_instance = self.setup_test_cls()

        request_kwargs = dict(performative=LedgerApiMessage.Performative.GET_BALANCE)
        response_kwargs = dict(performative=LedgerApiMessage.Performative.BALANCE)
        with pytest.raises(
            AssertionError,
            match="Invalid number of messages in outbox. Expected 1. Found 0.",
        ):
            test_instance.mock_ledger_api_request(request_kwargs, response_kwargs)

        message = LedgerApiMessage(**request_kwargs, dialogue_reference=("a", "b"))  # type: ignore
        envelope = Envelope(
            to=str(LEDGER_CONNECTION_PUBLIC_ID),
            sender=str(PUBLIC_ID),
            protocol_specification_id=LedgerApiMessage.protocol_specification_id,
            message=message,
        )
        multiplexer = test_instance._multiplexer  # pylint: disable=protected-access
        multiplexer.out_queue.put_nowait(envelope)
        test_instance.mock_ledger_api_request(request_kwargs, response_kwargs)

    def test_mock_contract_api_request(self) -> None:
        """Test mock_contract_api_request"""

        self.set_path_to_skill()
        test_instance = self.setup_test_cls()

        contract_id = "dummy_contract"
        request_kwargs = dict(performative=ContractApiMessage.Performative.GET_STATE)
        response_kwargs = dict(performative=ContractApiMessage.Performative.STATE)
        with pytest.raises(
            AssertionError,
            match="Invalid number of messages in outbox. Expected 1. Found 0.",
        ):
            test_instance.mock_contract_api_request(
                contract_id, request_kwargs, response_kwargs
            )

        message = ContractApiMessage(
            **request_kwargs,  # type: ignore
            dialogue_reference=("a", "b"),
            ledger_id="ethereum",
            contract_id=contract_id
        )
        envelope = Envelope(
            to=str(LEDGER_CONNECTION_PUBLIC_ID),
            sender=str(PUBLIC_ID),
            protocol_specification_id=ContractApiMessage.protocol_specification_id,
            message=message,
        )
        multiplexer = test_instance._multiplexer  # pylint: disable=protected-access
        multiplexer.out_queue.put_nowait(envelope)
        test_instance.mock_contract_api_request(
            contract_id, request_kwargs, response_kwargs
        )


def test_dummy_context_is_abstract_component() -> None:
    """Test dummy context is abstract component"""

    shared_state = SharedState(name="dummy_shared_state", skill_context=DummyContext())
    assert shared_state.context.is_abstract_component
