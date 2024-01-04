# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Tests the behaviours of the slashing."""

# pylint: disable=protected-access

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, cast
from unittest import mock
from unittest.mock import MagicMock

import pytest

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.contract_api.custom_types import RawTransaction
from packages.valory.skills.abstract_round_abci.base import AbciAppDB, OffenceStatus
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    AsyncBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.abstract_round_abci.utils import inverse
from packages.valory.skills.slashing_abci.behaviours import (
    SlashingAbciBehaviours,
    SlashingCheckBehaviour,
    StatusResetBehaviour,
)
from packages.valory.skills.slashing_abci.rounds import Event, SynchronizedData
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.rounds import TX_HASH_LENGTH


STUB_OPERATORS_MAPPING = {
    "test_instance_1": "test_operator",
    "test_instance_0": "test_operator",
}
DUMMY_SLASH_THRESHOLD = 1
DUMMY_SLASH_COOLDOWN = 1


class BaseSlashingTest(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(__file__).parents[1]
    behaviour: SlashingAbciBehaviours
    behaviour_class: Type[BaseBehaviour] = SlashingCheckBehaviour
    next_behaviour_class: Type[
        BaseBehaviour
    ] = TransactionSettlementRoundBehaviour.initial_behaviour_cls
    synchronized_data: SynchronizedData
    done_event = Event.SLASH_START

    @property
    def current_behaviour(
        self,
    ) -> Union[BaseBehaviour, SlashingCheckBehaviour, StatusResetBehaviour]:
        """Get the current behaviour."""
        return cast(
            Union[BaseBehaviour, SlashingCheckBehaviour, StatusResetBehaviour],
            self.behaviour.current_behaviour,
        )

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Fast-forward on initialization"""

        data = data or {}
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.auto_behaviour_id(),
            SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert (
            self.behaviour.current_behaviour is not None
            and self.behaviour.current_behaviour.behaviour_id
            == self.behaviour_class.auto_behaviour_id()
        )
        self.current_behaviour.params.__dict__["_frozen"] = False
        self.current_behaviour.params.slash_threshold_amount = DUMMY_SLASH_THRESHOLD
        self.current_behaviour.params.slash_cooldown_hours = DUMMY_SLASH_COOLDOWN
        self.current_behaviour.params.__dict__["_frozen"] = True

    def complete(self) -> None:
        """Complete test"""
        self.mock_a2a_transaction()
        self.end_round(done_event=self.done_event)
        assert (
            self.behaviour.current_behaviour is not None
            and self.behaviour.current_behaviour.behaviour_id
            == self.next_behaviour_class.auto_behaviour_id()
        )


class TestSlashingCheckBehaviour(BaseSlashingTest):
    """Tests for `SlashingCheckBehaviour`."""

    behaviour_class = SlashingCheckBehaviour

    def _mock_get_slash_data(
        self, error: bool = False, invalid_data: bool = False
    ) -> None:
        """Mock a ServiceRegistryContract.get_slash_data() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.RAW_TRANSACTION
            response_body = {} if invalid_data else {"data": b"slash_data"}
        else:
            response_performative = ContractApiMessage.Performative.ERROR
            response_body = {}

        self.mock_contract_api_request(
            contract_id=str(ServiceRegistryContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                contract_address=self.current_behaviour.params.service_registry_address,
            ),
            response_kwargs=dict(
                performative=response_performative,
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_safe_tx_hash(
        self,
        error: bool = False,
        invalid_hash: bool = False,
    ) -> None:
        """Mock a GnosisSafeContract.get_raw_safe_transaction_hash() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.RAW_TRANSACTION
            response_body = (
                {"tx_hash": "0x"}
                if invalid_hash
                else {"tx_hash": "0x" + "0" * (TX_HASH_LENGTH - 2)}
            )
        else:
            response_performative = ContractApiMessage.Performative.ERROR
            response_body = {}

        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                contract_address=self.current_behaviour.synchronized_data.safe_contract_address,
            ),
            response_kwargs=dict(
                performative=response_performative,
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    @mock.patch.object(AsyncBehaviour, "try_send")
    def test_get_callback_request(self, try_send_mock: mock.Mock) -> None:
        """Test `get_callback_request` method."""
        self.fast_forward(
            data=dict(
                slashing_in_flight=False,
                all_participants=["a"],
                participants=["a"],
                consensus_threshold=1,
            )
        )
        self.current_behaviour.round_sequence._offence_status = {"a": OffenceStatus()}
        self.current_behaviour.round_sequence._last_round_transition_timestamp = (
            datetime(2000, 1, 1)
        )

        # `__stopped` is `True` in the beginning
        callback = self.current_behaviour.get_callback_request()
        message_mock = MagicMock()
        callback(message_mock, MagicMock())
        try_send_mock.assert_not_called()

        # call act wrapper so that `__call_act_first_time()` is triggered, which sets `self.__stopped = False`
        # however, state is not `AsyncState.WAITING_MESSAGE`
        self.behaviour.act_wrapper()
        callback(message_mock, MagicMock())
        try_send_mock.assert_not_called()

        # call `wait_for_message()` which sets `self.__state = self.AsyncState.WAITING_MESSAGE`
        wait_gen = self.current_behaviour.wait_for_message()
        next(wait_gen)
        callback(message_mock, MagicMock())
        try_send_mock.assert_called_once_with(message_mock)

    @pytest.mark.parametrize(
        "offence_status, timestamps, last_timestamp, expected_amounts",
        (
            (
                {"agent": MagicMock(slash_amount=MagicMock(return_value=0))},
                {"agent": 0},
                datetime(2000, 1, 1),
                {},
            ),
            (
                {
                    "agent": MagicMock(
                        slash_amount=MagicMock(return_value=DUMMY_SLASH_THRESHOLD)
                    )
                },
                {"agent": 946684800 - DUMMY_SLASH_COOLDOWN},
                datetime(2000, 1, 1),
                {},
            ),
            (
                {
                    "agent": MagicMock(
                        slash_amount=MagicMock(return_value=DUMMY_SLASH_THRESHOLD + 1)
                    )
                },
                {"agent": 946684800},
                datetime(2000, 1, 1),
                {},
            ),
            (
                {
                    "agent": MagicMock(
                        slash_amount=MagicMock(return_value=DUMMY_SLASH_THRESHOLD + 1)
                    )
                },
                {"agent": 946684800 - DUMMY_SLASH_COOLDOWN - 1},
                datetime(2000, 1, 1),
                {"agent": DUMMY_SLASH_THRESHOLD + 1},
            ),
        ),
    )
    def test_check_offence_status(
        self,
        offence_status: Dict[str, MagicMock],
        timestamps: Dict[str, int],
        last_timestamp: datetime,
        expected_amounts: Dict[str, int],
    ) -> None:
        """Test the `_check_offence_status` method."""
        self.fast_forward(data={"slash_timestamps": json.dumps(timestamps)})
        # repeating this check for the `current_behaviour` here to avoid `mypy` reporting:
        # `error: Item "None" of "Optional[BaseBehaviour]" has no attribute "context"` when accessing the context below
        assert self.current_behaviour is not None

        self.current_behaviour._slash_amounts = {"agent": "something_random"}
        self.current_behaviour.round_sequence._offence_status = offence_status  # type: ignore
        self.current_behaviour.round_sequence._last_round_transition_timestamp = (
            last_timestamp
        )

        self.current_behaviour._check_offence_status()
        assert self.current_behaviour._slash_amounts == expected_amounts

    @dataclass
    class SlashingCheckBehaviourTestCase:
        """Test case parametrization for the `SlashingCheckBehaviour`."""

        slashing_in_flight: bool = False
        consensus_threshold: int = 1
        num_double_signed: int = 1
        slash_data_error: bool = False
        slash_data_invalid: bool = False
        safe_tx_error: bool = False
        safe_tx_invalid: bool = False

        @property
        def all_participants(self) -> List[str]:
            """Generate a stub list with participants."""
            return [f"participant{i}" for i in range(self.consensus_threshold)]

    @pytest.mark.parametrize(
        "test_case",
        (
            SlashingCheckBehaviourTestCase(slashing_in_flight=True),
            SlashingCheckBehaviourTestCase(consensus_threshold=2),
            SlashingCheckBehaviourTestCase(num_double_signed=0),
            SlashingCheckBehaviourTestCase(slash_data_error=True),
            SlashingCheckBehaviourTestCase(slash_data_invalid=True),
            SlashingCheckBehaviourTestCase(safe_tx_error=True),
            SlashingCheckBehaviourTestCase(safe_tx_invalid=True),
            SlashingCheckBehaviourTestCase(),
        ),
    )
    @mock.patch.object(AsyncBehaviour, "sleep")
    def test_slashing_check_act(
        self, sleep_mock: mock.Mock, test_case: SlashingCheckBehaviourTestCase
    ) -> None:
        """Test `PendingOffencesBehaviour`'s async act."""
        first_participant = test_case.all_participants[0]
        self.fast_forward(
            data=dict(
                slashing_in_flight=test_case.slashing_in_flight,
                all_participants=test_case.all_participants,
                participants=[first_participant],
                consensus_threshold=test_case.consensus_threshold,
                safe_contract_address="test_safe_contract_address",
            )
        )
        self.current_behaviour.round_sequence._offence_status = {
            first_participant: OffenceStatus()
        }
        self.current_behaviour.round_sequence._offence_status[
            first_participant
        ].num_double_signed += test_case.num_double_signed
        self.current_behaviour.round_sequence._last_round_transition_timestamp = (
            datetime(2000, 1, 1)
        )
        self.behaviour.act_wrapper()
        if test_case.slashing_in_flight or test_case.consensus_threshold == 2:
            with pytest.raises(AssertionError):
                self._mock_get_slash_data(
                    test_case.slash_data_error, test_case.slash_data_invalid
                )
            return

        if test_case.num_double_signed == 0:
            with pytest.raises(AssertionError):
                self._mock_get_slash_data(
                    test_case.slash_data_error, test_case.slash_data_invalid
                )
            sleep_mock.assert_called_once_with(self.current_behaviour.params.sleep_time)
            return

        self._mock_get_slash_data(
            test_case.slash_data_error, test_case.slash_data_invalid
        )

        if test_case.slash_data_error or test_case.slash_data_invalid:
            with pytest.raises(AssertionError):
                self._mock_get_safe_tx_hash(
                    test_case.safe_tx_error, test_case.safe_tx_invalid
                )
            return

        self._mock_get_safe_tx_hash(test_case.safe_tx_error, test_case.safe_tx_invalid)

        if test_case.safe_tx_error or test_case.safe_tx_invalid:
            with pytest.raises(AssertionError):
                self.complete()
            return

        self.complete()
        sleep_mock.assert_not_called()


class TestStatusResetBehaviour(BaseSlashingTest):
    """Tests for `StatusResetBehaviour`."""

    behaviour_class = StatusResetBehaviour
    next_behaviour_class = StatusResetBehaviour
    done_event = Event.SLASH_END

    def _mock_process_slash_receipt(
        self,
        error: bool = False,
    ) -> None:
        """Mock a ServiceRegistryContract.process_slash_receipt() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.RAW_TRANSACTION
            response_body = {
                "slash_timestamp": 10,
                "events": [{"amount": 2, "operator": "test_operator", "serviceId": 1}],
            }
        else:
            response_performative = ContractApiMessage.Performative.ERROR
            response_body = {}

        self.mock_contract_api_request(
            contract_id=str(ServiceRegistryContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                contract_address=self.current_behaviour.params.service_registry_address,
            ),
            response_kwargs=dict(
                performative=response_performative,
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_instances_mapping(
        self,
        error: bool = False,
    ) -> None:
        """Mock a ServiceRegistryContract.get_operators_mapping() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.RAW_TRANSACTION
            response_body = STUB_OPERATORS_MAPPING
        else:
            response_performative = ContractApiMessage.Performative.ERROR
            response_body = {}

        self.mock_contract_api_request(
            contract_id=str(ServiceRegistryContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                contract_address=self.current_behaviour.params.service_registry_address,
            ),
            response_kwargs=dict(
                performative=response_performative,
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    @dataclass
    class StatusResetBehaviourTestCase:
        """Test case parametrization for the `StatusResetBehaviour`."""

        operators_mapping: Optional[str] = None
        get_mapping_error: bool = False
        process_receipt_error: bool = False

    @pytest.mark.parametrize(
        "test_case",
        (
            StatusResetBehaviourTestCase(get_mapping_error=True),
            StatusResetBehaviourTestCase(process_receipt_error=True),
            StatusResetBehaviourTestCase(
                operators_mapping=json.dumps(
                    inverse(dict(sorted(STUB_OPERATORS_MAPPING.items())))
                )
            ),
            StatusResetBehaviourTestCase(),
        ),
    )
    @mock.patch.object(AsyncBehaviour, "sleep")
    def test_status_reset_act(
        self, sleep_mock: mock.Mock, test_case: StatusResetBehaviourTestCase
    ) -> None:
        """Test `PendingOffencesBehaviour`'s async act."""
        self.fast_forward(
            data=dict(
                final_tx_hash="final_tx_hash",
                all_participants=["a"],
                participants=["a"],
                consensus_threshold=1,
                operators_mapping=test_case.operators_mapping,
            )
        )
        # initialize the offence status with a fake offence
        first_instance = list(STUB_OPERATORS_MAPPING.keys())[0]
        initial_offence_status = {
            instance: OffenceStatus() for instance in STUB_OPERATORS_MAPPING
        }
        offence_status = deepcopy(initial_offence_status)
        offence_status[first_instance].num_double_signed = 1
        self.current_behaviour.round_sequence._offence_status = deepcopy(offence_status)
        self.behaviour.act_wrapper()

        if test_case.operators_mapping is None and test_case.get_mapping_error:
            self._mock_get_instances_mapping(test_case.get_mapping_error)
            sleep_mock.assert_called_once_with(self.current_behaviour.params.sleep_time)
            with pytest.raises(AssertionError):
                self._mock_process_slash_receipt(test_case.process_receipt_error)
            return

        if test_case.operators_mapping is None:
            self._mock_get_instances_mapping(test_case.get_mapping_error)

        assert self.current_behaviour.offence_status == offence_status
        self._mock_process_slash_receipt(test_case.process_receipt_error)

        if test_case.process_receipt_error:
            sleep_mock.assert_called_once_with(self.current_behaviour.params.sleep_time)
            with pytest.raises(AssertionError):
                self.complete()
            return

        assert self.current_behaviour.offence_status == initial_offence_status
        # check the order for determinism
        assert list(self.current_behaviour.offence_status.keys()) == sorted(
            initial_offence_status.keys()
        )
        self.complete()
        sleep_mock.assert_not_called()
