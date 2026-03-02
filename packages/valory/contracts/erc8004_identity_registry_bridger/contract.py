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

"""This module contains the class to connect to the `ERC8004IdentityRegistryBridger` contract."""

from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi

from autonomy.chain.service import MultiSendOperation

PUBLIC_ID = PublicId.from_str("valory/erc8004_identity_registry_bridger:0.1.0")


class ERC8004IdentityRegistryBridgerContract(Contract):
    """The ERC8004IdentityRegistryBridger contract"""

    contract_id = PUBLIC_ID

    @classmethod
    def get_set_agent_wallet_tx_data(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        deadline: int,
    ) -> dict:
        """Get transaction data for setAgentWallet call.

        Args:
            ledger_api: LedgerApi instance
            contract_address: Identity Registry Bridger contract address
            deadline: Deadline timestamp

        Returns:
            Transaction dict with to, data, operation, value
        """
        instance = cls.get_instance(
            ledger_api=ledger_api,
            contract_address=contract_address,
        )

        txd = instance.encode_abi(
            abi_element_identifier="setAgentWallet",
            args=[deadline, "0x"],
        )

        return {
            "to": contract_address,
            "data": txd[2:],
            "operation": MultiSendOperation.CALL,
            "value": 0,
        }
