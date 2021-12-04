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
"""Tests for valory/liquidity_provision skill behaviours with Hardhat."""
import asyncio
import binascii
import os
import tempfile
from pathlib import Path
from threading import Thread
from typing import Any, Dict, Optional, Union, cast

from aea.crypto.registries import make_crypto
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import (
    DecisionMakerHandler as DefaultDecisionMakerHandler,
)
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    TransactionDigest,
)
from aea.identity.base import Identity
from aea.mail.base import Envelope, Message
from aea.multiplexer import Multiplexer
from aea.skills.base import Handler

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.liquidity_provision.behaviours import (
    EnterPoolTransactionHashBehaviour,
    EnterPoolTransactionSendBehaviour,
    EnterPoolTransactionSignatureBehaviour,
    ExitPoolTransactionHashBehaviour,
    get_strategy_update,
)
from packages.valory.skills.liquidity_provision.handlers import (
    ContractApiHandler,
    SigningHandler,
)
from packages.valory.skills.liquidity_provision.rounds import PeriodState
from packages.valory.skills.price_estimation_abci.payloads import SignaturePayload

from tests.conftest import ROOT_DIR, make_ledger_api_connection
from tests.fixture_helpers import HardHatAMMBaseTest
from tests.helpers.contracts import get_register_contract
from tests.test_skills.test_liquidity_provision.test_behaviours import (
    LiquidityProvisionBehaviourBaseCase,
)


DEFAULT_GAS = 1000000
DEFAULT_GAS_PRICE = 1000000


