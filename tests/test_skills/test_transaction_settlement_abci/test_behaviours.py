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

import datetime
import json
import logging
import time
from pathlib import Path
from typing import Generator, cast
from unittest import mock
from unittest.mock import patch

import pytest
from aea.exceptions import AEAActException
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
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseState
from packages.valory.skills.price_estimation_abci.behaviours import (
    FinalizeBehaviour,
    ObserveBehaviour,
    ResetAndPauseBehaviour,
    ResetBehaviour,
    SignatureBehaviour,
    ValidateTransactionBehaviour,
    payload_to_hex,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    RandomnessTransactionSubmissionBehaviour,
    SelectKeeperTransactionSubmissionBehaviourA,
    SelectKeeperTransactionSubmissionBehaviourB,
    TransactionSettlementBaseState,
)
from packages.valory.skills.transaction_settlement_abci.rounds import (
    Event as TransactionSettlementEvent,
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


class PriceEstimationFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "price_estimation_abci"
    )


class TestRandomnessInOperation(BaseRandomnessBehaviourTest):
    """Test randomness in operation."""

    randomness_behaviour_class = RandomnessTransactionSubmissionBehaviour
    next_behaviour_class = SelectKeeperTransactionSubmissionBehaviourA
    done_event = TransactionSettlementEvent.DONE


class TestSelectKeeperTransactionSubmissionBehaviourA(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    select_keeper_behaviour_class = SelectKeeperTransactionSubmissionBehaviourA
    next_behaviour_class = SignatureBehaviour
    done_event = TransactionSettlementEvent.DONE


class TestSelectKeeperTransactionSubmissionBehaviourB(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    select_keeper_behaviour_class = SelectKeeperTransactionSubmissionBehaviourB
    next_behaviour_class = FinalizeBehaviour
    done_event = TransactionSettlementEvent.DONE


class TestSignatureBehaviour(PriceEstimationFSMBehaviourBaseCase):
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


class TestFinalizeBehaviour(PriceEstimationFSMBehaviourBaseCase):
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

    def test_sender_act(
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
                        most_voted_keeper_address=self.skill.skill_context.agent_address,
                        safe_contract_address="safe_contract_address",
                        oracle_contract_address="oracle_contract_address",
                        participants=participants,
                        participant_to_signature={},
                        most_voted_tx_hash=payload_to_hex(
                            "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                            1,
                            1,
                            "0x77E9b2EF921253A171Fa0CB9ba80558648Ff7215",
                            "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                        ),
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
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ),
            contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_deploy_transaction",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum", body={"tx_hash": "0x3b"}
                ),
            ),
        )
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


