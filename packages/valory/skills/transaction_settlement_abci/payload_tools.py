# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Tools for payload serialization and deserialization."""

from enum import Enum
from typing import Any, Optional, Tuple

from packages.valory.contracts.gnosis_safe.contract import SafeOperation


NULL_ADDRESS: str = "0x" + "0" * 40
MAX_UINT256 = 2 ** 256 - 1


class VerificationStatus(Enum):
    """Tx verification status enumeration."""

    VERIFIED = 1
    NOT_VERIFIED = 2
    INVALID_PAYLOAD = 3
    PENDING = 4
    ERROR = 5
    INSUFFICIENT_FUNDS = 6


class PayloadDeserializationError(Exception):
    """Exception for payload deserialization errors."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception.

        :param args: extra arguments to pass to the constructor of `Exception`.
        """
        msg: str = "Cannot decode provided payload!"
        if not args:
            args = (msg,)

        super().__init__(*args)


def tx_hist_payload_to_hex(
    verification: VerificationStatus, tx_hash: Optional[str] = None
) -> str:
    """Serialise history payload to a hex string."""
    if tx_hash is None:
        tx_hash = ""
    else:
        tx_hash = tx_hash[2:] if tx_hash.startswith("0x") else tx_hash
        if len(tx_hash) != 64:
            raise ValueError("Cannot encode tx_hash of non-32 bytes")
    verification_ = verification.value.to_bytes(32, "big").hex()
    concatenated = verification_ + tx_hash
    return concatenated


def tx_hist_hex_to_payload(payload: str) -> Tuple[VerificationStatus, Optional[str]]:
    """Decode history payload."""
    if len(payload) != 64 and len(payload) != 64 * 2:
        raise PayloadDeserializationError()

    verification_value = int.from_bytes(bytes.fromhex(payload[:64]), "big")

    try:
        verification_status = VerificationStatus(verification_value)
    except ValueError as e:
        raise PayloadDeserializationError(str(e)) from e

    if len(payload) == 64:
        return verification_status, None

    return verification_status, "0x" + payload[64:]


def hash_payload_to_hex(  # pylint: disable=too-many-arguments, too-many-locals
    safe_tx_hash: str,
    ether_value: int,
    safe_tx_gas: int,
    to_address: str,
    data: bytes,
    operation: int = SafeOperation.CALL.value,
    base_gas: int = 0,
    safe_gas_price: int = 0,
    gas_token: str = NULL_ADDRESS,
    refund_receiver: str = NULL_ADDRESS,
) -> str:
    """Serialise to a hex string."""
    if len(safe_tx_hash) != 64:  # should be exactly 32 bytes!
        raise ValueError(
            "cannot encode safe_tx_hash of non-32 bytes"
        )  # pragma: nocover

    if len(to_address) != 42 or len(gas_token) != 42 or len(refund_receiver) != 42:
        raise ValueError("cannot encode address of non 42 length")  # pragma: nocover

    if (
        ether_value > MAX_UINT256
        or safe_tx_gas > MAX_UINT256
        or base_gas > MAX_UINT256
        or safe_gas_price > MAX_UINT256
    ):
        raise ValueError(
            "Value is bigger than the max 256 bit value"
        )  # pragma: nocover

    if operation not in [v.value for v in SafeOperation]:
        raise ValueError("SafeOperation value is not valid")  # pragma: nocover

    ether_value_ = ether_value.to_bytes(32, "big").hex()
    safe_tx_gas_ = safe_tx_gas.to_bytes(32, "big").hex()
    operation_ = operation.to_bytes(1, "big").hex()
    base_gas_ = base_gas.to_bytes(32, "big").hex()
    safe_gas_price_ = safe_gas_price.to_bytes(32, "big").hex()

    concatenated = (
        safe_tx_hash
        + ether_value_
        + safe_tx_gas_
        + to_address
        + operation_
        + base_gas_
        + safe_gas_price_
        + gas_token
        + refund_receiver
        + data.hex()
    )
    return concatenated


def skill_input_hex_to_payload(payload: str) -> dict:
    """Decode payload."""
    if len(payload) < 234:
        raise PayloadDeserializationError()  # pragma: nocover
    tx_params = dict(
        safe_tx_hash=payload[:64],
        ether_value=int.from_bytes(bytes.fromhex(payload[64:128]), "big"),
        safe_tx_gas=int.from_bytes(bytes.fromhex(payload[128:192]), "big"),
        to_address=payload[192:234],
        operation=int.from_bytes(bytes.fromhex(payload[234:236]), "big"),
        base_gas=int.from_bytes(bytes.fromhex(payload[236:300]), "big"),
        safe_gas_price=int.from_bytes(bytes.fromhex(payload[300:364]), "big"),
        gas_token=payload[364:406],
        refund_receiver=payload[406:448],
        data=bytes.fromhex(payload[448:]),
    )
    return tx_params
