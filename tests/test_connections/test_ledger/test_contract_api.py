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

"""This module contains the tests of the ledger API connection for the contract APIs."""
import asyncio
from typing import List, Tuple, cast

import pytest
from aea.common import Address
from aea.contracts.base import Contract
from aea.crypto.registries import make_crypto
from aea.helpers.transaction.base import RawTransaction
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea_ledger_ethereum import EthereumCrypto

from packages.valory.connections.ledger.connection import LedgerConnection
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_PUBLIC_ID,
)
from packages.valory.protocols.contract_api.dialogues import ContractApiDialogue
from packages.valory.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage

from tests.conftest import ETHEREUM_KEY_DEPLOYER


SOME_SKILL_ID = "some/skill:0.1.0"


class ContractApiDialogues(BaseContractApiDialogues):
    """This class keeps track of all contract_api dialogues."""

    def __init__(self, self_address: str) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message.

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return ContractApiDialogue.Role.AGENT

        BaseContractApiDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


@pytest.mark.asyncio
async def test_get_deploy_transaction(
    gnosis_safe_contract: Tuple[Contract, str],
    ledger_apis_connection: LedgerConnection,
    owners: List[str],
    threshold: int,
) -> None:
    """
    Test get deploy transaction with contract gnosis_safe_contract.

    NOTE: we already deploy it once at base!

    :param gnosis_safe_contract: fixture
    :param ledger_apis_connection: fixture
    :param owners: fixture
    :param threshold: fixture
    """
    _, contract_address = gnosis_safe_contract
    contract_api_dialogues = ContractApiDialogues(SOME_SKILL_ID)
    crypto = make_crypto(
        EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_DEPLOYER
    )
    request, contract_api_dialogue = contract_api_dialogues.create(
        counterparty=str(ledger_apis_connection.connection_id),
        performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
        ledger_id=EthereumCrypto.identifier,
        contract_id=str(GNOSIS_SAFE_PUBLIC_ID),
        callable="get_deploy_transaction",
        kwargs=ContractApiMessage.Kwargs(
            body=dict(
                deployer_address=crypto.address,
                gas=5000000,
                owners=owners,
                threshold=threshold,
            )
        ),
    )
    envelope = Envelope(
        to=request.to,
        sender=request.sender,
        message=request,
    )

    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == ContractApiMessage
    response_message = cast(ContractApiMessage, response.message)
    assert (
        response_message.performative == ContractApiMessage.Performative.RAW_TRANSACTION
    ), "Error: {}".format(response_message.message)
    response_dialogue = contract_api_dialogues.update(response_message)
    assert response_dialogue == contract_api_dialogue
    assert type(response_message.raw_transaction) == RawTransaction
    assert response_message.raw_transaction.ledger_id == EthereumCrypto.identifier
    assert len(response.message.raw_transaction.body) == 9
    assert len(str(response.message.raw_transaction.body["data"])) > 0
    assert (
        response.message.raw_transaction.body["contract_address"] != contract_address
    ), "new deployment should have new address"
