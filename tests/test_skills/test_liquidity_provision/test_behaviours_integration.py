# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
"""Tests for valory/liquidity_provision skill behaviours with Hardhat."""
import asyncio
import binascii
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from threading import Thread
from typing import Any, Dict, List, Optional, Tuple, cast

from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import (
    DecisionMakerHandler as DefaultDecisionMakerHandler,
)
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    State,
    TransactionDigest,
    TransactionReceipt,
)
from aea.identity.base import Identity
from aea.mail.base import Envelope, Message
from aea.multiplexer import Multiplexer
from aea.skills.base import Handler
from aea_ledger_ethereum import EthereumApi
from web3 import Web3

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.liquidity_provision.behaviours import (
    EnterPoolTransactionHashBehaviour,
    EnterPoolTransactionSendBehaviour,
    EnterPoolTransactionSignatureBehaviour,
    EnterPoolTransactionValidationBehaviour,
    ExitPoolTransactionHashBehaviour,
    ExitPoolTransactionSendBehaviour,
    ExitPoolTransactionSignatureBehaviour,
    ExitPoolTransactionValidationBehaviour,
    SwapBackTransactionHashBehaviour,
    SwapBackTransactionSendBehaviour,
    SwapBackTransactionSignatureBehaviour,
    SwapBackTransactionValidationBehaviour,
    get_strategy_update,
)
from packages.valory.skills.liquidity_provision.handlers import SigningHandler
from packages.valory.skills.liquidity_provision.rounds import PeriodState
from packages.valory.skills.transaction_settlement_abci.payloads import SignaturePayload

from tests.conftest import ROOT_DIR, make_ledger_api_connection
from tests.fixture_helpers import HardHatAMMBaseTest
from tests.helpers.contracts import get_register_contract
from tests.test_skills.test_liquidity_provision.test_behaviours import (
    LiquidityProvisionBehaviourBaseCase,
)


DEFAULT_GAS = 1000000
DEFAULT_GAS_PRICE = 1000000
HANDLERS = List[Optional[Handler]]
EXPECTED_CONTENT = List[
    Optional[
        Dict[
            str,
            Any,
        ]
    ]
]
EXPECTED_TYPES = List[
    Optional[
        Dict[
            str,
            Any,
        ]
    ]
]


