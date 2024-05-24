# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
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

from typing import Any
from unittest import mock

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError

from autonomy.chain.config import ChainType
from autonomy.chain.exceptions import ChainInteractionError, ChainTimeoutError, RPCError
from autonomy.chain.tx import TxSettler


def test_rpc_error() -> None:
    """Test RPC error."""
    settler = TxSettler(
        ledger_api=mock.Mock(),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
    )

    def _waitable(*args: Any, **kwargs: Any) -> Any:
        raise RequestsConnectionError()

    with pytest.raises(RPCError):
        settler.transact(_waitable, "service_registry", {})


def test_none_retriable_exception() -> None:
    """Test none retriable exception."""
    settler = TxSettler(
        ledger_api=mock.Mock(),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
    )

    def _method(*args: Any, **kwargs: Any) -> Any:
        raise Exception("some error")

    with pytest.raises(ChainInteractionError):
        settler.transact(_method, contract="service_registry", kwargs={})  # type: ignore


def test_retriable_exception(capsys: Any) -> None:
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
    )
    settler.transact(_retriable_method(), contract="service_registry", kwargs={})  # type: ignore
    captured = capsys.readouterr()
    assert "Error occured when interacting with chain" in captured.out


def test_repricing(capsys: Any) -> None:
    """Test retriable exception."""

    class _repricable_method:
        tx_dict = {
            "maxFeePerGas": 100,
            "maxPriorityFeePerGas": 100,
        }

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return self.tx_dict

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
    )
    settler.transact(_repricable_method(), contract="service_registry", kwargs={})  # type: ignore
    captured = capsys.readouterr()
    assert "Repricing the transaction..." in captured.out


def test_repricing_bad_tx(capsys: Any) -> None:
    """Test retriable exception."""

    class _repricable_method:
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
    )
    settler.transact(_repricable_method(), contract="service_registry", kwargs={})  # type: ignore
    captured = capsys.readouterr()
    assert "Repricing the transaction..." in captured.out


def test_tx_not_found(capsys: Any) -> None:
    """Test retriable exception."""

    class _get_transaction_receipt:
        _should_raise = True

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            if self._should_raise:
                self._should_raise = False
                raise Exception("Transaction with hash HASH not found")
            return "receipt"

    settler = TxSettler(
        ledger_api=mock.Mock(
            api=mock.Mock(
                eth=mock.Mock(
                    get_transaction_receipt=_get_transaction_receipt(),
                )
            )
        ),
        crypto=mock.Mock(
            sign_transaction=lambda transaction: transaction,
        ),
        chain_type=ChainType.LOCAL,
    )
    settler.transact(mock.Mock(), contract="service_registry", kwargs={})  # type: ignore
    captured = capsys.readouterr()

    assert "Error getting transaction receipt" in captured.out
    assert "Transaction with hash HASH not found" in captured.out
    assert "Will retry in 3.0..." in captured.out


def test_already_known(capsys: Any) -> None:
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
    )
    with mock.patch.object(settler, "_already_known") as _mock:
        settler.transact(_method(), contract="service_registry", kwargs={})  # type: ignore
        _mock.assert_called_with("AlreadyKnown")


def test_should_rebuild_with_oldnonce(capsys: Any) -> None:
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
                raise Exception("OldNonce")
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
    )
    settler.transact(builder, contract="service_registry", kwargs={})  # type: ignore
    assert (
        builder.call_count == 2
    )  # should be 2 since the build method will be called twice


def test_timeout() -> None:
    """Test transact."""

    def _waitable(*arg: Any, **kwargs: Any) -> None:
        return None

    settler = TxSettler(
        ledger_api=mock.Mock(
            api=mock.Mock(
                eth=mock.Mock(
                    get_transaction_receipt=_waitable,
                )
            )
        ),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
        sleep=0.1,
        retries=1,
    )

    with pytest.raises(ChainTimeoutError):
        settler.transact(lambda **x: None, "service_registry", {})  # type: ignore
