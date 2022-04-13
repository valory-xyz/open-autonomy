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
"""Tests for valory/liquidity_rebalancing_abci skill behaviours with Hardhat."""
import json
from copy import deepcopy
from typing import List, Optional, cast

from aea.helpers.transaction.base import RawTransaction, State
from aea.skills.base import Handler

from packages.valory.contracts.gnosis_safe.contract import SafeOperation
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.liquidity_rebalancing_abci.behaviours import (
    EnterPoolTransactionHashBehaviour,
    ExitPoolTransactionHashBehaviour,
    SAFE_TX_GAS_ENTER,
    SAFE_TX_GAS_EXIT,
    SAFE_TX_GAS_SWAP_BACK,
    SwapBackTransactionHashBehaviour,
    parse_tx_token_balance,
)
from packages.valory.skills.liquidity_rebalancing_abci.rounds import (
    PeriodState as LiquidityRebalancingPeriodState,
)

from tests.test_skills.integration.base import ExpectedContentType, ExpectedTypesType
from tests.test_skills.integration.test_liquidity_provision import (
    LiquidityProvisionIntegrationBaseCase,
)
from tests.test_skills.test_liquidity_rebalancing_abci.test_behaviours import (
    A_WETH_POOL_ADDRESS,
    B_WETH_POOL_ADDRESS,
    DEFAULT_MINTER,
    LP_TOKEN_ADDRESS,
    TOKEN_A_ADDRESS,
    TOKEN_B_ADDRESS,
    WETH_ADDRESS,
)


