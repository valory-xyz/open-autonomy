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
from autonomy.chain.exceptions import ChainTimeoutError, RPCError, TxBuildError
from autonomy.chain.tx import TxSettler, Web3Exception


CALLS = 0


class TestWait:
    """Test wait method."""

    def test_timeout(self) -> None:
        """Test timeout."""
        settler = TxSettler(
            ledger_api=mock.Mock(),
            crypto=mock.Mock(),
            chain_type=mock.Mock(),
            timeout=0.1,
            sleep=0.1,
        )
        assert settler.wait(lambda: None, lambda x: x) is None

    def test_rpc_error(self) -> None:
        """Test RPC error."""
        settler = TxSettler(
            ledger_api=mock.Mock(),
            crypto=mock.Mock(),
            chain_type=mock.Mock(),
        )

        def _waitable() -> None:
            raise RequestsConnectionError()

        with pytest.raises(RPCError):
            settler.wait(_waitable, w3_error_handler=lambda x: x)


def test_build() -> None:
    """Test tx build."""
    settler = TxSettler(
        ledger_api=mock.Mock(),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
        sleep=0.1,
        retries=1,
    )

    def _waitable(**kwargs: Any) -> None:
        return None

    with pytest.raises(ChainTimeoutError):
        settler.build(_waitable, contract="service_registry", kwargs={})  # type: ignore


def test_w3_exception() -> None:
    """Test RPC error."""
    settler = TxSettler(
        ledger_api=mock.Mock(),
        crypto=mock.Mock(),
        chain_type=ChainType.LOCAL,
    )

    def _method(*args: Any, **kwargs: Any) -> None:
        raise Web3Exception("some error")

    with pytest.raises(TxBuildError):
        settler.build(_method, contract="service_registry", kwargs={})  # type: ignore


def test_transact() -> None:
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
        settler.transact({})
