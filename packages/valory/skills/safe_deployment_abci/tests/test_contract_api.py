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

# pylint: skip-file

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple, cast
from unittest import mock

import pytest
from aea.common import Address
from aea.contracts.base import Contract
from aea.crypto.ledger_apis import LedgerApi
from aea.crypto.registries import make_crypto
from aea.helpers.transaction.base import RawMessage, RawTransaction, State
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea_ledger_ethereum import EthereumCrypto
from aea_test_autonomy.configurations import ETHEREUM_KEY_DEPLOYER, KEY_PAIRS, get_key
from aea_test_autonomy.docker.base import skip_docker_tests
from aea_test_autonomy.fixture_helpers import hardhat_addr  # noqa: F401
from aea_test_autonomy.fixture_helpers import hardhat_port  # noqa: F401
from aea_test_autonomy.fixture_helpers import (  # noqa: F401
    gnosis_safe_hardhat_scope_class,
)
from aea_test_autonomy.helpers.contracts import get_register_contract
from web3 import Web3

from packages.valory.connections.ledger.connection import LedgerConnection
from packages.valory.connections.ledger.tests.conftest import ganache_addr  # noqa: F401
from packages.valory.connections.ledger.tests.conftest import ganache_port  # noqa: F401
from packages.valory.connections.ledger.tests.conftest import ledger_api  # noqa: F401
from packages.valory.connections.ledger.tests.conftest import (  # noqa: F401
    ethereum_testnet_config,
    ledger_apis_connection,
)
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_PUBLIC_ID,
)
from packages.valory.protocols.contract_api.dialogues import ContractApiDialogue
from packages.valory.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.safe_deployment_abci import PUBLIC_ID as SKILL_ID


NB_OWNERS = 4
THRESHOLD = 1
PACKAGE_DIR = Path(__file__).parent.parent


@pytest.fixture()
def key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for hardhat."""
    return KEY_PAIRS


@pytest.fixture()
def owners(key_pairs: List[Tuple[str, str]]) -> List[str]:
    """Get the owners."""
    return [Web3.toChecksumAddress(t[0]) for t in key_pairs[:NB_OWNERS]]


@pytest.fixture()
def threshold() -> int:
    """Returns the amount of threshold."""
    return THRESHOLD


@pytest.fixture()
def gnosis_safe_contract(
    ledger_api: LedgerApi,  # noqa: F811
    owners: List[str],
    threshold: int,
) -> Generator[Tuple[Contract, str], None, None]:
    """
    Instantiate an Gnosis Safe contract instance.

    As a side effect, register it to the registry, if not already registered.
    :param ledger_api: ledger_api fixture
    :param owners: onwers fixture
    :param threshold: threshold fixture
    :yield: contract and contract_address
    """
    directory = Path(
        PACKAGE_DIR.parent.parent, "contracts", "gnosis_safe_proxy_factory"
    )
    _ = get_register_contract(
        directory
    )  # we need to load this too as it's a dependency of the gnosis_safe
    directory = Path(PACKAGE_DIR.parent.parent, "contracts", "gnosis_safe")
    contract = get_register_contract(directory)
    crypto = make_crypto(
        EthereumCrypto.identifier, private_key_path=ETHEREUM_KEY_DEPLOYER
    )
    tx = contract.get_deploy_transaction(
        ledger_api=ledger_api,
        deployer_address=crypto.address,
        gas=5000000,
        owners=owners,
        threshold=threshold,
    )
    assert tx is not None
    contract_address = tx.pop("contract_address")  # hack
    assert isinstance(contract_address, str)
    gas = ledger_api.api.eth.estimate_gas(transaction=tx)
    tx["gas"] = gas
    tx_signed = crypto.sign_transaction(tx)
    tx_digest = ledger_api.send_signed_transaction(tx_signed)
    assert tx_digest is not None
    time.sleep(0.5)
    receipt = ledger_api.get_transaction_receipt(tx_digest)
    assert receipt is not None
    # contract_address = ledger_api.get_contract_address(receipt)  # noqa: E800 won't work as it's a proxy
    yield contract, contract_address


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
        gnosis_safe_contract: Tuple[Contract, str],  # noqa: F811
        ledger_apis_connection: LedgerConnection,  # noqa: F811
        owners: List[str],  # noqa: F811
        threshold: int,  # noqa: F811
    ) -> None:
        """
        Test get deploy transaction with contract gnosis_safe_contract.

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        :param owners: fixture
        :param threshold: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(str(SKILL_ID))
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
        gnosis_safe_contract: Tuple[Contract, str],  # noqa: F811
        ledger_apis_connection: LedgerConnection,  # noqa: F811
        owners: List[str],  # noqa: F811
        threshold: int,  # noqa: F811
    ) -> None:
        """
        Test get deploy transaction with contract gnosis_safe_contract ( using _validate_and_call_callable instead of _stub_call method ).

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        :param owners: fixture
        :param threshold: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(str(SKILL_ID))
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
        gnosis_safe_contract: Tuple[Contract, str],  # noqa: F811
        ledger_apis_connection: LedgerConnection,  # noqa: F811
    ) -> None:
        """
        Test get state with contract gnosis_safe_contract.

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(str(SKILL_ID))
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
            GnosisSafeContract,
            "get_state",
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
        gnosis_safe_contract: Tuple[Contract, str],  # noqa: F811
        ledger_apis_connection: LedgerConnection,  # noqa: F811
    ) -> None:
        """
        Test get state with contract gnosis_safe_contract ( using _validate_and_call_callable instead of _call_stub method).

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(str(SKILL_ID))
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
                ledger_api: Any,  # noqa: F811
                contract_address: str,
                *args: Any,
                **kwargs: Any,
            ) -> Dict:
                """Mock `get_state` method from GnosisSafeContract."""
                return {}

            with mock.patch.object(
                GnosisSafeContract,
                "get_state",
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
        gnosis_safe_contract: Tuple[Contract, str],  # noqa: F811
        ledger_apis_connection: LedgerConnection,  # noqa: F811
    ) -> None:
        """
        Test get raw transaction with contract get_raw_transaction.

        NOTE: we already deploy it once at base!

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(str(SKILL_ID))
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

        with mock.patch.object(
            GnosisSafeContract,
            "get_raw_transaction",
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
        gnosis_safe_contract: Tuple[Contract, str],  # noqa: F811
        ledger_apis_connection: LedgerConnection,  # noqa: F811
    ) -> None:
        """
        Test get raw message with contract get_raw_transaction.

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(str(SKILL_ID))
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

        with mock.patch.object(
            GnosisSafeContract,
            "get_raw_message",
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
        gnosis_safe_contract: Tuple[Contract, str],  # noqa: F811
        ledger_apis_connection: LedgerConnection,  # noqa: F811
        owners: List[str],  # noqa: F811
        threshold: int,  # noqa: F811
    ) -> None:
        """
        Test get_error_message method of contract dispatcher.

        :param gnosis_safe_contract: fixture
        :param ledger_apis_connection: fixture
        :param owners: fixture
        :param threshold: fixture
        """
        _, contract_address = gnosis_safe_contract
        contract_api_dialogues = ContractApiDialogues(str(SKILL_ID))
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
