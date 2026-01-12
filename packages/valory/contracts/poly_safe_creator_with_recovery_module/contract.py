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

import eth_abi
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import Crypto, LedgerApi


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

    @classmethod
    def get_service_manager_deploy_data(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        crypto: Crypto,
    ) -> bytes:
        """
        Get the `data` parameter required for the ServiceManager contract `deploy` function.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param crypto: Crypto instance holding the Safe owner private key.
        :return: Hex-encoded ABI payload (`0x...`) containing the `data` payload.
        """

        # Poly Safe deployment data requires two (legacy) signatures by the safe owner packed in a specific format:
        # - Signature 1: Poly Safe creation signature
        # - Signature 2: Enable recovery module signature
        #
        # See deploy function at https://github.com/valory-xyz/autonolas-registries/blob/main/contracts/ServiceManager.sol#L310
        # See contract at https://github.com/valory-xyz/autonolas-registries/blob/main/contracts/multisigs/PolySafeCreatorWithRecoveryModule.sol
        # See example test at https://github.com/valory-xyz/autonolas-registries/blob/main/test/PolySafeCreatorWithRecoveryModule.t.sol#L49

        create_transaction_hash = cls.get_poly_safe_create_transaction_hash(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )

        sig1 = crypto.sign_message(
            create_transaction_hash,
            is_deprecated_mode=True,  # Legacy signature, do not use EIP-191 signing
        )
        sig1_bytes = bytes.fromhex(sig1[2:])

        enable_module_hash = cls.get_enable_module_transaction_hash(
            ledger_api=ledger_api,
            contract_address=contract_address,
            signer_address=crypto.address,
        )
        sig2 = crypto.sign_message(
            enable_module_hash,
            is_deprecated_mode=True,  # Legacy signature, do not use EIP-191 signing
        )
        sig2_bytes = bytes.fromhex(sig2[2:])

        # Pack both signatures in the format required by PolySafeCreatorWithRecoveryModule.create(...)
        r1 = sig1_bytes[0:32]
        s1 = sig1_bytes[32:64]
        v1 = sig1_bytes[64]
        data = eth_abi.encode(
            ["(uint8,bytes32,bytes32)", "bytes"], [(v1, r1, s1), sig2_bytes]
        )

        return data
