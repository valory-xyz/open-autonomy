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

"""Tests for valory/transaction settlement skill's payload tools."""

# pylint: skip-file

import sys

import pytest

from packages.valory.contracts.gnosis_safe.contract import SafeOperation
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    NULL_ADDRESS,
    PayloadDeserializationError,
    VerificationStatus,
    hash_payload_to_hex,
    skill_input_hex_to_payload,
    tx_hist_hex_to_payload,
    tx_hist_payload_to_hex,
)


try:
    import atheris  # type: ignore
except (ImportError, ModuleNotFoundError):
    pytestmark = pytest.mark.skip


class TestTxHistPayloadEncodingDecoding:
    """Tests for the transaction history's payload encoding - decoding."""

    @staticmethod
    @pytest.mark.parametrize(
        "verification_status, tx_hash",
        (
            (
                VerificationStatus.VERIFIED,
                "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
            ),
            (VerificationStatus.ERROR, None),
        ),
    )
    def test_tx_hist_payload_to_hex_and_back(
        verification_status: VerificationStatus, tx_hash: str
    ) -> None:
        """Test `tx_hist_payload_to_hex` and `tx_hist_hex_to_payload` functions."""
        intermediate = tx_hist_payload_to_hex(verification_status, tx_hash)
        verification_status_, tx_hash_ = tx_hist_hex_to_payload(intermediate)
        assert verification_status == verification_status_
        assert tx_hash == tx_hash_

    @staticmethod
    def test_invalid_tx_hash_during_serialization() -> None:
        """Test encoding when transaction hash is invalid."""
        with pytest.raises(ValueError):
            tx_hist_payload_to_hex(VerificationStatus.VERIFIED, "")

    @staticmethod
    @pytest.mark.parametrize(
        "payload",
        ("0000000000000000000000000000000000000000000000000000000000000007", ""),
    )
    def test_invalid_payloads_during_deserialization(payload: str) -> None:
        """Test decoding payload is invalid."""
        with pytest.raises(PayloadDeserializationError):
            tx_hist_hex_to_payload(payload)


def test_payload_to_hex_and_back() -> None:
    """Test `payload_to_hex` function."""
    tx_params = dict(
        safe_tx_hash="b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
        ether_value=0,
        safe_tx_gas=40000000,
        to_address="0x77E9b2EF921253A171Fa0CB9ba80558648Ff7215",
        data=b"b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
        operation=SafeOperation.CALL.value,
        base_gas=0,
        safe_gas_price=0,
        gas_token=NULL_ADDRESS,
        refund_receiver=NULL_ADDRESS,
    )

    intermediate = hash_payload_to_hex(**tx_params)  # type: ignore
    assert tx_params == skill_input_hex_to_payload(intermediate)


@pytest.mark.skip
def test_fuzz_tx_hist_payload_to_hex() -> None:
    """Test fuzz tx_hist_payload_to_hex."""

    @atheris.instrument_func
    def fuzz_tx_hist_payload_to_hex(input_bytes: bytes) -> None:
        """Fuzz tx_hist_payload_to_hex."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        verification_int = fdp.ConsumeInt(4)
        if verification_int < 1 or verification_int > 6:
            return
        verification = VerificationStatus(verification_int)
        tx_hash = fdp.ConsumeString(12)
        if len(tx_hash) != 64:
            return
        tx_hist_payload_to_hex(verification, tx_hash)

    atheris.instrument_all()
    atheris.Setup(sys.argv, fuzz_tx_hist_payload_to_hex)
    atheris.Fuzz()


@pytest.mark.skip
def test_fuzz_tx_hist_hex_to_payload() -> None:
    """Test fuzz tx_hist_hex_to_payload."""

    @atheris.instrument_func
    def fuzz_tx_hist_hex_to_payload(input_bytes: bytes) -> None:
        """Fuzz tx_hist_hex_to_payload."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        try:
            payload = fdp.ConsumeString(12)
            tx_hist_hex_to_payload(payload)
        except PayloadDeserializationError:
            pass

    atheris.instrument_all()
    atheris.Setup(sys.argv, fuzz_tx_hist_hex_to_payload)
    atheris.Fuzz()


@pytest.mark.skip
def test_fuzz_hash_payload_to_hex() -> None:
    """Test fuzz hash_payload_to_hex."""

    @atheris.instrument_func
    def fuzz_hash_payload_to_hex(input_bytes: bytes) -> None:
        """Fuzz hash_payload_to_hex."""
        fdp = atheris.FuzzedDataProvider(input_bytes)

        safe_tx_hash = fdp.ConsumeString(64)
        ether_value = fdp.ConsumeInt(4)
        safe_tx_gas = fdp.ConsumeInt(4)
        to_address = fdp.ConsumeString(42)
        data = fdp.ConsumeBytes(12)
        operation = fdp.ConsumeInt(4)
        base_gas = fdp.ConsumeInt(4)
        safe_gas_price = fdp.ConsumeInt(4)

        if len(safe_tx_hash) != 64:
            return

        if len(to_address) != 42:
            return

        hash_payload_to_hex(
            safe_tx_hash,
            ether_value,
            safe_tx_gas,
            to_address,
            data,
            operation,
            base_gas,
            safe_gas_price,
        )

    atheris.instrument_all()
    atheris.Setup(sys.argv, fuzz_hash_payload_to_hex)
    atheris.Fuzz()


@pytest.mark.skip
def test_fuzz_skill_input_hex_to_payload() -> None:
    """Test fuzz skill_input_hex_to_payload."""

    @atheris.instrument_func
    def fuzz_skill_input_hex_to_payload(input_bytes: bytes) -> None:
        """Fuzz skill_input_hex_to_payload."""
        fdp = atheris.FuzzedDataProvider(input_bytes)
        payload = fdp.ConsumeString(500)
        if len(payload) < 500:
            return
        try:
            skill_input_hex_to_payload(payload)
        except TypeError:
            pass

    atheris.instrument_all()
    atheris.Setup(sys.argv, fuzz_skill_input_hex_to_payload)
    atheris.Fuzz()