class TestLiquidityProvisionHardhat(
    LiquidityProvisionBehaviourBaseCase, HardHatAMMBaseTest
):
    """Test liquidity pool behaviours in a Hardhat environment."""

    running_loop: asyncio.AbstractEventLoop
    thread_loop: Thread
    multiplexer: Multiplexer
    decision_maker: DecisionMaker
    strategy: Dict
    default_period_state_enter: PeriodState
    default_period_state_exit: PeriodState
    default_period_state_swap_back: PeriodState
    safe_owners: Dict
    safe_contract_address: str
    multisend_contract_address: str
    router_contract_address: str
    keeper_address: str
    multisend_data_enter: str
    multisend_data_exit: str
    multisend_data_swap_back: str
    most_voted_tx_hash_enter: str
    most_voted_tx_hash_exit: str
    most_voted_tx_hash_swap_back: str
    ethereum_api: EthereumApi
    gnosis_instance: Any
    multisend_instance: Any
    router_instance: Any

    @classmethod
    def _setup_class(cls, **kwargs: Any) -> None:
        """Setup class."""
        pass

    def get_decoded_logs(self, gnosis_instance: Any, receipt: dict) -> List[Dict]:
        """Get decoded logs."""
        # Find ABI events
        decoded_logs = []
        abi_events = [abi for abi in gnosis_instance.abi if abi["type"] == "event"]
        for logs in receipt["logs"]:
            for receipt_event_signature_hex in logs["topics"]:
                for event in abi_events:
                    # Get event signature components
                    name = event["name"]
                    inputs = [param["type"] for param in event["inputs"]]
                    inputs_ = ",".join(inputs)
                    # Hash event signature
                    event_signature_text = f"{name}({inputs_})"
                    event_signature_hex = Web3.toHex(
                        Web3.keccak(text=event_signature_text)
                    )
                    # Find match between log's event signature and ABI's event signature
                    if event_signature_hex == receipt_event_signature_hex:
                        decoded_log = gnosis_instance.events[
                            event["name"]
                        ]().processReceipt(receipt)
                        decoded_logs.append({name: decoded_log})
        return decoded_logs

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()
        # register all contracts we need
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_router_02"
        )
        router = get_register_contract(directory)
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "uniswap_v2_erc20"
        )
        _ = get_register_contract(directory)
        directory = Path(ROOT_DIR, "packages", "valory", "contracts", "multisend")
        multisend = get_register_contract(directory)
        directory = Path(ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe")
        gnosis = get_register_contract(directory)
        # setup a multiplexer with the required connections
        cls.running_loop = asyncio.new_event_loop()
        cls.thread_loop = Thread(target=cls.running_loop.run_forever)
        cls.thread_loop.start()
        cls.multiplexer = Multiplexer(
            [make_ledger_api_connection()], loop=cls.running_loop
        )
        cls.multiplexer.connect()

        # hardhat configuration
        cls.safe_contract_address = "0x68FCdF52066CcE5612827E872c45767E5a1f6551"
        cls.multisend_contract_address = "0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6"
        cls.router_contract_address = "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0"
        safe_owners = {
            "0xBcd4042DE499D14e55001CcbB24a551F3b954096": "0xf214f2b2cd398c806f84e317254e0f0b801d0643303237d97a22a48e01628897",
            "0x71bE63f3384f5fb98995898A86B02Fb2426c5788": "0x701b615bbdfb9de65240bc28bd21bbc0d996645a3dd57e7b12bc2bdf6f192c82",
            "0xFABB0ac9d68B0B445fB7357272Ff202C5651694a": "0xa267530f49f8280200edf313ee7af6b827f2a8bce2897751d06a843f644967b1",
            "0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec": "0x47c99abed3324a2707c28affff1267e45918ec8c3f20b8aa892e8b065d2942dd",
        }
        # setup decision maker
        with tempfile.TemporaryDirectory() as temp_dir:
            fp = os.path.join(temp_dir, "key.txt")
            f = open(fp, "w")
            f.write(safe_owners[next(iter(safe_owners))])
            f.close()
            wallet = Wallet(private_key_paths={"ethereum": str(fp)})
        identity = Identity(
            "test_agent_name",
            addresses=wallet.addresses,
            public_keys=wallet.public_keys,
            default_address_key="ethereum",
        )
        cls._skill._skill_context._agent_context._identity = identity  # type: ignore
        cls.keeper_address = identity.address

        cls.safe_owners = {}
        for address, p_key in safe_owners.items():
            with tempfile.TemporaryDirectory() as temp_dir:
                fp = os.path.join(temp_dir, "key.txt")
                f = open(fp, "w")
                f.write(p_key)
                f.close()
                crypto = make_crypto("ethereum", private_key_path=str(fp))
            cls.safe_owners[address] = crypto
        assert cls.keeper_address in cls.safe_owners

        cls.decision_maker = DecisionMaker(
            decision_maker_handler=DefaultDecisionMakerHandler(identity, wallet, {})
        )
        cls._skill._skill_context._agent_context._decision_maker_message_queue = (  # type: ignore
            cls.decision_maker.message_in_queue
        )
        cls._skill.skill_context._agent_context._decision_maker_address = (  # type: ignore
            "decision_maker"
        )
        cls.multisend_data_enter = "8d80ff0a000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000005d600dc64a140aa3e981100a9beca4e685f962f0cf6c900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001048803dbee00000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000271000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c90000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd8200a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001048803dbee00000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000271000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c90000000000000000000000009a676e781a523b5d0c0e43731313a708cb607508000dcd1bf9a1b36ce34237eeafef220932846bcd8200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000104e8e337000000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd820000000000000000000000009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000001f400000000000000000000000000000000000000000000000000000000000001f400000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef00000000000000000000"
        cls.multisend_data_exit = "8d80ff0a000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001d20050cd56fb094f8f06063066a619d898475dd3eede00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e4baa2abde0000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd820000000000000000000000009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000001f400000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef0000000000000000000000000000"
        cls.multisend_data_swap_back = "8d80ff0a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000034b00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd82000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c900a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef00000000000000000000000000000000000000000000000000000000000000020000000000000000000000009a676e781a523b5d0c0e43731313a708cb607508000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c9000dcd1bf9a1b36ce34237eeafef220932846bcd8200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

        cls.most_voted_tx_hash_enter = (
            "109709ac6f55b4023671b90aca07391d15f922c1f4c47e85990edaff826e8c35"
        )
        cls.most_voted_tx_hash_exit = (
            "68645602edac4b5f12ce78c8d18226e9b3556478e0b7f3a8a96dc172bc110d8f"
        )
        cls.most_voted_tx_hash_swap_back = (
            "58d8c8e1376e3a2aaf937a9b17a9ac809ba91e79ca780324ea937ba9909571af"
        )

        # setup default objects
        cls.strategy = get_strategy_update()
        cls.strategy[
            "deadline"
        ] = 1672527599  # corresponds to datetime.datetime(2022, 12, 31, 23, 59, 59) using  datetime.datetime.fromtimestamp(.)
        cls.default_period_state_enter = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash=cls.most_voted_tx_hash_enter,
                    safe_contract_address=cls.safe_contract_address,
                    most_voted_keeper_address=cls.keeper_address,
                    most_voted_strategy=cls.strategy,
                    multisend_contract_address=cls.multisend_contract_address,
                    router_contract_address=cls.router_contract_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                ),
            )
        )

        cls.default_period_state_exit = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash=cls.most_voted_tx_hash_exit,
                    safe_contract_address=cls.safe_contract_address,
                    most_voted_keeper_address=cls.keeper_address,
                    most_voted_strategy=cls.strategy,
                    multisend_contract_address=cls.multisend_contract_address,
                    router_contract_address=cls.router_contract_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                ),
            )
        )

        cls.default_period_state_swap_back = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash=cls.most_voted_tx_hash_swap_back,
                    safe_contract_address=cls.safe_contract_address,
                    most_voted_keeper_address=cls.keeper_address,
                    most_voted_strategy=cls.strategy,
                    multisend_contract_address=cls.multisend_contract_address,
                    router_contract_address=cls.router_contract_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                ),
            )
        )

        cls.ethereum_api = make_ledger_api("ethereum")
        cls.gnosis_instance = gnosis.get_instance(
            cls.ethereum_api, cls.safe_contract_address
        )
        cls.multisend_instance = multisend.get_instance(
            cls.ethereum_api, cls.multisend_contract_address
        )
        cls.router_instance = router.get_instance(
            cls.ethereum_api, cls.router_contract_address
        )
        # import eth_event  # noqa: E800
        # cls.topic_map_gnosis = eth_event.get_topic_map(cls.gnosis_instance.abi)  # noqa: E800
        # cls.topic_map_multisend = eth_event.get_topic_map(cls.multisend_instance.abi)  # noqa: E800
        # cls.topic_map_router = eth_event.get_topic_map(cls.router_instance.abi)  # noqa: E800

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
        self.liquidity_provision_behaviour.act_wrapper()

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

    def process_n_messsages(
        self,
        state_id: str,
        ncycles: int,
        period_state: PeriodState,
        handlers: Optional[HANDLERS] = None,
        expected_content: Optional[EXPECTED_CONTENT] = None,
        expected_types: Optional[EXPECTED_TYPES] = None,
    ) -> Tuple[Optional[Message], ...]:
        """
        Process n message cycles.

        :param: state_id: the behaviour to fast forward to
        :param: ncycles: the number of message cycles to process
        :param: handlers: a list of handlers
        :param expected_content: the expected_content
        :param expected_types: the expected type
        :param: period_state: a period_state
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

        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == state_id
        )

        incoming_messages = []
        for i in range(ncycles):
            incoming_message = self.process_message_cycle(
                handlers[i], expected_content[i], expected_types[i]
            )
            incoming_messages.append(incoming_message)

        self.liquidity_provision_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        return tuple(incoming_messages)

    # Enter pool behaviours

    def test_enter_pool_tx_hash_behaviour(self) -> None:
        """test_enter_pool_tx_hash_behaviour"""
        timestamp = self.ethereum_api.api.eth.get_block("latest")["timestamp"]
        assert self.strategy["deadline"] > timestamp, "Increase timestamp!"
        cycles = 8
        handlers: List[Optional[Handler]] = [self.contract_handler] * cycles
        expected_content: EXPECTED_CONTENT = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            }
        ] * cycles
        expected_types: EXPECTED_TYPES = [
            {
                "raw_transaction": RawTransaction,
            }
        ] * cycles
        _, _, _, _, _, _, msg_a, msg_b = self.process_n_messsages(
            EnterPoolTransactionHashBehaviour.state_id,
            cycles,
            self.default_period_state_enter,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg_a is not None and isinstance(msg_a, ContractApiMessage)
        tx_data = cast(str, msg_a.raw_transaction.body["data"])[2:]
        assert tx_data == self.multisend_data_enter
        assert msg_b is not None and isinstance(msg_b, ContractApiMessage)
        tx_hash = cast(str, msg_b.raw_transaction.body["tx_hash"])[2:]
        assert tx_hash == self.most_voted_tx_hash_enter

    def test_enter_pool_tx_sign_behaviour(self) -> None:
        """test_enter_pool_tx_sign_behaviour"""
        # value taken from test_enter_pool_tx_hash_behaviour flow
        period_state = cast(
            PeriodState,
            self.default_period_state_enter.update(
                most_voted_tx_hash=self.most_voted_tx_hash_enter
            ),
        )

        cycles = 1
        handlers: HANDLERS = [self.signing_handler] * cycles
        expected_content: EXPECTED_CONTENT = [
            {"performative": SigningMessage.Performative.SIGNED_MESSAGE}  # type: ignore
        ] * cycles
        expected_types: EXPECTED_TYPES = [None] * cycles
        self.process_n_messsages(
            EnterPoolTransactionSignatureBehaviour.state_id,
            cycles,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )

    def test_enter_exit_swap_back_send_and_validate_behaviour(self) -> None:
        """test_enter_pool_tx_send_behaviour"""

        # send
        participant_to_signature = {
            address: SignaturePayload(
                sender=address,
                signature=crypto.sign_message(
                    binascii.unhexlify(self.most_voted_tx_hash_enter),
                    is_deprecated_mode=True,
                )[2:],
            )
            for address, crypto in self.safe_owners.items()
        }
        # values taken from test_enter_pool_tx_hash_behaviour flow
        period_state = cast(
            PeriodState,
            self.default_period_state_enter.update(
                most_voted_tx_hash=self.most_voted_tx_hash_enter,
                most_voted_tx_data=self.multisend_data_enter,
                participant_to_signature=participant_to_signature,
            ),
        )
        handlers: HANDLERS = [
            self.contract_handler,
            self.signing_handler,
            self.ledger_handler,
        ]
        expected_content: EXPECTED_CONTENT = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": SigningMessage.Performative.SIGNED_TRANSACTION  # type: ignore
            },
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_DIGEST  # type: ignore
            },
        ]
        expected_types: EXPECTED_TYPES = [
            {
                "raw_transaction": RawTransaction,
            },
            {
                "signed_transaction": SignedTransaction,
            },
            {
                "transaction_digest": TransactionDigest,
            },
        ]
        _, _, msg = self.process_n_messsages(
            EnterPoolTransactionSendBehaviour.state_id,
            3,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg is not None and isinstance(msg, LedgerApiMessage)
        tx_digest = msg.transaction_digest.body

        # validate
        period_state = cast(
            PeriodState,
            self.default_period_state_enter.update(
                final_tx_hash=tx_digest,
                most_voted_tx_hash=self.most_voted_tx_hash_enter,
                most_voted_tx_data=self.multisend_data_enter,
                participant_to_signature=participant_to_signature,
            ),
        )
        handlers = [
            self.ledger_handler,
            self.contract_handler,
        ]
        expected_content = [
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT  # type: ignore
            },
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
        ]
        expected_types = [
            {
                "transaction_receipt": TransactionReceipt,
            },
            {
                "state": State,
            },
        ]
        _, msg = self.process_n_messsages(
            EnterPoolTransactionValidationBehaviour.state_id,
            2,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg is not None and isinstance(msg, ContractApiMessage)
        assert msg.state.body["verified"], f"Message not verified: {msg.state.body}"
        # eventually replace with https://pypi.org/project/eth-event/
        receipt = self.ethereum_api.get_transaction_receipt(tx_digest)
        logs = self.get_decoded_logs(self.gnosis_instance, receipt)
        assert all(
            [key != "ExecutionFailure" for dict_ in logs for key in dict_.keys()]
        )
        # import eth_event  # noqa: E800
        # decoded_logs = eth_event.decode_logs(receipt["logs"], self.topic_map_gnosis)  # noqa: E800
        # print(decoded_logs)  # noqa: E800
        # trace = self.ethereum_api.api.provider.make_request("debug_traceTransaction",[tx_digest, {}])  # noqa: E800
        # struct_log = trace['result']['structLogs']  # noqa: E800
        # decoded_trace = eth_event.decode_trace(struct_log, self.topic_map_gnosis, initial_address="0x5fc8d32690cc91d4c39d9d3abcbd16989f875707")  # noqa: E800

        """test_exit_pool_tx_send_behaviour"""

        strategy = deepcopy(self.strategy)
        strategy["safe_nonce"] = 1

        # send
        participant_to_signature = {
            address: SignaturePayload(
                sender=address,
                signature=crypto.sign_message(
                    binascii.unhexlify(self.most_voted_tx_hash_exit),
                    is_deprecated_mode=True,
                )[2:],
            )
            for address, crypto in self.safe_owners.items()
        }
        # values taken from test_exit_pool_tx_hash_behaviour flow
        period_state = cast(
            PeriodState,
            self.default_period_state_exit.update(
                most_voted_tx_hash=self.most_voted_tx_hash_exit,
                most_voted_tx_data=self.multisend_data_exit,
                participant_to_signature=participant_to_signature,
                most_voted_strategy=strategy,
            ),
        )
        handlers = [
            self.contract_handler,
            self.signing_handler,
            self.ledger_handler,
        ]
        expected_content = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": SigningMessage.Performative.SIGNED_TRANSACTION  # type: ignore
            },
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_DIGEST  # type: ignore
            },
        ]
        expected_types = [
            {
                "raw_transaction": RawTransaction,
            },
            {
                "signed_transaction": SignedTransaction,
            },
            {
                "transaction_digest": TransactionDigest,
            },
        ]
        _, _, msg = self.process_n_messsages(
            ExitPoolTransactionSendBehaviour.state_id,
            3,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg is not None and isinstance(msg, LedgerApiMessage)
        tx_digest = msg.transaction_digest.body

        # validate
        period_state = cast(
            PeriodState,
            self.default_period_state_exit.update(
                final_tx_hash=tx_digest,
                most_voted_tx_hash=self.most_voted_tx_hash_exit,
                most_voted_tx_data=self.multisend_data_exit,
                participant_to_signature=participant_to_signature,
            ),
        )
        handlers = [
            self.ledger_handler,
            self.contract_handler,
        ]
        expected_content = [
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT  # type: ignore
            },
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
        ]
        expected_types = [
            {
                "transaction_receipt": TransactionReceipt,
            },
            {
                "state": State,
            },
        ]
        _, msg = self.process_n_messsages(
            ExitPoolTransactionValidationBehaviour.state_id,
            2,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg is not None and isinstance(msg, ContractApiMessage)
        assert msg.state.body["verified"], f"Message not verified: {msg.state.body}"
        # eventually replace with https://pypi.org/project/eth-event/
        receipt = self.ethereum_api.get_transaction_receipt(tx_digest)
        logs = self.get_decoded_logs(self.gnosis_instance, receipt)

        assert all(
            [key != "ExecutionFailure" for dict_ in logs for key in dict_.keys()]
        )

        """test_swap_back_tx_send_behaviour"""

        strategy = deepcopy(self.strategy)
        strategy["safe_nonce"] = 2

        # send
        participant_to_signature = {
            address: SignaturePayload(
                sender=address,
                signature=crypto.sign_message(
                    binascii.unhexlify(self.most_voted_tx_hash_swap_back),
                    is_deprecated_mode=True,
                )[2:],
            )
            for address, crypto in self.safe_owners.items()
        }
        # values taken from test_swap_back_tx_hash_behaviour flow
        period_state = cast(
            PeriodState,
            self.default_period_state_swap_back.update(
                most_voted_tx_hash=self.most_voted_tx_hash_swap_back,
                most_voted_tx_data=self.multisend_data_swap_back,
                participant_to_signature=participant_to_signature,
                most_voted_strategy=strategy,
            ),
        )
        handlers = [
            self.contract_handler,
            self.signing_handler,
            self.ledger_handler,
        ]
        expected_content = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": SigningMessage.Performative.SIGNED_TRANSACTION  # type: ignore
            },
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_DIGEST  # type: ignore
            },
        ]
        expected_types = [
            {
                "raw_transaction": RawTransaction,
            },
            {
                "signed_transaction": SignedTransaction,
            },
            {
                "transaction_digest": TransactionDigest,
            },
        ]
        _, _, msg = self.process_n_messsages(
            SwapBackTransactionSendBehaviour.state_id,
            3,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg is not None and isinstance(msg, LedgerApiMessage)
        tx_digest = msg.transaction_digest.body

        # validate
        period_state = cast(
            PeriodState,
            self.default_period_state_swap_back.update(
                final_tx_hash=tx_digest,
                most_voted_tx_hash=self.most_voted_tx_hash_swap_back,
                most_voted_tx_data=self.multisend_data_swap_back,
                participant_to_signature=participant_to_signature,
            ),
        )
        handlers = [
            self.ledger_handler,
            self.contract_handler,
        ]
        expected_content = [
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT  # type: ignore
            },
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
        ]
        expected_types = [
            {
                "transaction_receipt": TransactionReceipt,
            },
            {
                "state": State,
            },
        ]
        _, msg = self.process_n_messsages(
            SwapBackTransactionValidationBehaviour.state_id,
            2,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg is not None and isinstance(msg, ContractApiMessage)
        assert msg.state.body["verified"], f"Message not verified: {msg.state.body}"
        # eventually replace with https://pypi.org/project/eth-event/
        receipt = self.ethereum_api.get_transaction_receipt(tx_digest)
        logs = self.get_decoded_logs(self.gnosis_instance, receipt)

        assert all(
            [key != "ExecutionFailure" for dict_ in logs for key in dict_.keys()]
        )

    # Exit pool behaviours

    def test_exit_pool_tx_hash_behaviour(self) -> None:
        """test_exit_pool_tx_hash_behaviour"""
        strategy = deepcopy(self.strategy)
        strategy["safe_nonce"] = 1

        period_state = cast(
            PeriodState,
            self.default_period_state_exit.update(most_voted_strategy=strategy),
        )

        timestamp = self.ethereum_api.api.eth.get_block("latest")["timestamp"]
        assert self.strategy["deadline"] > timestamp, "Increase timestamp!"
        cycles = 4
        handlers: List[Optional[Handler]] = [self.contract_handler] * cycles
        expected_content: EXPECTED_CONTENT = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            }
        ] * cycles
        expected_types: EXPECTED_TYPES = [
            {
                "raw_transaction": RawTransaction,
            }
        ] * cycles
        _, _, msg_a, msg_b = self.process_n_messsages(
            ExitPoolTransactionHashBehaviour.state_id,
            cycles,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg_a is not None and isinstance(msg_a, ContractApiMessage)
        tx_data = cast(str, msg_a.raw_transaction.body["data"])[2:]
        assert tx_data == self.multisend_data_exit
        assert msg_b is not None and isinstance(msg_b, ContractApiMessage)
        tx_hash = cast(str, msg_b.raw_transaction.body["tx_hash"])[2:]
        assert tx_hash == self.most_voted_tx_hash_exit

    def test_exit_pool_tx_sign_behaviour(self) -> None:
        """test_exit_pool_tx_sign_behaviour"""

        strategy = deepcopy(self.strategy)
        strategy["safe_nonce"] = 1

        # values taken from test_exit_pool_tx_hash_behaviour flow
        period_state = cast(
            PeriodState,
            self.default_period_state_exit.update(
                most_voted_tx_hash=self.most_voted_tx_hash_exit,
                most_voted_strategy=strategy,
            ),
        )
        cycles = 1
        handlers: HANDLERS = [self.signing_handler] * cycles
        expected_content: EXPECTED_CONTENT = [
            {"performative": SigningMessage.Performative.SIGNED_MESSAGE}  # type: ignore
        ] * cycles
        expected_types: EXPECTED_TYPES = [None] * cycles
        self.process_n_messsages(
            ExitPoolTransactionSignatureBehaviour.state_id,
            cycles,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )

    # Swap back behaviours

    def test_swap_back_tx_hash_behaviour(self) -> None:
        """test_swap_back_tx_hash_behaviour"""
        strategy = deepcopy(self.strategy)
        strategy["safe_nonce"] = 2

        period_state = cast(
            PeriodState,
            self.default_period_state_swap_back.update(most_voted_strategy=strategy),
        )

        timestamp = self.ethereum_api.api.eth.get_block("latest")["timestamp"]
        assert self.strategy["deadline"] > timestamp, "Increase timestamp!"
        cycles = 5
        handlers: List[Optional[Handler]] = [self.contract_handler] * cycles
        expected_content: EXPECTED_CONTENT = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            }
        ] * cycles
        expected_types: EXPECTED_TYPES = [
            {
                "raw_transaction": RawTransaction,
            }
        ] * cycles
        _, _, _, msg_a, msg_b = self.process_n_messsages(
            SwapBackTransactionHashBehaviour.state_id,
            cycles,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg_a is not None and isinstance(msg_a, ContractApiMessage)
        tx_data = cast(str, msg_a.raw_transaction.body["data"])[2:]
        assert tx_data == self.multisend_data_swap_back
        assert msg_b is not None and isinstance(msg_b, ContractApiMessage)
        tx_hash = cast(str, msg_b.raw_transaction.body["tx_hash"])[2:]
        assert tx_hash == self.most_voted_tx_hash_swap_back

    def test_swap_back_tx_sign_behaviour(self) -> None:
        """test_swap_back_tx_sign_behaviour"""

        strategy = deepcopy(self.strategy)
        strategy["safe_nonce"] = 2

        # values taken from test_swap_back_tx_hash_behaviour flow
        period_state = cast(
            PeriodState,
            self.default_period_state_swap_back.update(
                most_voted_tx_hash=self.most_voted_tx_hash_swap_back,
                most_voted_strategy=strategy,
            ),
        )
        cycles = 1
        handlers: HANDLERS = [self.signing_handler] * cycles
        expected_content: EXPECTED_CONTENT = [
            {"performative": SigningMessage.Performative.SIGNED_MESSAGE}  # type: ignore
        ] * cycles
        expected_types: EXPECTED_TYPES = [None] * cycles
        self.process_n_messsages(
            SwapBackTransactionSignatureBehaviour.state_id,
            cycles,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
