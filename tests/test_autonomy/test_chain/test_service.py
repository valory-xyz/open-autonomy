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

"""Test service helpers."""


from aea_test_autonomy.fixture_helpers import registries_scope_class  # noqa: F401

from autonomy.chain.service import get_reuse_multisig_payload

from tests.test_autonomy.test_chain.base import (
    AGENT_ID,
    BaseChainInteractionTest,
    COST_OF_BOND_FOR_AGENT,
    DUMMY_SERVICE,
    NUMBER_OF_SLOTS_PER_AGENT,
    THRESHOLD,
)


class TestReuseMultisigPayload(BaseChainInteractionTest):
    """Test get_reuse_multisig_payload method."""

    def test_inproper_termination(self) -> None:
        """Test inproper termination failure"""

        _, error = get_reuse_multisig_payload(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=1,
        )

        assert (
            error
            == "Service was not terminated properly, the service owner should be the only owner of the safe"
        )

    def test_no_previous_deployment(self) -> None:
        """Test inproper termination failure"""
        service_id = self.mint_component(
            package_id=DUMMY_SERVICE,
            service_mint_parameters=dict(
                agent_ids=[AGENT_ID],
                number_of_slots_per_agent=[NUMBER_OF_SLOTS_PER_AGENT],
                cost_of_bond_per_agent=[COST_OF_BOND_FOR_AGENT],
                threshold=THRESHOLD,
            ),
        )
        _, error = get_reuse_multisig_payload(
            ledger_api=self.ledger_api,
            crypto=self.crypto,
            chain_type=self.chain_type,
            service_id=service_id,
        )

        assert error == "Cannot reuse multisig, No previous deployment exist!"
