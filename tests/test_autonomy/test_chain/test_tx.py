# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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


class _retriable_method:
    should_raise = True

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.should_raise:
            self.should_raise = False
            raise Exception("FeeTooLow")
        return {}


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
    settler = TxSettler(
        ledger_api=mock.Mock(),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
    )
    settler.transact(_retriable_method(), contract="service_registry", kwargs={})  # type: ignore
    captured = capsys.readouterr()
    assert (
        "Error occured when interacting with chain: FeeTooLow; will retry in 3.0..."
        in captured.out
    )


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
