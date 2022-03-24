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

"""Tests for valory/registration_abci skill's behaviours."""

import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Type, Union, cast
from unittest import mock
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedMessage,
    SignedTransaction,
)
from aea.helpers.transaction.base import State as TrState
from aea.helpers.transaction.base import TransactionDigest, TransactionReceipt

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.protocols.abci import AbciMessage  # noqa: F401
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import StateDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    RPCResponseStatus,
    make_degenerate_state,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    CheckLateTxHashesBehaviour,
    CheckTransactionHistoryBehaviour,
    FinalizeBehaviour,
    RandomnessTransactionSubmissionBehaviour,
    ResetBehaviour,
    SelectKeeperTransactionSubmissionBehaviourA,
    SelectKeeperTransactionSubmissionBehaviourB,
    SignatureBehaviour,
    SynchronizeLateMessagesBehaviour,
    TransactionSettlementBaseState,
    TxDataType,
    ValidateTransactionBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    VerificationStatus,
    hash_payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    Event as TransactionSettlementEvent,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    FinishedTransactionSubmissionRound,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    PeriodState as TransactionSettlementPeriodState,
)

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase
from tests.test_skills.test_abstract_round_abci.test_common import (
    BaseRandomnessBehaviourTest,
    BaseSelectKeeperBehaviourTest,
)
from tests.test_skills.test_price_estimation_abci.test_behaviours import (
    PriceEstimationFSMBehaviourBaseCase,
)


class TransactionSettlementFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing TransactionSettlement FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "transaction_settlement_abci"
    )


class TestTransactionSettlementBaseState(PriceEstimationFSMBehaviourBaseCase):
    """Test `TransactionSettlementBaseState`."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "transaction_settlement_abci"
    )

    @pytest.mark.parametrize(
        "message, tx_digest, rpc_status, expected_data",
        (
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.ERROR, message="GS026"
                ),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "status": VerificationStatus.VERIFIED,
                    "tx_digest": "",
                    "nonce": "",
                    "max_priority_fee_per_gas": "",
                },
            ),
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.ERROR, message="test"
                ),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "status": VerificationStatus.ERROR,
                    "tx_digest": "",
                    "nonce": "",
                    "max_priority_fee_per_gas": "",
                },
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_MESSAGE),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                    "nonce": "",
                    "max_priority_fee_per_gas": "",
                },
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.INCORRECT_NONCE,
                {
                    "status": VerificationStatus.ERROR,
                    "tx_digest": "",
                    "nonce": "",
                    "max_priority_fee_per_gas": "",
                },
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.UNCLASSIFIED_ERROR,
                {
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                    "nonce": "",
                    "max_priority_fee_per_gas": "",
                },
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.UNDERPRICED,
                {
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                    "nonce": "",
                    "max_priority_fee_per_gas": "",
                },
            ),
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    raw_transaction=MagicMock(
                        body={"nonce": 0, "maxPriorityFeePerGas": 10}
                    ),
                ),
                "test_digest",
                RPCResponseStatus.SUCCESS,
                {
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test_digest",
                    "nonce": 0,
                    "max_priority_fee_per_gas": 10,
                },
            ),
        ),
    )
    def test__get_tx_data(
        self,
        message: ContractApiMessage,
        tx_digest: Optional[str],
        rpc_status: RPCResponseStatus,
        expected_data: TxDataType,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test `_get_tx_data`."""
        # fast-forward to any state of the tx settlement skill
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=SignatureBehaviour.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_tx_hash="b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002625a000x77E9b2EF921253A171Fa0CB9ba80558648Ff7215b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == SignatureBehaviour.state_id
        )

        # patch the `send_raw_transaction` method
        def dummy_send_raw_transaction(
            *_: Any,
        ) -> Generator[None, None, Tuple[Optional[str], RPCResponseStatus]]:
            """Dummy `send_raw_transaction` method."""
            yield
            return tx_digest, rpc_status

        monkeypatch.setattr(
            BaseState, "send_raw_transaction", dummy_send_raw_transaction
        )
        # call `_get_tx_data`
        tx_data_iterator = cast(
            TransactionSettlementBaseState, self.behaviour.current_state
        )._get_tx_data(message)

        if message.performative == ContractApiMessage.Performative.RAW_TRANSACTION:
            next(tx_data_iterator)

        try:
            next(tx_data_iterator)
        except StopIteration as res:
            assert res.value == expected_data


