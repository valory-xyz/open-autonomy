# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
    DeploySafePayload,
    EstimatePayload,
    FinalizationTxPayload,
    ObservationPayload,
    RandomnessPayload,
    SelectKeeperPayload,
    SignaturePayload,
    TransactionHashPayload,
    TransactionType,
)


def test_select_keeper_payload() -> None:
    """Test `SelectKeeperPayload`."""

    payload = SelectKeeperPayload(sender="sender", keeper="keeper")

    assert payload.keeper == "keeper"
    assert payload.data == {"keeper": "keeper"}
    assert payload.transaction_type == TransactionType.SELECT_KEEPER


def test_deploy_safe_payload() -> None:
    """Test `DeploySafePayload`."""

    payload = DeploySafePayload(sender="sender", safe_contract_address="address")

    assert payload.safe_contract_address == "address"
    assert payload.data == {"safe_contract_address": "address"}
    assert payload.transaction_type == TransactionType.DEPLOY_SAFE


def test_observation_payload() -> None:
    """Test `ObservationPayload`."""

    payload = ObservationPayload(sender="sender", observation=1.0)

    assert payload.observation == 1.0
    assert payload.data == {"observation": 1.0}
    assert payload.transaction_type == TransactionType.OBSERVATION


def test_estimate_payload() -> None:
    """Test `EstimatePayload`."""

    payload = EstimatePayload(sender="sender", estimate=1.0)

    assert payload.estimate == 1.0
    assert payload.data == {"estimate": 1.0}
    assert payload.transaction_type == TransactionType.ESTIMATE


def test_signature_payload() -> None:
    """Test `SignaturePayload`."""

    payload = SignaturePayload(sender="sender", signature="sign")

    assert payload.signature == "sign"
    assert payload.data == {"signature": "sign"}
    assert payload.transaction_type == TransactionType.SIGNATURE


def test_transaction_hash_payload() -> None:
    """Test `TransactionHashPayload`."""

    payload = TransactionHashPayload(sender="sender", tx_hash="hash")

    assert payload.tx_hash == "hash"
    assert payload.data == {"tx_hash": "hash"}
    assert payload.transaction_type == TransactionType.TX_HASH


def test_finalization_tx_payload() -> None:
    """Test `FinalizationTxPayload`."""

    payload = FinalizationTxPayload(sender="sender", tx_hash="hash")

    assert payload.tx_hash == "hash"
    assert payload.data == {"tx_hash": "hash"}
    assert payload.transaction_type == TransactionType.FINALIZATION


def test_randomness_payload() -> None:
    """Test `RandomnessPayload`"""

    payload = RandomnessPayload(sender="sender", round_id=1, randomness="1", id_="id")

    assert payload.round_id == 1
    assert payload.randomness == "1"
    assert payload.id_ == "id"
    assert payload.data == {"round_id": 1, "randomness": "1"}

    assert payload.transaction_type == TransactionType.RANDOMNESS
