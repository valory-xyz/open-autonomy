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

import binascii
import json
from typing import Any, Dict, List, cast

from web3 import Web3

from packages.open_aea.protocols.signing import SigningMessage
from packages.open_aea.protocols.signing.custom_types import (
    RawTransaction,
    SignedTransaction,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.protocols.ledger_api.custom_types import (
    State,
    TransactionDigest,
    TransactionReceipt,
)
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.liquidity_rebalancing_abci.rounds import (
    PeriodState as LiquidityRebalancingPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    FinalizeBehaviour,
    ValidateTransactionBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.payloads import SignaturePayload
from packages.valory.skills.transaction_settlement_abci.rounds import (
    PeriodState as TransactionSettlementPeriodState,
)

from tests.test_skills.integration.base import (
    AMMIntegrationBaseCase,
    ExpectedContentType,
    ExpectedTypesType,
    HandlersType,
    LiquidityRebalancingBehaviourBaseCase,
)
from tests.test_skills.test_liquidity_rebalancing_abci.test_behaviours import (
    get_default_strategy,
)


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
    default_period_state_hash: LiquidityRebalancingPeriodState
    default_period_state_settlement: TransactionSettlementPeriodState

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

        cls.default_period_state_hash = LiquidityRebalancingPeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    safe_contract_address=cls.safe_contract_address,
                    most_voted_keeper_address=cls.keeper_address,
                    most_voted_strategy=json.dumps(cls.strategy),
                    multisend_contract_address=cls.multisend_contract_address,
                    router_contract_address=cls.router_contract_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                ),
            )
        )

        keeper_retries = 1
        keepers = next(iter(cls.agents.keys()))
        cls.default_period_state_settlement = TransactionSettlementPeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    safe_contract_address=cls.safe_contract_address,
                    most_voted_keeper_address=cls.keeper_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                    keepers=keeper_retries.to_bytes(32, "big").hex() + keepers,
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

    def send_and_validate(
        self,
        tx_hash: str,
        data: bytes,
        to_address: str,
        safe_tx_gas: int,
        operation: int,
    ) -> str:
        """Send and validate a transaction"""
        # Sign and send the transaction
        participant_to_signature = {
            address: SignaturePayload(
                sender=address,
                signature=crypto.sign_message(
                    binascii.unhexlify(tx_hash),
                    is_deprecated_mode=True,
                )[2:],
            )
            for address, crypto in self.safe_owners.items()
        }

        payload_string = hash_payload_to_hex(
            tx_hash,
            ether_value=0,
            safe_tx_gas=safe_tx_gas,
            to_address=to_address,
            data=data,
            operation=operation,
        )

        period_state = cast(
            TransactionSettlementPeriodState,
            self.default_period_state_settlement.update(
                most_voted_tx_hash=payload_string,
                participant_to_signature=participant_to_signature,
            ),
        )

        handlers: HandlersType = [
            self.contract_handler,
            self.signing_handler,
            self.ledger_handler,
        ]
        expected_content: ExpectedContentType = [
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
        expected_types: ExpectedTypesType = [
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
        _, _, msg = self.process_n_messages(
            3,
            period_state,
            FinalizeBehaviour.state_id,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg is not None and isinstance(msg, LedgerApiMessage)
        tx_digest = msg.transaction_digest.body

        # Validate the transaction

        period_state = cast(
            TransactionSettlementPeriodState,
            self.default_period_state_settlement.update(
                most_voted_tx_hash=payload_string,
                tx_hashes_history=[tx_digest],
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
        _, verif_msg = self.process_n_messages(
            2,
            period_state,
            ValidateTransactionBehaviour.state_id,
            handlers,
            expected_content,
            expected_types,
        )
        assert verif_msg is not None and isinstance(verif_msg, ContractApiMessage)
        assert verif_msg.state.body[
            "verified"
        ], f"Message not verified: {verif_msg.state.body}"

        # eventually replace with https://pypi.org/project/eth-event/
        receipt = self.ethereum_api.get_transaction_receipt(tx_digest)
        logs = self.get_decoded_logs(self.gnosis_instance, receipt)
        assert all(
            [key != "ExecutionFailure" for dict_ in logs for key in dict_.keys()]
        )

        return tx_digest
