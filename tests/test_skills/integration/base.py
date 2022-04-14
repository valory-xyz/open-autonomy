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

"""Integration tests for various transaction settlement skill's failure modes."""


import asyncio
import os
import tempfile
from pathlib import Path
from threading import Thread
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import DecisionMakerHandler
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.protocols.base import Address, Message
from aea.skills.base import Handler
from aea_ledger_ethereum import EthereumApi
from web3 import HTTPProvider, Web3
from web3.providers import BaseProvider

from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.liquidity_rebalancing_abci.behaviours import (
    LiquidityRebalancingConsensusBehaviour,
)
from packages.valory.skills.liquidity_rebalancing_abci.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
)
from packages.valory.skills.liquidity_rebalancing_abci.rounds import (
    PeriodState as LiquidityRebalancingPeriodState,
)
from packages.valory.skills.oracle_abci.behaviours import (
    OracleAbciAppConsensusBehaviour,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    PeriodState as PriceEstimationPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.handlers import SigningHandler
from packages.valory.skills.transaction_settlement_abci.rounds import (
    PeriodState as TxSettlementPeriodState,
)

from tests.conftest import ROOT_DIR, make_ledger_api_connection
from tests.fixture_helpers import HardHatAMMBaseTest
from tests.helpers.contracts import get_register_contract
from tests.test_skills.base import FSMBehaviourBaseCase


HandlersType = List[Optional[Handler]]
ExpectedContentType = List[
    Optional[
        Dict[
            str,
            Any,
        ]
    ]
]
ExpectedTypesType = List[
    Optional[
        Dict[
            str,
            Any,
        ]
    ]
]


class _IntegrationBaseCase(FSMBehaviourBaseCase):
    """Base test class for integration tests."""

    running_loop: asyncio.AbstractEventLoop
    thread_loop: Thread
    multiplexer: Multiplexer
    decision_maker: DecisionMaker
    agents: Dict[str, Address] = {
        "0xBcd4042DE499D14e55001CcbB24a551F3b954096": "0xf214f2b2cd398c806f84e317254e0f0b801d0643303237d97a22a48e01628897",
        "0x71bE63f3384f5fb98995898A86B02Fb2426c5788": "0x701b615bbdfb9de65240bc28bd21bbc0d996645a3dd57e7b12bc2bdf6f192c82",
        "0xFABB0ac9d68B0B445fB7357272Ff202C5651694a": "0xa267530f49f8280200edf313ee7af6b827f2a8bce2897751d06a843f644967b1",
        "0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec": "0x47c99abed3324a2707c28affff1267e45918ec8c3f20b8aa892e8b065d2942dd",
    }
    current_agent: Address

    @classmethod
    def _setup_class(cls, **kwargs: Any) -> None:
        """Setup class."""

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        # set up a multiplexer with the required connections
        cls.running_loop = asyncio.new_event_loop()
        cls.thread_loop = Thread(target=cls.running_loop.run_forever)
        cls.thread_loop.start()
        cls.multiplexer = Multiplexer(
            [make_ledger_api_connection()], loop=cls.running_loop
        )
        cls.multiplexer.connect()

        # hardhat configuration
        # setup decision maker
        with tempfile.TemporaryDirectory() as temp_dir:
            fp = os.path.join(temp_dir, "key.txt")
            f = open(fp, "w")
            f.write(cls.agents[next(iter(cls.agents))])
            f.close()
            wallet = Wallet(private_key_paths={"ethereum": str(fp)})
        identity = Identity(
            "test_agent_name",
            addresses=wallet.addresses,
            public_keys=wallet.public_keys,
            default_address_key="ethereum",
        )
        cls._skill._skill_context._agent_context._identity = identity  # type: ignore
        cls.current_agent = identity.address

        cls.decision_maker = DecisionMaker(
            decision_maker_handler=DecisionMakerHandler(identity, wallet, {})
        )
        cls._skill._skill_context._agent_context._decision_maker_message_queue = (  # type: ignore
            cls.decision_maker.message_in_queue
        )
        cls._skill.skill_context._agent_context._decision_maker_address = (  # type: ignore
            "decision_maker"
        )

    @classmethod
    def teardown(cls) -> None:
        """Tear down the multiplexer."""
        super().teardown()
        cls.multiplexer.disconnect()
        cls.running_loop.call_soon_threadsafe(cls.running_loop.stop)
        cls.thread_loop.join()

    def get_message_from_decision_maker_inbox(self) -> Optional[Message]:
        """Get message from decision maker inbox."""
        if self._skill.skill_context.decision_maker_message_queue.empty():
            return None
        return self._skill.skill_context.decision_maker_message_queue.protected_get(  # type: ignore
            self.decision_maker._queue_access_code, block=True
        )

    def process_message_cycle(
        self,
        handler: Optional[Handler] = None,
        expected_content: Optional[Dict] = None,
        expected_types: Optional[Dict] = None,
    ) -> Optional[Message]:
        """
        Processes one request-response type message cycle.

        Steps:
        1. Calls act on behaviour to generate outgoing message
        2. Checks for message in outbox
        3. Sends message to multiplexer and waits for response.
        4. Passes message to handler
        5. Calls act on behaviour to process incoming message

        :param handler: the handler to handle a potential incoming message
        :param expected_content: the content to be expected
        :param expected_types: the types to be expected
        :return: the incoming message
        """
        self.behaviour.act_wrapper()
        incoming_message = None

        if type(handler) == SigningHandler:
            self.assert_quantity_in_decision_making_queue(1)
            message = self.get_message_from_decision_maker_inbox()
            assert message is not None, "No message in outbox."
            self.decision_maker.handle(message)
            if handler is not None:
                incoming_message = self.decision_maker.message_out_queue.get(block=True)
                assert isinstance(incoming_message, Message)
        else:
            self.assert_quantity_in_outbox(1)
            message = self.get_message_from_outbox()
            assert message is not None, "No message in outbox."
            self.multiplexer.put(
                Envelope(
                    to=message.to,
                    sender=message.sender,
                    message=message,
                    context=None,
                )
            )
            if handler is not None:
                envelope = self.multiplexer.get(block=True)
                assert envelope is not None, "No envelope"
                incoming_message = envelope.message
                assert isinstance(incoming_message, Message)

        if handler is not None:
            assert incoming_message is not None
            if expected_content is not None:
                assert all(
                    [
                        incoming_message._body.get(key, None) == value
                        for key, value in expected_content.items()
                    ]
                ), f"Actual content: {incoming_message._body}, expected: {expected_content}"

            if expected_types is not None:
                assert all(
                    [
                        type(incoming_message._body.get(key, None)) == value_type
                        for key, value_type in expected_types.items()
                    ]
                ), "Content type mismatch"
            handler.handle(incoming_message)
            return incoming_message
        return None

    def process_n_messages(
        self,
        ncycles: int,
        period_state: Union[
            TxSettlementPeriodState,
            PriceEstimationPeriodState,
            LiquidityRebalancingPeriodState,
            None,
        ] = None,
        state_id: Optional[str] = None,
        handlers: Optional[HandlersType] = None,
        expected_content: Optional[ExpectedContentType] = None,
        expected_types: Optional[ExpectedTypesType] = None,
    ) -> Tuple[Optional[Message], ...]:
        """
        Process n message cycles.

        :param state_id: the behaviour to fast forward to
        :param ncycles: the number of message cycles to process
        :param period_state: a period_state
        :param handlers: a list of handlers
        :param expected_content: the expected_content
        :param expected_types: the expected type

        :return: tuple of incoming messages
        """
        handlers = [None] * ncycles if handlers is None else handlers
        expected_content = (
            [None] * ncycles if expected_content is None else expected_content
        )
        expected_types = [None] * ncycles if expected_types is None else expected_types
        assert (
            len(expected_content) == len(expected_types)
            and len(expected_content) == len(handlers)
            and len(expected_content) == ncycles
        ), "Number of cycles, handlers, contents and types does not match"

        if state_id is not None and period_state is not None:
            self.fast_forward_to_state(
                behaviour=self.behaviour,
                state_id=state_id,
                period_state=period_state,
            )
            assert cast(BaseState, self.behaviour.current_state).state_id == state_id

        incoming_messages = []
        for i in range(ncycles):
            incoming_message = self.process_message_cycle(
                handlers[i], expected_content[i], expected_types[i]
            )
            incoming_messages.append(incoming_message)

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        return tuple(incoming_messages)


class _SafeConfiguredIntegrationBaseCase(_IntegrationBaseCase):
    """Base test class for integration tests with Gnosis, but no contract, deployed."""

    safe_owners: Dict[str, Crypto]
    keeper_address: str

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        # safe configuration
        cls.safe_owners = {}
        for address, p_key in cls.agents.items():
            with tempfile.TemporaryDirectory() as temp_dir:
                fp = os.path.join(temp_dir, "key.txt")
                f = open(fp, "w")
                f.write(p_key)
                f.close()
                crypto = make_crypto("ethereum", private_key_path=str(fp))
            cls.safe_owners[address] = crypto
        cls.keeper_address = cls.current_agent
        assert cls.keeper_address in cls.safe_owners


class _HarHatIntegrationBaseCase(_IntegrationBaseCase):
    """Base test class for integration tests with HardHat provider."""

    hardhat_provider: BaseProvider

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        # create an API for HardHat
        cls.hardhat_provider = Web3(
            provider=HTTPProvider("http://localhost:8545")
        ).provider


class GnosisIntegrationBaseCase(
    _SafeConfiguredIntegrationBaseCase, _HarHatIntegrationBaseCase, HardHatAMMBaseTest
):
    """Base test class for integration tests in a Hardhat environment, with Gnosis deployed."""

    # TODO change this class to use the `HardHatGnosisBaseTest` instead of `HardHatAMMBaseTest`.

    safe_contract_address: str = "0x68FCdF52066CcE5612827E872c45767E5a1f6551"
    ethereum_api: EthereumApi
    gnosis_instance: Any

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        # register gnosis and offchain aggregator contracts
        directory = Path(ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe")
        gnosis = get_register_contract(directory)
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "offchain_aggregator"
        )
        _ = get_register_contract(directory)

        cls.ethereum_api = make_ledger_api("ethereum")
        cls.gnosis_instance = gnosis.get_instance(
            cls.ethereum_api, cls.safe_contract_address
        )


class AMMIntegrationBaseCase(
    _SafeConfiguredIntegrationBaseCase, _HarHatIntegrationBaseCase, HardHatAMMBaseTest
):
    """Base test class for integration tests in a Hardhat environment, with AMM interaction."""

    safe_contract_address: str = "0x68FCdF52066CcE5612827E872c45767E5a1f6551"
    ethereum_api: EthereumApi
    gnosis_instance: Any

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        # register all contracts we need
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_router_02"
        )
        _ = get_register_contract(directory)
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_erc20"
        )
        _ = get_register_contract(directory)
        directory = Path(ROOT_DIR, "packages", "valory", "contracts", "multisend")
        _ = get_register_contract(directory)
        directory = Path(ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe")
        gnosis = get_register_contract(directory)

        cls.ethereum_api = make_ledger_api("ethereum")
        cls.gnosis_instance = gnosis.get_instance(
            cls.ethereum_api, cls.safe_contract_address
        )
