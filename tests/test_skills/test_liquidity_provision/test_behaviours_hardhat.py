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

from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.liquidity_provision.behaviours import (
    EnterPoolTransactionHashBehaviour, get_strategy_update
)
from packages.valory.skills.liquidity_provision.payloads import StrategyType
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
    def _setup_class(cls, **kwargs: Any):
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
                    [incoming_message._body.get(key, None) == value for key, value in expected_content.items()]
                ), f"Actual content: {incoming_message._body}, expected: {expected_content}"
            handler.handle(incoming_message)
        self.liquidity_provision_behaviour.act_wrapper()

    def test_swap(self):
        """Test a swap tx: WETH for token A."""
        strategy = get_strategy_update()
        period_state = PeriodState(
            most_voted_tx_hash="0x",
            safe_contract_address="safe_contract_address",
            most_voted_keeper_address="most_voted_keeper_address",
            most_voted_strategy=strategy,
            multisend_contract_address="multisend_contract_address",
        )
        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=EnterPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == EnterPoolTransactionHashBehaviour.state_id
        )
        # amount_in = 10  # noqa: E800
        # amount_out_min = 1  # noqa: E800

        # contract_address = "0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9"  # noqa: E800
        # weth_address = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"  # noqa: E800
        # tokenA_address = "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9"  # noqa: E800
        # account_1_address = "0xBcd4042DE499D14e55001CcbB24a551F3b954096"  # noqa: E800
        expected_content = {"performative": ContractApiMessage.Performative.RAW_TRANSACTION}
        self.process_message_cycle(self.contract_handler, expected_content)
