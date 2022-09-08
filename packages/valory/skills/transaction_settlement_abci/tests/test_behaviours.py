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

# pylint: skip-file

import time
from collections import deque
from pathlib import Path
from typing import (
    Any,
    Deque,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)
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
from aea.skills.base import SkillContext

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.protocols.abci import AbciMessage  # noqa: F401
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseBehaviour,
    RPCResponseStatus,
    make_degenerate_behaviour,
)
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.abstract_round_abci.test_tools.common import (
    BaseRandomnessBehaviourTest,
    BaseSelectKeeperBehaviourTest,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    CheckLateTxHashesBehaviour,
    CheckTransactionHistoryBehaviour,
    FinalizeBehaviour,
    REVERT_CODES_TO_REASONS,
    RandomnessTransactionSubmissionBehaviour,
    ResetBehaviour,
    SelectKeeperTransactionSubmissionBehaviourA,
    SelectKeeperTransactionSubmissionBehaviourB,
    SignatureBehaviour,
    SynchronizeLateMessagesBehaviour,
    TransactionSettlementBaseBehaviour,
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
    SynchronizedData as TransactionSettlementSynchronizedSata,
)


PACKAGE_DIR = Path(__file__).parent.parent


class TransactionSettlementFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base case for testing TransactionSettlement FSMBehaviour."""

    path_to_skill = PACKAGE_DIR


class TestTransactionSettlementBaseBehaviour(FSMBehaviourBaseCase):
    """Test `TransactionSettlementBaseBehaviour`."""

    path_to_skill = PACKAGE_DIR

    @pytest.mark.parametrize(
        "message, tx_digest, rpc_status, expected_data, replacement",
        (
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.ERROR, message="GS026"
                ),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.VERIFIED,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.ERROR, message="test"
                ),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.ERROR,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_MESSAGE),
                None,
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.INCORRECT_NONCE,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.ERROR,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.INSUFFICIENT_FUNDS,
                {
                    "blacklisted_keepers": {"agent_1" + "-" * 35},
                    "keeper_retries": 1,
                    "keepers": deque(("agent_3" + "-" * 35,)),
                    "status": VerificationStatus.INSUFFICIENT_FUNDS,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.UNCLASSIFIED_ERROR,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                None,
                RPCResponseStatus.UNDERPRICED,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "",
                },
                False,
            ),
            (
                MagicMock(performative=ContractApiMessage.Performative.RAW_TRANSACTION),
                "test_digest_0",
                RPCResponseStatus.ALREADY_KNOWN,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test_digest_0",
                },
                False,
            ),
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    raw_transaction=MagicMock(
                        body={
                            "nonce": 0,
                            "maxPriorityFeePerGas": 10,
                            "maxFeePerGas": 20,
                            "gas": 0,
                        }
                    ),
                ),
                "test_digest_1",
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test_digest_1",
                },
                False,
            ),
            (
                MagicMock(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    raw_transaction=MagicMock(
                        body={
                            "nonce": 0,
                            "maxPriorityFeePerGas": 10,
                            "maxFeePerGas": 20,
                            "gas": 0,
                        }
                    ),
                ),
                "test_digest_2",
                RPCResponseStatus.SUCCESS,
                {
                    "blacklisted_keepers": set(),
                    "keeper_retries": 2,
                    "keepers": deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35)),
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test_digest_2",
                },
                True,
            ),
        ),
    )
    def test__get_tx_data(
        self,
        message: ContractApiMessage,
        tx_digest: Optional[str],
        rpc_status: RPCResponseStatus,
        expected_data: TxDataType,
        replacement: bool,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test `_get_tx_data`."""
        # fast-forward to any behaviour of the tx settlement skill
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SignatureBehaviour.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            most_voted_tx_hash="b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d90000000"
                            "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                            "0000000000000000000000002625a000x77E9b2EF921253A171Fa0CB9ba80558648Ff7215b0e6add595e00477c"
                            "f347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283"
                            "ac76e4efce2a674fe72d9",
                            keepers=int(2).to_bytes(32, "big").hex()
                            + "".join(
                                deque(("agent_1" + "-" * 35, "agent_3" + "-" * 35))
                            ),
                        )
                    ),
                )
            ),
        )
        behaviour = cast(SignatureBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == SignatureBehaviour.behaviour_id
        # Set `nonce` to the same value as the returned, so that we test the tx replacement logging.
        if replacement:
            behaviour.params.nonce = 0

        # patch the `send_raw_transaction` method
        def dummy_send_raw_transaction(
            *_: Any,
        ) -> Generator[None, None, Tuple[Optional[str], RPCResponseStatus]]:
            """Dummy `send_raw_transaction` method."""
            yield
            return tx_digest, rpc_status

        monkeypatch.setattr(
            BaseBehaviour, "send_raw_transaction", dummy_send_raw_transaction
        )
        # call `_get_tx_data`
        tx_data_iterator = cast(
            TransactionSettlementBaseBehaviour, self.behaviour.current_behaviour
        )._get_tx_data(message)

        if message.performative == ContractApiMessage.Performative.RAW_TRANSACTION:
            next(tx_data_iterator)

        try:
            next(tx_data_iterator)
        except StopIteration as res:
            assert res.value == expected_data

        """Test the serialized_keepers method."""
        behaviour_ = self.behaviour.current_behaviour
        assert behaviour_ is not None
        assert behaviour_.serialized_keepers(deque([]), 1) == ""
        assert (
            behaviour_.serialized_keepers(deque(["-" * 42]), 1)
            == "0000000000000000000000000000000000000000000000000000000000000001"
            "------------------------------------------"
        )

    @pytest.mark.parametrize(
        argnames=["tx_body", "expected_params"],
        argvalues=[
            [
                {"maxPriorityFeePerGas": "dummy", "maxFeePerGas": "dummy"},
                ["maxPriorityFeePerGas", "maxFeePerGas"],
            ],
            [{"gasPrice": "dummy"}, ["gasPrice"]],
            [
                {"maxPriorityFeePerGas": "dummy"},
                [],
            ],
            [
                {"maxFeePerGas": "dummy"},
                [],
            ],
            [
                {},
                [],
            ],
            [
                {
                    "maxPriorityFeePerGas": "dummy",
                    "maxFeePerGas": "dummy",
                    "gasPrice": "dummy",
                },
                ["maxPriorityFeePerGas", "maxFeePerGas"],
            ],
        ],
    )
    def test_get_gas_price_params(
        self, tx_body: dict, expected_params: List[str]
    ) -> None:
        """Test the get_gas_price_params method"""
        # fast-forward to any behaviour of the tx settlement skill
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SignatureBehaviour.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(dict()),
                )
            ),
        )

        assert (
            cast(
                TransactionSettlementBaseBehaviour, self.behaviour.current_behaviour
            ).get_gas_price_params(tx_body)
            == expected_params
        )

    def test_parse_revert_reason_successful(self) -> None:
        """Test `_parse_revert_reason` method."""
        # fast-forward to any behaviour of the tx settlement skill
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SignatureBehaviour.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(dict()),
                )
            ),
        )

        for code, explanation in REVERT_CODES_TO_REASONS.items():
            message = MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message=f"some text {code}.",
            )

            expected = f"Received a {code} revert error: {explanation}."

            assert (
                cast(
                    TransactionSettlementBaseBehaviour, self.behaviour.current_behaviour
                )._parse_revert_reason(message)
                == expected
            )

    @pytest.mark.parametrize(
        "message",
        (
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message="Non existing code should be invalid GS086.",
            ),
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message="Code not matching the regex should be invalid GS0265.",
            ),
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message="No code in the message should be invalid.",
            ),
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message="",  # empty message should be invalid
            ),
            MagicMock(
                performative=ContractApiMessage.Performative.ERROR,
                message=None,  # `None` message should be invalid
            ),
        ),
    )
    def test_parse_revert_reason_unsuccessful(
        self, message: ContractApiMessage
    ) -> None:
        """Test `_parse_revert_reason` method."""
        # fast-forward to any behaviour of the tx settlement skill
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SignatureBehaviour.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(dict()),
                )
            ),
        )

        expected = f"get_raw_safe_transaction unsuccessful! Received: {message}"

        assert (
            cast(
                TransactionSettlementBaseBehaviour, self.behaviour.current_behaviour
            )._parse_revert_reason(message)
            == expected
        )