class TestEnterPoolTransactionHashBehaviourHardhat(
    LiquidityProvisionBehaviourBaseCase, HardHatAMMBaseTest
):
    """Test liquidity pool behaviours in a Hardhat environment."""

    running_loop: asyncio.AbstractEventLoop
    thread_loop: Thread
    multiplexer: Multiplexer
    decision_maker: DecisionMaker
    strategy: Dict
    default_period_state: PeriodState
    safe_owners: Dict
    safe_contract_address: str
    multisend_contract_address: str
    router_contract_address: str
    keeper_address: str
    multisend_data: str
    most_voted_tx_hash: str

    @classmethod
    def _setup_class(cls, **kwargs: Any) -> None:
        """Setup class."""
        pass

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
        _ = get_register_contract(directory)
        # setup a multiplexer with the required connections
        cls.running_loop = asyncio.new_event_loop()
        cls.thread_loop = Thread(target=cls.running_loop.run_forever)
        cls.thread_loop.start()
        cls.multiplexer = Multiplexer(
            [make_ledger_api_connection()], loop=cls.running_loop
        )
        cls.multiplexer.connect()

        # hardhat configuration
        cls.safe_contract_address = "0xB5d1634d337C36016c2F6c0043Db74A2032f6281"
        cls.multisend_contract_address = "0x5FC8d32690cc91D4c39d9d3abcBD16989F875707"
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
        cls.multisend_data = "8d80ff0a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000053d005fc8d32690cc91d4c39d9d3abcbd16989f8757070000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000010438ed17390000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000b5d1634d337c36016c2f6c0043db74a2032f6281000000000000000000000000000000000000000000000000000000000000012c0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000610178da211fef7d417bc0e6fed39f05609ad7880000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd82005fc8d32690cc91d4c39d9d3abcbd16989f8757070000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000010438ed17390000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000b5d1634d337c36016c2f6c0043db74a2032f6281000000000000000000000000000000000000000000000000000000000000012c0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000610178da211fef7d417bc0e6fed39f05609ad7880000000000000000000000009a676e781a523b5d0c0e43731313a708cb607508005fc8d32690cc91d4c39d9d3abcbd16989f87570700000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff005fc8d32690cc91d4c39d9d3abcbd16989f87570700000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff005fc8d32690cc91d4c39d9d3abcbd16989f87570700000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000104e8e337000000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd820000000000000000000000009a676e781a523b5d0c0e43731313a708cb6075080000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000b5d1634d337c36016c2f6c0043db74a2032f6281000000000000000000000000000000000000000000000000000000000000012c000000"
        cls.most_voted_tx_hash = (
            "73372550056a76035676ec5322a203b053b2c3db14491e7466984862f1d2d641"
        )

        # setup default objects
        cls.strategy = get_strategy_update()
        cls.default_period_state = PeriodState(
            most_voted_tx_hash=cls.most_voted_tx_hash,
            safe_contract_address=cls.safe_contract_address,
            most_voted_keeper_address=cls.keeper_address,
            most_voted_strategy=cls.strategy,
            multisend_contract_address=cls.multisend_contract_address,
            router_contract_address=cls.router_contract_address,
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
    ) -> None:
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

    def process_n_messsages(
        self,
        state_id: str,
        ncycles: int,
        handler: Optional[Handler] = None,
        period_state: Optional[PeriodState] = None,
    ) -> None:
        """
        Process n message cycles.

        :param: state_id: the behaviour to fast forward to
        :param: ncycles: the number of message cycles to process
        :param: handler: a handler
        :param: period_state: a period_state
        """

        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=state_id,
            period_state=period_state if period_state else self.default_period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == state_id
        )

        expected_content: Dict[
            str, Union[ContractApiMessage.Performative, SigningMessage.Performative]
        ]
        expected_types = None

        if type(handler) == ContractApiHandler:
            expected_content = {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            }
            expected_types = {
                "dialogue_reference": tuple,
                "message_id": int,
                "raw_transaction": RawTransaction,
                "target": int,
            }

        elif type(handler) == SigningHandler:
            expected_content = {
                "performative": SigningMessage.Performative.SIGNED_MESSAGE  # type: ignore
            }

        for _ in range(ncycles):
            self.process_message_cycle(handler, expected_content, expected_types)

        self.liquidity_provision_behaviour.act_wrapper()
        self.mock_a2a_transaction()

    # Safe behaviours

    def test_deploy_safe_send_behaviour(self) -> None:
        """test_deploy_safe_behaviour"""

    def test_deploy_safe_validation_behaviour(self) -> None:
        """test_deploy_safe_validation_behaviour"""

    # Enter pool behaviours

    def test_enter_pool_tx_hash_behaviour(self) -> None:
        """test_enter_pool_tx_hash_behaviour"""
        self.process_n_messsages(
            EnterPoolTransactionHashBehaviour.state_id, 7, self.contract_handler
        )

    def test_enter_pool_tx_sign_behaviour(self) -> None:
        """test_enter_pool_tx_sign_behaviour"""
        participants = frozenset(list(self.safe_owners.keys()))

        # first value taken from test_enter_pool_tx_hash_behaviour flow
        period_state = PeriodState(
            most_voted_tx_hash=self.most_voted_tx_hash,
            most_voted_keeper_address=self.keeper_address,
            most_voted_strategy=self.strategy,
            participants=participants,
        )
        self.process_n_messsages(
            EnterPoolTransactionSignatureBehaviour.state_id,
            1,
            self.signing_handler,
            period_state,
        )

    def test_enter_pool_tx_send_behaviour(self) -> None:
        """test_enter_pool_tx_send_behaviour"""

        participant_to_signature = {
            address: SignaturePayload(
                sender=address,
                signature=crypto.sign_message(
                    binascii.unhexlify(self.most_voted_tx_hash), is_deprecated_mode=True
                )[2:],
            )
            for address, crypto in self.safe_owners.items()
        }

        # first two values taken from test_enter_pool_tx_hash_behaviour flow
        period_state = PeriodState(
            most_voted_tx_hash=self.most_voted_tx_hash,
            most_voted_tx_data=self.multisend_data,
            safe_contract_address=self.safe_contract_address,
            most_voted_keeper_address=self.keeper_address,
            most_voted_strategy=self.strategy,
            multisend_contract_address=self.multisend_contract_address,
            router_contract_address=self.router_contract_address,
            participants=frozenset(list(participant_to_signature.keys())),
            participant_to_signature=participant_to_signature,
        )

        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=EnterPoolTransactionSendBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == EnterPoolTransactionSendBehaviour.state_id
        )

        expected_content = {
            "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
        }
        expected_types = {
            "dialogue_reference": tuple,
            "message_id": int,
            "raw_transaction": RawTransaction,
            "target": int,
        }
        self.process_message_cycle(
            self.contract_handler, expected_content, expected_types
        )
        expected_content = {
            "performative": SigningMessage.Performative.SIGNED_TRANSACTION  # type: ignore
        }
        expected_types = {
            "dialogue_reference": tuple,
            "message_id": int,
            "signed_transaction": SignedTransaction,
            "target": int,
        }
        self.process_message_cycle(
            self.signing_handler, expected_content, expected_types
        )
        expected_content = {
            "performative": LedgerApiMessage.Performative.TRANSACTION_DIGEST  # type: ignore
        }
        expected_types = {
            "dialogue_reference": tuple,
            "message_id": int,
            "transaction_digest": TransactionDigest,
            "target": int,
        }
        self.process_message_cycle(
            self.ledger_handler, expected_content, expected_types
        )

        self.liquidity_provision_behaviour.act_wrapper()
        self.mock_a2a_transaction()

    def test_enter_pool_tx_validation_behaviour(self) -> None:
        """test_enter_pool_tx_validation_behaviour"""

    # Exit pool behaviours

    def test_exit_pool_tx_hash_behaviour(self) -> None:
        """test_exit_pool_tx_hash_behaviour"""
        self.process_n_messsages(
            ExitPoolTransactionHashBehaviour.state_id, 7, self.contract_handler
        )

    def test_exit_pool_tx_sign_behaviour(self) -> None:
        """test_exit_pool_tx_sign_behaviour"""

    def test_exit_pool_tx_send_behaviour(self) -> None:
        """test_exit_pool_tx_send_behaviour"""

    def test_exit_pool_tx_validation_behaviour(self) -> None:
        """test_exit_pool_tx_validation_behaviour"""
