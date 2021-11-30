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
from pathlib import Path
from threading import Thread
from typing import Any, Dict, Optional, cast

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.skills.base import Handler

from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.liquidity_provision.behaviours import (
    EnterPoolTransactionHashBehaviour,
    ExitPoolTransactionHashBehaviour,
    get_strategy_update,
)
from packages.valory.skills.liquidity_provision.rounds import PeriodState

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

    @classmethod
    def teardown(cls) -> None:
        """Tear down the multiplexer."""
        super().teardown()
        cls.multiplexer.disconnect()
        cls.running_loop.call_soon_threadsafe(cls.running_loop.stop)
        cls.thread_loop.join()

    def process_message_cycle(
        self, handler: Optional[Handler] = None, expected_content: Optional[Dict] = None
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
        """
        self.liquidity_provision_behaviour.act_wrapper()
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
            if expected_content is not None:
                assert all(
                    [
                        incoming_message._body.get(key, None) == value
                        for key, value in expected_content.items()
                    ]
                ), f"Actual content: {incoming_message._body}, expected: {expected_content}"

            handler.handle(incoming_message)
        self.liquidity_provision_behaviour.act_wrapper()

    def process_n_messsages(self, state_id, ncycles):
        """
        Process n message cycles.

        :param: state_id: the behaviour to fast forward to
        :param: ncycles: the number of message cycles to process
        """
        strategy = get_strategy_update()
        period_state = PeriodState(
            most_voted_tx_hash="0x",
            safe_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            most_voted_keeper_address="most_voted_keeper_address",
            most_voted_strategy=strategy,
            multisend_contract_address="0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512",
            router_contract_address="0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9",
        )
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

        expected_content = {
            "performative": ContractApiMessage.Performative.RAW_TRANSACTION
        }

        for _ in range(ncycles):
            self.process_message_cycle(self.contract_handler, expected_content)

        self.mock_a2a_transaction()

    def test_enter_pool(self):
        """Test enter pool."""
        self.process_n_messsages(EnterPoolTransactionHashBehaviour.state_id, 7)

    def test_exit_pool(self):
        """Test exit pool."""
        self.process_n_messsages(ExitPoolTransactionHashBehaviour.state_id, 7)
