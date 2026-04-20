# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Tests for PolySafeCreatorWithRecoveryModule contract."""

# pylint: skip-file

from unittest.mock import MagicMock, patch

import pytest

from packages.valory.contracts.poly_safe_creator_with_recovery_module.contract import (
    POLYGON_CHAIN_ID,
    PolySafeCreatorWithRecoveryModule,
    _validate_hash_bytes,
)

# --- _validate_hash_bytes tests ---


class TestValidateHashBytes:
    """Test the _validate_hash_bytes helper."""

    def test_valid_32_bytes(self) -> None:
        """Test that 32 bytes passes validation."""
        valid = b"\x00" * 32
        assert _validate_hash_bytes(valid) == valid

    def test_not_bytes(self) -> None:
        """Test that non-bytes raises ValueError."""
        with pytest.raises(ValueError, match="expected bytes"):
            _validate_hash_bytes(42)

    def test_wrong_length(self) -> None:
        """Test that wrong-length bytes raises ValueError."""
        with pytest.raises(ValueError, match="expected 32 bytes, got 16"):
            _validate_hash_bytes(b"\x00" * 16)

    def test_empty_bytes(self) -> None:
        """Test that empty bytes raises ValueError."""
        with pytest.raises(ValueError, match="expected 32 bytes, got 0"):
            _validate_hash_bytes(b"")

    def test_string_rejected(self) -> None:
        """Test that a string is rejected."""
        with pytest.raises(ValueError, match="expected bytes"):
            _validate_hash_bytes("0x" + "00" * 32)


# --- Contract method tests ---


def _mock_ledger_api(chain_id: int = POLYGON_CHAIN_ID) -> MagicMock:
    """Create a mock LedgerApi with a configurable chain_id."""
    api = MagicMock()
    api.api.eth.chain_id = chain_id
    api.api.to_checksum_address = lambda addr: addr
    api.api.codec.encode = MagicMock(return_value=b"\x00" * 64)
    return api


def _mock_contract_instance(
    create_hash: object = b"\x01" * 32,
    enable_hash: object = b"\x02" * 32,
) -> MagicMock:
    """Create a mock contract instance with configurable return values."""
    instance = MagicMock()
    instance.functions.getPolySafeCreateTransactionHash.return_value.call.return_value = (
        create_hash
    )
    instance.functions.getEnableModuleTransactionHash.return_value.call.return_value = (
        enable_hash
    )
    return instance


class TestGetPolySafeCreateTransactionHash:
    """Test get_poly_safe_create_transaction_hash."""

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_valid_hash(self, mock_get_instance: MagicMock) -> None:
        """Test happy path with valid 32-byte hash."""
        expected = b"\xab" * 32
        mock_get_instance.return_value = _mock_contract_instance(create_hash=expected)
        result = (
            PolySafeCreatorWithRecoveryModule.get_poly_safe_create_transaction_hash(
                ledger_api=_mock_ledger_api(),
                contract_address="0x1234",
            )
        )
        assert result["hash_bytes"] == expected

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_invalid_hash_type(self, mock_get_instance: MagicMock) -> None:
        """Test that non-bytes return raises ValueError."""
        mock_get_instance.return_value = _mock_contract_instance(create_hash=123)
        with pytest.raises(ValueError, match="expected bytes"):
            PolySafeCreatorWithRecoveryModule.get_poly_safe_create_transaction_hash(
                ledger_api=_mock_ledger_api(),
                contract_address="0x1234",
            )

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_invalid_hash_length(self, mock_get_instance: MagicMock) -> None:
        """Test that wrong-length bytes raises ValueError."""
        mock_get_instance.return_value = _mock_contract_instance(
            create_hash=b"\x00" * 20
        )
        with pytest.raises(ValueError, match="expected 32 bytes, got 20"):
            PolySafeCreatorWithRecoveryModule.get_poly_safe_create_transaction_hash(
                ledger_api=_mock_ledger_api(),
                contract_address="0x1234",
            )


