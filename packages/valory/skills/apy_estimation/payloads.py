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

"""This module contains the transaction payloads for the APY estimation app."""
from typing import Dict, Optional

import pandas as pd

from packages.valory.skills.simple_abci.payloads import BaseSimpleAbciPayload
from packages.valory.skills.simple_abci.payloads import (
    TransactionType as BaseTransactionType,
)


class TransactionType(BaseTransactionType):
    """Enumeration of transaction types."""

    TRANSFORMATION = "transformation"


class TransformationPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'transformation'."""

    transaction_type = TransactionType.TRANSFORMATION

    def __init__(
        self, sender: str, transformation: pd.DataFrame, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'rest' transaction payload.

        :param sender: the sender (Ethereum) address
        :param transformation: the transformation of the observations.
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._transformation = transformation

    @property
    def transformation(self) -> pd.DataFrame:
        """Get the transformation."""
        return self._transformation

    @property
    def data(self) -> Dict:
        """Get the data."""
        return {"transformation": self.transformation}
