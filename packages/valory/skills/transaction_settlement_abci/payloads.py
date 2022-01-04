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

"""This module contains the transaction payloads for common apps."""
from enum import Enum
from typing import Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    VALIDATE = "validate_transaction"
    SIGNATURE = "signature_transaction"
    FINALIZATION = "finalization_transaction"
    RESET = "reset_transaction"
    RANDOMNESS = "randomness_transaction"
    SELECT_KEEPER = "select_keeper_transaction"
    GAS = "gas"

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


class GasPayload(BaseTxPayload):
    """Represent a transaction payload of type 'gas_adjustment'."""

    transaction_type = TransactionType.GAS

    def __init__(
        self,
        sender: str,
        safe_tx_gas: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        id_: Optional[str] = None,
    ) -> None:
        """Initialize an 'validate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param safe_tx_gas: the safe_tx_gas
        :param max_fee_per_gas: the max_fee_per_gas
        :param max_priority_fee_per_gas: the max_priority_fee_per_gas
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._safe_tx_gas = safe_tx_gas
        self._max_fee_per_gas = max_fee_per_gas
        self._max_priority_fee_per_gas = max_priority_fee_per_gas

    @property
    def safe_tx_gas(self) -> Optional[int]:
        """Get the safe_tx_gas."""
        return self._safe_tx_gas

    @property
    def max_fee_per_gas(self) -> Optional[int]:
        """Get the max_fee_per_gas."""
        return self._max_fee_per_gas

    @property
    def max_priority_fee_per_gas(self) -> Optional[int]:
        """Get the max_priority_fee_per_gas."""
        return self._max_priority_fee_per_gas

    @property
    def data(self) -> Dict:
        """Get the data."""
        return (
            dict(
                safe_tx_gas=self.safe_tx_gas,
                max_fee_per_gas=self.max_fee_per_gas,
                max_priority_fee_per_gas=self.max_priority_fee_per_gas,
            )
            if (
                self.safe_tx_gas is not None
                and self.max_fee_per_gas is not None
                and self.max_priority_fee_per_gas is not None
            )
            else {}
        )


class ValidatePayload(BaseTxPayload):
    """Represent a transaction payload of type 'validate'."""

    transaction_type = TransactionType.VALIDATE

    def __init__(
        self, sender: str, vote: Optional[bool] = None, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'validate' transaction payload.

        :param sender: the sender (Ethereum) address
        :param vote: the vote
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._vote = vote

    @property
    def vote(self) -> Optional[bool]:
        """Get the vote."""
        return self._vote

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(vote=self.vote) if self.vote is not None else {}


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
        self, sender: str, tx_hash: Optional[str] = None, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'finalization' transaction payload.

        :param sender: the sender (Ethereum) address
        :param tx_hash: the 'safe' transaction hash
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._tx_hash = tx_hash

    @property
    def tx_hash(self) -> Optional[str]:
        """Get the signature."""
        return self._tx_hash

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(tx_hash=self.tx_hash) if self.tx_hash is not None else {}


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