class TestGetEnableModuleTransactionHash:
    """Test get_enable_module_transaction_hash."""

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_valid_hash(self, mock_get_instance: MagicMock) -> None:
        """Test happy path with valid 32-byte hash."""
        expected = b"\xcd" * 32
        mock_get_instance.return_value = _mock_contract_instance(enable_hash=expected)
        result = PolySafeCreatorWithRecoveryModule.get_enable_module_transaction_hash(
            ledger_api=_mock_ledger_api(),
            contract_address="0x1234",
            signer_address="0x5678",
        )
        assert result["hash_bytes"] == expected

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_invalid_hash_type(self, mock_get_instance: MagicMock) -> None:
        """Test that non-bytes return raises ValueError."""
        mock_get_instance.return_value = _mock_contract_instance(enable_hash="bad")
        with pytest.raises(ValueError, match="expected bytes"):
            PolySafeCreatorWithRecoveryModule.get_enable_module_transaction_hash(
                ledger_api=_mock_ledger_api(),
                contract_address="0x1234",
                signer_address="0x5678",
            )

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_invalid_hash_length(self, mock_get_instance: MagicMock) -> None:
        """Test that wrong-length bytes raises ValueError."""
        mock_get_instance.return_value = _mock_contract_instance(
            enable_hash=b"\x00" * 10
        )
        with pytest.raises(ValueError, match="expected 32 bytes, got 10"):
            PolySafeCreatorWithRecoveryModule.get_enable_module_transaction_hash(
                ledger_api=_mock_ledger_api(),
                contract_address="0x1234",
                signer_address="0x5678",
            )


class TestGetServiceManagerDeployData:
    """Test get_service_manager_deploy_data."""

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_wrong_chain_id(self, mock_get_instance: MagicMock) -> None:
        """Test that non-Polygon chain_id raises ValueError."""
        mock_get_instance.return_value = _mock_contract_instance()
        ledger_api = _mock_ledger_api(chain_id=1)  # Ethereum mainnet
        crypto = MagicMock()
        with pytest.raises(ValueError, match="Chain ID mismatch"):
            PolySafeCreatorWithRecoveryModule.get_service_manager_deploy_data(
                ledger_api=ledger_api,
                contract_address="0x1234",
                crypto=crypto,
            )

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_happy_path(self, mock_get_instance: MagicMock) -> None:
        """Test happy path returns data_bytes."""
        mock_get_instance.return_value = _mock_contract_instance()
        ledger_api = _mock_ledger_api(chain_id=POLYGON_CHAIN_ID)

        # mock crypto.sign_message to return a valid 65-byte hex signature
        sig_hex = "0x" + "ab" * 65
        crypto = MagicMock()
        crypto.sign_message.return_value = sig_hex
        crypto.address = "0xOwner"

        result = PolySafeCreatorWithRecoveryModule.get_service_manager_deploy_data(
            ledger_api=ledger_api,
            contract_address="0x1234",
            crypto=crypto,
        )
        assert "data_bytes" in result
        assert crypto.sign_message.call_count == 2  # two signatures

    @patch.object(PolySafeCreatorWithRecoveryModule, "get_instance")
    def test_polygon_chain_id_accepted(self, mock_get_instance: MagicMock) -> None:
        """Test that Polygon chain ID (137) is accepted."""
        mock_get_instance.return_value = _mock_contract_instance()
        ledger_api = _mock_ledger_api(chain_id=137)
        sig_hex = "0x" + "00" * 65
        crypto = MagicMock()
        crypto.sign_message.return_value = sig_hex
        crypto.address = "0xOwner"

        # should not raise
        result = PolySafeCreatorWithRecoveryModule.get_service_manager_deploy_data(
            ledger_api=ledger_api,
            contract_address="0x1234",
            crypto=crypto,
        )
        assert "data_bytes" in result
