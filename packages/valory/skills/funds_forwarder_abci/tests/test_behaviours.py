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

"""Tests for FundsForwarderBehaviour."""

from typing import Any
from unittest.mock import MagicMock, patch

from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.skills.funds_forwarder_abci.behaviours import (
    ETHER_VALUE,
    FundsForwarderBehaviour,
    FundsForwarderRoundBehaviour,
)
from packages.valory.skills.funds_forwarder_abci.models import ZERO_ADDRESS
from packages.valory.skills.funds_forwarder_abci.rounds import (
    FundsForwarderAbciApp,
    FundsForwarderRound,
)

AGENT_ADDRESS = "0x1234567890123456789012345678901234567890"
OWNER_ADDRESS = "0xOwner567890123456789012345678901234567890"
SAFE_ADDRESS = "0xSafe5678901234567890123456789012345678901"
TOKEN_ADDRESS = "0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d"


def _make_gen(return_value: Any) -> Any:
    """Create a no-yield generator returning the given value."""

    def gen(*args: Any, **kwargs: Any) -> Any:
        return return_value
        yield  # noqa: unreachable

    return gen


def _exhaust_gen(gen: Any) -> Any:
    """Exhaust a generator and return its value."""
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value


def _make_behaviour(
    token_limits: Any = None,
    expected_owner: str = OWNER_ADDRESS,
) -> FundsForwarderBehaviour:
    """Create a FundsForwarderBehaviour with mocked context."""
    context_mock = MagicMock()
    context_mock.logger = MagicMock()
    context_mock.params = MagicMock()
    context_mock.state.round_sequence = MagicMock()
    context_mock.benchmark_tool = MagicMock()
    context_mock.agent_address = AGENT_ADDRESS
    context_mock.params.expected_service_owner_address = expected_owner
    context_mock.params.funds_forwarder_token_config = (
        token_limits if token_limits is not None else {}
    )
    context_mock.params.multisend_address = "0xMultisend"
    return FundsForwarderBehaviour(name="test", skill_context=context_mock)


def _sync_data_mock(
    service_owner: str = OWNER_ADDRESS,
    safe_address: str = SAFE_ADDRESS,
) -> Any:
    """Create a synchronized_data property mock."""
    return lambda: property(
        lambda self: MagicMock(
            service_owner=service_owner,
            safe_contract_address=safe_address,
        )
    )


