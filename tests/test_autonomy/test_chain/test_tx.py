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
from autonomy.chain.tx import TxSettler

from tests.test_autonomy.test_chain.base import BaseChainInteractionTest


def _raise_connection_error(*args: Any, **kwargs: Any) -> Any:
    raise RequestsConnectionError("Cannot connect to the given RPC")


def _raise_value_error(*args: Any, **kwargs: Any) -> Any:
    raise ValueError("Some value error")


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
        ledger_api=mock.Mock(),
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
        raise Exception("FeeTooLow")

    def _reprice(old_price: Any, **kwargs: Any) -> Any:
        return {"maxFeePerGas": 110, "maxPriorityFeePerGas": 110}

    settler = TxSettler(
        ledger_api=mock.Mock(
            send_signed_transaction=_raise_fee_too_low,
            try_get_gas_pricing=_reprice,
        ),
        crypto=mock.Mock(
            sign_transaction=lambda transaction: transaction,
        ),
        chain_type=ChainType.LOCAL,
        tx_builder=method,
    )
    settler.transact()
    logger.warning.assert_called_with(  # type: ignore[attr-defined]
        "Low gas error: FeeTooLow; Repricing the transaction..."
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


def test_programming_errors() -> None:
    """Test programming errors."""

    settler = TxSettler(
        ledger_api=mock.Mock(),
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

    missing_event_exception = Exception("SomeEvent not found")
    with pytest.raises(Exception, match="SomeEvent not found"):
        settler.verify_events(
            contract=mock_contract,
            event_name="SomeEvent",
            expected_event_arg_name="someName",
            expected_event_arg_value="someValue",
            missing_event_exception=missing_event_exception,
        )

    mock_contract.events.SomeEvent.return_value.process_receipt.return_value = (
        {"args": {"someName": "someValue"}},
    )
    settler.verify_events(
        contract=mock_contract,
        event_name="SomeEvent",
        expected_event_arg_name="someName",
        expected_event_arg_value="someValue",
        missing_event_exception=missing_event_exception,
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
        with pytest.raises(
            ChainTimeoutError,
            match=f"Failed to send transaction after {settler.retries} retries",
        ):
            settler.transact()

    @mock.patch("autonomy.chain.tx.logger")
    def test_different_tx_sent_twice(self, mock_logger: mock.Mock) -> None:
        """Test different tx sent twice."""

        first_nonce = None
        second_nonce = None

        def _build_tx() -> dict:
            nonlocal first_nonce, second_nonce
            if first_nonce is None:
                first_nonce = self.ledger_api.api.eth.get_transaction_count(
                    self.crypto.address
                )
            else:
                second_nonce = self.ledger_api.api.eth.get_transaction_count(
                    self.crypto.address
                )
            return {
                "nonce": second_nonce or first_nonce,
                "from": self.crypto.address,
                "to": self.crypto.address,
                "value": 10**18,
                "gas": 21000,
                "gasPrice": self.ledger_api.api.eth.gas_price,
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
        assert second_nonce == first_nonce + 1  # type: ignore[operator]

    @mock.patch("autonomy.chain.tx.logger")
    def test_underpriced_tx_to_get_repriced(self, mock_logger: mock.Mock) -> None:
        """Test underpriced tx to get repriced."""
        # Wrap try_get_gas_pricing to count calls while preserving original logic
        original_try_get_gas_pricing = self.ledger_api.try_get_gas_pricing
        call_count = 0
        call_args = None

        def wrapped_try_get_gas_pricing(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count, call_args
            call_count += 1
            call_args = (args, kwargs)
            return original_try_get_gas_pricing(*args, **kwargs)

        self.ledger_api.try_get_gas_pricing = wrapped_try_get_gas_pricing

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
                "gas": 21000,
                "gasPrice": 1,  # very low
            },
        )

        settler.transact()

        # Verify the method was called once with expected arguments
        assert (
            "Transaction gasPrice (1) is too low for the next block"
            in mock_logger.warning.call_args[0][0]
        )
        assert call_count == 1
        assert call_args == (
            (),
            {"old_price": {"gasPrice": 1}, "gas_price_strategy": "gas_station"},
        )
        assert settler.tx_hash is not None
