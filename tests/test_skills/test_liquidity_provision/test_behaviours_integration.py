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
"""Tests for valory/liquidity_provision skill behaviours with Hardhat."""
import asyncio
import binascii
import json
import os
import tempfile
from copy import copy, deepcopy
from pathlib import Path
from threading import Thread
from typing import Any, Dict, List, Optional, Tuple, Type, cast
from unittest import mock

from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import (
    DecisionMakerHandler as DefaultDecisionMakerHandler,
)
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedMessage,
    SignedTransaction,
    State,
    TransactionDigest,
    TransactionReceipt,
)
from aea.identity.base import Identity
from aea.mail.base import Envelope, Message
from aea.multiplexer import Multiplexer
from aea.skills.base import Handler
from aea.test_tools.test_skill import BaseSkillTestCase
from aea_ledger_ethereum import EthereumApi
from web3 import Web3

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.valory.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BasePeriodState,
    BaseTxPayload,
    OK_CODE,
    StateDB,
    _MetaPayload,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.liquidity_provision.behaviours import (
    AB_POOL_ADDRESS,
    DEFAULT_MINTER,
    EnterPoolTransactionHashBehaviour,
    ExitPoolTransactionHashBehaviour,
    LP_TOKEN_ADDRESS,
    LiquidityProvisionConsensusBehaviour,
    SwapBackTransactionHashBehaviour,
    TOKEN_A_ADDRESS,
    get_dummy_strategy,
    parse_tx_token_balance,
)
from packages.valory.skills.liquidity_provision.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.valory.skills.liquidity_provision.rounds import Event, PeriodState
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    FinalizeBehaviour,
    ValidateTransactionBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payloads import (
    SignaturePayload,
    ValidatePayload,
)

from tests.conftest import ROOT_DIR, make_ledger_api_connection
from tests.fixture_helpers import HardHatAMMBaseTest
from tests.helpers.contracts import get_register_contract


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


def payload_to_hex(
    tx_hash: str, ether_value: int, safe_tx_gas: int, to_address: str, data: bytes
) -> str:
    """Serialise to a hex string."""
    if len(tx_hash) != 64:  # should be exactly 32 bytes!
        raise ValueError("cannot encode tx_hash of non-32 bytes")  # pragma: nocover
    ether_value_ = ether_value.to_bytes(32, "big").hex()
    safe_tx_gas_ = safe_tx_gas.to_bytes(32, "big").hex()
    if len(to_address) != 42:
        raise ValueError("cannot encode to_address of non 42 length")  # pragma: nocover
    concatenated = tx_hash + ether_value_ + safe_tx_gas_ + to_address + data.hex()
    return concatenated


def transfer_to_string(
    source_address: str, destination_address: str, token_address: str, value: int
) -> str:
    """
    Returns the string representation of a transfer according to the validation payload.

    :param source_address: the source address.
    :param destination_address: the destination address.
    :param token_address: the token address.
    :param value: the transfered value.
    :return: the transfered amount
    """

    result = dict(
        transfers=[
            {
                "from": source_address,
                "to": destination_address,
                "token_address": token_address,
                "value": value,
            }
        ]
    )
    return json.dumps(result)


def merge_transfer_strings(transfer_strings: List[str]) -> str:
    """
    Returns the merged version of stringified transfers.

    :param transfer_strings: a list of stringified transfers.
    :return: the transfered amounts
    """
    transfers = [
        json.loads(transfer_string)["transfers"][0]
        for transfer_string in transfer_strings
    ]
    return json.dumps(dict(transfers=transfers))


