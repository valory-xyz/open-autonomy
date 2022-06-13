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
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    BaseSynchronizedData,
    BaseTxPayload,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
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
from tests.test_skills.base import FSMBehaviourBaseCase


class AbciFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing FSMBehaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "test_abci")

    test_abci_behaviour: TestAbciConsensusBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]
    synchronized_data: BaseSynchronizedData
    benchmark_dir: TemporaryDirectory


class TestDummyBehaviour(AbciFSMBehaviourBaseCase):
    """Test case to test DummyBehaviour."""

    def test_run(self) -> None:
        """Test registration."""
        self.synchronized_data = BaseSynchronizedData(AbciAppDB(setup_data={}))

        self.fast_forward_to_behaviour(
            self.behaviour,
            DummyBehaviour.behaviour_id,
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == DummyBehaviour.behaviour_id
        )
        self.behaviour.act_wrapper()
        assert self.behaviour.current_behaviour is None
