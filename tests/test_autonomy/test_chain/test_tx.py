# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2025 Valory AG
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

"""Test tx settlement tool."""

from logging import Logger
from time import sleep
from typing import Any, Callable
from unittest import mock

import pytest
from aea_ledger_ethereum import GAS_STATION
from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.config import ChainType
from autonomy.chain.exceptions import (
    ChainInteractionError,
    ChainTimeoutError,
    RPCError,
    TxSettleError,
    TxVerifyError,
)
from autonomy.chain.tx import ERRORS_TO_RETRY, TxSettler

from tests.test_autonomy.test_chain.base import BaseChainInteractionTest


def _raise_connection_error(*args: Any, **kwargs: Any) -> Any:
    raise RequestsConnectionError("Cannot connect to the given RPC")


def _raise_value_error(*args: Any, **kwargs: Any) -> Any:
    raise ValueError("Some value error")


def test_errors_are_lower_case() -> None:
    """Test errors are lower case."""
    for error in ERRORS_TO_RETRY:
        assert error == error.lower()


@pytest.mark.parametrize(
    "tx_builder, expected_exception, match",
    [
        (_raise_connection_error, RPCError, "Cannot connect to the given RPC"),
        (_raise_value_error, ChainInteractionError, "Some value error"),
    ],
)
def test_rpc_and_chain_error(
    tx_builder: Callable[[], Any], expected_exception: type, match: str
) -> None:
    """Test RPC error."""

    settler = TxSettler(
        ledger_api=mock.Mock(),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
        tx_builder=tx_builder,
    )

    with pytest.raises(expected_exception, match=match):
        settler.transact()


@mock.patch("autonomy.chain.tx.logger")
def test_retriable_exception(logger: Logger) -> None:
    """Test retriable exception."""

    class _retriable_method:
        should_raise = True

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            if self.should_raise:
                self.should_raise = False
                raise Exception("wrong transaction nonce")
            return {}

    settler = TxSettler(
        ledger_api=mock.Mock(
            send_signed_transaction=mock.Mock(return_value="0x123"),
            try_get_gas_pricing=lambda **kwargs: {
                "maxFeePerGas": 100,
                "maxPriorityFeePerGas": 100,
            },
            update_with_gas_estimate=lambda tx: tx,
        ),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
        tx_builder=_retriable_method(),
    )
    settler.transact()
    logger.error.assert_called_with(  # type: ignore[attr-defined]
        "Unexpected error occured when interacting with chain: wrong transaction nonce; will retry in 3.0..."
    )


class _same_repricing_method:
    tx_dict = {
        "maxFeePerGas": 100,
        "maxPriorityFeePerGas": 100,
    }

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.tx_dict


class _increasing_repricing_method:
    retries = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.retries == 0:
            self.retries += 1
            return {
                "maxFeePerGas": 100,
            }
        return {
            "maxFeePerGas": 100,
            "maxPriorityFeePerGas": 100,
        }


@mock.patch("autonomy.chain.tx.logger")
@pytest.mark.parametrize(
    "method", [(_same_repricing_method()), (_increasing_repricing_method())]
)
def test_repricing(
    logger: Logger, method: _same_repricing_method | _increasing_repricing_method
) -> None:
    """Test retriable exception."""

    def _raise_fee_too_low(tx_signed: Any, **kwargs: Any) -> None:
        if tx_signed["maxFeePerGas"] == 110:
            return
        raise ValueError("gas too low: gas 1, minimum needed 21644")

    state = {"first_reprice_call": True}

    def _reprice(**kwargs: Any) -> Any:
        if state["first_reprice_call"]:
            state["first_reprice_call"] = False
            return {"maxFeePerGas": 1, "maxPriorityFeePerGas": 1}
        return {"maxFeePerGas": 110, "maxPriorityFeePerGas": 110}

    settler = TxSettler(
        ledger_api=mock.Mock(
            send_signed_transaction=_raise_fee_too_low,
            try_get_gas_pricing=_reprice,
            update_with_gas_estimate=lambda tx: tx,
        ),
        crypto=mock.Mock(
            sign_transaction=lambda transaction: transaction,
        ),
        chain_type=ChainType.LOCAL,
        tx_builder=method,
    )
    settler.transact()
    logger.warning.assert_called_with(  # type: ignore[attr-defined]
        "Low gas error: gas too low: gas 1, minimum needed 21644; Repricing the transaction..."
    )


