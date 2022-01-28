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

"""Test the payloads.py module of the skill."""

from packages.valory.skills.price_estimation_abci.payloads import (
    EstimatePayload,
    ObservationPayload,
    TransactionHashPayload,
)
from packages.valory.skills.price_estimation_abci.payloads import (
    TransactionType as PETransactionType,
)
from packages.valory.skills.safe_deployment_abci.payloads import (
    DeploySafePayload,
    RandomnessPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.safe_deployment_abci.payloads import (
    TransactionType as DSTransactionType,
)


def test_select_keeper_payload() -> None:
    """Test `SelectKeeperPayload`."""

    payload = SelectKeeperPayload(sender="sender", keeper="keeper")

    assert payload.keeper == "keeper"
    assert payload.data == {"keeper": "keeper"}
    assert payload.transaction_type == DSTransactionType.SELECT_KEEPER


def test_deploy_safe_payload() -> None:
    """Test `DeploySafePayload`."""

    payload = DeploySafePayload(sender="sender", safe_contract_address="address")

    assert payload.safe_contract_address == "address"
    assert payload.data == {"safe_contract_address": "address"}
    assert payload.transaction_type == DSTransactionType.DEPLOY_SAFE


def test_observation_payload() -> None:
    """Test `ObservationPayload`."""

    payload = ObservationPayload(sender="sender", observation=1.0)

    assert payload.observation == 1.0
    assert payload.data == {"observation": 1.0}
    assert payload.transaction_type == PETransactionType.OBSERVATION


def test_estimate_payload() -> None:
    """Test `EstimatePayload`."""

    payload = EstimatePayload(sender="sender", estimate=1.0)

    assert payload.estimate == 1.0
    assert payload.data == {"estimate": 1.0}
    assert payload.transaction_type == PETransactionType.ESTIMATE


def test_transaction_hash_payload() -> None:
    """Test `TransactionHashPayload`."""

    payload = TransactionHashPayload(sender="sender", tx_hash="hash")

    assert payload.tx_hash == "hash"
    assert payload.data == {"tx_hash": "hash"}
    assert payload.transaction_type == PETransactionType.TX_HASH


def test_randomness_payload() -> None:
    """Test `RandomnessPayload`"""

    payload = RandomnessPayload(sender="sender", round_id=1, randomness="1", id_="id")

    assert payload.round_id == 1
    assert payload.randomness == "1"
    assert payload.id_ == "id"
    assert payload.data == {"round_id": 1, "randomness": "1"}

    assert payload.transaction_type == DSTransactionType.RANDOMNESS
