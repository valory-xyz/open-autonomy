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

"""Integration tests for various transaction settlement skill's failure modes."""

from pathlib import Path
from typing import Any

from aea_test_autonomy.fixture_helpers import HardHatAMMBaseTest
from aea_test_autonomy.helpers.contracts import get_register_contract

from packages.valory.skills.abstract_round_abci.test_tools.integration import (
    _HarHatHelperIntegration,
)
from packages.valory.skills.transaction_settlement_abci.test_tools.integration import (
    _TxHelperIntegration,
)


# pylint: disable=protected-access,too-many-ancestors,unbalanced-tuple-unpacking,too-many-locals,consider-using-with,unspecified-encoding,too-many-arguments,unidiomatic-typecheck


class AMMIntegrationBaseCase(
    _TxHelperIntegration, _HarHatHelperIntegration, HardHatAMMBaseTest
):
    """Base test class for integration tests in a Hardhat environment, with AMM interaction."""

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        # register all contracts we need
        directory = Path(
            cls.ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_router_02"
        )
        _ = get_register_contract(directory)
        directory = Path(
            cls.ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_erc20"
        )
        _ = get_register_contract(directory)
        directory = Path(cls.ROOT_DIR, "packages", "valory", "contracts", "multisend")
        _ = get_register_contract(directory)
