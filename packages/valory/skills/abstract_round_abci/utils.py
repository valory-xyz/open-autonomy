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

"""This module contains utility functions for the 'abstract_round_abci' skill."""
from decimal import Decimal
from hashlib import sha256
from typing import Dict, Optional, Tuple, Union, cast

from eth_typing.bls import BLSPubkey, BLSSignature
from py_ecc.bls import G2Basic as bls  # type: ignore


MAX_UINT64 = 2 ** 64 - 1


class VerifyDrand:  # pylint: disable=too-few-public-methods
    """
    Tool to verify Randomness retrieved from various external APIs.

    The ciphersuite used is BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_

    cryptographic-specification section in https://drand.love/docs/specification/
    https://github.com/ethereum/py_ecc
    """

    @classmethod
    def _int_to_bytes_big(cls, value: int) -> bytes:
        """Convert int to bytes."""
        if value < 0 or value > MAX_UINT64:
            raise ValueError(
                "VerifyDrand can only handle positive numbers representable with 8 bytes"
            )
        return int.to_bytes(value, 8, byteorder="big", signed=False)

    @classmethod
    def _verify_randomness_hash(cls, randomness: bytes, signature: bytes) -> bool:
        """Verify randomness hash."""
        return sha256(signature).digest() == randomness

    @classmethod
    def _verify_signature(
        cls,
        pubkey: Union[BLSPubkey, bytes],
        message: bytes,
        signature: Union[BLSSignature, bytes],
    ) -> bool:
        """Verify randomness signature."""
        return bls.Verify(
            cast(BLSPubkey, pubkey), message, cast(BLSSignature, signature)
        )

    def verify(self, data: Dict, pubkey: str) -> Tuple[bool, Optional[str]]:
        """
        Verify drand value retried from external APIs.

        :param data: dictionary containing drand parameters.
        :param pubkey: league of entropy public key
                       public-endpoints section in https://drand.love/developer/http-api/
        :returns: bool, error message
        """

        encoded_pubkey = bytes.fromhex(pubkey)
        try:
            randomness = data["randomness"]
            signature = data["signature"]
            round_value = int(data["round"])
        except KeyError as e:
            return False, f"DRAND dict is missing value for {e}"

        previous_signature = data.pop("previous_signature", "")
        encoded_randomness = bytes.fromhex(randomness)
        encoded_signature = bytes.fromhex(signature)
        int_encoded_round = self._int_to_bytes_big(round_value)
        encoded_previous_signature = bytes.fromhex(previous_signature)

        if not self._verify_randomness_hash(encoded_randomness, encoded_signature):
            return False, "Failed randomness hash check."

        msg_b = encoded_previous_signature + int_encoded_round
        msg_hash_b = sha256(msg_b).digest()

        if not self._verify_signature(encoded_pubkey, msg_hash_b, encoded_signature):
            return False, "Failed bls.Verify check."

        return True, None


def to_int(most_voted_estimate: float, decimals: int) -> int:
    """Convert to int."""
    most_voted_estimate_ = str(most_voted_estimate)
    decimal_places = most_voted_estimate_[::-1].find(".")
    if decimal_places > decimals:
        most_voted_estimate_ = most_voted_estimate_[: -(decimal_places - decimals)]
    most_voted_estimate_decimal = Decimal(most_voted_estimate_)
    int_value = int(most_voted_estimate_decimal * (10 ** decimals))
    return int_value
