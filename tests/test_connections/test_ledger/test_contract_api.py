"""This module contains the tests of the ledger API connection for the contract APIs."""
import asyncio
import logging
import unittest.mock
from typing import cast

import pytest
from aea.common import Address
from aea.helpers.transaction.base import RawMessage, RawTransaction, State
from aea.mail.base import Envelope
from aea.multiplexer import MultiplexerStatus
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea_ledger_ethereum import EthereumCrypto

from packages.valory.connections.ledger.contract_dispatcher import (
    ContractApiRequestDispatcher,
)
from packages.valory.protocols.contract_api.dialogues import ContractApiDialogue
from packages.valory.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage

from packages.valory.contracts.gnosis_safe.contract import PUBLIC_ID as GNOSIS_SAFE_PUBLIC_ID

from tests.conftest import ETHEREUM_KEY_DEPLOYER


SOME_SKILL_ID = "some/skill:0.1.0"


class ContractApiDialogues(BaseContractApiDialogues):
    """This class keeps track of all contract_api dialogues."""

    def __init__(self, self_address: str) -> None:
        """
        Initialize dialogues.
        :param self_address: the address of the entity for whom dialogues are maintained
        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message
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
async def test_gnosis_safe_contract_get_deploy_transaction(gnosis_safe_contract, ledger_apis_connection):
    """Test get state with contract gnosis_safe_contract."""
    contract_api_dialogues = ContractApiDialogues(SOME_SKILL_ID)
    request, contract_api_dialogue = contract_api_dialogues.create(
        counterparty=str(ledger_apis_connection.connection_id),
        performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
        ledger_id=EthereumCrypto.identifier,
        contract_id=str(GNOSIS_SAFE_PUBLIC_ID),
        callable="get_deploy_transaction",
    )
    envelope = Envelope(to=request.to, sender=request.sender, message=request,)

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
    assert len(response.message.raw_transaction.body) == 6
    assert len(response.message.raw_transaction.body["data"]) > 0
