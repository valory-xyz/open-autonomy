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

"""This module contains the transaction payloads for the oracle deployment app."""

from typing import Dict, Optional

from packages.valory.skills.common_apps.payloads import (
    BaseCommonAppsPayload,
    TransactionType,
)


class DeployOraclePayload(BaseCommonAppsPayload):
    """Represent a transaction payload of type 'deploy_oracle'."""

    transaction_type = TransactionType.DEPLOY_ORACLE

    def __init__(
        self, sender: str, oracle_contract_address: str, id_: Optional[str] = None
    ) -> None:
        """Initialize a 'deploy_safe' transaction payload.

        :param sender: the sender (Ethereum) address
        :param oracle_contract_address: the Safe contract address
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._oracle_contract_address = oracle_contract_address

    @property
    def oracle_contract_address(self) -> str:
        """Get the Oracle contract address."""
        return self._oracle_contract_address

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(oracle_contract_address=self.oracle_contract_address)
