# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024-2025 Valory AG
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

"""This module contains the class to connect to the `StakingActivityChecker` contract."""

from enum import Enum

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


class StakingActivityCheckerContract(Contract):
    """The Staking Activity Checker contract."""

    contract_id = PublicId.from_str("valory/staking_activity_checker:0.1.0")

    @classmethod
    def liveness_ratio(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> JSONLike:
        """Retrieve the liveness ratio."""
        contract = cls.get_instance(ledger_api, contract_address)
        liveness_ratio = contract.functions.livenessRatio().call()
        return dict(data=liveness_ratio)

    @classmethod
    def get_multisig_nonces(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        multisig: str,
    ) -> JSONLike:
        """Retrieve the nonces for a given multisig address."""
        contract = cls.get_instance(ledger_api, contract_address)
        nonces = contract.functions.getMultisigNonces(multisig).call()
        return dict(data=nonces)