class TestFundsForwarderBehaviour:
    """Test FundsForwarderBehaviour."""

    def test_matching_round(self) -> None:
        """Test matching_round is correctly set."""
        b = _make_behaviour()
        assert b.matching_round == FundsForwarderRound

    def test_get_tx_hash_zero_owner(self) -> None:
        """Test _get_tx_hash when service owner is zero address."""
        b = _make_behaviour()
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(service_owner=ZERO_ADDRESS),
        ):
            gen = b._get_tx_hash()
            result = _exhaust_gen(gen)
        assert result is None

    def test_get_tx_hash_empty_owner(self) -> None:
        """Test _get_tx_hash when service owner is empty string."""
        b = _make_behaviour()
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(service_owner=""),
        ):
            gen = b._get_tx_hash()
            result = _exhaust_gen(gen)
        assert result is None

    def test_get_tx_hash_owner_mismatch(self) -> None:
        """Test _get_tx_hash when owner does not match expected."""
        b = _make_behaviour(expected_owner="0xDifferentOwner")
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ):
            gen = b._get_tx_hash()
            result = _exhaust_gen(gen)
        assert result is None

    def test_get_tx_hash_no_token_limits(self) -> None:
        """Test _get_tx_hash when token limits is empty."""
        b = _make_behaviour(token_limits={})
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ):
            gen = b._get_tx_hash()
            result = _exhaust_gen(gen)
        assert result is None

    def test_get_tx_hash_no_excess(self) -> None:
        """Test _get_tx_hash when no token exceeds threshold."""
        b = _make_behaviour(
            token_limits={
                TOKEN_ADDRESS: {"retain_balance": 10**18, "max_transfer": 10**17}
            }
        )
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_build_transfer_txs", new=_make_gen([])
        ):
            gen = b._get_tx_hash()
            result = _exhaust_gen(gen)
        assert result is None

    def test_get_tx_hash_single_tx(self) -> None:
        """Test _get_tx_hash with a single transfer."""
        b = _make_behaviour(
            token_limits={
                TOKEN_ADDRESS: {"retain_balance": 10**18, "max_transfer": 10**17}
            }
        )
        tx = {"to": OWNER_ADDRESS, "value": 10**17, "data": b"\x01"}
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_build_transfer_txs", new=_make_gen([tx])
        ), patch.object(
            b, "_get_safe_tx_hash", new=_make_gen("abcdef")
        ), patch(
            "packages.valory.skills.funds_forwarder_abci.behaviours.hash_payload_to_hex",
            return_value="0xpayload",
        ):
            gen = b._get_tx_hash()
            result = _exhaust_gen(gen)
        assert result == "0xpayload"

    def test_get_tx_hash_single_tx_safe_hash_none(self) -> None:
        """Test _get_tx_hash when safe tx hash fails for single tx."""
        b = _make_behaviour(
            token_limits={
                TOKEN_ADDRESS: {"retain_balance": 10**18, "max_transfer": 10**17}
            }
        )
        tx = {"to": OWNER_ADDRESS, "value": 10**17, "data": b"\x01"}
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_build_transfer_txs", new=_make_gen([tx])
        ), patch.object(
            b, "_get_safe_tx_hash", new=_make_gen(None)
        ):
            gen = b._get_tx_hash()
            result = _exhaust_gen(gen)
        assert result is None

    def test_get_tx_hash_multisend(self) -> None:
        """Test _get_tx_hash with multiple transfers."""
        b = _make_behaviour(
            token_limits={
                ZERO_ADDRESS: {"retain_balance": 10**18, "max_transfer": 10**17},
                TOKEN_ADDRESS: {"retain_balance": 10**18, "max_transfer": 10**17},
            }
        )
        txs = [
            {"to": OWNER_ADDRESS, "value": 10**17, "data": b""},
            {"to": TOKEN_ADDRESS, "value": 0, "data": b"\x01"},
        ]
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_build_transfer_txs", new=_make_gen(txs)
        ), patch.object(
            b, "_to_multisend", new=_make_gen("0xmultisend")
        ):
            gen = b._get_tx_hash()
            result = _exhaust_gen(gen)
        assert result == "0xmultisend"

    def test_get_native_balance_success(self) -> None:
        """Test _get_native_balance success."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = LedgerApiMessage.Performative.STATE
        mock_response.state.body = {"get_balance_result": 5 * 10**18}

        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "get_ledger_api_response", new=_make_gen(mock_response)
        ):
            gen = b._get_native_balance()
            result = _exhaust_gen(gen)
        assert result == 5 * 10**18

    def test_get_native_balance_error(self) -> None:
        """Test _get_native_balance when ledger API fails."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = LedgerApiMessage.Performative.ERROR

        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "get_ledger_api_response", new=_make_gen(mock_response)
        ):
            gen = b._get_native_balance()
            result = _exhaust_gen(gen)
        assert result is None

    def test_get_erc20_balance_success(self) -> None:
        """Test _get_erc20_balance success."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.STATE
        mock_response.state.body = {"token": 10 * 10**18}

        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_response)
        ):
            gen = b._get_erc20_balance(TOKEN_ADDRESS)
            result = _exhaust_gen(gen)
        assert result == 10 * 10**18

    def test_get_erc20_balance_error(self) -> None:
        """Test _get_erc20_balance when contract call fails."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.ERROR

        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_response)
        ):
            gen = b._get_erc20_balance(TOKEN_ADDRESS)
            result = _exhaust_gen(gen)
        assert result is None

    def test_build_erc20_transfer_success(self) -> None:
        """Test _build_erc20_transfer success."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.STATE
        mock_response.state.body = {"data": "0xabcdef"}

        with patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_response)
        ):
            gen = b._build_erc20_transfer(TOKEN_ADDRESS, OWNER_ADDRESS, 10**17)
            result = _exhaust_gen(gen)
        assert result == bytes.fromhex("abcdef")

    def test_build_erc20_transfer_error(self) -> None:
        """Test _build_erc20_transfer when contract call fails."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.ERROR

        with patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_response)
        ):
            gen = b._build_erc20_transfer(TOKEN_ADDRESS, OWNER_ADDRESS, 10**17)
            result = _exhaust_gen(gen)
        assert result is None

    def test_build_transfer_txs_native_excess(self) -> None:
        """Test _build_transfer_txs with native token above threshold."""
        b = _make_behaviour(
            token_limits={
                ZERO_ADDRESS: {"retain_balance": 10**18, "max_transfer": 5 * 10**17}
            }
        )
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_get_native_balance", new=_make_gen(3 * 10**18)
        ):
            gen = b._build_transfer_txs(OWNER_ADDRESS)
            result = _exhaust_gen(gen)
        assert len(result) == 1
        assert result[0]["to"] == OWNER_ADDRESS
        assert result[0]["value"] == 5 * 10**17  # min(max_transfer, excess)
        assert result[0]["data"] == b""

    def test_build_transfer_txs_erc20_excess(self) -> None:
        """Test _build_transfer_txs with ERC20 above threshold."""
        b = _make_behaviour(
            token_limits={
                TOKEN_ADDRESS: {"retain_balance": 10**18, "max_transfer": 5 * 10**17}
            }
        )
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_get_erc20_balance", new=_make_gen(3 * 10**18)
        ), patch.object(
            b, "_build_erc20_transfer", new=_make_gen(b"\x01\x02")
        ):
            gen = b._build_transfer_txs(OWNER_ADDRESS)
            result = _exhaust_gen(gen)
        assert len(result) == 1
        assert result[0]["to"] == TOKEN_ADDRESS
        assert result[0]["value"] == ETHER_VALUE
        assert result[0]["data"] == b"\x01\x02"

    def test_build_transfer_txs_below_threshold(self) -> None:
        """Test _build_transfer_txs when balance is below retain."""
        b = _make_behaviour(
            token_limits={
                TOKEN_ADDRESS: {"retain_balance": 10**18, "max_transfer": 5 * 10**17}
            }
        )
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_get_erc20_balance", new=_make_gen(5 * 10**17)
        ):
            gen = b._build_transfer_txs(OWNER_ADDRESS)
            result = _exhaust_gen(gen)
        assert len(result) == 0

    def test_build_transfer_txs_balance_none(self) -> None:
        """Test _build_transfer_txs when balance check fails."""
        b = _make_behaviour(
            token_limits={
                TOKEN_ADDRESS: {"retain_balance": 10**18, "max_transfer": 5 * 10**17}
            }
        )
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_get_erc20_balance", new=_make_gen(None)
        ):
            gen = b._build_transfer_txs(OWNER_ADDRESS)
            result = _exhaust_gen(gen)
        assert len(result) == 0

    def test_build_transfer_txs_erc20_transfer_fails(self) -> None:
        """Test _build_transfer_txs when ERC20 transfer build fails."""
        b = _make_behaviour(
            token_limits={
                TOKEN_ADDRESS: {"retain_balance": 10**18, "max_transfer": 5 * 10**17}
            }
        )
        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "_get_erc20_balance", new=_make_gen(3 * 10**18)
        ), patch.object(
            b, "_build_erc20_transfer", new=_make_gen(None)
        ):
            gen = b._build_transfer_txs(OWNER_ADDRESS)
            result = _exhaust_gen(gen)
        assert len(result) == 0

    def test_get_safe_tx_hash_success(self) -> None:
        """Test _get_safe_tx_hash success."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.STATE
        mock_response.state.body = {"tx_hash": "0xabcdef1234"}

        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_response)
        ):
            gen = b._get_safe_tx_hash("0xto", b"\x01")
            result = _exhaust_gen(gen)
        assert result == "abcdef1234"

    def test_get_safe_tx_hash_error(self) -> None:
        """Test _get_safe_tx_hash when contract call fails."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.ERROR

        with patch.object(
            type(b),
            "synchronized_data",
            new_callable=_sync_data_mock(),
        ), patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_response)
        ):
            gen = b._get_safe_tx_hash("0xto", b"\x01")
            result = _exhaust_gen(gen)
        assert result is None

    def test_to_multisend_error(self) -> None:
        """Test _to_multisend when multisend compilation fails."""
        b = _make_behaviour()
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.ERROR

        with patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_response)
        ):
            txs = [{"to": OWNER_ADDRESS, "value": 10**17}]
            gen = b._to_multisend(txs)
            result = _exhaust_gen(gen)
        assert result is None

    def test_to_multisend_safe_hash_none(self) -> None:
        """Test _to_multisend when safe tx hash fails."""
        b = _make_behaviour()
        mock_ms_response = MagicMock()
        mock_ms_response.performative = (
            ContractApiMessage.Performative.RAW_TRANSACTION
        )
        mock_ms_response.raw_transaction.body = {"data": "0xaabb"}

        with patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_ms_response)
        ), patch.object(
            b, "_get_safe_tx_hash", new=_make_gen(None)
        ):
            txs = [{"to": OWNER_ADDRESS, "value": 10**17}]
            gen = b._to_multisend(txs)
            result = _exhaust_gen(gen)
        assert result is None

    def test_to_multisend_success(self) -> None:
        """Test _to_multisend success."""
        b = _make_behaviour()
        mock_ms_response = MagicMock()
        mock_ms_response.performative = (
            ContractApiMessage.Performative.RAW_TRANSACTION
        )
        mock_ms_response.raw_transaction.body = {"data": "0xaabb"}

        with patch.object(
            b, "get_contract_api_response", new=_make_gen(mock_ms_response)
        ), patch.object(
            b, "_get_safe_tx_hash", new=_make_gen("safehash")
        ), patch(
            "packages.valory.skills.funds_forwarder_abci.behaviours.hash_payload_to_hex",
            return_value="0xfinal",
        ):
            txs = [{"to": OWNER_ADDRESS, "value": 10**17}]
            gen = b._to_multisend(txs)
            result = _exhaust_gen(gen)
        assert result == "0xfinal"

    def test_async_act_with_tx(self) -> None:
        """Test async_act when tx_hash is not None."""
        b = _make_behaviour()
        with patch.object(
            b, "_get_tx_hash", new=_make_gen("0xtxhash")
        ), patch.object(
            b, "send_a2a_transaction", new=_make_gen(None)
        ), patch.object(
            b, "wait_until_round_end", new=_make_gen(None)
        ), patch.object(
            b, "set_done"
        ) as mock_set_done:
            gen = b.async_act()
            _exhaust_gen(gen)
            mock_set_done.assert_called_once()

    def test_async_act_without_tx(self) -> None:
        """Test async_act when tx_hash is None."""
        b = _make_behaviour()
        with patch.object(
            b, "_get_tx_hash", new=_make_gen(None)
        ), patch.object(
            b, "send_a2a_transaction", new=_make_gen(None)
        ), patch.object(
            b, "wait_until_round_end", new=_make_gen(None)
        ), patch.object(
            b, "set_done"
        ) as mock_set_done:
            gen = b.async_act()
            _exhaust_gen(gen)
            mock_set_done.assert_called_once()


class TestFundsForwarderBaseBehaviour:
    """Test base behaviour properties."""

    def test_synchronized_data_property(self) -> None:
        """Test synchronized_data property returns cast SynchronizedData."""
        b = _make_behaviour()
        mock_sync = MagicMock()
        with patch(
            "packages.valory.skills.abstract_round_abci.behaviours.BaseBehaviour.synchronized_data",
            new_callable=lambda: property(lambda self: mock_sync),
        ):
            result = b.synchronized_data
        assert result == mock_sync


class TestFundsForwarderRoundBehaviour:
    """Test FundsForwarderRoundBehaviour."""

    def test_initial_behaviour_cls(self) -> None:
        """Test initial_behaviour_cls."""
        assert (
            FundsForwarderRoundBehaviour.initial_behaviour_cls
            is FundsForwarderBehaviour
        )

    def test_abci_app_cls(self) -> None:
        """Test abci_app_cls."""
        assert (
            FundsForwarderRoundBehaviour.abci_app_cls
            is FundsForwarderAbciApp
        )

    def test_behaviours(self) -> None:
        """Test behaviours set."""
        assert FundsForwarderBehaviour in (
            FundsForwarderRoundBehaviour.behaviours
        )