class TestLiquidityRebalancingHardhat(LiquidityProvisionIntegrationBaseCase):
    """Test liquidity pool behaviours in a Hardhat environment."""

    def test_full_run(self) -> None:
        """Run the test"""
        timestamp = self.ethereum_api.api.eth.get_block("latest")["timestamp"]
        assert self.strategy["deadline"] > timestamp, "Increase timestamp!"
        strategy = deepcopy(self.strategy)

        # ENTER POOL ------------------------------------------------------

        # Prepare the transaction
        strategy["safe_nonce"] = 0

        period_state_enter_hash = cast(
            LiquidityRebalancingPeriodState,
            self.default_period_state_hash.update(),
        )

        cycles_enter = 8
        handlers_enter: List[Optional[Handler]] = [self.contract_handler] * cycles_enter
        expected_content_enter: ExpectedContentType = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            }
        ] * cycles_enter
        expected_types_enter: ExpectedTypesType = [
            {
                "raw_transaction": RawTransaction,
            }
        ] * cycles_enter
        _, _, _, _, _, _, msg_a, msg_b = self.process_n_messages(
            cycles_enter,
            period_state_enter_hash,
            EnterPoolTransactionHashBehaviour.state_id,
            handlers_enter,
            expected_content_enter,
            expected_types_enter,
        )
        assert msg_a is not None and isinstance(msg_a, ContractApiMessage)
        tx_data_enter = cast(str, msg_a.raw_transaction.body["data"])[2:]
        assert tx_data_enter == self.multisend_data_enter
        assert msg_b is not None and isinstance(msg_b, ContractApiMessage)
        tx_hash_enter = cast(str, msg_b.raw_transaction.body["tx_hash"])[2:]
        assert tx_hash_enter == self.most_voted_tx_hash_enter

        # Send and validate
        tx_digest_enter = self.send_and_validate(
            tx_hash=tx_hash_enter,
            data=bytes.fromhex(self.multisend_data_enter),
            to_address=self.multisend_contract_address,
            safe_tx_gas=SAFE_TX_GAS_ENTER,
            operation=SafeOperation.DELEGATE_CALL.value,
        )

        # EXIT POOL ------------------------------------------------------

        # Prepare the transaction
        strategy["safe_nonce"] = 1

        period_state_exit_hash = cast(
            LiquidityRebalancingPeriodState,
            self.default_period_state_hash.update(
                most_voted_strategy=json.dumps(strategy),
                final_tx_hash=tx_digest_enter,
            ),
        )

        cycles_exit = 6
        handlers_exit: List[Optional[Handler]] = [self.contract_handler] * cycles_exit
        expected_content_exit: ExpectedContentType = [
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
        ]
        expected_types_exit: ExpectedTypesType = [
            {"state": State},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
        ]
        transfers_msg_enter, _, _, _, msg_a, msg_b = self.process_n_messages(
            cycles_exit,
            period_state_exit_hash,
            ExitPoolTransactionHashBehaviour.state_id,
            handlers_exit,
            expected_content_exit,
            expected_types_exit,
        )
        assert msg_a is not None and isinstance(msg_a, ContractApiMessage)
        tx_data_exit = cast(str, msg_a.raw_transaction.body["data"])[2:]
        assert tx_data_exit == self.multisend_data_exit
        assert msg_b is not None and isinstance(msg_b, ContractApiMessage)
        tx_hash_exit = cast(str, msg_b.raw_transaction.body["tx_hash"])[2:]
        assert tx_hash_exit == self.most_voted_tx_hash_exit

        transfers_enter = cast(ContractApiMessage, transfers_msg_enter).state.body[
            "logs"
        ]

        amount_weth_sent_a = parse_tx_token_balance(
            cast(list, transfers_enter),
            WETH_ADDRESS,
            self.safe_contract_address,
            A_WETH_POOL_ADDRESS,
        )
        assert (
            amount_weth_sent_a == 1004
        ), f"Token base amount sent is not correct (A): {amount_weth_sent_a} != 1004"

        amount_weth_sent_b = parse_tx_token_balance(
            cast(list, transfers_enter),
            WETH_ADDRESS,
            self.safe_contract_address,
            B_WETH_POOL_ADDRESS,
        )
        assert (
            amount_weth_sent_b == 1004
        ), f"Token base amount sent is not correct (B): {amount_weth_sent_b} != 1004"

        amount_a_received = parse_tx_token_balance(
            cast(list, transfers_enter),
            TOKEN_A_ADDRESS,
            A_WETH_POOL_ADDRESS,
            self.safe_contract_address,
        )
        assert (
            amount_a_received == 1000
        ), f"Token A amount received is not correct: {amount_a_received} != 1000"

        amount_b_received = parse_tx_token_balance(
            cast(list, transfers_enter),
            TOKEN_B_ADDRESS,
            B_WETH_POOL_ADDRESS,
            self.safe_contract_address,
        )
        assert (
            amount_b_received == 1000
        ), f"Token B amount received is not correct: {amount_b_received} != 1000"

        amount_a_sent = parse_tx_token_balance(
            cast(list, transfers_enter),
            TOKEN_A_ADDRESS,
            self.safe_contract_address,
            LP_TOKEN_ADDRESS,
        )
        assert (
            amount_a_sent == 1000
        ), f"Token A amount sent is not correct: {amount_a_sent} != 1000"

        amount_b_sent = parse_tx_token_balance(
            cast(list, transfers_enter),
            TOKEN_B_ADDRESS,
            self.safe_contract_address,
            LP_TOKEN_ADDRESS,
        )
        assert (
            amount_b_sent == 1000
        ), f"Token B amount sent is not correct: {amount_b_sent} != 1000"

        amount_lp_received = parse_tx_token_balance(
            cast(list, transfers_enter),
            LP_TOKEN_ADDRESS,
            DEFAULT_MINTER,
            self.safe_contract_address,
        )
        assert (
            amount_lp_received == 1000
        ), f"LP amount received is not correct: {amount_lp_received} != 1000"

        # Send and validate
        tx_digest_exit = self.send_and_validate(
            tx_hash=tx_hash_exit,
            data=bytes.fromhex(self.multisend_data_exit),
            to_address=self.multisend_contract_address,
            safe_tx_gas=SAFE_TX_GAS_EXIT,
            operation=SafeOperation.DELEGATE_CALL.value,
        )

        # SWAP BACK ------------------------------------------------------

        # Prepare the transaction
        strategy["safe_nonce"] = 2

        period_state_swap_back_hash = cast(
            LiquidityRebalancingPeriodState,
            self.default_period_state_hash.update(
                most_voted_strategy=json.dumps(strategy),
                final_tx_hash=tx_digest_exit,
            ),
        )

        cycles_swap_back = 8
        handlers_swap_back: List[Optional[Handler]] = [
            self.contract_handler
        ] * cycles_swap_back
        expected_content_swap_back: ExpectedContentType = [
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION  # type: ignore
            },
        ]
        expected_types_swap_back: ExpectedTypesType = [
            {"state": State},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
            {"raw_transaction": RawTransaction},
        ]
        transfers_msg_exit, _, _, _, _, _, msg_a, msg_b = self.process_n_messages(
            cycles_swap_back,
            period_state_swap_back_hash,
            SwapBackTransactionHashBehaviour.state_id,
            handlers_swap_back,
            expected_content_swap_back,
            expected_types_swap_back,
        )
        assert msg_a is not None and isinstance(msg_a, ContractApiMessage)
        tx_data_swap_back = cast(str, msg_a.raw_transaction.body["data"])[2:]
        assert tx_data_swap_back == self.multisend_data_swap_back
        assert msg_b is not None and isinstance(msg_b, ContractApiMessage)
        tx_hash_swap_back = cast(str, msg_b.raw_transaction.body["tx_hash"])[2:]
        assert tx_hash_swap_back == self.most_voted_tx_hash_swap_back

        transfers_exit = cast(ContractApiMessage, transfers_msg_exit).state.body["logs"]

        amount_lp_sent = parse_tx_token_balance(
            cast(list, transfers_exit),
            LP_TOKEN_ADDRESS,
            self.safe_contract_address,
            LP_TOKEN_ADDRESS,
        )
        assert (
            amount_lp_sent == 1000
        ), f"Token LP amount sent is not correct: {amount_lp_sent} != 1000"

        amount_a_received = parse_tx_token_balance(
            cast(list, transfers_exit),
            TOKEN_A_ADDRESS,
            LP_TOKEN_ADDRESS,
            self.safe_contract_address,
        )
        assert (
            amount_a_received == 1000
        ), f"Token A amount received is not correct: {amount_a_received} != 1000"

        amount_b_received = parse_tx_token_balance(
            cast(list, transfers_exit),
            TOKEN_B_ADDRESS,
            LP_TOKEN_ADDRESS,
            self.safe_contract_address,
        )
        assert (
            amount_b_received == 1000
        ), f"Token B amount received is not correct: {amount_b_received} != 1000"

        # Send and validate
        self.send_and_validate(
            tx_hash=tx_hash_swap_back,
            data=bytes.fromhex(self.multisend_data_swap_back),
            to_address=self.multisend_contract_address,
            safe_tx_gas=SAFE_TX_GAS_SWAP_BACK,
            operation=SafeOperation.DELEGATE_CALL.value,
        )