@mock.patch("autonomy.chain.tx.already_known")
def test_already_known(mock_already_known: Callable[[], bool]) -> None:
    """Test AlreadyKnown exception."""

    class _method:
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return {}

    class _raise:
        _should_raise = True

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            if self._should_raise:
                self._should_raise = False
                raise Exception("AlreadyKnown")
            return {}

    settler = TxSettler(
        ledger_api=mock.Mock(
            send_signed_transaction=_raise(),
            try_get_gas_pricing=lambda **kwargs: {
                "maxFeePerGas": 100,
                "maxPriorityFeePerGas": 100,
            },
            update_with_gas_estimate=lambda tx: tx,
        ),
        crypto=mock.Mock(
            sign_transaction=lambda transaction: transaction,
        ),
        chain_type=ChainType.LOCAL,
        tx_builder=_method(),
    )
    settler.transact()
    mock_already_known.assert_called_with("AlreadyKnown")  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "error", ("wrong transaction nonce", "OldNonce", "nonce too low")
)
def test_should_rebuild_with_oldnonce(capsys: Any, error: str) -> None:
    """Test OldNonce exception."""

    class _method:
        call_count = 0

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            self.call_count += 1
            return {}

    class _raise:
        _should_raise = True

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            if self._should_raise:
                self._should_raise = False
                raise Exception(error)
            return {}

    builder = _method()
    settler = TxSettler(
        ledger_api=mock.Mock(
            send_signed_transaction=_raise(),
            try_get_gas_pricing=lambda **kwargs: {
                "maxFeePerGas": 100,
                "maxPriorityFeePerGas": 100,
            },
            update_with_gas_estimate=lambda tx: tx,
        ),
        crypto=mock.Mock(
            sign_transaction=lambda transaction: transaction,
        ),
        chain_type=ChainType.LOCAL,
        tx_builder=builder,
    )
    settler.transact()
    assert (
        builder.call_count == 2
    )  # should be 2 since the build method will be called twice


def test_timeout() -> None:
    """Test transact."""

    def _waitable(*arg: Any, **kwargs: Any) -> None:
        sleep(2)

    settler = TxSettler(
        ledger_api=mock.Mock(
            api=mock.Mock(
                eth=mock.Mock(
                    wait_for_transaction_receipt=_waitable,
                )
            )
        ),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
        tx_builder=lambda: None,  # type: ignore[arg-type, return-value]
        sleep=0.1,
        retries=1,
    )

    with pytest.raises(ChainTimeoutError):
        settler.transact()


@mock.patch("autonomy.chain.tx.logger")
def test_settle_waits_until_rpc_syncs(logger: mock.Mock) -> None:
    """Test settler loops until RPC catches up with receipt block."""

    class _LaggingEth:
        def __init__(self, block_sequence: list[int], receipt_block: int) -> None:
            self._blocks = block_sequence
            self.wait_for_transaction_receipt = mock.Mock(
                return_value=mock.Mock(blockNumber=receipt_block)
            )

        @property
        def block_number(self) -> int:
            if len(self._blocks) > 1:
                return self._blocks.pop(0)
            return self._blocks[0]

    receipt_block = 10
    lagging_eth = _LaggingEth(
        block_sequence=[receipt_block - 1, receipt_block], receipt_block=receipt_block
    )
    ledger_api = mock.Mock(api=mock.Mock(eth=lagging_eth))
    settler = TxSettler(
        ledger_api=ledger_api,
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
        tx_builder=lambda: {},
    )
    settler.tx_hash = "0x123"

    with mock.patch("autonomy.chain.tx.time.sleep") as mocked_sleep:
        settler.settle()

    lagging_eth.wait_for_transaction_receipt.assert_called_once_with(
        transaction_hash="0x123",
        timeout=settler.timeout,
        poll_latency=settler.sleep,
    )
    logger.warning.assert_called_once_with(
        f"RPC state not synced with block {receipt_block}. Retrying in {settler.sleep} seconds..."
    )
    mocked_sleep.assert_called_once_with(settler.sleep)


