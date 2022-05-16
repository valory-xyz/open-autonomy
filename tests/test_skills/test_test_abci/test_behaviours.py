# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Tests for valory/test_abci skill's behaviours."""
from copy import copy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Type, cast

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.valory.skills.abstract_round_abci.base import (
    BasePeriodState,
    BaseTxPayload,
    StateDB,
    _MetaPayload,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.test_abci.behaviours import (
    DummyBehaviour,
    TestAbciConsensusBehaviour,
)
from packages.valory.skills.test_abci.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)

from tests.conftest import ROOT_DIR


class AbciFSMBehaviourBaseCase(BaseSkillTestCase):
    """Base case for testing FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "test_abci")

    test_abci_behaviour: TestAbciConsensusBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]
    period_state: BasePeriodState
    benchmark_dir: TemporaryDirectory

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        # we need to store the current value of the meta-class attribute
        # _MetaPayload.transaction_type_to_payload_cls, and restore it
        # in the teardown function. We do a shallow copy so we avoid
        # to modify the old mapping during the execution of the tests.
        cls.old_tx_type_to_payload_cls = copy(
            _MetaPayload.transaction_type_to_payload_cls
        )
        _MetaPayload.transaction_type_to_payload_cls = {}
        super().setup()
        assert cls._skill.skill_context._agent_context is not None
        cls._skill.skill_context._agent_context.identity._default_address_key = (
            "ethereum"
        )
        cls._skill.skill_context._agent_context._default_ledger_id = "ethereum"
        cls.test_abci_behaviour = cast(
            TestAbciConsensusBehaviour,
            cls._skill.skill_context.behaviours.main,
        )

        cls.test_abci_behaviour.setup()
        cls._skill.skill_context.state.setup()
        cls._skill.skill_context.state.period.end_sync()

        assert (
            cast(BaseState, cls.test_abci_behaviour.current_state).state_id
            == cls.test_abci_behaviour.initial_state_cls.state_id
        )
        cls.period_state = BasePeriodState(StateDB(initial_period=0, initial_data={}))

    def fast_forward_to_state(
        self,
        behaviour: AbstractRoundBehaviour,
        state_id: str,
        period_state: BasePeriodState,
    ) -> None:
        """Fast forward the FSM to a state."""
        next_state = {s.state_id: s for s in behaviour.behaviour_states}[state_id]
        assert next_state is not None, f"State {state_id} not found"
        next_state = cast(Type[BaseState], next_state)
        behaviour.current_state = next_state(
            name=next_state.state_id, skill_context=behaviour.context
        )
        self.skill.skill_context.state.period.abci_app._round_results.append(
            period_state
        )
        self.skill.skill_context.state.period.abci_app._extend_previous_rounds_with_current_round()
        self.skill.skill_context.behaviours.main._last_round_height = (
            self.skill.skill_context.state.period.abci_app.current_round_height
        )
        self.skill.skill_context.state.period.abci_app._current_round = (
            next_state.matching_round(
                period_state, self.skill.skill_context.params.consensus_params
            )
        )

    @classmethod
    def teardown(cls) -> None:
        """Teardown the test class."""
        _MetaPayload.transaction_type_to_payload_cls = cls.old_tx_type_to_payload_cls  # type: ignore


class TestDummyBehaviour(AbciFSMBehaviourBaseCase):
    """Test case to test DummyBehaviour."""

    def test_run(self) -> None:
        """Test registration."""
        self.fast_forward_to_state(
            self.test_abci_behaviour,
            DummyBehaviour.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.test_abci_behaviour.current_state),
            ).state_id
            == DummyBehaviour.state_id
        )
        self.test_abci_behaviour.act_wrapper()
        assert self.test_abci_behaviour.current_state is None
