# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Test mint helpers."""

import re
from pathlib import Path
from typing import Dict
from unittest import mock

import pytest

from autonomy.chain.base import registry_contracts
from autonomy.chain.config import ChainType
from autonomy.chain.constants import COMPONENT_REGISTRY_CONTRACT, CONTRACTS_DIR_LOCAL
from autonomy.chain.exceptions import InvalidMintParameter
from autonomy.chain.mint import mint_service, sort_service_dependency_metadata

from tests.test_autonomy.test_chain.base import DUMMY_HASH


@pytest.mark.parametrize(
    argnames=("parameters", "error_message"),
    argvalues=(
        (
            dict(
                chain_type=ChainType.LOCAL,
                metadata_hash=DUMMY_HASH,
                agent_ids=[],
                number_of_slots_per_agent=[],
                cost_of_bond_per_agent=[],
                threshold=0,
            ),
            "Please provide at least one agent id",
        ),
        (
            dict(
                chain_type=ChainType.LOCAL,
                metadata_hash=DUMMY_HASH,
                agent_ids=[1],
                number_of_slots_per_agent=[],
                cost_of_bond_per_agent=[],
                threshold=0,
            ),
            "Please for provide number of slots for agents",
        ),
        (
            dict(
                chain_type=ChainType.LOCAL,
                metadata_hash=DUMMY_HASH,
                agent_ids=[1],
                number_of_slots_per_agent=[4],
                cost_of_bond_per_agent=[],
                threshold=0,
            ),
            "Please for provide cost of bond for agents",
        ),
        (
            dict(
                chain_type=ChainType.LOCAL,
                metadata_hash=DUMMY_HASH,
                agent_ids=[1],
                number_of_slots_per_agent=[4],
                cost_of_bond_per_agent=[1000],
                threshold=2,
            ),
            re.escape(
                "The threshold value should at least be greater than or equal to ceil((n * 2 + 1) / 3), "
                "n is total number of agent instances in the service"
            ),
        ),
        (
            dict(
                chain_type=ChainType.LOCAL,
                metadata_hash=DUMMY_HASH,
                agent_ids=[1],
                number_of_slots_per_agent=[0],
                cost_of_bond_per_agent=[1000],
                threshold=0,
            ),
            "Number of slots cannot be zero",
        ),
        (
            dict(
                chain_type=ChainType.LOCAL,
                metadata_hash=DUMMY_HASH,
                agent_ids=[1],
                number_of_slots_per_agent=[4],
                cost_of_bond_per_agent=[0],
                threshold=0,
            ),
            "Cost of bond cannot be zero",
        ),
    ),
)
def test_mint_service_invalid_paramters(parameters: Dict, error_message: str) -> None:
    """Test invalid parameters"""

    with pytest.raises(InvalidMintParameter, match=error_message):
        mint_service(
            ledger_api=mock.MagicMock(),  # type: ignore
            crypto=mock.MagicMock(),  # type: ignore
            **parameters
        )


def test_get_contract_method() -> None:
    """Test `get_contract` method"""

    contract = registry_contracts.get_contract(COMPONENT_REGISTRY_CONTRACT)
    assert (
        contract.configuration.directory
        == CONTRACTS_DIR_LOCAL / COMPONENT_REGISTRY_CONTRACT.name
    )

    with mock.patch.object(Path, "exists", return_value=False):
        with pytest.raises(
            FileNotFoundError,
            match="Contract package not found in the distribution, please reinstall the package",
        ):
            contract = registry_contracts.get_contract(COMPONENT_REGISTRY_CONTRACT)


def test_sort_service_dependency_metadata() -> None:
    """Test `sort_service_dependency_metadata` method"""

    agent_ids = [2, 4, 1, 3]
    expected_agent_ids = sorted(agent_ids)

    number_of_slots_per_agents = [8, 4, 2, 1]
    expected_number_of_slots_per_agents = [2, 8, 1, 4]

    cost_of_bond_per_agent = [10, 100, 1000, 10000]
    expected_cost_of_bond_per_agent = [1000, 10, 10000, 100]

    (
        cal_agent_ids,
        cal_number_of_slots_per_agents,
        cal_cost_of_bond_per_agent,
    ) = sort_service_dependency_metadata(
        agent_ids=agent_ids,
        number_of_slots_per_agents=number_of_slots_per_agents,
        cost_of_bond_per_agent=cost_of_bond_per_agent,
    )

    assert cal_agent_ids == expected_agent_ids
    assert cal_number_of_slots_per_agents == expected_number_of_slots_per_agents
    assert cal_cost_of_bond_per_agent == expected_cost_of_bond_per_agent