class TestValidateTransactionBehaviour(PriceEstimationFSMBehaviourBaseCase):
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
                        oracle_contract_address="oracle_contract_address",
                        final_tx_hash="final_tx_hash",
                        participants=participants,
                        most_voted_keeper_address=most_voted_keeper_address,
                        participant_to_signature={},
                        most_voted_tx_hash=payload_to_hex(
                            "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                            1,
                            1,
                            "0x77E9b2EF921253A171Fa0CB9ba80558648Ff7215",
                            "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                        ),
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
        assert state.state_id == ResetAndPauseBehaviour.state_id

    def test_validate_transaction_safe_behaviour_no_tx_sent(
        self,
    ) -> None:
        """Test ValidateTransactionBehaviour when tx cannot be sent."""
        self._fast_forward()

        with mock.patch.object(self.behaviour.context.logger, "error") as mock_logger:

            def _mock_generator() -> Generator[None, None, None]:
                """Mock the 'get_transaction_receipt' method."""
                yield None

            with mock.patch.object(
                self.behaviour.current_state,
                "get_transaction_receipt",
                return_value=_mock_generator(),
            ):
                self.behaviour.act_wrapper()
                self.behaviour.act_wrapper()
            state = cast(
                TransactionSettlementBaseState,
                self.behaviour.current_state,
            )
            final_tx_hash = state.period_state.final_tx_hash
            mock_logger.assert_any_call(f"tx {final_tx_hash} receipt check timed out!")


class TestResetAndPauseBehaviour(PriceEstimationFSMBehaviourBaseCase):
    """Test ResetBehaviour."""

    behaviour_class = ResetAndPauseBehaviour
    next_behaviour_class = ObserveBehaviour

    def test_reset_behaviour(
        self,
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=0,
                    initial_data=dict(
                        most_voted_estimate=0.1,
                        final_tx_hash="68656c6c6f776f726c64",
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        with mock.patch(
            "packages.valory.skills.abstract_round_abci.base.AbciApp.last_timestamp",
            new_callable=mock.PropertyMock,
        ) as pmock:
            pmock.return_value = datetime.datetime.now()
            self.behaviour.context.params.observation_interval = 0.1
            self.behaviour.act_wrapper()
            time.sleep(0.3)
            self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(TransactionSettlementEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id

    def _tendermint_reset(
        self, reset_response: bytes, status_response: bytes
    ) -> Generator:
        """Test reset behaviour."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=2,
                    initial_data=dict(
                        most_voted_estimate=0.1,
                        final_tx_hash="68656c6c6f776f726c64",
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        with mock.patch(
            "packages.valory.skills.abstract_round_abci.base.AbciApp.last_timestamp",
            new_callable=mock.PropertyMock,
        ) as pmock:
            pmock.return_value = datetime.datetime.now()
            self.behaviour.context.params.observation_interval = 0.1
            self.behaviour.act_wrapper()
            time.sleep(0.3)
            self.behaviour.act_wrapper()
            self.behaviour.act_wrapper()
            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_com_url
                    + "/hard_reset",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="",
                    status_code=500,
                    status_text="",
                    headers="",
                    body=reset_response,
                ),
            )
            yield

            self.mock_http_request(
                request_kwargs=dict(
                    method="GET",
                    url=self.skill.skill_context.params.tendermint_url + "/status",
                    headers="",
                    version="",
                    body=b"",
                ),
                response_kwargs=dict(
                    version="",
                    status_code=200,
                    status_text="",
                    headers="",
                    body=status_response,
                ),
            )
            yield

            time.sleep(0.3)
            self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(TransactionSettlementEvent.DONE)
        state = cast(BaseState, self.behaviour.current_state)
        assert state.state_id == self.next_behaviour_class.state_id
        yield

    def test_reset_behaviour_with_tendermint_reset(
        self,
    ) -> None:
        """Test reset behaviour."""
        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                json.dumps(
                    {"message": "Tendermint reset was successful.", "status": True}
                ).encode(),
                json.dumps(
                    {
                        "result": {
                            "sync_info": {
                                "latest_block_height": self.behaviour.context.state.period.height
                            }
                        }
                    }
                ).encode(),
            )
            for _ in range(3):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.INFO,
                "Tendermint reset was successful.",
            )

    def test_reset_behaviour_with_tendermint_reset_error_message(
        self,
    ) -> None:
        """Test reset behaviour with error message."""
        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                json.dumps(
                    {"message": "Error resetting tendermint.", "status": False}
                ).encode(),
                json.dumps(
                    {
                        "result": {
                            "sync_info": {
                                "latest_block_height": self.behaviour.context.state.period.height
                            }
                        }
                    }
                ).encode(),
            )
            for _ in range(1):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.ERROR,
                "Error resetting: Error resetting tendermint.",
            )

    def test_reset_behaviour_with_tendermint_reset_wrong_response(
        self,
    ) -> None:
        """Test reset behaviour with wrong response."""
        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                b"",
                b"",
            )
            for _ in range(1):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.ERROR,
                "Error communicating with tendermint com server.",
            )

    def test_timeout_expired(
        self,
    ) -> None:
        """Test reset behaviour with wrong response."""
        self.fast_forward_to_state(
            behaviour=self.behaviour,
            state_id=self.behaviour_class.state_id,
            period_state=TransactionSettlementPeriodState(
                StateDB(
                    initial_period=2,
                    initial_data=dict(
                        most_voted_estimate=0.1,
                        final_tx_hash="68656c6c6f776f726c64",
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.behaviour.current_state),
            ).state_id
            == self.behaviour_class.state_id
        )
        with mock.patch.object(
            self.behaviour.current_state,
            "_is_timeout_expired",
            return_value=True,
        ):
            with pytest.raises(AEAActException):
                self.behaviour.act_wrapper()

    def test_reset_behaviour_with_tendermint_transaction_error(
        self,
    ) -> None:
        """Test reset behaviour with error message."""
        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                json.dumps({"message": "Reset Successful.", "status": True}).encode(),
                b"",
            )
            for _ in range(2):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.ERROR,
                "Tendermint not accepting transactions yet, trying again!",
            )

    def test_reset_behaviour_with_block_height_dont_match(
        self,
    ) -> None:
        """Test reset behaviour with error message."""
        with patch.object(self.behaviour.context.logger, "log") as mock_logger:
            test_runner = self._tendermint_reset(
                json.dumps({"message": "Reset Successful.", "status": True}).encode(),
                json.dumps(
                    {"result": {"sync_info": {"latest_block_height": -1}}}
                ).encode(),
            )
            for _ in range(2):
                next(test_runner)
            mock_logger.assert_any_call(
                logging.INFO,
                "local height != remote height; retrying...",
            )


class TestResetBehaviour(PriceEstimationFSMBehaviourBaseCase):
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
