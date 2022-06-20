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

"""This module contains the tests of the ledger API connection for the contract APIs."""
import asyncio
from typing import Any, Dict, List, Tuple, cast
from unittest import mock

import pytest
from aea.common import Address
from aea.contracts.base import Contract
from aea.crypto.registries import make_crypto
from aea.helpers.transaction.base import RawMessage, RawTransaction, State
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

from tests.conftest import ETHEREUM_KEY_DEPLOYER, get_key
from tests.helpers.docker.base import skip_docker_tests


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


@skip_docker_tests
@pytest.mark.usefixtures("gnosis_safe_hardhat_scope_class")
class TestContractDispatcher:
    """Test contract dispatcher."""

    @pytest.mark.asyncio
    async def test_get_deploy_transaction(
        self,
        gnosis_safe_contract: Tuple[Contract, str],
        ledger_apis_connection: LedgerConnection,
        owners: List[str],
        threshold: int,
    ) -> None:
        """
        Test get deploy transaction with contract gnosis_safe_contract.

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
                    gas_price=10 * 10,
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
        assert isinstance(response.message, ContractApiMessage)
        response_message = cast(ContractApiMessage, response.message)
        assert (
            response_message.performative
            == ContractApiMessage.Performative.RAW_TRANSACTION
        ), "Error: {}".format(response_message.message)
        response_dialogue = contract_api_dialogues.update(response_message)
        assert response_dialogue == contract_api_dialogue
        assert isinstance(response_message.raw_transaction, RawTransaction)
        assert response_message.raw_transaction.ledger_id == EthereumCrypto.identifier
        assert len(response.message.raw_transaction.body) == 9
        assert len(str(response.message.raw_transaction.body["data"])) > 0
        assert (
            response.message.raw_transaction.body["contract_address"]
            != contract_address
        ), "new deployment should have new address"

    @pytest.mark.asyncio
    async def test_get_deploy_transaction_with_validate_and_call_callable(
        self,
        gnosis_safe_contract: Tuple[Contract, str],
        ledger_apis_connection: LedgerConnection,
        owners: List[str],
        threshold: int,
    ) -> None:
        """
        Test get deploy transaction with contract gnosis_safe_contract ( using _validate_and_call_callable instead of _stub_call method ).

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
                    gas_price=10 ** 10,
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

        with mock.patch.object(
            ledger_apis_connection._contract_dispatcher, "_call_stub", return_value=None
        ):
            await ledger_apis_connection.send(envelope)
            await asyncio.sleep(0.01)
            response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, ContractApiMessage)
        response_message = cast(ContractApiMessage, response.message)
        assert (
            response_message.performative
            == ContractApiMessage.Performative.RAW_TRANSACTION
        ), "Error: {}".format(response_message.message)
        response_dialogue = contract_api_dialogues.update(response_message)
        assert response_dialogue == contract_api_dialogue
        assert isinstance(response_message.raw_transaction, RawTransaction)
        assert response_message.raw_transaction.ledger_id == EthereumCrypto.identifier
        assert len(response.message.raw_transaction.body) == 9
        assert len(str(response.message.raw_transaction.body["data"])) > 0
        assert (
            response.message.raw_transaction.body["contract_address"]
            != contract_address
        ), "new deployment should have new address"

    @pytest.mark.asyncio
    async def test_get_state(
        self,
        gnosis_safe_contract: Tuple[Contract, str],
        ledger_apis_connection: LedgerConnection,
    ) -> None:
        """
        Test get state with contract gnosis_safe_contract.

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(SOME_SKILL_ID)
        request, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=ContractApiMessage.Performative.GET_STATE,
            ledger_id=EthereumCrypto.identifier,
            contract_id=str(GNOSIS_SAFE_PUBLIC_ID),
            callable="get_state",
            contract_address=contract_address,
            kwargs=ContractApiMessage.Kwargs(
                {"agent_address": get_key(ETHEREUM_KEY_DEPLOYER), "token_id": 1}
            ),
        )
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        with mock.patch(
            "packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_state",
            return_value={},
        ):
            await ledger_apis_connection.send(envelope)
            await asyncio.sleep(0.01)
            response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, ContractApiMessage)
        response_message = cast(ContractApiMessage, response.message)
        assert (
            response_message.performative == ContractApiMessage.Performative.STATE
        ), "Error: {}".format(response_message.message)
        response_dialogue = contract_api_dialogues.update(response_message)
        assert response_dialogue == contract_api_dialogue
        assert isinstance(response_message.state, State)
        assert response_message.state.ledger_id == EthereumCrypto.identifier
        assert len(response.message.state.body) == 0

    @pytest.mark.asyncio
    async def test_get_state_with_validate_and_call_callable(
        self,
        gnosis_safe_contract: Tuple[Contract, str],
        ledger_apis_connection: LedgerConnection,
    ) -> None:
        """
        Test get state with contract gnosis_safe_contract ( using _validate_and_call_callable instead of _call_stub method).

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(SOME_SKILL_ID)
        request, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=ContractApiMessage.Performative.GET_STATE,
            ledger_id=EthereumCrypto.identifier,
            contract_id=str(GNOSIS_SAFE_PUBLIC_ID),
            callable="get_state",
            contract_address=contract_address,
            kwargs=ContractApiMessage.Kwargs(
                {"agent_address": get_key(ETHEREUM_KEY_DEPLOYER), "token_id": 1}
            ),
        )
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        with mock.patch.object(
            ledger_apis_connection._contract_dispatcher, "_call_stub", return_value=None
        ):

            def get_state(
                ledger_api: Any, contract_address: str, *args: Any, **kwargs: Any
            ) -> Dict:
                """Mock `get_state` method from GnosisSafeContract."""
                return {}

            with mock.patch(
                "packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_state",
                new_callable=lambda: get_state,
            ):
                await ledger_apis_connection.send(envelope)
                await asyncio.sleep(0.01)
                response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, ContractApiMessage)
        response_message = cast(ContractApiMessage, response.message)
        assert (
            response_message.performative == ContractApiMessage.Performative.STATE
        ), "Error: {}".format(response_message.message)
        response_dialogue = contract_api_dialogues.update(response_message)
        assert response_dialogue == contract_api_dialogue
        assert isinstance(response_message.state, State)
        assert response_message.state.ledger_id == EthereumCrypto.identifier
        assert len(response.message.state.body) == 0

    @pytest.mark.asyncio
    async def test_get_raw_transaction(
        self,
        gnosis_safe_contract: Tuple[Contract, str],
        ledger_apis_connection: LedgerConnection,
    ) -> None:
        """
        Test get raw transaction with contract get_raw_transaction.

        NOTE: we already deploy it once at base!

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(SOME_SKILL_ID)
        request, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ledger_id=EthereumCrypto.identifier,
            contract_id=str(GNOSIS_SAFE_PUBLIC_ID),
            callable="get_raw_transaction",
            contract_address=contract_address,
            kwargs=ContractApiMessage.Kwargs(
                {"agent_address": get_key(ETHEREUM_KEY_DEPLOYER), "token_id": 1}
            ),
        )
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        with mock.patch(
            "packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_raw_transaction",
            return_value={},
        ):
            await ledger_apis_connection.send(envelope)
            await asyncio.sleep(0.01)
            response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, ContractApiMessage)
        response_message = cast(ContractApiMessage, response.message)
        assert (
            response_message.performative
            == ContractApiMessage.Performative.RAW_TRANSACTION
        ), "Error: {}".format(response_message.message)
        response_dialogue = contract_api_dialogues.update(response_message)
        assert response_dialogue == contract_api_dialogue
        assert isinstance(response_message.raw_transaction, RawTransaction)
        assert response_message.raw_transaction.ledger_id == EthereumCrypto.identifier
        assert len(response.message.raw_transaction.body) == 0

    @pytest.mark.asyncio
    async def test_get_raw_message(
        self,
        gnosis_safe_contract: Tuple[Contract, str],
        ledger_apis_connection: LedgerConnection,
    ) -> None:
        """
        Test get raw message with contract get_raw_transaction.

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(SOME_SKILL_ID)
        request, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
            ledger_id=EthereumCrypto.identifier,
            contract_id=str(GNOSIS_SAFE_PUBLIC_ID),
            callable="get_raw_message",
            contract_address=contract_address,
            kwargs=ContractApiMessage.Kwargs(
                {"agent_address": get_key(ETHEREUM_KEY_DEPLOYER), "token_id": 1}
            ),
        )
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        with mock.patch(
            "packages.valory.contracts.gnosis_safe.contract.GnosisSafeContract.get_raw_message",
            return_value=b"{}",
        ):
            await ledger_apis_connection.send(envelope)
            await asyncio.sleep(0.01)
            response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, ContractApiMessage)
        response_message = cast(ContractApiMessage, response.message)
        assert (
            response_message.performative == ContractApiMessage.Performative.RAW_MESSAGE
        ), "Error: {}".format(response_message.message)
        response_dialogue = contract_api_dialogues.update(response_message)
        assert response_dialogue == contract_api_dialogue
        assert isinstance(response_message.raw_message, RawMessage)
        assert response_message.raw_message.ledger_id == EthereumCrypto.identifier
        assert response.message.raw_message.body == b"{}"

    @pytest.mark.asyncio
    async def test_get_error_message(
        self,
        gnosis_safe_contract: Tuple[Contract, str],
        ledger_apis_connection: LedgerConnection,
        owners: List[str],
        threshold: int,
    ) -> None:
        """
        Test get_error_message method of contract dispatcher.

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
            callable="callable",
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

        with mock.patch.object(
            ledger_apis_connection._contract_dispatcher.contract_registry,  # type: ignore
            "make",
            return_value=None,
        ):
            await ledger_apis_connection.send(envelope)
            await asyncio.sleep(0.01)
            response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, ContractApiMessage)
        response_message = cast(ContractApiMessage, response.message)
        assert (
            response_message.performative == ContractApiMessage.Performative.ERROR
        ), "Error: {}".format(response_message.message)
