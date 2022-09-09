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

"""Tests for valory/registration_abci skill's rounds."""

import logging  # noqa: F401
from typing import Dict, FrozenSet, Optional

from packages.valory.skills.abstract_round_abci.base import AbciAppDB, MAX_INT_256
from packages.valory.skills.oracle_deployment_abci.payloads import (
    RandomnessPayload,
    SelectKeeperPayload,
)
from packages.valory.skills.safe_deployment_abci.payloads import DeploySafePayload
from packages.valory.skills.safe_deployment_abci.rounds import DeploySafeRound
from packages.valory.skills.safe_deployment_abci.rounds import (
    Event as SafeDeploymentEvent,
)
from packages.valory.skills.safe_deployment_abci.rounds import SelectKeeperSafeRound
from packages.valory.skills.safe_deployment_abci.rounds import (
    SynchronizedData as SafeDeploymentSynchronizedSata,
)
from packages.valory.skills.safe_deployment_abci.rounds import ValidateSafeRound
from packages.valory.skills.transaction_settlement_abci.payloads import ValidatePayload

from tests.test_skills.test_oracle_deployment_abci.test_rounds import (
    BaseDeployTestClass,
    BaseValidateRoundTest,
)
from tests.test_skills.test_transaction_settlement_abci.test_rounds import (
    BaseSelectKeeperRoundTest,
)


MAX_PARTICIPANTS: int = 4
RANDOMNESS: str = "d1c29dce46f979f9748210d24bce4eae8be91272f5ca1a6aea2832d3dd676f51"


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


def get_participant_to_randomness(
    participants: FrozenSet[str], round_id: int
) -> Dict[str, RandomnessPayload]:
    """participant_to_randomness"""
    return {
        participant: RandomnessPayload(
            sender=participant,
            round_id=round_id,
            randomness=RANDOMNESS,
        )
        for participant in participants
    }


def get_most_voted_randomness() -> str:
    """most_voted_randomness"""
    return RANDOMNESS


def get_participant_to_selection(
    participants: FrozenSet[str],
) -> Dict[str, SelectKeeperPayload]:
    """participant_to_selection"""
    return {
        participant: SelectKeeperPayload(sender=participant, keeper="keeper")
        for participant in participants
    }


def get_most_voted_keeper_address() -> str:
    """most_voted_keeper_address"""
    return "keeper"


def get_safe_contract_address() -> str:
    """safe_contract_address"""
    return "0x6f6ab56aca12"


def get_participant_to_votes(
    participants: FrozenSet[str], vote: Optional[bool] = True
) -> Dict[str, ValidatePayload]:
    """participant_to_votes"""
    return {
        participant: ValidatePayload(sender=participant, vote=vote)
        for participant in participants
    }


class TestDeploySafeRound(BaseDeployTestClass):
    """Test DeploySafeRound."""

    round_class = DeploySafeRound
    payload_class = DeploySafePayload
    update_keyword = "safe_contract_address"
    _event_class = SafeDeploymentEvent
    _synchronized_data_class = SafeDeploymentSynchronizedSata


class TestValidateSafeRound(BaseValidateRoundTest):
    """Test ValidateSafeRound."""

    test_class = ValidateSafeRound
    test_payload = ValidatePayload
    _event_class = SafeDeploymentEvent
    _synchronized_data_class = SafeDeploymentSynchronizedSata


class TestSelectKeeperSafeRound(BaseSelectKeeperRoundTest):
    """Test SelectKeeperTransactionSubmissionRoundB."""

    test_class = SelectKeeperSafeRound
    test_payload = SelectKeeperPayload
    _event_class = SafeDeploymentEvent


def test_synchronized_datas() -> None:
    """Test SynchronizedData."""

    participants = get_participants()
    participant_to_randomness = get_participant_to_randomness(participants, 1)
    most_voted_randomness = get_most_voted_randomness()
    participant_to_selection = get_participant_to_selection(participants)
    most_voted_keeper_address = get_most_voted_keeper_address()
    safe_contract_address = get_safe_contract_address()
    participant_to_votes = get_participant_to_votes(participants)
    actual_keeper_randomness = int(most_voted_randomness, base=16) / MAX_INT_256

    synchronized_data_ = SafeDeploymentSynchronizedSata(
        AbciAppDB(
            setup_data=AbciAppDB.data_to_lists(
                dict(
                    participants=participants,
                    participant_to_randomness=participant_to_randomness,
                    most_voted_randomness=most_voted_randomness,
                    participant_to_selection=participant_to_selection,
                    participant_to_votes=participant_to_votes,
                    most_voted_keeper_address=most_voted_keeper_address,
                    safe_contract_address=safe_contract_address,
                )
            ),
        )
    )
    assert (
        abs(synchronized_data_.keeper_randomness - actual_keeper_randomness) < 1e-10
    )  # avoid equality comparisons between floats
    assert synchronized_data_.most_voted_randomness == most_voted_randomness
    assert synchronized_data_.most_voted_keeper_address == most_voted_keeper_address
    assert synchronized_data_.safe_contract_address == safe_contract_address