class TestRandomnessInOperation(BaseRandomnessBehaviourTest):
    """Test randomness in operation."""

    path_to_skill = PACKAGE_DIR

    randomness_behaviour_class = RandomnessTransactionSubmissionBehaviour
    next_behaviour_class = SelectKeeperTransactionSubmissionBehaviourA
    done_event = TransactionSettlementEvent.DONE


class TestSelectKeeperTransactionSubmissionBehaviourA(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    path_to_skill = PACKAGE_DIR

    select_keeper_behaviour_class = SelectKeeperTransactionSubmissionBehaviourA
    next_behaviour_class = SignatureBehaviour
    done_event = TransactionSettlementEvent.DONE
    _synchronized_data = TransactionSettlementSynchronizedSata


class TestSelectKeeperTransactionSubmissionBehaviourB(
    TestSelectKeeperTransactionSubmissionBehaviourA
):
    """Test SelectKeeperBehaviour."""

    select_keeper_behaviour_class = SelectKeeperTransactionSubmissionBehaviourB
    next_behaviour_class = FinalizeBehaviour

    @mock.patch.object(
        TransactionSettlementSynchronizedSata,
        "keepers",
        new_callable=mock.PropertyMock,
    )
    @mock.patch.object(
        TransactionSettlementSynchronizedSata,
        "keeper_retries",
        new_callable=mock.PropertyMock,
    )
    @pytest.mark.parametrize(
        "keepers, keeper_retries, blacklisted_keepers",
        (
            (deque(f"keeper_{i}" for i in range(4)), 1, set()),
            (deque(("test_keeper",)), 2, set()),
            (deque(("test_keeper",)), 2, {"a1"}),
            (deque(("test_keeper",)), 2, {"test_keeper"}),
            (deque(("test_keeper",)), 2, {"a_1", "a_2", "test_keeper"}),
            (deque(("test_keeper",)), 1, set()),
            (deque(("test_keeper",)), 3, set()),
        ),
    )
    def test_select_keeper(
        self,
        keeper_retries_mock: mock.PropertyMock,
        keepers_mock: mock.PropertyMock,
        keepers: Deque[str],
        keeper_retries: int,
        blacklisted_keepers: Set[str],
    ) -> None:
        """Test select keeper agent."""
        keepers_mock.return_value = keepers
        keeper_retries_mock.return_value = keeper_retries
        super().test_select_keeper(blacklisted_keepers=blacklisted_keepers)


class TestSignatureBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test SignatureBehaviour."""

    def test_signature_behaviour(
        self,
    ) -> None:
        """Test signature behaviour."""

        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SignatureBehaviour.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=dict(
                        most_voted_tx_hash=[
                            "b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002625a000x77E9b2EF921253A171Fa0CB9ba80558648Ff7215b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"
                        ]
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == SignatureBehaviour.behaviour_id
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
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == FinalizeBehaviour.behaviour_id


class TestFinalizeBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test FinalizeBehaviour."""

    behaviour_class = FinalizeBehaviour

    def test_non_sender_act(
        self,
    ) -> None:
        """Test finalize behaviour."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        retries = 1
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.behaviour_class.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            most_voted_keeper_address="most_voted_keeper_address",
                            participants=participants,
                            # keeper needs to have length == 42 in order to be parsed
                            keepers=retries.to_bytes(32, "big").hex()
                            + "other_agent"
                            + "-" * 31,
                        )
                    ),
                )
            ),
        )
        assert self.behaviour.current_behaviour is not None
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == self.behaviour_class.behaviour_id
        )
        cast(
            FinalizeBehaviour, self.behaviour.current_behaviour
        ).params.tx_hash = "test"
        self.behaviour.act_wrapper()
        self._test_done_flag_set()
        self.end_round(TransactionSettlementEvent.DONE)
        behaviour = cast(ValidateTransactionBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == ValidateTransactionBehaviour.behaviour_id
        assert behaviour.params.tx_hash == "test"

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
    @mock.patch.object(SkillContext, "agent_address", new_callable=mock.PropertyMock)
    def test_sender_act(
        self,
        agent_address_mock: mock.PropertyMock,
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

        # keepers need to have length == 42 in order to be parsed
        agent_address_mock.return_value = "-" * 42
        retries = 1
        participants = frozenset(
            {self.skill.skill_context.agent_address, "a_1" + "-" * 39, "a_2" + "-" * 39}
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.behaviour_class.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
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
                            keepers=retries.to_bytes(32, "big").hex()
                            + self.skill.skill_context.agent_address,
                        )
                    ),
                )
            ),
        )

        assert self.behaviour.current_behaviour is not None
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == self.behaviour_class.behaviour_id
        )
        cast(
            FinalizeBehaviour, self.behaviour.current_behaviour
        ).params.tx_hash = "test"
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
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == ValidateTransactionBehaviour.behaviour_id
        )
        assert (
            cast(
                ValidateTransactionBehaviour, self.behaviour.current_behaviour
            ).params.tx_hash
            == ""
        )

    def test_handle_late_messages(self) -> None:
        """Test `handle_late_messages.`"""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.behaviour_class.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            most_voted_keeper_address="most_voted_keeper_address",
                            participants=participants,
                            keepers=deque([self.skill.skill_context.agent_address]),
                        )
                    ),
                )
            ),
        )
        self.behaviour.current_behaviour = cast(
            BaseBehaviour, self.behaviour.current_behaviour
        )
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == self.behaviour_class.behaviour_id
        )

        message = ContractApiMessage(ContractApiMessage.Performative.RAW_MESSAGE)  # type: ignore
        self.behaviour.current_behaviour.handle_late_messages(
            self.behaviour.current_behaviour.behaviour_id, message
        )
        assert cast(
            TransactionSettlementBaseBehaviour, self.behaviour.current_behaviour
        ).params.late_messages == [message]

        with mock.patch.object(self.behaviour.context.logger, "warning") as mock_info:
            self.behaviour.current_behaviour.handle_late_messages(
                "other_behaviour_id", message
            )
            mock_info.assert_called_with(
                f"No callback defined for request with nonce: {message.dialogue_reference[0]}, "
                "arriving for behaviour: other_behaviour_id"
            )
            message = MagicMock()
            self.behaviour.current_behaviour.handle_late_messages(
                self.behaviour.current_behaviour.behaviour_id, message
            )
            mock_info.assert_called_with(
                f"No callback defined for request with nonce: {message.dialogue_reference[0]}, "
                "arriving for behaviour: finalize"
            )


class TestValidateTransactionBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test ValidateTransactionBehaviour."""

    def _fast_forward(self) -> None:
        """Fast-forward to relevant behaviour."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        most_voted_keeper_address = self.skill.skill_context.agent_address
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=ValidateTransactionBehaviour.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            safe_contract_address="safe_contract_address",
                            tx_hashes_history="t" * 66,
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
                        )
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == ValidateTransactionBehaviour.behaviour_id
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
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert (
            behaviour.behaviour_id
            == make_degenerate_behaviour(
                FinishedTransactionSubmissionRound.round_id
            ).behaviour_id
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
            behaviour = cast(
                TransactionSettlementBaseBehaviour,
                self.behaviour.current_behaviour,
            )
            latest_tx_hash = behaviour.synchronized_data.tx_hashes_history[-1]
            mock_logger.assert_any_call(f"tx {latest_tx_hash} receipt check timed out!")


class TestCheckTransactionHistoryBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test CheckTransactionHistoryBehaviour."""

    def _fast_forward(self, hashes_history: str) -> None:
        """Fast-forward to relevant behaviour."""
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=CheckTransactionHistoryBehaviour.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            safe_contract_address="safe_contract_address",
                            participants=frozenset(
                                {self.skill.skill_context.agent_address, "a_1", "a_2"}
                            ),
                            participant_to_signature={},
                            most_voted_tx_hash="b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002625a000x77E9b2EF921253A171Fa0CB9ba80558648Ff7215b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9b0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9",
                            tx_hashes_history=hashes_history,
                        )
                    ),
                )
            ),
        )
        assert (
            cast(BaseBehaviour, self.behaviour.current_behaviour).behaviour_id
            == CheckTransactionHistoryBehaviour.behaviour_id
        )

    @pytest.mark.parametrize(
        "verified, status, hashes_history, revert_reason",
        (
            (False, -1, "0x" + "t" * 64, "test"),
            (False, 0, "", "test"),
            (False, 0, "0x" + "t" * 64, "test"),
            (False, 0, "0x" + "t" * 64, "GS026"),
            (True, 1, "0x" + "t" * 64, "test"),
        ),
    )
    def test_check_tx_history_behaviour(
        self,
        verified: bool,
        status: int,
        hashes_history: str,
        revert_reason: str,
    ) -> None:
        """Test CheckTransactionHistoryBehaviour."""
        self._fast_forward(hashes_history)
        self.behaviour.act_wrapper()

        if hashes_history:
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
                        body={
                            "verified": verified,
                            "status": status,
                            "transaction": {},
                        },
                    ),
                ),
            )

            if not verified and status != -1:
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
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert (
            behaviour.behaviour_id
            == make_degenerate_behaviour(
                FinishedTransactionSubmissionRound.round_id
            ).behaviour_id
        )


class TestSynchronizeLateMessagesBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test `SynchronizeLateMessagesBehaviour`"""

    def _check_behaviour_id(
        self, expected: Type[TransactionSettlementBaseBehaviour]
    ) -> None:
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == expected.behaviour_id

    @pytest.mark.parametrize("late_messages", ([], [MagicMock, MagicMock]))
    def test_async_act(self, late_messages: List[MagicMock]) -> None:
        """Test `async_act`"""
        cast(
            TransactionSettlementBaseBehaviour, self.behaviour.current_behaviour
        ).params.late_messages = late_messages

        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=SynchronizeLateMessagesBehaviour.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(
                    setup_data=dict(
                        participants=[participants],
                        participant_to_signature=[{}],
                        safe_contract_address=["safe_contract_address"],
                    ),
                )
            ),
        )
        self._check_behaviour_id(SynchronizeLateMessagesBehaviour)  # type: ignore

        if not late_messages:
            self.behaviour.act_wrapper()
            self.mock_a2a_transaction()
            self._test_done_flag_set()
            self.end_round(TransactionSettlementEvent.DONE)
            self._check_behaviour_id(CheckLateTxHashesBehaviour)  # type: ignore

        else:

            def _dummy_get_tx_data(
                _: ContractApiMessage,
            ) -> Generator[None, None, TxDataType]:
                yield
                return {
                    "status": VerificationStatus.PENDING,
                    "tx_digest": "test",
                }

            cast(  # type: ignore
                TransactionSettlementBaseBehaviour, self.behaviour.current_behaviour
            )._get_tx_data = _dummy_get_tx_data  # type: ignore
            for _ in range(len(late_messages)):
                self.behaviour.act_wrapper()


class TestResetBehaviour(TransactionSettlementFSMBehaviourBaseCase):
    """Test the reset behaviour."""

    behaviour_class = ResetBehaviour
    next_behaviour_class = RandomnessTransactionSubmissionBehaviour

    def test_reset_behaviour(
        self,
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.behaviour_class.behaviour_id,
            synchronized_data=TransactionSettlementSynchronizedSata(
                AbciAppDB(setup_data=dict(estimate=[1.0])),
            ),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.behaviour_class.behaviour_id
        )
        self.behaviour.context.params.observation_interval = 0.1
        self.behaviour.act_wrapper()
        time.sleep(0.3)
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(TransactionSettlementEvent.DONE)
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id