@mock.patch("autonomy.chain.tx.logger")
def test_settle_raises_when_rpc_never_syncs(logger: mock.Mock) -> None:
    """Test settler raises when RPC node never reaches receipt block."""

    class _StuckEth:
        def __init__(self, block_number: int, receipt_block: int) -> None:
            self._block_number = block_number
            self.wait_for_transaction_receipt = mock.Mock(
                return_value=mock.Mock(blockNumber=receipt_block)
            )

        @property
        def block_number(self) -> int:
            return self._block_number

    receipt_block = 10
    stuck_eth = _StuckEth(block_number=receipt_block - 2, receipt_block=receipt_block)
    ledger_api = mock.Mock(api=mock.Mock(eth=stuck_eth))
    settler = TxSettler(
        ledger_api=ledger_api,
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
        tx_builder=lambda: {},
        retries=2,
        sleep=0.01,
    )
    settler.tx_hash = "0x123"

    with mock.patch("autonomy.chain.tx.time.sleep") as mocked_sleep:
        with pytest.raises(ChainTimeoutError, match="RPC node not synced"):
            settler.settle()

    stuck_eth.wait_for_transaction_receipt.assert_called_once()
    assert logger.warning.call_count == settler.retries + 1
    assert mocked_sleep.call_count == settler.retries + 1


def test_programming_errors() -> None:
    """Test programming errors."""

    settler = TxSettler(
        ledger_api=mock.Mock(
            try_get_gas_pricing=lambda **kwargs: {
                "maxFeePerGas": 100,
                "maxPriorityFeePerGas": 100,
            },
            update_with_gas_estimate=lambda tx: tx,
            api=mock.Mock(
                eth=mock.Mock(
                    block_number=1,
                    wait_for_transaction_receipt=mock.Mock(
                        return_value=mock.Mock(blockNumber=1)
                    ),
                ),
            ),
        ),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
        tx_builder=lambda: {"from": "0x123", "to": "0x456", "value": 100},
    )

    settler.transact(dry_run=True)
    with pytest.raises(
        TxSettleError, match="Cannot settle the transaction before it is sent."
    ):
        settler.settle()

    settler.transact()
    with pytest.raises(
        TxVerifyError, match="Cannot get events before the transaction is settled."
    ):
        settler.verify_events(
            contract=mock.Mock(),
            event_name="SomeEvent",
            expected_event_arg_name="someName",
            expected_event_arg_value="someValue",
        )

    with pytest.raises(
        TxVerifyError, match="Cannot get events before the transaction is settled."
    ):
        settler.get_events(
            contract=mock.Mock(),
            event_name="SomeEvent",
        )

    settler.settle()
    mock_contract = mock.Mock(
        events=mock.Mock(
            SomeEvent=mock.Mock(
                return_value=mock.Mock(process_receipt=mock.Mock(return_value=()))
            ),
            SomeOtherEvent=None,
        )
    )
    with pytest.raises(
        TxVerifyError, match="Contract has no event with name 'SomeOtherEvent'"
    ):
        settler.get_events(
            contract=mock_contract,
            event_name="SomeOtherEvent",
        )

    settler.get_events(
        contract=mock_contract,
        event_name="SomeEvent",
    )

    with pytest.raises(TxVerifyError, match="Could not find event"):
        settler.verify_events(
            contract=mock_contract,
            event_name="SomeEvent",
            expected_event_arg_name="someName",
            expected_event_arg_value="someValue",
        )

    mock_contract.events.SomeEvent.return_value.process_receipt.return_value = (
        {"args": {"someName": "someValue"}},
    )
    settler.verify_events(
        contract=mock_contract,
        event_name="SomeEvent",
        expected_event_arg_name="someName",
        expected_event_arg_value="someValue",
    )


