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
"""Tests for valory/liquidity_provision_behaviour skill's behaviours."""
import binascii
import json
from copy import copy
from pathlib import Path
from typing import Any, Dict, Type, cast
from unittest import mock

import pytest
from aea.exceptions import AEAActException
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedMessage,
    SignedTransaction,
    State,
    TransactionDigest,
    TransactionReceipt,
)
from aea.test_tools.test_skill import BaseSkillTestCase
from aea_ledger_ethereum.ethereum import EthereumApi

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
from packages.valory.contracts.gnosis_safe.contract import SafeOperation
from packages.valory.contracts.multisend.contract import MultiSendContract
from packages.valory.contracts.uniswap_v2_erc20.contract import UniswapV2ERC20Contract
from packages.valory.contracts.uniswap_v2_router_02.contract import (
    UniswapV2Router02Contract,
)
from packages.valory.protocols.contract_api.custom_types import Kwargs
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
    CURRENT_BLOCK_TIMESTAMP,
    ETHER_VALUE,
    EnterPoolTransactionHashBehaviour,
    EnterPoolTransactionSendBehaviour,
    EnterPoolTransactionSignatureBehaviour,
    EnterPoolTransactionValidationBehaviour,
    ExitPoolTransactionHashBehaviour,
    GnosisSafeContract,
    LP_TOKEN_ADDRESS,
    LiquidityProvisionConsensusBehaviour,
    MAX_ALLOWANCE,
    SAFE_TX_GAS,
    StrategyEvaluationBehaviour,
    SwapBackTransactionHashBehaviour,
    parse_tx_token_balance,
)
from packages.valory.skills.liquidity_provision.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.valory.skills.liquidity_provision.payloads import StrategyType
from packages.valory.skills.liquidity_provision.rounds import Event, PeriodState

from tests.conftest import ROOT_DIR
from tests.test_skills.test_liquidity_provision.test_rounds import get_participants
from tests.test_skills.test_transaction_settlement_abci.test_rounds import (
    get_participant_to_signature,
)


def get_default_strategy(
    is_base_native: bool, is_a_native: bool, is_b_native: bool
) -> Dict:
    """Returns default strategy."""
    return {
        "action": StrategyType.GO.value,
        "safe_nonce": 0,
        "chain": "Ethereum",
        "safe_tx_gas": SAFE_TX_GAS,
        "deadline": CURRENT_BLOCK_TIMESTAMP + 300,  # 5 min into future
        "base": {
            "ticker": "WETH",
            "address": "0xWETH_ADDRESS",
            "amount_in_max_a": int(1e4),
            "amount_min_after_swap_back_a": int(1e2),
            "amount_in_max_b": int(1e4),
            "amount_min_after_swap_back_b": int(1e2),
            "is_native": is_base_native,
            "set_allowance": MAX_ALLOWANCE,
            "remove_allowance": 0,
        },
        "pair": {
            "token_LP": {
                "address": LP_TOKEN_ADDRESS,
                "set_allowance": MAX_ALLOWANCE,
                "remove_allowance": 0,
            },
            "token_a": {
                "ticker": "TKA",
                "address": "0xTKA_ADDRESS",
                "amount_after_swap": int(1e3),
                "amount_min_after_add_liq": int(0.5e3),
                "is_native": is_a_native,
                "set_allowance": MAX_ALLOWANCE,
                "remove_allowance": 0,
            },
            "token_b": {
                "ticker": "TKB",
                "address": "0xTKB_ADDRESS",
                "amount_after_swap": int(1e3),
                "amount_min_after_add_liq": int(0.5e3),
                "is_native": is_b_native,
                "set_allowance": MAX_ALLOWANCE,
                "remove_allowance": 0,
            },
        },
    }


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


class TestStrategyEvaluationBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test StrategyEvaluationBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=StrategyEvaluationBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == StrategyEvaluationBehaviour.state_id
        )
        self.liquidity_provision_behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()


class TestEnterPoolTransactionHashBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test EnterPoolTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
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
        self.liquidity_provision_behaviour.act_wrapper()

        # Add allowance for base token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap first token
        method_name = (
            "swap_tokens_for_exact_ETH"
            if strategy["pair"]["token_a"]["is_native"]
            else "swap_tokens_for_exact_tokens"
        )

        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name=method_name,
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(
                            strategy["pair"]["token_a"]["amount_after_swap"]
                        ),
                        amount_in_max=int(strategy["base"]["amount_in_max_a"]),
                        path=[
                            strategy["base"]["address"],
                            strategy["pair"]["token_a"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_swap_tokens_for_exact_ETH_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore  # type: ignore
                ),
            ),
        )

        # Swap second token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_tokens_for_exact_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(
                            strategy["pair"]["token_b"]["amount_after_swap"]
                        ),
                        amount_in_max=int(strategy["base"]["amount_in_max_b"]),
                        path=[
                            strategy["base"]["address"],
                            strategy["pair"]["token_b"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,  # 5 min into the future
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_swap_exact_tokens_for_tokens_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add allowance for token B
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add liquidity
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="add_liquidity_ETH",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token=strategy["pair"]["token_b"]["address"],
                        amount_token_desired=int(
                            strategy["pair"]["token_b"]["amount_after_swap"]
                        ),
                        amount_token_min=int(
                            strategy["pair"]["token_b"]["amount_min_after_add_liq"]
                        ),
                        amount_ETH_min=int(
                            strategy["pair"]["token_a"]["amount_min_after_add_liq"]
                        ),
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
                kwargs=Kwargs(
                    dict(
                        to_address=period_state.multisend_contract_address,
                        value=ETHER_VALUE,
                        data=b"ummy_tx",  # type: ignore
                        operation=SafeOperation.DELEGATE_CALL.value,
                        safe_tx_gas=4000000,
                        safe_nonce=strategy["safe_nonce"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

    def test_transaction_hash_when_strategy_is_not_native(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=False, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
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
        self.liquidity_provision_behaviour.act_wrapper()

        # Add allowance for base token
        method_name = (
            "swap_tokens_for_exact_ETH"
            if strategy["pair"]["token_a"]["is_native"]
            else "swap_tokens_for_exact_tokens"
        )

        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap first token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name=method_name,
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(
                            strategy["pair"]["token_a"]["amount_after_swap"]
                        ),
                        amount_in_max=int(strategy["base"]["amount_in_max_a"]),
                        path=[
                            strategy["base"]["address"],
                            strategy["pair"]["token_a"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_swap_tokens_for_exact_tokens_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap second token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_tokens_for_exact_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out=int(
                            strategy["pair"]["token_b"]["amount_after_swap"]
                        ),
                        amount_in_max=int(strategy["base"]["amount_in_max_b"]),
                        path=[
                            strategy["base"]["address"],
                            strategy["pair"]["token_b"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,  # 5 min into the future
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_swap_tokens_for_exact_tokens_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add allowance for token A
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_a"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add allowance for token B
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Add liquidity
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="add_liquidity",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token_a=strategy["pair"]["token_a"]["address"],
                        token_b=strategy["pair"]["token_b"]["address"],
                        amount_a_desired=int(
                            strategy["pair"]["token_a"]["amount_after_swap"]
                        ),
                        amount_b_desired=int(
                            strategy["pair"]["token_b"]["amount_after_swap"]
                        ),
                        amount_a_min=int(
                            strategy["pair"]["token_a"]["amount_min_after_add_liq"]
                        ),
                        amount_b_min=int(
                            strategy["pair"]["token_b"]["amount_min_after_add_liq"]
                        ),
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
                kwargs=Kwargs(
                    dict(
                        to_address=period_state.multisend_contract_address,
                        value=ETHER_VALUE,
                        data=b"ummy_tx",  # type: ignore
                        operation=SafeOperation.DELEGATE_CALL.value,
                        safe_tx_gas=4000000,
                        safe_nonce=strategy["safe_nonce"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

    def test_transaction_hash_bad_swap_parameters(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=True, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
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

        with pytest.raises(AEAActException):

            self.liquidity_provision_behaviour.act_wrapper()

            # Add allowance for base token
            self.mock_contract_api_request(
                contract_id=str(UniswapV2ERC20Contract.contract_id),
                request_kwargs=dict(
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                    contract_address=strategy["base"]["address"],
                    kwargs=Kwargs(
                        dict(
                            method_name="approve",
                            spender=period_state.router_contract_address,
                            value=MAX_ALLOWANCE,
                        )
                    ),
                ),
                response_kwargs=dict(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    callable="get_method_data",
                    raw_transaction=RawTransaction(
                        ledger_id="ethereum",
                        body={"data": b"dummy_tx"},  # type: ignore
                    ),
                ),
            )


class TestEnterPoolTransactionSignatureBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test EnterPoolTransactionSignatureBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash=binascii.hexlify(b"dummy_tx").decode(),
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=EnterPoolTransactionSignatureBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == EnterPoolTransactionSignatureBehaviour.state_id
        )
        self.liquidity_provision_behaviour.act_wrapper()

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
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()


class TestEnterPoolTransactionSendBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test EnterPoolTransactionSendBehaviour."""

    def test_not_sender_act(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash=binascii.hexlify(b"dummy_tx").decode(),
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                ),
            )
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
        self.liquidity_provision_behaviour.act_wrapper()
        self._test_done_flag_set()
        self.end_round()

    def test_sender_act(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        participants = get_participants()
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    participants=participants,
                    most_voted_tx_hash=b"dummy_tx".hex(),
                    most_voted_tx_data=b"some_data".hex(),
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address=self.skill.skill_context.agent_address,
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    participant_to_signature=get_participant_to_signature(participants),
                    router_contract_address="router_contract_address",
                ),
            )
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
        self.liquidity_provision_behaviour.act_wrapper()

        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
                kwargs=Kwargs(
                    dict(
                        sender_address=self.skill.skill_context.agent_address,
                        owners=tuple(period_state.participants),  # type: ignore
                        to_address="multisend_contract_address",
                        value=0,
                        data=b"some_data",  # type: ignore
                        operation=SafeOperation.DELEGATE_CALL.value,
                        safe_tx_gas=4000000,
                        signatures_by_owner={
                            key: payload.signature
                            for key, payload in period_state.participant_to_signature.items()
                        },
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        self.mock_signing_request(
            request_kwargs=dict(
                performative=SigningMessage.Performative.SIGN_TRANSACTION,
            ),
            response_kwargs=dict(
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=SignedTransaction(
                    ledger_id="ethereum", body={"body": "stub_signature"}
                ),
            ),
        )

        self.mock_ledger_api_request(
            request_kwargs=dict(
                performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION
            ),
            response_kwargs=dict(
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                transaction_digest=TransactionDigest(
                    ledger_id="ethereum", body="tx_hash"
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()


class TestEnterPoolTransactionValidationBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test EnterPoolTransactionValidationBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        participants = get_participants()
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    participants=participants,
                    most_voted_tx_hash="0x",
                    most_voted_tx_data=b"data".hex(),
                    most_voted_strategy=strategy,
                    final_tx_hash=binascii.hexlify(b"dummy_tx").decode(),
                    multisend_contract_address="multisend_contract_address",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    participant_to_signature=get_participant_to_signature(participants),
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=EnterPoolTransactionValidationBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == EnterPoolTransactionValidationBehaviour.state_id
        )

        self.liquidity_provision_behaviour.act_wrapper()
        with mock.patch.object(
            EthereumApi, "is_transaction_settled", return_value=True
        ):
            self.mock_ledger_api_request(
                request_kwargs=dict(
                    performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT
                ),
                response_kwargs=dict(
                    performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                    transaction_receipt=TransactionReceipt(
                        ledger_id="ethereum",
                        transaction={"body": "tx_receipt"},
                        receipt={"body": "tx_receipt"},
                    ),
                ),
            )

        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=period_state.safe_contract_address,
                kwargs=Kwargs(
                    dict(
                        tx_hash=period_state.final_tx_hash,
                        owners=tuple(period_state.participants),  # type: ignore
                        to_address="multisend_contract_address",
                        value=0,
                        data=b"data",  # type: ignore
                        operation=SafeOperation.DELEGATE_CALL.value,
                        safe_tx_gas=4000000,
                        signatures_by_owner={
                            key: payload.signature
                            for key, payload in period_state.participant_to_signature.items()
                        },
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="verify_tx",
                state=State(
                    ledger_id="ethereum",
                    body={"verified": True},
                ),
            ),
        )

        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=strategy["pair"]["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        tx_hash=period_state.final_tx_hash,
                        target_address=period_state.safe_contract_address,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="verify_tx",
                state=State(
                    ledger_id="ethereum",
                    body={"logs": []},
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()


class TestExitPoolTransactionHashBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test ExitPoolTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )

        amount_base_sent = 0
        amount_b_sent = 0
        amount_liquidity_received = 0

        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=ExitPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == ExitPoolTransactionHashBehaviour.state_id
        )
        self.liquidity_provision_behaviour.act_wrapper()

        # Add allowance for LP token to be spent by the router
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=strategy["pair"]["token_LP"]["set_allowance"],
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove liquidity
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="remove_liquidity_ETH",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token=strategy["pair"]["token_b"]["address"],
                        liquidity=amount_liquidity_received,
                        amount_token_min=int(amount_b_sent),
                        amount_ETH_min=int(amount_base_sent),
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self.end_round()

    def test_transaction_hash_when_strategy_is_not_native(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=False, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )

        amount_a_sent = 0
        amount_b_sent = 0
        amount_liquidity_received = 0

        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=ExitPoolTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == ExitPoolTransactionHashBehaviour.state_id
        )
        self.liquidity_provision_behaviour.act_wrapper()

        # Add allowance for LP token to be spent by the router
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_LP"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=MAX_ALLOWANCE,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove liquidity
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="remove_liquidity",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        token_a=strategy["pair"]["token_a"]["address"],
                        token_b=strategy["pair"]["token_b"]["address"],
                        liquidity=amount_liquidity_received,
                        amount_a_min=int(amount_a_sent),
                        amount_b_min=int(amount_b_sent),
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()


class TestSwapBackTransactionHashBehaviour(LiquidityProvisionBehaviourBaseCase):
    """Test SwapBackTransactionHashBehaviour."""

    def test_transaction_hash(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=True, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=SwapBackTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == SwapBackTransactionHashBehaviour.state_id
        )
        self.liquidity_provision_behaviour.act_wrapper()

        # Swap first token back
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_ETH_for_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_out_min=int(
                            strategy["base"]["amount_min_after_swap_back_a"]
                        ),
                        path=[
                            strategy["pair"]["token_a"]["address"],
                            strategy["base"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap second token back
        amount_b_received = 0
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(
                            amount_b_received,
                        ),
                        amount_out_min=int(
                            strategy["base"]["amount_min_after_swap_back_b"]
                        ),
                        path=[
                            strategy["pair"]["token_b"]["address"],
                            strategy["base"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for base token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for the second token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

    def test_transaction_hash_when_strategy_is_not_native(
        self,
    ) -> None:
        """Test tx hash behaviour."""

        strategy = get_default_strategy(
            is_base_native=False, is_a_native=False, is_b_native=False
        )
        period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    most_voted_tx_hash="0x",
                    safe_contract_address="safe_contract_address",
                    most_voted_keeper_address="most_voted_keeper_address",
                    most_voted_strategy=strategy,
                    multisend_contract_address="multisend_contract_address",
                    router_contract_address="router_contract_address",
                    most_voted_transfers='{"transfers":[]}',
                ),
            )
        )
        self.fast_forward_to_state(
            behaviour=self.liquidity_provision_behaviour,
            state_id=SwapBackTransactionHashBehaviour.state_id,
            period_state=period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.liquidity_provision_behaviour.current_state),
            ).state_id
            == SwapBackTransactionHashBehaviour.state_id
        )
        self.liquidity_provision_behaviour.act_wrapper()

        # Swap first token back
        amount_a_received = 0
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(amount_a_received),
                        amount_out_min=int(
                            strategy["base"]["amount_min_after_swap_back_a"]
                        ),
                        path=[
                            strategy["pair"]["token_a"]["address"],
                            strategy["base"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Swap second token back
        amount_b_received = 0
        self.mock_contract_api_request(
            contract_id=str(UniswapV2Router02Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.router_contract_address,
                kwargs=Kwargs(
                    dict(
                        method_name="swap_exact_tokens_for_tokens",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        amount_in=int(amount_b_received),
                        amount_out_min=int(
                            strategy["base"]["amount_min_after_swap_back_b"]
                        ),
                        path=[
                            strategy["pair"]["token_b"]["address"],
                            strategy["base"]["address"],
                        ],
                        to=period_state.safe_contract_address,
                        deadline=CURRENT_BLOCK_TIMESTAMP + 300,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for base token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["base"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for the first token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_a"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Remove allowance for the second token
        self.mock_contract_api_request(
            contract_id=str(UniswapV2ERC20Contract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=strategy["pair"]["token_b"]["address"],
                kwargs=Kwargs(
                    dict(
                        method_name="approve",
                        # sender=period_state.safe_contract_address,  # noqa: E800
                        # gas=TEMP_GAS,  # noqa: E800
                        # gas_price=TEMP_GAS_PRICE,  # noqa: E800
                        spender=period_state.router_contract_address,
                        value=0,
                    )
                ),
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_method_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx"},  # type: ignore
                ),
            ),
        )

        # Get the tx list data from multisend contract
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_tx_data",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"data": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        # Get the tx hash from Gnosis Safe contract
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=period_state.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"tx_hash": b"dummy_tx".hex()},  # type: ignore
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()


def test_parse_tx_token_balance() -> None:
    """Test test_parse_tx_token_balance"""

    transfer_logs = [
        {"from": "from", "to": "to", "token_address": "token_address", "value": 1},
        {"from": "from", "to": "to", "token_address": "token_address", "value": 1},
        {
            "from": "from_2",
            "to": "to_2",
            "token_address": "token_address_2",
            "value": 1,
        },
    ]

    amount_1 = parse_tx_token_balance(  # nosec
        transfer_logs=transfer_logs,
        token_address="token_address",
        source_address="from",
        destination_address="to",
    )
    amount_2 = parse_tx_token_balance(  # nosec
        transfer_logs=transfer_logs,
        token_address="token_address_2",
        source_address="from_2",
        destination_address="to_2",
    )
    assert amount_1 == 2, "The transfered amount is not correct"
    assert amount_2 == 1, "The transfered amount is not correct"
