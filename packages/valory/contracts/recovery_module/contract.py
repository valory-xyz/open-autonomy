# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2025 Valory AG
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

"""This module contains the class to connect to the `RecoveryModule` contract."""


from typing import Any, Dict

from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("valory/recovery_module:0.1.0")


class RecoveryModule(Contract):
    """The RecoveryModule contract"""

    contract_id = PUBLIC_ID

    @classmethod
    def get_recover_access_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        raise_on_try: bool = False,
    ) -> Dict[str, Any]:
        """Get the recover access transaction."""

        tx_params = ledger_api.build_transaction(
            contract_instance=cls.get_instance(
                ledger_api=ledger_api, contract_address=contract_address
            ),
            method_name="recoverAccess",
            method_args={
                "serviceId": service_id,
            },
            tx_args={"sender_address": owner},
            raise_on_try=raise_on_try,
        )

        return tx_params