class TestRandomnessInOperation(BaseRandomnessBehaviourTest):
    """Test randomness in operation."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "transaction_settlement_abci"
    )

    randomness_behaviour_class = RandomnessTransactionSubmissionBehaviour
    next_behaviour_class = SelectKeeperTransactionSubmissionBehaviourA
    done_event = TransactionSettlementEvent.DONE


class TestSelectKeeperTransactionSubmissionBehaviourA(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "transaction_settlement_abci"
    )

    select_keeper_behaviour_class = SelectKeeperTransactionSubmissionBehaviourA
    next_behaviour_class = SignatureBehaviour
    done_event = TransactionSettlementEvent.DONE


class TestSelectKeeperTransactionSubmissionBehaviourB(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "transaction_settlement_abci"
    )

    select_keeper_behaviour_class = SelectKeeperTransactionSubmissionBehaviourB
    next_behaviour_class = FinalizeBehaviour
    done_event = TransactionSettlementEvent.DONE


class TestSignatureBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test SignatureBehaviour."""

    def test_signature_behaviour(
        self,
    ) -> None:
        """Test signature behaviour."""

        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=SignatureBehaviour.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_tx_hash="b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002625a000x77E9b2EF921253A171Fa0CB9ba80558648Ff7215b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == SignatureBehaviour.state_id
        )
        self.behaviour.act_wrapper()
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
        self.end_round(TransactionSettlementEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == FinalizeBehaviour.state_id


class TestFinalizeBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test FinalizeBehaviour."""

    def test_non_sender_act(
        self,
    ) -> None:
        """Test finalize behaviour."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=FinalizeBehaviour.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_keeper_address="most_voted_keeper_address",
                        participants=participants,
                        is_reset_params_set=True,
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == FinalizeBehaviour.state_id
        )
        self.behaviour.act_wrapper()
        self._test_done_flag_set()
        self.end_round(TransactionSettlementEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == ValidateTransactionBehaviour.state_id

    @pytest.mark.parametrize(
        "resubmitting, response_kwargs",
        (
            (
                (
                    True,
                    dict(
                        performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                        callable="get_deploy_transaction",
                        raw_transaction=RawTransaction(
                            ledger_id="ethereum",
                            body={
                                "tx_hash": "0x3b",
                                "nonce": 0,
                                "maxFeePerGas": int(10e10),
                                "maxPriorityFeePerGas": int(10e10),
                            },
                        ),
                    ),
                )
            ),
            (
                False,
                dict(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    callable="get_deploy_transaction",
                    raw_transaction=RawTransaction(
                        ledger_id="ethereum",
                        body={
                            "tx_hash": "0x3b",
                            "nonce": 0,
                            "maxFeePerGas": int(10e10),
                            "maxPriorityFeePerGas": int(10e10),
                        },
                    ),
                ),
            ),
            (
                False,
                dict(
                    performative=ContractApiMessage.Performative.ERROR,
                    callable="get_deploy_transaction",
                    code=500,
                    message="GS026",
                    data=b"",
                ),
            ),
            (
                False,
                dict(
                    performative=ContractApiMessage.Performative.ERROR,
                    callable="get_deploy_transaction",
                    code=500,
                    message="other error",
                    data=b"",
                ),
            ),
        ),
    )
    def test_sender_act(
        self,
        resubmitting: bool,
        response_kwargs: Dict[
            str,
            Union[
                int,
                str,
                bytes,
                Dict[str, Union[int, str]],
                ContractApiMessage.Performative,
                RawTransaction,
            ],
        ],
    ) -> None:
        """Test finalize behaviour."""
        nonce: Optional[int] = None
        max_priority_fee_per_gas: Optional[int] = None

        if resubmitting:
            nonce = 0
            max_priority_fee_per_gas = 1

        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=FinalizeBehaviour.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_keeper_address=self.skill.skill_context.agent_address,
                        safe_contract_address="safe_contract_address",
                        participants=participants,
                        participant_to_signature={},
                        most_voted_tx_hash=hash_payload_to_hex(
                            "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                            1,
                            1,
                            "0x77E9b2EF921253A171Fa0CB9ba80558648Ff7215",
                            b"b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                        ),
                        nonce=nonce,
                        max_priority_fee_per_gas=max_priority_fee_per_gas,
                    ),
                )
            ),
        )

        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == FinalizeBehaviour.state_id
        self.behaviour.act_wrapper()

        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ),
            contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
            response_kwargs=response_kwargs,
        )

        if (
            response_kwargs["performative"]
            == ContractApiMessage.Performative.RAW_TRANSACTION
        ):
            self.mock_signing_request(
                request_kwargs=dict(
                    performative=SigningMessage.Performative.SIGN_TRANSACTION
                ),
                response_kwargs=dict(
                    performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                    signed_transaction=SignedTransaction(ledger_id="ethereum", body={}),
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
        self.end_round(TransactionSettlementEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == ValidateTransactionBehaviour.state_id

    def test_handle_late_messages(self) -> None:
        """Test `handle_late_messages.`"""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=FinalizeBehaviour.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_keeper_address="most_voted_keeper_address",
                        participants=participants,
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == FinalizeBehaviour.state_id
        )

        message = ContractApiMessage(ContractApiMessage.Performative.RAW_MESSAGE)  # type: ignore
        cast(BaseState, self.behaviour.current_state).handle_late_messages(message)
        assert cast(
            TransactionSettlementBaseState, self.behaviour.current_state
        ).params.late_messages == [message]

        message = MagicMock()
        with mock.patch.object(self.behaviour.context.logger, "warning") as mock_info:
            cast(BaseState, self.behaviour.current_state).handle_late_messages(message)
            mock_info.assert_called_with(
                f"No callback defined for request with nonce: {message.dialogue_reference[0]}"
            )


class TestValidateTransactionBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test ValidateTransactionBehaviour."""

    def _fast_forward(self) -> None:
        """Fast-forward to relevant state."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        most_voted_keeper_address = self.skill.skill_context.agent_address
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=ValidateTransactionBehaviour.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        safe_contract_address="safe_contract_address",
                        tx_hashes_history=["final_tx_hash"],
                        final_tx_hash="dummy_hash",
                        participants=participants,
                        most_voted_keeper_address=most_voted_keeper_address,
                        participant_to_signature={},
                        most_voted_tx_hash=hash_payload_to_hex(
                            "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                            1,
                            1,
                            "0x77E9b2EF921253A171Fa0CB9ba80558648Ff7215",
                            b"b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                        ),
                        max_priority_fee_per_gas=int(10e10),
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == ValidateTransactionBehaviour.state_id
        )

    def test_validate_transaction_safe_behaviour(
        self,
    ) -> None:
        """Test ValidateTransactionBehaviour."""
        self._fast_forward()
        self.behaviour.act_wrapper()
        self.mock_ledger_api_request(
            request_kwargs=dict(
                performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT
            ),
            response_kwargs=dict(
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=TransactionReceipt(
                    ledger_id="ethereum", receipt={"status": 1}, transaction={}
                ),
            ),
        )
        self.mock_contract_api_request(
            request_kwargs=dict(performative=ContractApiMessage.Performative.GET_STATE),
            contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="get_deploy_transaction",
                state=TrState(ledger_id="ethereum", body={"verified": True}),
            ),
        )
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(TransactionSettlementEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert (
            state.state_id
            == make_degenerate_state(
                FinishedTransactionSubmissionRound.round_id
            ).state_id
        )

    def test_validate_transaction_safe_behaviour_no_tx_sent(
        self,
    ) -> None:
        """Test ValidateTransactionBehaviour when tx cannot be sent."""
        self._fast_forward()

        with mock.patch.object(self.behaviour.context.logger, "error") as mock_logger:
            self.behaviour.act_wrapper()
            self.mock_ledger_api_request(
                request_kwargs=dict(
                    performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                ),
                response_kwargs=dict(
                    performative=LedgerApiMessage.Performative.ERROR,
                    code=1,
                ),
            )
            state = cast(
                TransactionSettlementBaseState,
                self.behaviour.current_state,
            )
            latest_tx_hash = state.period_state.tx_hashes_history[-1]
            mock_logger.assert_any_call(f"tx {latest_tx_hash} receipt check timed out!")


class TestCheckTransactionHistoryBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test CheckTransactionHistoryBehaviour."""

    def _fast_forward(self, hashes_history: Optional[List[Optional[str]]]) -> None:
        """Fast-forward to relevant state."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=CheckTransactionHistoryBehaviour.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        safe_contract_address="safe_contract_address",
                        participants=frozenset(
                            {self.skill.skill_context.agent_address, "a_1", "a_2"}
                        ),
                        participant_to_signature={},
                        most_voted_tx_hash="b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002625a000x77E9b2EF921253A171Fa0CB9ba80558648Ff7215b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                        tx_hashes_history=hashes_history,
                    ),
                )
            ),
        )
        assert (
            cast(BaseState, self.behaviour.current_state).state_id
            == CheckTransactionHistoryBehaviour.state_id
        )

    @pytest.mark.parametrize(
        "verified, hashes_history, revert_reason",
        (
            (0, None, "test"),
            (0, [None], "test"),
            (0, [None], "GS026"),
            (1, [None], "test"),
        ),
    )
    def test_check_tx_history_behaviour(
        self,
        verified: int,
        hashes_history: Optional[List[Optional[str]]],
        revert_reason: str,
    ) -> None:
        """Test CheckTransactionHistoryBehaviour."""
        self._fast_forward(hashes_history)
        self.behaviour.act_wrapper()

        if hashes_history is not None:
            self.mock_contract_api_request(
                request_kwargs=dict(
                    performative=ContractApiMessage.Performative.GET_STATE
                ),
                contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
                response_kwargs=dict(
                    performative=ContractApiMessage.Performative.STATE,
                    callable="verify_tx",
                    state=TrState(
                        ledger_id="ethereum",
                        body={"verified": verified, "transaction": {}},
                    ),
                ),
            )

            if not bool(verified):
                self.mock_contract_api_request(
                    request_kwargs=dict(
                        performative=ContractApiMessage.Performative.GET_STATE
                    ),
                    contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
                    response_kwargs=dict(
                        performative=ContractApiMessage.Performative.STATE,
                        callable="revert_reason",
                        state=TrState(
                            ledger_id="ethereum", body={"revert_reason": revert_reason}
                        ),
                    ),
                )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(TransactionSettlementEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert (
            state.state_id
            == make_degenerate_state(
                FinishedTransactionSubmissionRound.round_id
            ).state_id
        )


class TestSynchronizeLateMessagesBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test `SynchronizeLateMessagesBehaviour`"""

    def _check_state_id(self, expected: Type[TransactionSettlementBaseState]) -> None:
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == expected.state_id

    @pytest.mark.parametrize("late_message_empty", (True, False))
    def test_async_act(self, late_message_empty: bool) -> None:
        """Test `async_act`"""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=SynchronizeLateMessagesBehaviour.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        participants=participants,
                        participant_to_signature={},
                        safe_contract_address="safe_contract_address",
                    ),
                )
            ),
        )
        self._check_state_id(SynchronizeLateMessagesBehaviour)  # type: ignore

        if late_message_empty:
            cast(
                TransactionSettlementBaseState, self.behaviour.current_state
            ).params.late_messages = []
            self.behaviour.act_wrapper()
            self.mock_a2a_transaction()
            self._test_done_flag_set()
            self.end_round(TransactionSettlementEvent.DONE)
            self._check_state_id(CheckLateTxHashesBehaviour)  # type: ignore

        else:
            cast(
                TransactionSettlementBaseState, self.behaviour.current_state
            ).params.late_messages = [MagicMock(), MagicMock()]

            def _dummy_get_tx_data(
                _: ContractApiMessage,
            ) -> Generator[None, None, TxDataType]:
                yield
                return {
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test",
                    "nonce": 0,
                    "max_priority_fee_per_gas": 0,
                }

            cast(  # type: ignore
                TransactionSettlementBaseState, self.behaviour.current_state
            )._get_tx_data = _dummy_get_tx_data  # type: ignore
            self.behaviour.act_wrapper()
            self.behaviour.act_wrapper()


class TestResetBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test the reset behaviour."""

    behaviour_class = ResetBehaviour
    next_behaviour_class = RandomnessTransactionSubmissionBehaviour

    def test_reset_behaviour(
        self,
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(initial_period=0, initial_data=dict(estimate=1.0)),
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        self.behaviour.context.params.observation_interval = 0.1
        self.behaviour.act_wrapper()
        time.sleep(0.3)
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(TransactionSettlementEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
