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
from math import ceil
from typing import Any, Callable, Dict, Optional, cast

from aea_ledger_ethereum import EthereumApi
from web3.types import Nonce, Wei

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
from packages.valory.skills.oracle_deployment_abci.behaviours import (
    DeployOracleBehaviour,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    TransactionHashBehaviour,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    PeriodState as PriceEstimationPeriodState,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    FinalizeBehaviour,
    ValidateTransactionBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
    hash_payload_to_hex,
    skill_input_hex_to_payload,
)
from packages.valory.skills.transaction_settlement_abci.payloads import SignaturePayload
from packages.valory.skills.transaction_settlement_abci.rounds import (
    PeriodState as TxSettlementPeriodState,
)

from tests.test_skills.integration.base import (
    ExpectedContentType,
    ExpectedTypesType,
    GnosisIntegrationBaseCase,
    HandlersType,
    OracleBehaviourBaseCase,
)


SAFE_TX_GAS = 120000
ETHER_VALUE = 0
DUMMY_MAX_PRIORITY_FEE_PER_GAS = 3000000000
DUMMY_MAX_FEE_PER_GAS = 4000000000
DUMMY_REPRICING_MULTIPLIER = 1.1


class TransactionSettlementIntegrationBaseCase(
    OracleBehaviourBaseCase, GnosisIntegrationBaseCase
):
    """Base case for integration testing TransactionSettlement FSM Behaviour."""

    tx_settlement_period_state: TxSettlementPeriodState
    price_estimation_period_state: PriceEstimationPeriodState

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        keeper_initial_retries = 1
        cls.tx_settlement_period_state = TxSettlementPeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    safe_contract_address=cls.safe_contract_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                    keepers=keeper_initial_retries.to_bytes(32, "big").hex()
                    + cls.keeper_address,
                ),
            )
        )

        cls.price_estimation_period_state = PriceEstimationPeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    safe_contract_address=cls.safe_contract_address,
                    participants=frozenset(list(cls.safe_owners.keys())),
                    most_voted_keeper_address=cls.keeper_address,
                    most_voted_estimate=1,
                ),
            )
        )

    def deploy_oracle(self) -> None:
        """Deploy the oracle."""
        cycles_enter = 4
        handlers_enter: HandlersType = [
            self.contract_handler,
            self.signing_handler,
            self.ledger_handler,
            self.ledger_handler,
        ]
        expected_content_enter: ExpectedContentType = [
            {
                "performative": ContractApiMessage.Performative.RAW_TRANSACTION,
            },
            {
                "performative": SigningMessage.Performative.SIGNED_TRANSACTION,
            },
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_DIGEST,
            },
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            },
        ]
        expected_types_enter: ExpectedTypesType = [
            {
                "raw_transaction": RawTransaction,
            },
            {
                "signed_transaction": SignedTransaction,
            },
            {
                "transaction_digest": TransactionDigest,
            },
            {
                "transaction_receipt": TransactionReceipt,
            },
        ]
        _, _, _, msg4 = self.process_n_messages(
            cycles_enter,
            self.price_estimation_period_state,
            DeployOracleBehaviour.state_id,
            handlers_enter,
            expected_content_enter,
            expected_types_enter,
        )
        assert msg4 is not None and isinstance(msg4, LedgerApiMessage)
        oracle_contract_address = EthereumApi.get_contract_address(
            msg4.transaction_receipt.receipt
        )

        # update period state with oracle contract address
        self.price_estimation_period_state.update(
            oracle_contract_address=oracle_contract_address,
        )

    def gen_safe_tx_hash(self) -> None:
        """Generate safe's transaction hash."""
        cycles_enter = 3
        handlers_enter: HandlersType = [self.contract_handler] * cycles_enter
        expected_content_enter: ExpectedContentType = [
            {"performative": ContractApiMessage.Performative.RAW_TRANSACTION}
        ] * cycles_enter
        expected_types_enter: ExpectedTypesType = [
            {
                "raw_transaction": RawTransaction,
            }
        ] * cycles_enter
        _, msg_a, msg_b = self.process_n_messages(
            cycles_enter,
            self.price_estimation_period_state,
            TransactionHashBehaviour.state_id,
            handlers_enter,
            expected_content_enter,
            expected_types_enter,
        )

        assert msg_a is not None and isinstance(msg_a, ContractApiMessage)
        tx_data = cast(bytes, msg_a.raw_transaction.body["data"])
        assert msg_b is not None and isinstance(msg_b, ContractApiMessage)
        tx_hash = cast(str, msg_b.raw_transaction.body["tx_hash"])[2:]

        payload = hash_payload_to_hex(
            tx_hash,
            ETHER_VALUE,
            SAFE_TX_GAS,
            self.price_estimation_period_state.oracle_contract_address,
            tx_data,
        )

        # update period state with safe's tx hash
        self.tx_settlement_period_state.update(
            most_voted_tx_hash=payload,
        )

    def sign_tx(self) -> None:
        """Sign a transaction"""
        tx_params = skill_input_hex_to_payload(
            self.tx_settlement_period_state.most_voted_tx_hash
        )
        safe_tx_hash_bytes = binascii.unhexlify(tx_params["safe_tx_hash"])
        participant_to_signature = {}
        for address, crypto in self.safe_owners.items():
            signature_hex = crypto.sign_message(
                safe_tx_hash_bytes,
                is_deprecated_mode=True,
            )
            signature_hex = signature_hex[2:]
            participant_to_signature[address] = SignaturePayload(
                sender=address,
                signature=signature_hex,
            )

        self.tx_settlement_period_state.update(
            participant_to_signature=participant_to_signature,
        )

        actual_safe_owners = self.gnosis_instance.functions.getOwners().call()
        expected_safe_owners = (
            self.tx_settlement_period_state.participant_to_signature.keys()
        )
        assert len(actual_safe_owners) == len(expected_safe_owners)
        assert all(
            owner == signer
            for owner, signer in zip(actual_safe_owners, expected_safe_owners)
        )

    def send_tx(self) -> None:
        """Send a transaction"""

        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=FinalizeBehaviour.state_id,
            period_state=self.tx_settlement_period_state,
        )
        behaviour = cast(FinalizeBehaviour, self.behaviour.current_state)
        assert behaviour.state_id == FinalizeBehaviour.state_id
        stored_nonce = behaviour.params.nonce
        stored_gas_price = behaviour.params.gas_price

        handlers: HandlersType = [
            self.contract_handler,
            self.signing_handler,
            self.ledger_handler,
        ]
        expected_content: ExpectedContentType = [
            {"performative": ContractApiMessage.Performative.RAW_TRANSACTION},
            {"performative": SigningMessage.Performative.SIGNED_TRANSACTION},
            {"performative": LedgerApiMessage.Performative.TRANSACTION_DIGEST},
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
        msg1, _, msg3 = self.process_n_messages(
            3,
            self.tx_settlement_period_state,
            None,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg1 is not None and isinstance(msg1, ContractApiMessage)
        assert msg3 is not None and isinstance(msg3, LedgerApiMessage)
        tx_digest = msg3.transaction_digest.body
        tx_data = {
            "status": VerificationStatus.PENDING,
            "tx_digest": cast(str, tx_digest),
        }

        behaviour = cast(FinalizeBehaviour, self.behaviour.current_state)
        assert behaviour.params.gas_price is not None
        assert behaviour.params.nonce is not None

        nonce_used = Nonce(int(cast(str, msg1.raw_transaction.body["nonce"])))
        gas_price_used = {
            gas_price_param: Wei(
                int(
                    cast(
                        str,
                        msg1.raw_transaction.body[gas_price_param],
                    )
                )
            )
            for gas_price_param in ("maxPriorityFeePerGas", "maxFeePerGas")
        }

        # if we are repricing
        if nonce_used == stored_nonce:
            assert stored_nonce is not None
            assert stored_gas_price is not None
            assert gas_price_used == {
                gas_price_param: ceil(
                    stored_gas_price[gas_price_param] * DUMMY_REPRICING_MULTIPLIER
                )
                for gas_price_param in ("maxPriorityFeePerGas", "maxFeePerGas")
            }, "The repriced parameters do not match the ones returned from the gas pricing method!"
        # if we are not repricing
        else:
            assert gas_price_used == {
                "maxPriorityFeePerGas": DUMMY_MAX_PRIORITY_FEE_PER_GAS,
                "maxFeePerGas": DUMMY_MAX_FEE_PER_GAS,
            }, "The used parameters do not match the ones returned from the gas pricing method!"

        hashes = self.tx_settlement_period_state.tx_hashes_history
        hashes.append(tx_digest)

        self.tx_settlement_period_state.update(
            tx_hashes_history=hashes,
            final_verification_status=tx_data["status"],
        )

    def validate_tx(self) -> None:
        """Validate the given transaction."""

        handlers: HandlersType = [
            self.ledger_handler,
            self.contract_handler,
        ]
        expected_content: ExpectedContentType = [
            {"performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT},
            {"performative": ContractApiMessage.Performative.STATE},
        ]
        expected_types: ExpectedTypesType = [
            {
                "transaction_receipt": TransactionReceipt,
            },
            {
                "state": State,
            },
        ]
        _, verif_msg = self.process_n_messages(
            2,
            self.tx_settlement_period_state,
            ValidateTransactionBehaviour.state_id,
            handlers,
            expected_content,
            expected_types,
        )
        assert verif_msg is not None and isinstance(verif_msg, ContractApiMessage)
        assert verif_msg.state.body[
            "verified"
        ], f"Message not verified: {verif_msg.state.body}"

        self.tx_settlement_period_state.update(
            final_verification_status=VerificationStatus.VERIFIED,
            final_tx_hash=self.tx_settlement_period_state.to_be_validated_tx_hash,
        )

    @staticmethod
    def dummy_try_get_gas_pricing_wrapper(
        max_priority_fee_per_gas: Wei = DUMMY_MAX_PRIORITY_FEE_PER_GAS,
        max_fee_per_gas: Wei = DUMMY_MAX_FEE_PER_GAS,
        repricing_multiplier: float = DUMMY_REPRICING_MULTIPLIER,
    ) -> Callable[
        [Optional[str], Optional[Dict], Optional[Dict[str, Wei]]], Dict[str, Wei]
    ]:
        """A dummy wrapper of `EthereumAPI`'s `try_get_gas_pricing`."""

        def dummy_try_get_gas_pricing(
            _gas_price_strategy: Optional[str] = None,
            _extra_config: Optional[Dict] = None,
            old_price: Optional[Dict[str, Wei]] = None,
        ) -> Dict[str, Wei]:
            """Get a dummy gas price."""
            tip = max_priority_fee_per_gas
            gas = max_fee_per_gas

            if old_price is not None:
                tip = ceil(max_priority_fee_per_gas * repricing_multiplier)
                gas = ceil(max_fee_per_gas * repricing_multiplier)
            return {"maxPriorityFeePerGas": tip, "maxFeePerGas": gas}

        return dummy_try_get_gas_pricing
