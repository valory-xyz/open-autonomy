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
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from aea.helpers.transaction.base import RawTransaction, State
from aea.skills.base import Handler
from web3 import Web3

from packages.valory.contracts.gnosis_safe.contract import SafeOperation
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.liquidity_rebalancing_abci.behaviours import (
    EnterPoolTransactionHashBehaviour,
    ExitPoolTransactionHashBehaviour,
    LiquidityRebalancingConsensusBehaviour,
    SAFE_TX_GAS_ENTER,
    SAFE_TX_GAS_EXIT,
    SAFE_TX_GAS_SWAP_BACK,
    SwapBackTransactionHashBehaviour,
    parse_tx_token_balance,
)
from packages.valory.skills.liquidity_rebalancing_abci.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.valory.skills.liquidity_rebalancing_abci.rounds import (
    SynchronizedData as LiquidityRebalancingSynchronizedSata,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TransactionSettlementSynchronizedSata,
)

from tests.conftest import ROOT_DIR
from tests.helpers.docker.base import skip_docker_tests
from tests.test_skills.base import FSMBehaviourBaseCase
from tests.test_skills.integration import (
    AMMIntegrationBaseCase,
    ExpectedContentType,
    ExpectedTypesType,
)
from tests.test_skills.test_liquidity_rebalancing_abci.test_behaviours import (
    A_WETH_POOL_ADDRESS,
    B_WETH_POOL_ADDRESS,
    DEFAULT_MINTER,
    LP_TOKEN_ADDRESS,
    TOKEN_A_ADDRESS,
    TOKEN_B_ADDRESS,
    WETH_ADDRESS,
    get_default_strategy,
)


class LiquidityRebalancingBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing LiquidityRebalancing FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "liquidity_provision_abci"
    )

    behaviour: LiquidityRebalancingConsensusBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler


class LiquidityProvisionIntegrationBaseCase(
    LiquidityRebalancingBehaviourBaseCase, AMMIntegrationBaseCase
):
    """Base case for integration testing `LiquidityProvision` FSM Behaviour."""

    strategy: Dict
    multisend_contract_address: str = "0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6"
    router_contract_address: str = "0xA51c1fc2f0D1a1b8494Ed1FE312d7C3a78Ed91C0"
    enter_nonce: int
    exit_nonce: int
    swap_back_nonce: int
    default_synchronized_data_hash: LiquidityRebalancingSynchronizedSata

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        cls.multisend_data_enter = "8d80ff0a000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000005d600dc64a140aa3e981100a9beca4e685f962f0cf6c900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001048803dbee00000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000271000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c90000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd8200a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001048803dbee00000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000271000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c90000000000000000000000009a676e781a523b5d0c0e43731313a708cb607508000dcd1bf9a1b36ce34237eeafef220932846bcd8200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000104e8e337000000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd820000000000000000000000009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000001f400000000000000000000000000000000000000000000000000000000000001f400000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef00000000000000000000"
        cls.multisend_data_exit = "8d80ff0a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000026b0050cd56fb094f8f06063066a619d898475dd3eede00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e4baa2abde0000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd820000000000000000000000009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000003e80000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef0050cd56fb094f8f06063066a619d898475dd3eede00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        cls.multisend_data_swap_back = "8d80ff0a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000047d00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd82000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c900a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef00000000000000000000000000000000000000000000000000000000000000020000000000000000000000009a676e781a523b5d0c0e43731313a708cb607508000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c900dc64a140aa3e981100a9beca4e685f962f0cf6c900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd8200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000"

        cls.most_voted_tx_hash_enter = (
            "b68291e2144f384f927e423d78702463543dd56e8fc8910b2edd20ddf47bbf46"
        )
        cls.most_voted_tx_hash_exit = (
            "70de1e8c13f56ea56f36fdc9d69635b60f1d0dc7fe4fb4a89024e16aa8ad0e12"
        )
        cls.most_voted_tx_hash_swap_back = (
            "7920b96f55935f49f636143d6071aadc5a7b53670a9ad5ddc16ab1c692a55e1f"
        )

        cls.enter_nonce = 8
        cls.exit_nonce = cls.enter_nonce + 1
        cls.swap_back_nonce = cls.enter_nonce + 2

        # setup default objects
        cls.strategy = get_default_strategy(
            is_base_native=False, is_a_native=False, is_b_native=False
        )
        # corresponds to datetime.datetime(2022, 12, 31, 23, 59, 59) using datetime.datetime.fromtimestamp(.)
        cls.strategy["deadline"] = 1672527599

        cls.default_synchronized_data_hash = LiquidityRebalancingSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        safe_contract_address=cls.safe_contract_address,
                        most_voted_keeper_address=cls.keeper_address,
                        most_voted_strategy=json.dumps(cls.strategy),
                        multisend_contract_address=cls.multisend_contract_address,
                        router_contract_address=cls.router_contract_address,
                        participants=frozenset(list(cls.safe_owners.keys())),
                    )
                ),
            )
        )

        keeper_retries = 1
        keepers = next(iter(cls.agents.keys()))
        cls.tx_settlement_synchronized_data = TransactionSettlementSynchronizedSata(
            AbciAppDB(
                setup_data=AbciAppDB.data_to_lists(
                    dict(
                        safe_contract_address=cls.safe_contract_address,
                        most_voted_keeper_address=cls.keeper_address,
                        participants=frozenset(list(cls.safe_owners.keys())),
                        keepers=keeper_retries.to_bytes(32, "big").hex() + keepers,
                    )
                ),
            )
        )

    @staticmethod
    def get_decoded_logs(gnosis_instance: Any, receipt: dict) -> List[Dict]:
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

    def validate_tx(
        self, simulate_timeout: bool = False, mining_interval_secs: float = 0
    ) -> None:
        """Validate the sent transaction."""
        super().validate_tx(simulate_timeout, mining_interval_secs)

        # eventually replace with https://pypi.org/project/eth-event/
        receipt = self.ethereum_api.get_transaction_receipt(
            self.tx_settlement_synchronized_data.to_be_validated_tx_hash
        )
        logs = self.get_decoded_logs(self.gnosis_instance, receipt)

        assert all(
            [key != "ExecutionFailure" for dict_ in logs for key in dict_.keys()]
        )

    def send_and_validate(
        self,
    ) -> None:
        """Send and validate a transaction"""
        # Sign the transaction
        self.sign_tx()
        # Send the transaction
        self.send_tx()
        # Validate the transaction
        self.validate_tx()


