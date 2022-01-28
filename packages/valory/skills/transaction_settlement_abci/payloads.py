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

"""This module contains the transaction payloads for common apps."""
import json
from enum import Enum
from typing import Dict, List, Optional, Union

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    VALIDATE = "validate_transaction"
    SIGNATURE = "signature_transaction"
    FINALIZATION = "finalization_transaction"
    RESET = "reset_transaction"
    RANDOMNESS = "randomness_transaction"
    SELECT_KEEPER = "select_keeper_transaction"
    CHECK = "check"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class RandomnessPayload(BaseTxPayload):
    """Represent a transaction payload of type 'randomness'."""

    transaction_type = TransactionType.RANDOMNESS

    def __init__(
        self, sender: str, round_id: int, randomness: str, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param round_id: the round id
        :param randomness: the randomness
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._round_id = round_id
        self._randomness = randomness

    @property
    def round_id(self) -> int:
        """Get the round id."""
        return self._round_id  # pragma: nocover

    @property
    def randomness(self) -> str:
        """Get the randomness."""
        return self._randomness  # pragma: nocover

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(round_id=self._round_id, randomness=self._randomness)


class SelectKeeperPayload(BaseTxPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    transaction_type = TransactionType.SELECT_KEEPER

    def __init__(self, sender: str, keeper: str, id_: Optional[str] = None) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param keeper: the keeper selection
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._keeper = keeper

    @property
    def keeper(self) -> str:
        """Get the keeper."""
        return self._keeper

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(keeper=self.keeper)


class ValidatePayload(BaseTxPayload):
    """Represent a transaction payload of type 'validate'."""

    transaction_type = TransactionType.VALIDATE

    def __init__(
        self,
        sender: str,
        is_settled: Optional[bool] = None,
        transfers: Optional[List] = None,
        tx_result: Optional[str] = None,
        id_: Optional[str] = None,
    ) -> None:
        """Initialize an 'validate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param is_settled: boolean to check whether the transaction is settled
        :param transfers: the transfer events
        :param tx_result: a stringified dict containing is_settled and transfers
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)

        if tx_result:
            tx_data = json.loads(tx_result)
            self._is_settled = tx_data["is_settled"]
            self._transfers = tx_data["transfers"]
        else:
            self._is_settled = is_settled
            self._transfers = transfers

    @property
    def vote(self) -> Optional[bool]:
        """Get the vote."""
        return self._is_settled

    @property
    def transfers(self) -> Optional[List]:
        """Get the transfers."""
        return self._transfers

    @property
    def tx_result(self) -> Optional[str]:
        """Get the tx result."""
        return json.dumps(dict(is_settled=self.vote, transfers=self.transfers))

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(tx_result=self.tx_result)


class CheckTransactionHistoryPayload(BaseTxPayload):
    """Represent a transaction payload of type 'check'."""

    transaction_type = TransactionType.CHECK

    def __init__(
        self,
        sender: str,
        verified_res: str,
        id_: Optional[str] = None,
    ) -> None:
        """Initialize an 'validate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param verified_res: the vote
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._verified_res = verified_res

    @property
    def verified_res(self) -> str:
        """Get the verified result."""
        return self._verified_res

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(verified_res=self.verified_res)


class SignaturePayload(BaseTxPayload):
    """Represent a transaction payload of type 'signature'."""

    transaction_type = TransactionType.SIGNATURE

    def __init__(self, sender: str, signature: str, id_: Optional[str] = None) -> None:
        """Initialize an 'signature' transaction payload.

        :param sender: the sender (Ethereum) address
        :param signature: the signature
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._signature = signature

    @property
    def signature(self) -> str:
        """Get the signature."""
        return self._signature

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(signature=self.signature)


class FinalizationTxPayload(BaseTxPayload):
    """Represent a transaction payload of type 'finalization'."""

    transaction_type = TransactionType.FINALIZATION

    def __init__(
        self,
        sender: str,
        tx_data: Optional[Dict[str, Union[str, int, None]]] = None,
        id_: Optional[str] = None,
    ) -> None:
        """Initialize an 'finalization' transaction payload.

        :param sender: the sender (Ethereum) address
        :param tx_data: the transaction data
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._tx_data = tx_data

    @property
    def tx_data(self) -> Optional[Dict[str, Union[str, int, None]]]:
        """Get the tx_data."""
        return self._tx_data

    @property
    def data(self) -> Dict[str, Dict[str, Union[str, int, None]]]:
        """Get the data."""
        return dict(tx_data=self._tx_data) if self._tx_data is not None else {}


class ResetPayload(BaseTxPayload):
    """Represent a transaction payload of type 'reset'."""

    transaction_type = TransactionType.RESET

    def __init__(
        self, sender: str, period_count: int, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'rest' transaction payload.

        :param sender: the sender (Ethereum) address
        :param period_count: the period count id
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._period_count = period_count

    @property
    def period_count(self) -> int:
        """Get the period_count."""
        return self._period_count

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(period_count=self.period_count)
