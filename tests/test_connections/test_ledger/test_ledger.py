"""This module contains the tests of the ledger API connection module."""
import asyncio
import logging
from typing import cast
from unittest.mock import Mock, patch

import pytest
from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.registries import make_crypto, make_ledger_api
from aea.helpers.async_utils import AsyncState
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea_ledger_ethereum import EthereumCrypto

from packages.valory.connections.ledger.connection import LedgerConnection
from packages.valory.connections.ledger.ledger_dispatcher import (
    LedgerApiRequestDispatcher,
)
from packages.valory.protocols.ledger_api.custom_types import Kwargs
from packages.valory.protocols.ledger_api.dialogues import LedgerApiDialogue
from packages.valory.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.valory.protocols.ledger_api.message import LedgerApiMessage

from tests.conftest import ETHEREUM_KEY_DEPLOYER


logger = logging.getLogger(__name__)


ledger_ids = pytest.mark.parametrize(
    "ledger_id,address",
    [
        (EthereumCrypto.identifier, EthereumCrypto(ETHEREUM_KEY_DEPLOYER).address),
    ],
)
gas_price_strategies = pytest.mark.parametrize("gas_price_strategy", [None, "average"],)

SOME_SKILL_ID = "some/skill:0.1.0"


class LedgerApiDialogues(BaseLedgerApiDialogues):
    """The dialogues class keeps track of all ledger_api dialogues."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.
        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message
            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return LedgerApiDialogue.Role.AGENT

        BaseLedgerApiDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
@ledger_ids
async def test_get_balance(
    ledger_id,
    address,
    ledger_apis_connection: Connection,
    update_default_ethereum_ledger_api,
    ethereum_testnet_config,
    ganache,
):
    """Test get balance."""
    import aea  # noqa # to load registries

    if ledger_id == FetchAICrypto.identifier:
        config = FETCHAI_TESTNET_CONFIG
    else:
        config = ethereum_testnet_config

    ledger_api_dialogues = LedgerApiDialogues(SOME_SKILL_ID)
    request, ledger_api_dialogue = ledger_api_dialogues.create(
        counterparty=str(ledger_apis_connection.connection_id),
        performative=LedgerApiMessage.Performative.GET_BALANCE,
        ledger_id=ledger_id,
        address=address,
    )
    envelope = Envelope(to=request.to, sender=request.sender, message=request,)

    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == LedgerApiMessage
    response_msg = cast(LedgerApiMessage, response.message)
    response_dialogue = ledger_api_dialogues.update(response_msg)
    assert response_dialogue == ledger_api_dialogue
    assert response_msg.performative == LedgerApiMessage.Performative.BALANCE
    actual_balance_amount = response_msg.balance
    expected_balance_amount = make_ledger_api(ledger_id, **config).get_balance(address)
    assert actual_balance_amount == expected_balance_amount
