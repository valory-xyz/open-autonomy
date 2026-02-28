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

"""This module contains the class to connect to the `ERC8004IdentityRegistry` contract."""

from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from eth_abi import encode
from web3 import Web3

PUBLIC_ID = PublicId.from_str("valory/erc8004_identity_registry:0.1.0")


class ERC8004IdentityRegistryContract(Contract):
    """The ERC8004IdentityRegistry contract"""

    contract_id = PUBLIC_ID

    @classmethod
    def compute_eip712_agent_wallet_set_digest(  # pylint: disable=too-many-locals
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        agent_id: int,
        new_wallet: str,
        identity_registry_bridger_address: str,
        deadline: int,
    ) -> str:
        """Compute EIP-712 digest for AgentWalletSet message.

        Args:
            ledger_api: LedgerApi instance
            contract_address: Identity Registry contract address
            agent_id: Agent ID
            new_wallet: New wallet address (service Safe)
            identity_registry_bridger_address: Identity Registry Bridger contract address
            deadline: Deadline timestamp

        Returns:
            Digest as hex string (without 0x prefix)
        """
        # Type hashes
        EIP712DOMAIN_TYPEHASH = Web3.keccak(
            text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
        )
        AGENT_WALLET_SET_TYPEHASH = Web3.keccak(
            text="AgentWalletSet(uint256 agentId,address newWallet,address owner,uint256 deadline)"
        )

        # Get IR domain info
        instance = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )

        domain = instance.functions.eip712Domain().call()
        name = domain[1]
        version = domain[2]
        chain_id = domain[3]

        # Compute struct hash
        struct_hash = Web3.keccak(
            encode(
                ["bytes32", "uint256", "address", "address", "uint256"],
                [
                    AGENT_WALLET_SET_TYPEHASH,
                    agent_id,
                    Web3.to_checksum_address(new_wallet),
                    Web3.to_checksum_address(identity_registry_bridger_address),
                    deadline,
                ],
            )
        )

        # Compute domain separator
        domain_separator = Web3.keccak(
            encode(
                ["bytes32", "bytes32", "bytes32", "uint256", "address"],
                [
                    EIP712DOMAIN_TYPEHASH,
                    Web3.keccak(text=name),
                    Web3.keccak(text=version),
                    chain_id,
                    Web3.to_checksum_address(contract_address),
                ],
            )
        )

        # Compute digest
        digest = ledger_api.api.solidity_keccak(
            ["string", "bytes32", "bytes32"],
            ["\x19\x01", domain_separator, struct_hash],
        )

        return digest.hex()
