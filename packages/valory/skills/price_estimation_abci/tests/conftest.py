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

"""Tests for valory/price_estimation_abci skill."""

from typing import Any

from aea_test_autonomy.fixture_helpers import HardHatAMMBaseTest
from aea_test_autonomy.helpers.contracts import get_register_contract

from packages.valory.contracts.offchain_aggregator.tests.test_contract import (
    PACKAGE_DIR as OFFCHAIN_AGGREGATOR_PACKAGE,
)
from packages.valory.skills.abstract_round_abci.test_tools.integration import (
    _HarHatHelperIntegration,
)
from packages.valory.skills.transaction_settlement_abci.test_tools.integration import (
    _TxHelperIntegration,
)


class GnosisIntegrationBaseCase(  # pylint: disable=too-many-ancestors
    _TxHelperIntegration, _HarHatHelperIntegration, HardHatAMMBaseTest
):
    """Base test class for integration tests in a Hardhat environment, with Gnosis deployed."""

    # TODO change this class to use the `HardHatGnosisBaseTest` instead of `HardHatAMMBaseTest`.

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup_class()

        # register offchain aggregator contract
        _ = get_register_contract(OFFCHAIN_AGGREGATOR_PACKAGE)
