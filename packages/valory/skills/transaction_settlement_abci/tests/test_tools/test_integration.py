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
from aea.exceptions import AEAActException

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
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.skills.transaction_settlement_abci.behaviours import FinalizeBehaviour


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

    def test_send_tx(self):
        """Test send tx"""

        test_instance = self.instantiate_test()

        nonce, gas_price = 0, {"maxPriorityFeePerGas": 0, "maxFeePerGas": 0}
        behaviour = cast(FinalizeBehaviour, test_instance.behaviour.current_behaviour)
        behaviour.params.gas_price = gas_price
        behaviour.params.nonce = nonce

        new_callable = lambda: lambda *x, **__: (
            ContractApiMessage(
            performative=ContractApiMessage.Performative.RAW_TRANSACTION,
            raw_transaction=ContractApiMessage.RawTransaction(
                ledger_id="", body={"nonce": str(nonce), **gas_price}
            ),
            ),
            None,
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                transaction_digest=LedgerApiMessage.TransactionDigest(ledger_id="", body=""),
            )
        )
        with mock.patch.object(test_instance, "process_n_messages", new_callable=new_callable):
            test_instance.send_tx()

    def test_validate_tx(self):
        """Test validate_tx"""

        test_instance = self.instantiate_test()
        test_instance.tx_settlement_synchronized_data.db.update(tx_hashes_history="a"*64)

        new_callable = lambda: lambda *x, **__: (
            None,
            ContractApiMessage(
                performative=ContractApiMessage.Performative.STATE,
                state=ContractApiMessage.State(
                    ledger_id="", body={"verified": True},
                ),
            ),
        )
        with mock.patch.object(test_instance, "process_n_messages", new_callable=new_callable):
            test_instance.validate_tx()

    def test_validate_tx_timeout(self):
        """Test validate_tx timeout"""

        test_instance = self.instantiate_test()
        synchronized_data = test_instance.tx_settlement_synchronized_data
        assert synchronized_data.missed_messages == 0
        test_instance.validate_tx(simulate_timeout=True)
        assert synchronized_data.missed_messages == 1

    def test_validate_tx_failure(self):
        """Test validate tx failure"""

        test_instance = self.instantiate_test()

        with pytest.raises(AEAActException, match="FSM design error: tx hash should exist"):
            test_instance.validate_tx()