class LiquidityProvisionBehaviourBaseCase(BaseSkillTestCase):
    """Base case for testing LiquidityProvision FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "liquidity_provision"
    )

    liquidity_provision_behaviour: LiquidityProvisionConsensusBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]
    period_state: PeriodState

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        # we need to store the current value of the meta-class attribute
        # _MetaPayload.transaction_type_to_payload_cls, and restore it
        # in the teardown function. We do a shallow copy so we avoid
        # to modify the old mapping during the execution of the tests.
        cls.old_tx_type_to_payload_cls = copy(
            _MetaPayload.transaction_type_to_payload_cls
        )
        _MetaPayload.transaction_type_to_payload_cls = {}
        super().setup()
        assert cls._skill.skill_context._agent_context is not None
        cls._skill.skill_context._agent_context.identity._default_address_key = (
            "ethereum"
        )
        cls._skill.skill_context._agent_context._default_ledger_id = "ethereum"
        cls.liquidity_provision_behaviour = cast(
            LiquidityProvisionConsensusBehaviour,
            cls._skill.skill_context.behaviours.main,
        )
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.contract_handler = cast(
            ContractApiHandler, cls._skill.skill_context.handlers.contract_api
        )
        cls.ledger_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )

        cls.liquidity_provision_behaviour.setup()
        cls._skill.skill_context.state.setup()
        assert (
            cast(BaseState, cls.liquidity_provision_behaviour.current_state).state_id
            == cls.liquidity_provision_behaviour.initial_state_cls.state_id
        )
        cls.period_state = PeriodState(StateDB(initial_period=0, initial_data={}))

    def fast_forward_to_state(
        self,
        behaviour: AbstractRoundBehaviour,
        state_id: str,
        period_state: BasePeriodState,
    ) -> None:
        """Fast forward the FSM to a state."""
        next_state = {s.state_id: s for s in behaviour.behaviour_states}[state_id]
        assert next_state is not None, f"State {state_id} not found"
        next_state = cast(Type[BaseState], next_state)
        behaviour.current_state = next_state(
            name=next_state.state_id, skill_context=behaviour.context
        )
        self.skill.skill_context.state.period.abci_app._round_results.append(
            period_state
        )
        if next_state.matching_round is not None:
            self.skill.skill_context.state.period.abci_app._current_round = (
                next_state.matching_round(
                    period_state, self.skill.skill_context.params.consensus_params
                )
            )

    def mock_ledger_api_request(
        self, request_kwargs: Dict, response_kwargs: Dict
    ) -> None:
        """
        Mock http request.

        :param request_kwargs: keyword arguments for request check.
        :param response_kwargs: keyword arguments for mock response.
        """

        self.assert_quantity_in_outbox(1)
        actual_ledger_api_message = self.get_message_from_outbox()
        assert actual_ledger_api_message is not None, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_ledger_api_message,
            message_type=LedgerApiMessage,
            to=str(LEDGER_CONNECTION_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            **request_kwargs,
        )

        assert has_attributes, error_str
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=(
                actual_ledger_api_message.dialogue_reference[0],
                "stub",
            ),
            target=actual_ledger_api_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(LEDGER_CONNECTION_PUBLIC_ID),
            ledger_id=str(LEDGER_CONNECTION_PUBLIC_ID),
            **response_kwargs,
        )
        self.ledger_handler.handle(incoming_message)
        self.liquidity_provision_behaviour.act_wrapper()

    def mock_contract_api_request(
        self, contract_id: str, request_kwargs: Dict, response_kwargs: Dict
    ) -> None:
        """
        Mock http request.

        :param contract_id: contract id.
        :param request_kwargs: keyword arguments for request check.
        :param response_kwargs: keyword arguments for mock response.
        """

        self.assert_quantity_in_outbox(1)
        actual_contract_ledger_message = self.get_message_from_outbox()
        assert actual_contract_ledger_message is not None, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_contract_ledger_message,
            message_type=ContractApiMessage,
            to=str(LEDGER_CONNECTION_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            ledger_id="ethereum",
            contract_id=contract_id,
            message_id=1,
            **request_kwargs,
        )
        assert has_attributes, error_str
        self.liquidity_provision_behaviour.act_wrapper()

        incoming_message = self.build_incoming_message(
            message_type=ContractApiMessage,
            dialogue_reference=(
                actual_contract_ledger_message.dialogue_reference[0],
                "stub",
            ),
            target=actual_contract_ledger_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(LEDGER_CONNECTION_PUBLIC_ID),
            ledger_id="ethereum",
            contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
            **response_kwargs,
        )
        self.contract_handler.handle(incoming_message)
        self.liquidity_provision_behaviour.act_wrapper()

    def mock_http_request(self, request_kwargs: Dict, response_kwargs: Dict) -> None:
        """
        Mock http request.

        :param request_kwargs: keyword arguments for request check.
        :param response_kwargs: keyword arguments for mock response.
        """

        self.assert_quantity_in_outbox(1)
        actual_http_message = self.get_message_from_outbox()
        assert actual_http_message is not None, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_http_message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            **request_kwargs,
        )
        assert has_attributes, error_str
        self.liquidity_provision_behaviour.act_wrapper()
        self.assert_quantity_in_outbox(0)
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=(actual_http_message.dialogue_reference[0], "stub"),
            performative=HttpMessage.Performative.RESPONSE,
            target=actual_http_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=str(HTTP_CLIENT_PUBLIC_ID),
            **response_kwargs,
        )
        self.http_handler.handle(incoming_message)
        self.liquidity_provision_behaviour.act_wrapper()

    def mock_signing_request(self, request_kwargs: Dict, response_kwargs: Dict) -> None:
        """Mock signing request."""
        self.assert_quantity_in_decision_making_queue(1)
        actual_signing_message = self.get_message_from_decision_maker_inbox()
        assert actual_signing_message is not None, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_signing_message,
            message_type=SigningMessage,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            **request_kwargs,
        )
        assert has_attributes, error_str
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=(actual_signing_message.dialogue_reference[0], "stub"),
            target=actual_signing_message.message_id,
            message_id=-1,
            to=str(self.skill.skill_context.skill_id),
            sender=self.skill.skill_context.decision_maker_address,
            **response_kwargs,
        )
        self.signing_handler.handle(incoming_message)
        self.liquidity_provision_behaviour.act_wrapper()

    def mock_a2a_transaction(
        self,
    ) -> None:
        """Performs mock a2a transaction."""

        self.mock_signing_request(
            request_kwargs=dict(
                performative=SigningMessage.Performative.SIGN_MESSAGE,
            ),
            response_kwargs=dict(
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SignedMessage(
                    ledger_id="ethereum", body="stub_signature"
                ),
            ),
        )

        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"result": {"hash": ""}}).encode("utf-8"),
            ),
        )
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps({"result": {"tx_result": {"code": OK_CODE}}}).encode(
                    "utf-8"
                ),
            ),
        )

    def end_round(
        self,
    ) -> None:
        """Ends round early to cover `wait_for_end` generator."""
        current_state = cast(
            BaseState, self.liquidity_provision_behaviour.current_state
        )
        if current_state is None:
            return
        current_state = cast(BaseState, current_state)
        if current_state.matching_round is None:
            return
        abci_app = current_state.context.state.period.abci_app
        old_round = abci_app._current_round
        abci_app._last_round = old_round
        abci_app._current_round = abci_app.transition_function[
            current_state.matching_round
        ][Event.DONE](abci_app.state, abci_app.consensus_params)
        abci_app._previous_rounds.append(old_round)
        self.liquidity_provision_behaviour._process_current_round()

    def _test_done_flag_set(self) -> None:
        """Test that, when round ends, the 'done' flag is set."""
        current_state = cast(
            BaseState, self.liquidity_provision_behaviour.current_state
        )
        assert not current_state.is_done()
        with mock.patch.object(
            self.liquidity_provision_behaviour.context.state, "period"
        ) as mock_period:
            mock_period.last_round_id = cast(
                AbstractRound, current_state.matching_round
            ).round_id
            current_state.act_wrapper()
            assert current_state.is_done()

    @classmethod
    def teardown(cls) -> None:
        """Teardown the test class."""
        _MetaPayload.transaction_type_to_payload_cls = cls.old_tx_type_to_payload_cls  # type: ignore


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
        cls.multisend_data_exit = "8d80ff0a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000026b0050cd56fb094f8f06063066a619d898475dd3eede00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e4baa2abde0000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd820000000000000000000000009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000003e800000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef0050cd56fb094f8f06063066a619d898475dd3eede00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        cls.multisend_data_swap_back = "8d80ff0a0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000047d00a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd82000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c900a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000a000000000000000000000000068fcdf52066cce5612827e872c45767e5a1f65510000000000000000000000000000000000000000000000000000000063b0beef00000000000000000000000000000000000000000000000000000000000000020000000000000000000000009a676e781a523b5d0c0e43731313a708cb607508000000000000000000000000dc64a140aa3e981100a9beca4e685f962f0cf6c900dc64a140aa3e981100a9beca4e685f962f0cf6c900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000dcd1bf9a1b36ce34237eeafef220932846bcd8200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000009a676e781a523b5d0c0e43731313a708cb60750800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000a51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c00000000000000000000000000000000000000000000000000000000000000000000000"

        cls.most_voted_tx_hash_enter = (
            "109709ac6f55b4023671b90aca07391d15f922c1f4c47e85990edaff826e8c35"
        )
        cls.most_voted_tx_hash_exit = (
            "9ac70bb9f261d81e11a7920c79a992443891ca631a643a138b621bddedd0c999"
        )
        cls.most_voted_tx_hash_swap_back = (
            "a2ad41587443107f74e4dfb4a2b00d8a1f50ad42104cd1b61d4482704694e571"
        )

        cls.safe_tx_gas = 4000000
        cls.enter_nonce =  1
        cls.exit_nonce = cls.enter_nonce + 1
        cls.swap_back_nonce = cls.enter_nonce + 2

        # setup default objects
        cls.strategy = get_dummy_strategy()
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
        payload_string = payload_to_hex(
            self.most_voted_tx_hash_enter,
            ether_value=0,
            safe_tx_gas=self.safe_tx_gas,
            to_address=self.router_contract_address,
            data=str.encode(self.multisend_data_enter),
        )
        period_state = cast(
            PeriodState,
            self.default_period_state_enter.update(
                most_voted_tx_hash=payload_string,
                most_voted_tx_data=self.multisend_data_enter,
                participant_to_signature=participant_to_signature,
                nonce=self.enter_nonce,
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
            FinalizeBehaviour.state_id,
            3,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert msg is not None and isinstance(msg, LedgerApiMessage)
        tx_digest = msg.transaction_digest.body

        # validate
        participant_to_lp_result = {
            address: ValidatePayload(
                sender=address,
            )
            for address, _ in self.safe_owners.items()
        }

        period_state = cast(
            PeriodState,
            self.default_period_state_enter.update(
                final_tx_hash=tx_digest,
                most_voted_tx_hash=self.most_voted_tx_hash_enter,
                most_voted_tx_data=self.multisend_data_enter,
                participant_to_lp_result=participant_to_lp_result,
            ),
        )
        handlers = [
            self.ledger_handler,
            self.contract_handler,
            self.contract_handler,
        ]
        expected_content = [
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT  # type: ignore
            },
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
        ]
        expected_types = [
            {
                "transaction_receipt": TransactionReceipt,
            },
            {
                "state": State,
            },
            {
                "state": State,
            },
        ]
        _, verif_msg, transfers_msg = self.process_n_messsages(
            ValidateTransactionBehaviour.state_id,
            3,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert verif_msg is not None and isinstance(verif_msg, ContractApiMessage)
        assert verif_msg.state.body[
            "verified"
        ], f"Message not verified: {verif_msg.state.body}"

        transfers = cast(ContractApiMessage, transfers_msg).state.body["logs"]
        transfered_amount = parse_tx_token_balance(
            cast(list, transfers),
            LP_TOKEN_ADDRESS,
            DEFAULT_MINTER,
            self.safe_contract_address,
        )
        assert (
            transfered_amount == 1000
        ), f"Enter pool amount is not correct: {transfered_amount} != 1000"

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
                most_voted_lp_result=1,
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
            FinalizeBehaviour.state_id,
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
            self.contract_handler,
        ]
        expected_content = [
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT  # type: ignore
            },
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
        ]
        expected_types = [
            {
                "transaction_receipt": TransactionReceipt,
            },
            {
                "state": State,
            },
            {
                "state": State,
            },
        ]
        _, verif_msg, transfers_msg = self.process_n_messsages(
            ValidateTransactionBehaviour.state_id,
            3,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert verif_msg is not None and isinstance(verif_msg, ContractApiMessage)
        assert verif_msg.state.body[
            "verified"
        ], f"Message not verified: {verif_msg.state.body}"
        transfers = cast(ContractApiMessage, transfers_msg).state.body["logs"]
        transfered_amount = parse_tx_token_balance(
            cast(list, transfers),
            LP_TOKEN_ADDRESS,
            self.safe_contract_address,
            LP_TOKEN_ADDRESS,
        )
        assert (
            transfered_amount == 1000
        ), f"Exit pool amount is not correct: {transfered_amount} != 1000"
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
            FinalizeBehaviour.state_id,
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
            self.contract_handler,
        ]
        expected_content = [
            {
                "performative": LedgerApiMessage.Performative.TRANSACTION_RECEIPT  # type: ignore
            },
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
            {"performative": ContractApiMessage.Performative.STATE},  # type: ignore
        ]
        expected_types = [
            {
                "transaction_receipt": TransactionReceipt,
            },
            {
                "state": State,
            },
            {
                "state": State,
            },
        ]
        _, verif_msg, transfers_msg = self.process_n_messsages(
            ValidateTransactionBehaviour.state_id,
            3,
            period_state,
            handlers,
            expected_content,
            expected_types,
        )
        assert verif_msg is not None and isinstance(verif_msg, ContractApiMessage)
        assert verif_msg.state.body[
            "verified"
        ], f"Message not verified: {verif_msg.state.body}"
        transfers = cast(ContractApiMessage, transfers_msg).state.body["logs"]
        transfered_amount = parse_tx_token_balance(
            cast(list, transfers),
            TOKEN_A_ADDRESS,
            self.safe_contract_address,
            AB_POOL_ADDRESS,
        )
        assert (
            transfered_amount == 250
        ), f"Swap back amount is not correct: {transfered_amount} != 250"
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
            self.default_period_state_exit.update(
                most_voted_strategy=strategy,
                most_voted_transfers=transfer_to_string(
                    source_address=DEFAULT_MINTER,
                    destination_address=self.safe_contract_address,
                    token_address=LP_TOKEN_ADDRESS,
                    value=1000,
                ),
            ),
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

    # Swap back behaviours

    def test_swap_back_tx_hash_behaviour(self) -> None:
        """test_swap_back_tx_hash_behaviour"""
        strategy = deepcopy(self.strategy)
        strategy["safe_nonce"] = 2

        transfer_a = transfer_to_string(
            source_address=self.router_contract_address,
            destination_address=self.safe_contract_address,
            token_address=strategy["pair"]["token_a"]["address"],
            value=250,
        )
        transfer_b = transfer_to_string(
            source_address=self.router_contract_address,
            destination_address=self.safe_contract_address,
            token_address=strategy["pair"]["token_b"]["address"],
            value=250,
        )

        transfers = merge_transfer_strings([transfer_a, transfer_b])

        period_state = cast(
            PeriodState,
            self.default_period_state_swap_back.update(
                most_voted_strategy=strategy,
                most_voted_transfers=transfers,
            ),
        )

        timestamp = self.ethereum_api.api.eth.get_block("latest")["timestamp"]
        assert self.strategy["deadline"] > timestamp, "Increase timestamp!"
        cycles = 7
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
        _, _, _, _, _, msg_a, msg_b = self.process_n_messsages(
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