class TestTxSetterOnChain(BaseChainInteractionTest):
    """Test TxSettler on chain."""

    def test_bad_tx(self) -> None:
        """Test bad tx."""
        settler = TxSettler(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            tx_builder=lambda: {
                "nonce": self.ledger_api.api.eth.get_transaction_count(
                    self.crypto.address
                ),
                "from": self.crypto.address,
                "to": self.crypto.address,
                "value": 10000 * 10**18 + 1,  # more than balance
                "gas": 21000,
                "gasPrice": self.ledger_api.api.eth.gas_price,
            },
        )

        with pytest.raises(
            ChainInteractionError, match="Sender doesn't have enough funds to send tx."
        ):
            settler.transact()

    def test_same_tx_sent_twice(self) -> None:
        """Test same tx sent twice should raise error when a programmer forgets to bump the nonce."""
        constant_nonce = self.ledger_api.api.eth.get_transaction_count(
            self.crypto.address
        )
        settler = TxSettler(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            tx_builder=lambda: {
                "nonce": constant_nonce,
                "from": self.crypto.address,
                "to": self.crypto.address,
                "value": 10**18,
                "gas": 21000,
                "gasPrice": self.ledger_api.api.eth.gas_price,
            },
            retries=1,
            sleep=0.1,
        )

        settler.transact()

        # try settling twice
        settler.settle()
        settler.settle()

        with pytest.raises(
            ChainTimeoutError,
            match=f"Failed to send transaction after {settler.retries} retries",
        ):
            settler.transact()

    @mock.patch("autonomy.chain.tx.logger")
    def test_different_tx_sent_twice(self, mock_logger: mock.Mock) -> None:
        """Test different tx sent twice."""

        state = {"first_nonce": None, "second_nonce": None}

        def _build_tx() -> dict:
            if state["first_nonce"] is None:
                state["first_nonce"] = self.ledger_api.api.eth.get_transaction_count(
                    self.crypto.address
                )
            else:
                state["second_nonce"] = self.ledger_api.api.eth.get_transaction_count(
                    self.crypto.address
                )
            return {
                "nonce": state["second_nonce"] or state["first_nonce"],
                "from": self.crypto.address,
                "to": self.crypto.address,
                "value": 10**18,
            }

        settler = TxSettler(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            tx_builder=_build_tx,
        )

        settler.transact()
        settler.transact()  # should not raise
        mock_logger.warning.assert_not_called()
        assert state["second_nonce"] == state["first_nonce"] + 1  # type: ignore[operator]

    @mock.patch("autonomy.chain.tx.logger")
    def test_underpriced_tx_to_get_repriced(self, mock_logger: mock.Mock) -> None:
        """Test underpriced tx to get repriced."""
        original_try_get_gas_pricing = self.ledger_api.try_get_gas_pricing
        original_update_with_gas_estimate = self.ledger_api.update_with_gas_estimate
        state = {
            "try_get_gas_pricing_call_count": 0,
            "try_update_with_gas_estimate_call_count": 0,
            "first_call": True,
        }

        def _get_try_get_gas_pricing_mock() -> Callable:
            def _mock_try_get_gas_pricing(**kwargs: Any) -> dict:
                state["try_get_gas_pricing_call_count"] += 1
                kwargs["gas_price_strategy"] = GAS_STATION
                gas_pricing = original_try_get_gas_pricing(**kwargs)
                if state["first_call"]:
                    gas_pricing["gasPrice"] = (
                        1  # very low gas price to trigger repricing
                    )
                    state["first_call"] = False

                return gas_pricing

            return _mock_try_get_gas_pricing

        def _update_with_gas_estimate_mock(tx: dict) -> dict:
            state["try_update_with_gas_estimate_call_count"] += 1
            return original_update_with_gas_estimate(tx)

        settler = TxSettler(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            tx_builder=lambda: {
                "nonce": self.ledger_api.api.eth.get_transaction_count(
                    self.crypto.address
                ),
                "from": self.crypto.address,
                "to": self.crypto.address,
                "value": 10**18,
            },
        )
        settler.ledger_api.try_get_gas_pricing = _get_try_get_gas_pricing_mock()
        settler.ledger_api.update_with_gas_estimate = _update_with_gas_estimate_mock

        settler.transact()

        # Verify the method was called once with expected arguments
        assert (
            "Transaction gasPrice (1) is too low for the next block"
            in mock_logger.warning.call_args[0][0]
        )
        assert state["try_update_with_gas_estimate_call_count"] == 2
        assert state["try_get_gas_pricing_call_count"] == 3
        assert settler.tx_hash is not None

        settler.settle()
        assert settler.tx_receipt is not None
