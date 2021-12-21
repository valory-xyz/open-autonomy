# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains the transaction payloads for the safe deployment app."""

from typing import Dict, Optional

from packages.valory.skills.common_apps.payloads import (
    BaseCommonAppsPayload,
    TransactionType,
)


class DeploySafePayload(BaseCommonAppsPayload):
    """Represent a transaction payload of type 'deploy_safe'."""

    transaction_type = TransactionType.DEPLOY_SAFE

    def __init__(
        self, sender: str, safe_contract_address: str, id_: Optional[str] = None
    ) -> None:
        """Initialize a 'deploy_safe' transaction payload.

        :param sender: the sender (Ethereum) address
        :param safe_contract_address: the Safe contract address
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._safe_contract_address = safe_contract_address

    @property
    def safe_contract_address(self) -> str:
        """Get the Safe contract address."""
        return self._safe_contract_address

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(safe_contract_address=self.safe_contract_address)
