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
import binascii
import os
import tempfile
from math import ceil
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from unittest import mock

from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import DecisionMakerHandler
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer
from aea.protocols.base import Message
from aea.skills.base import Handler
from aea_ledger_ethereum import EthereumApi
from web3 import HTTPProvider, Web3
from web3.types import RPCEndpoint

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
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.oracle_abci.behaviours import (
    OracleAbciAppConsensusBehaviour,
)
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
from packages.valory.skills.transaction_settlement_abci.handlers import SigningHandler
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
    hash_payload_to_hex,
    skill_input_hex_to_payload,
)
from packages.valory.skills.transaction_settlement_abci.payloads import SignaturePayload
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

SAFE_TX_GAS = 120000
ETHER_VALUE = 0


class OracleBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing TransactionSettlement FSM Behaviour."""

    path_to_skill = Path(ROOT_DIR, "packages", "valory", "skills", "oracle_abci")

    behaviour: OracleAbciAppConsensusBehaviour
    tx_settlement_period_state: TxSettlementPeriodState
    price_estimation_period_state: PriceEstimationPeriodState


class OracleBehaviourHardHatGnosisBaseCase(OracleBehaviourBaseCase, HardHatAMMBaseTest):
    """Test tx settlement behaviours in a Hardhat environment, with Gnosis deployed."""

    hardhat: Web3
    running_loop: asyncio.AbstractEventLoop
    thread_loop: Thread
    multiplexer: Multiplexer
    decision_maker: DecisionMaker
    safe_owners: Dict
    safe_contract_address: str
    keeper_address: str
    ethereum_api: EthereumApi
    gnosis_instance: Any

    @classmethod
    def _setup_class(cls, **kwargs: Any) -> None:
        """Setup class."""

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup."""
        super().setup()

        # create an API for HardHat
        cls.hardhat = Web3(provider=HTTPProvider("http://localhost:8545"))

        # register gnosis and offchain aggregator contracts
        directory = Path(ROOT_DIR, "packages", "valory", "contracts", "gnosis_safe")
        gnosis = get_register_contract(directory)
        directory = Path(
            ROOT_DIR, "packages", "valory", "contracts", "offchain_aggregator"
        )
        _ = get_register_contract(directory)
        # set up a multiplexer with the required connections
        cls.running_loop = asyncio.new_event_loop()
        cls.thread_loop = Thread(target=cls.running_loop.run_forever)
        cls.thread_loop.start()
        cls.multiplexer = Multiplexer(
            [make_ledger_api_connection()], loop=cls.running_loop
        )
        cls.multiplexer.connect()

        # hardhat configuration
        cls.safe_contract_address = "0x68FCdF52066CcE5612827E872c45767E5a1f6551"
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
            decision_maker_handler=DecisionMakerHandler(identity, wallet, {})
        )
        cls._skill._skill_context._agent_context._decision_maker_message_queue = (  # type: ignore
            cls.decision_maker.message_in_queue
        )
        cls._skill.skill_context._agent_context._decision_maker_address = (  # type: ignore
            "decision_maker"
        )

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

        cls.ethereum_api = make_ledger_api("ethereum")
        cls.gnosis_instance = gnosis.get_instance(
            cls.ethereum_api, cls.safe_contract_address
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
            TxSettlementPeriodState, PriceEstimationPeriodState, None
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
        stored_tip = behaviour.params.tip

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
            "nonce": int(cast(str, msg1.raw_transaction.body["nonce"])),
            "max_priority_fee_per_gas": int(
                cast(
                    str,
                    msg1.raw_transaction.body["maxPriorityFeePerGas"],
                )
            ),
        }

        behaviour = cast(FinalizeBehaviour, self.behaviour.current_state)
        assert behaviour.params.tip is not None
        assert behaviour.params.nonce is not None
        # if we are repricing
        if tx_data["nonce"] == stored_nonce:
            assert stored_nonce is not None
            assert stored_tip is not None
            assert tx_data["max_priority_fee_per_gas"] == ceil(
                stored_tip * 1.1
            ), "The repriced tip does not match the one returned from the gas pricing method!"
        # if we are not repricing
        else:
            assert (
                tx_data["max_priority_fee_per_gas"] == 3000000000
            ), "The used tip does not match the one returned from the gas pricing method!"

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

        # eventually replace with https://pypi.org/project/eth-event/
        receipt = self.ethereum_api.get_transaction_receipt(
            self.tx_settlement_period_state.to_be_validated_tx_hash
        )
        logs = self.get_decoded_logs(self.gnosis_instance, receipt)
        assert all(
            [key != "ExecutionFailure" for dict_ in logs for key in dict_.keys()]
        )

        self.tx_settlement_period_state.update(
            final_verification_status=VerificationStatus.VERIFIED,
            final_tx_hash=self.tx_settlement_period_state.to_be_validated_tx_hash,
        )

    @staticmethod
    def dummy_try_get_gas_pricing_wrapper(
        max_priority_fee_per_gas: int = 3000000000,
        max_fee_per_gas: int = 4000000000,
        repricing_multiplier: float = 1.1,
    ) -> Callable[[Optional[str], Optional[Dict], Optional[int]], Dict[str, int]]:
        """A dummy wrapper of `EthereumAPI`'s `try_get_gas_pricing`."""

        def dummy_try_get_gas_pricing(
            _gas_price_strategy: Optional[str] = None,
            _extra_config: Optional[Dict] = None,
            old_tip: Optional[int] = None,
        ) -> Dict[str, int]:
            """Get a dummy gas price."""
            tip = max_priority_fee_per_gas
            gas = max_fee_per_gas

            if old_tip is not None:
                tip = ceil(max_priority_fee_per_gas * repricing_multiplier)
                gas = ceil(max_fee_per_gas * repricing_multiplier)
            return {"maxPriorityFeePerGas": tip, "maxFeePerGas": gas}

        return dummy_try_get_gas_pricing


class TestRepricing(OracleBehaviourHardHatGnosisBaseCase):
    """Test failure modes related to repricing."""

    @mock.patch.object(
        EthereumApi,
        "try_get_gas_pricing",
        new_callable=OracleBehaviourHardHatGnosisBaseCase.dummy_try_get_gas_pricing_wrapper,
    )
    def test_same_keeper(self, _: mock.Mock) -> None:
        """
        Test repricing after the first failure.

        Test that we are using the same keeper to reprice when we fail or timeout for the first time.
        Also, test that we are adjusting the gas correctly when repricing.
        """

        self.deploy_oracle()
        self.gen_safe_tx_hash()
        self.sign_send_tx()

        # validate tx with timeout
        # send second tx
        # check repricing and keeper used
