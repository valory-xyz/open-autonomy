# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""This module contains the class to connect to the `PolySafeCreatorWithRecoveryModule` contract."""


from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/poly_safe_creator_with_recovery_module:0.1.0")


class PolySafeCreatorWithRecoveryModule(Contract):
    """The PolySafeCreatorWithRecoveryModule contract"""

    contract_id = PUBLIC_ID

    @classmethod
    def get_poly_safe_create_transaction_hash(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
    ) -> bytes:
        """Get the create transaction hash."""
        contract_instance = cls.get_instance(
            ledger_api=ledger_api, contract_address=contract_address
        )
        return contract_instance.functions.getPolySafeCreateTransactionHash().call()

    @classmethod
    def get_enable_module_transaction_hash(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        signer_address: str,
    ) -> bytes:
        """Get the enable module transaction hash for a given signer (Poly Safe owner)."""
        contract_instance = cls.get_instance(
            ledger_api=ledger_api, contract_address=contract_address
        )
        return contract_instance.functions.getEnableModuleTransactionHash(
            signer_address
        ).call()
