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

"""Tests for the funds_forwarder_abci dialogues."""

from packages.valory.skills.abstract_round_abci.dialogues import (
    AbciDialogue as BaseAbciDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    AbciDialogues as BaseAbciDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    ContractApiDialogue as BaseContractApiDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    HttpDialogue as BaseHttpDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    HttpDialogues as BaseHttpDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    IpfsDialogue as BaseIpfsDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    IpfsDialogues as BaseIpfsDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    LedgerApiDialogue as BaseLedgerApiDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    SigningDialogue as BaseSigningDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    TendermintDialogue as BaseTendermintDialogue,
)
from packages.valory.skills.abstract_round_abci.dialogues import (
    TendermintDialogues as BaseTendermintDialogues,
)
from packages.valory.skills.funds_forwarder_abci.dialogues import (
    AbciDialogue,
    AbciDialogues,
    ContractApiDialogue,
    ContractApiDialogues,
    HttpDialogue,
    HttpDialogues,
    IpfsDialogue,
    IpfsDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    SigningDialogue,
    SigningDialogues,
    TendermintDialogue,
    TendermintDialogues,
)


def test_abci_dialogue_alias() -> None:
    """Test AbciDialogue alias."""
    assert AbciDialogue is BaseAbciDialogue


def test_abci_dialogues_alias() -> None:
    """Test AbciDialogues alias."""
    assert AbciDialogues is BaseAbciDialogues


def test_http_dialogue_alias() -> None:
    """Test HttpDialogue alias."""
    assert HttpDialogue is BaseHttpDialogue


def test_http_dialogues_alias() -> None:
    """Test HttpDialogues alias."""
    assert HttpDialogues is BaseHttpDialogues


def test_signing_dialogue_alias() -> None:
    """Test SigningDialogue alias."""
    assert SigningDialogue is BaseSigningDialogue


def test_signing_dialogues_alias() -> None:
    """Test SigningDialogues alias."""
    assert SigningDialogues is BaseSigningDialogues


def test_ledger_api_dialogue_alias() -> None:
    """Test LedgerApiDialogue alias."""
    assert LedgerApiDialogue is BaseLedgerApiDialogue


def test_ledger_api_dialogues_alias() -> None:
    """Test LedgerApiDialogues alias."""
    assert LedgerApiDialogues is BaseLedgerApiDialogues


def test_contract_api_dialogue_alias() -> None:
    """Test ContractApiDialogue alias."""
    assert ContractApiDialogue is BaseContractApiDialogue


def test_contract_api_dialogues_alias() -> None:
    """Test ContractApiDialogues alias."""
    assert ContractApiDialogues is BaseContractApiDialogues


def test_tendermint_dialogue_alias() -> None:
    """Test TendermintDialogue alias."""
    assert TendermintDialogue is BaseTendermintDialogue


def test_tendermint_dialogues_alias() -> None:
    """Test TendermintDialogues alias."""
    assert TendermintDialogues is BaseTendermintDialogues


def test_ipfs_dialogue_alias() -> None:
    """Test IpfsDialogue alias."""
    assert IpfsDialogue is BaseIpfsDialogue


def test_ipfs_dialogues_alias() -> None:
    """Test IpfsDialogues alias."""
    assert IpfsDialogues is BaseIpfsDialogues
