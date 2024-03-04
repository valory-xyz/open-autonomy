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

"""This module contains the behaviours for the 'test_solana_behaviour' skill."""
import json
from abc import ABC
from typing import Any, Dict, Generator, Optional, Set, Type, cast

from packages.valory.contracts.squads_multisig.contract import SquadsMultisig
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)
from packages.valory.skills.squads_transaction_settlement_abci.behaviours import (
    SolanaTransactionSettlementRoundBehaviour,
)
from packages.valory.skills.test_solana_tx_abci.composition import ComposedAbciApp
from packages.valory.skills.test_solana_tx_abci.models import Params
from packages.valory.skills.test_solana_tx_abci.payloads import SolanaTransactionPayload
from packages.valory.skills.test_solana_tx_abci.rounds import SolanaRound


DUMMY_ADDRESS = "0x0"
SOLANA = "solana"


class SolanaTransferBehaviour(BaseBehaviour, ABC):
    """A behaviour that makes a solana transfer via the squad multisig."""

    matching_round = SolanaRound

    @property
    def params(self) -> Params:
        """Get the params."""
        return cast(Params, self.context.params)

    def async_act(self) -> Generator:
        """Do the action."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            payload_content = yield from self.get_payload_content()
            sender = self.context.agent_address
            payload = SolanaTransactionPayload(sender=sender, **payload_content)
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

    def _get_transfer_tx(self) -> Generator[None, None, Optional[Dict]]:
        """Get the transfer tx."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_id=str(SquadsMultisig.contract_id),
            contract_callable="get_transfer_tx",
            contract_address=DUMMY_ADDRESS,
            from_pubkey=self.params.squad_vault,
            to_pubkey=self.params.transfer_to_pubkey,
            lamports=self.params.transfer_lamports,
            chain_id=SOLANA,
            ledger_id=SOLANA,
        )
        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get the transfer tx. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        data = cast(Optional[Dict], response.state.body.get("data", None))
        return data

    def get_payload_content(self) -> Generator[None, None, Dict[str, Any]]:
        """Get the payload data."""
        transfer_tx = yield from self._get_transfer_tx()
        if transfer_tx is None:
            self.context.logger.error("Couldn't get the transfer tx.")
            return dict(instructions="", error=True)

        return dict(instructions=json.dumps([transfer_tx]), error=False)


class TestAbciConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the solana test abci app."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = ComposedAbciApp
    behaviours: Set[Type[BaseBehaviour]] = {
        *AgentRegistrationRoundBehaviour.behaviours,
        *ResetPauseABCIConsensusBehaviour.behaviours,
        *SolanaTransactionSettlementRoundBehaviour.behaviours,
        SolanaTransferBehaviour,  # type: ignore
    }
