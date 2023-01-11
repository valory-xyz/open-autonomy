# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
import os
import tempfile
from abc import ABC
from math import ceil
from typing import Any, Dict, cast

from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto, make_ledger_api
from aea_ledger_ethereum import EthereumApi
from aea_test_autonomy.helpers.contracts import get_register_contract
from web3.types import Nonce, Wei

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.tests.test_contract import (
    PACKAGE_DIR as GNOSIS_SAFE_PACKAGE,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.contract_api.custom_types import RawTransaction, State
from packages.valory.protocols.ledger_api import LedgerApiMessage
from packages.valory.protocols.ledger_api.custom_types import (
    SignedTransaction,
    TransactionDigest,
    TransactionReceipt,
)
from packages.valory.skills.abstract_round_abci.test_tools.integration import (
    ExpectedContentType,
    ExpectedTypesType,
    HandlersType,
    IntegrationBaseCase,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    FinalizeBehaviour,
    ValidateTransactionBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
    skill_input_hex_to_payload,
)
from packages.valory.skills.transaction_settlement_abci.payloads import SignaturePayload
from packages.valory.skills.transaction_settlement_abci.rounds import (
    SynchronizedData as TxSettlementSynchronizedSata,
)


# pylint: disable=protected-access,too-many-ancestors,unbalanced-tuple-unpacking,too-many-locals,consider-using-with,unspecified-encoding,too-many-arguments,unidiomatic-typecheck


DUMMY_MAX_FEE_PER_GAS = 4000000000
DUMMY_MAX_PRIORITY_FEE_PER_GAS = 3000000000
DUMMY_REPRICING_MULTIPLIER = 1.1


class _SafeConfiguredHelperIntegration(IntegrationBaseCase, ABC):  # pragma: no cover
    """Base test class for integration tests with Gnosis, but no contract, deployed."""

    safe_owners: Dict[str, Crypto]
    keeper_address: str

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup_class()

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
        assert cls.keeper_address in cls.safe_owners  # nosec


class _GnosisHelperIntegration(
    _SafeConfiguredHelperIntegration, ABC
):  # pragma: no cover
    """Class that assists Gnosis instantiation."""

    safe_contract_address: str = "0x68FCdF52066CcE5612827E872c45767E5a1f6551"
    ethereum_api: EthereumApi
    gnosis_instance: Any

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup_class()

        # register gnosis contract
        gnosis = get_register_contract(GNOSIS_SAFE_PACKAGE)

        cls.ethereum_api = make_ledger_api("ethereum")
        cls.gnosis_instance = gnosis.get_instance(
            cls.ethereum_api, cls.safe_contract_address
        )


class _TxHelperIntegration(_GnosisHelperIntegration, ABC):  # pragma: no cover
    """Class that assists tx settlement related operations."""

    tx_settlement_synchronized_data: TxSettlementSynchronizedSata

    def sign_tx(self) -> None:
        """Sign a transaction"""
        tx_params = skill_input_hex_to_payload(
            self.tx_settlement_synchronized_data.most_voted_tx_hash
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

        self.tx_settlement_synchronized_data.update(
            participant_to_signature=participant_to_signature,
        )

        actual_safe_owners = self.gnosis_instance.functions.getOwners().call()
        expected_safe_owners = (
            self.tx_settlement_synchronized_data.participant_to_signature.keys()
        )
        assert len(actual_safe_owners) == len(expected_safe_owners)  # nosec
        assert all(  # nosec
            owner == signer
            for owner, signer in zip(actual_safe_owners, expected_safe_owners)
        )

    def send_tx(self, simulate_timeout: bool = False) -> None:
        """Send a transaction"""

        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=FinalizeBehaviour.auto_behaviour_id(),
            synchronized_data=self.tx_settlement_synchronized_data,
        )
        behaviour = cast(FinalizeBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == FinalizeBehaviour.auto_behaviour_id()
        stored_nonce = behaviour.params.mutable_params.nonce
        stored_gas_price = behaviour.params.mutable_params.gas_price

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
            self.tx_settlement_synchronized_data,
            None,
            handlers,
            expected_content,
            expected_types,
            fail_send_a2a=simulate_timeout,
        )
        assert msg1 is not None and isinstance(msg1, ContractApiMessage)  # nosec
        assert msg3 is not None and isinstance(msg3, LedgerApiMessage)  # nosec
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
        tx_digest = msg3.transaction_digest.body
        tx_data = {
            "status": VerificationStatus.PENDING,
            "tx_digest": cast(str, tx_digest),
        }

        behaviour = cast(FinalizeBehaviour, self.behaviour.current_behaviour)
        assert behaviour.params.mutable_params.gas_price == gas_price_used  # nosec
        assert behaviour.params.mutable_params.nonce == nonce_used  # nosec
        if simulate_timeout:
            assert behaviour.params.mutable_params.tx_hash == tx_digest  # nosec
        else:
            assert behaviour.params.mutable_params.tx_hash == ""  # nosec

        # if we are repricing
        if nonce_used == stored_nonce:
            assert stored_nonce is not None  # nosec
            assert stored_gas_price is not None  # nosec
            assert gas_price_used == {  # nosec
                gas_price_param: ceil(
                    stored_gas_price[gas_price_param] * DUMMY_REPRICING_MULTIPLIER
                )
                for gas_price_param in ("maxPriorityFeePerGas", "maxFeePerGas")
            }, "The repriced parameters do not match the ones returned from the gas pricing method!"
        # if we are not repricing
        else:
            assert gas_price_used == {  # nosec
                "maxPriorityFeePerGas": DUMMY_MAX_PRIORITY_FEE_PER_GAS,
                "maxFeePerGas": DUMMY_MAX_FEE_PER_GAS,
            }, "The used parameters do not match the ones returned from the gas pricing method!"

        if not simulate_timeout:
            hashes = self.tx_settlement_synchronized_data.tx_hashes_history
            hashes.append(tx_digest)
            update_params = dict(
                tx_hashes_history="".join(hashes),
                final_verification_status=tx_data["status"],
            )
        else:
            # store the tx hash that we have missed and update missed messages.
            assert isinstance(  # nosec
                self.behaviour.current_behaviour, FinalizeBehaviour
            )
            self.mock_a2a_transaction()
            self.behaviour.current_behaviour.params.mutable_params.tx_hash = tx_digest
            update_params = dict(
                missed_messages=self.tx_settlement_synchronized_data.missed_messages
                + 1,
            )

        self.tx_settlement_synchronized_data.update(
            synchronized_data_class=None, **update_params
        )

    def validate_tx(
        self, simulate_timeout: bool = False, mining_interval_secs: float = 0
    ) -> None:
        """Validate the sent transaction."""

        if simulate_timeout:
            self.tx_settlement_synchronized_data.update(
                missed_messages=self.tx_settlement_synchronized_data.missed_messages + 1
            )
        else:
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
                self.tx_settlement_synchronized_data,
                ValidateTransactionBehaviour.auto_behaviour_id(),
                handlers,
                expected_content,
                expected_types,
                mining_interval_secs=mining_interval_secs,
            )
            assert verif_msg is not None and isinstance(  # nosec
                verif_msg, ContractApiMessage
            )
            assert verif_msg.state.body[  # nosec
                "verified"
            ], f"Message not verified: {verif_msg.state.body}"

            self.tx_settlement_synchronized_data.update(
                final_verification_status=VerificationStatus.VERIFIED,
                final_tx_hash=self.tx_settlement_synchronized_data.to_be_validated_tx_hash,
            )
