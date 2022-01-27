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

from enum import Enum, auto
from typing import Any, Optional, Tuple


class VerificationStatus(Enum):
    """Tx verification status enumeration."""

    VERIFIED = auto()
    NOT_VERIFIED = auto()
    INVALID_PAYLOAD = auto()
    ERROR = auto()


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
    elif len(tx_hash) != 64:  # should be exactly 32 bytes!
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

    return verification_status, payload[64:]


def skill_input_hex_to_payload(payload: str) -> Tuple[str, int, int, str, bytes]:
    """Decode payload."""
    if len(payload) < 234:
        raise PayloadDeserializationError()  # pragma: nocover
    tx_hash = payload[:64]
    ether_value = int.from_bytes(bytes.fromhex(payload[64:128]), "big")
    safe_tx_gas = int.from_bytes(bytes.fromhex(payload[128:192]), "big")
    to_address = payload[192:234]
    data = bytes.fromhex(payload[234:])
    return tx_hash, ether_value, safe_tx_gas, to_address, data