@skip_docker_tests
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

        synchronized_data_enter_hash = cast(
            LiquidityRebalancingSynchronizedSata,
            self.default_synchronized_data_hash.update(),
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
            synchronized_data_enter_hash,
            EnterPoolTransactionHashBehaviour.behaviour_id,
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

        payload = hash_payload_to_hex(
            tx_hash_enter,
            0,
            SAFE_TX_GAS_ENTER,
            self.multisend_contract_address,
            bytes.fromhex(self.multisend_data_enter),
            SafeOperation.DELEGATE_CALL.value,
        )

        # update period state with safe's tx hash
        self.tx_settlement_synchronized_data.update(
            most_voted_tx_hash=payload,
        )

        # Sign, send, validate
        self.send_and_validate()

        # EXIT POOL ------------------------------------------------------

        # Prepare the transaction
        strategy["safe_nonce"] = 1

        synchronized_data_exit_hash = cast(
            LiquidityRebalancingSynchronizedSata,
            self.default_synchronized_data_hash.update(
                most_voted_strategy=json.dumps(strategy),
                final_tx_hash=self.tx_settlement_synchronized_data.final_tx_hash,
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
            synchronized_data_exit_hash,
            ExitPoolTransactionHashBehaviour.behaviour_id,
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

        payload = hash_payload_to_hex(
            tx_hash_exit,
            0,
            SAFE_TX_GAS_EXIT,
            self.multisend_contract_address,
            bytes.fromhex(self.multisend_data_exit),
            SafeOperation.DELEGATE_CALL.value,
        )

        # update period state with safe's tx hash
        self.tx_settlement_synchronized_data.update(
            most_voted_tx_hash=payload,
        )

        # Sign, send, validate
        self.send_and_validate()

        # SWAP BACK ------------------------------------------------------

        # Prepare the transaction
        strategy["safe_nonce"] = 2

        synchronized_data_swap_back_hash = cast(
            LiquidityRebalancingSynchronizedSata,
            self.default_synchronized_data_hash.update(
                most_voted_strategy=json.dumps(strategy),
                final_tx_hash=self.tx_settlement_synchronized_data.final_tx_hash,
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
            synchronized_data_swap_back_hash,
            SwapBackTransactionHashBehaviour.behaviour_id,
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

        payload = hash_payload_to_hex(
            tx_hash_swap_back,
            0,
            SAFE_TX_GAS_SWAP_BACK,
            self.multisend_contract_address,
            bytes.fromhex(self.multisend_data_swap_back),
            SafeOperation.DELEGATE_CALL.value,
        )

        # update period state with safe's tx hash
        self.tx_settlement_synchronized_data.update(
            most_voted_tx_hash=payload,
        )

        # Sign, send, validate
        self.send_and_validate()
