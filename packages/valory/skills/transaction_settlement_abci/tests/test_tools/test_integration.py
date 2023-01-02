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

from packages.valory.skills.transaction_settlement_abci.test_tools.integration import (
    _SafeConfiguredHelperIntegration,
    _GnosisHelperIntegration,
)
from packages.valory.connections.ledger.tests.conftest import make_ledger_api_connection

from packages.valory.skills.abstract_round_abci.tests.test_tools.base import FSMBehaviourTestToolSetup


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
