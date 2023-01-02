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

from typing import cast

import pytest

from packages.valory.skills.transaction_settlement_abci.test_tools.integration import (
    _SafeConfiguredHelperIntegration,
    _GnosisHelperIntegration,
    _TxHelperIntegration,
)
from packages.valory.connections.ledger.tests.conftest import make_ledger_api_connection

from packages.valory.skills.abstract_round_abci.tests.test_tools.base import FSMBehaviourTestToolSetup
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TxSettlementSynchronizedSata,
)
from pathlib import Path
from packages.valory.skills import transaction_settlement_abci
from unittest import mock


class Test_SafeConfiguredHelperIntegration(FSMBehaviourTestToolSetup):
    """Test_SafeConfiguredHelperIntegration"""

    test_cls = _SafeConfiguredHelperIntegration

    def test_instantiation(self):
        """"""

        self.set_path_to_skill()
        self.test_cls.make_ledger_api_connection_callable = make_ledger_api_connection
        test_instance = cast(_SafeConfiguredHelperIntegration, self.setup_test_cls())

        assert test_instance.keeper_address in test_instance.safe_owners


class Test_GnosisHelperIntegration(FSMBehaviourTestToolSetup):
    """Test_SafeConfiguredHelperIntegration"""

    test_cls = _GnosisHelperIntegration

    def test_instantiation(self):
        """"""

        self.set_path_to_skill()
        self.test_cls.make_ledger_api_connection_callable = make_ledger_api_connection
        test_instance = cast(_GnosisHelperIntegration, self.setup_test_cls())

        assert test_instance.safe_contract_address
        assert test_instance.gnosis_instance
        assert test_instance.ethereum_api


class Test_TxHelperIntegration(FSMBehaviourTestToolSetup):
    """Test_SafeConfiguredHelperIntegration"""

    test_cls = _TxHelperIntegration

    def instantiate_test(self):
        """"""

        path_to_skill = Path(transaction_settlement_abci.__file__).parent
        self.set_path_to_skill(path_to_skill=path_to_skill)
        self.test_cls.make_ledger_api_connection_callable = make_ledger_api_connection

        db = AbciAppDB(setup_data={})
        self.test_cls.tx_settlement_synchronized_data = TxSettlementSynchronizedSata(db)

        test_instance = cast(_TxHelperIntegration, self.setup_test_cls())
        return test_instance

    def test_sign_tx(self):
        """Test sign_tx"""

        test_instance = self.instantiate_test()
        most_voted_tx_hash = "a" * 234
        test_instance.tx_settlement_synchronized_data.db.update(most_voted_tx_hash=most_voted_tx_hash)

        target = test_instance.gnosis_instance.functions.getOwners
        new_callable = lambda: lambda: test_instance.safe_owners
        with mock.patch.object(target, "call", new_callable=new_callable):
            test_instance.sign_tx()

    def test_sign_tx_failure(self):
        """Test sign_tx failure"""

        test_instance = self.instantiate_test()
        most_voted_tx_hash = "a" * 234
        test_instance.tx_settlement_synchronized_data.db.update(most_voted_tx_hash=most_voted_tx_hash)
        target = test_instance.gnosis_instance.functions.getOwners
        with mock.patch.object(target, "call", new_callable=lambda: lambda: {}):
            with pytest.raises(AssertionError):
                test_instance.sign_tx()
