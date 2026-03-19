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

"""Tests for the identify_service_owner_abci handlers."""

from packages.valory.skills.abstract_round_abci.handlers import (
    ABCIRoundHandler as BaseABCIRoundHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    ContractApiHandler as BaseContractApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    HttpHandler as BaseHttpHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    IpfsHandler as BaseIpfsHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    LedgerApiHandler as BaseLedgerApiHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    SigningHandler as BaseSigningHandler,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    TendermintHandler as BaseTendermintHandler,
)
from packages.valory.skills.identify_service_owner_abci.handlers import (
    ABCIHandler,
    ContractApiHandler,
    HttpHandler,
    IpfsHandler,
    LedgerApiHandler,
    SigningHandler,
    TendermintHandler,
)


def test_abci_handler_alias() -> None:
    """Test ABCIHandler alias."""
    assert ABCIHandler is BaseABCIRoundHandler


def test_http_handler_alias() -> None:
    """Test HttpHandler alias."""
    assert HttpHandler is BaseHttpHandler


def test_signing_handler_alias() -> None:
    """Test SigningHandler alias."""
    assert SigningHandler is BaseSigningHandler


def test_ledger_api_handler_alias() -> None:
    """Test LedgerApiHandler alias."""
    assert LedgerApiHandler is BaseLedgerApiHandler


def test_contract_api_handler_alias() -> None:
    """Test ContractApiHandler alias."""
    assert ContractApiHandler is BaseContractApiHandler


def test_tendermint_handler_alias() -> None:
    """Test TendermintHandler alias."""
    assert TendermintHandler is BaseTendermintHandler


def test_ipfs_handler_alias() -> None:
    """Test IpfsHandler alias."""
    assert IpfsHandler is BaseIpfsHandler
