# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""This package contains round behaviours of Background Behaviours."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
from unittest import mock

import pytest
from _pytest.logging import LogCaptureFixture

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.multisend.contract import MultiSendContract
from packages.valory.contracts.service_registry.contract import ServiceRegistryContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.contract_api.custom_types import RawTransaction, State
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import AsyncBehaviour
from packages.valory.skills.abstract_round_abci.behaviours import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.termination_abci import PUBLIC_ID
from packages.valory.skills.termination_abci.behaviours import (
    BackgroundBehaviour,
    TerminationAbciBehaviours,
    TerminationBehaviour,
)
from packages.valory.skills.termination_abci.rounds import Event, SynchronizedData
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)


SERVICE_REGISTRY_ADDRESS = "0x48b6af7B12C71f09e2fC8aF4855De4Ff54e775cA"
SAFE_ADDRESS = "0x0"
MULTISEND_ADDRESS = "0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761"
SERVICE_OWNER_ADDRESS = "0x0"
SERVICE_ID = None


def test_skill_public_id() -> None:
    """Test skill module public ID"""

    # pylint: disable=no-member
    assert PUBLIC_ID.name == Path(__file__).parents[1].name
    assert PUBLIC_ID.author == Path(__file__).parents[3].name


@dataclass
class BehaviourTestCase:
    """BehaviourTestCase"""

    name: str
    initial_data: Dict[str, Any]
    ok_reqs: List[Callable]
    err_reqs: List[Callable]
    expected_logs: List[str]


class BaseTerminationTest(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(__file__).parents[1]

    behaviour: TerminationAbciBehaviours
    behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[
        BaseBehaviour
    ] = TransactionSettlementRoundBehaviour.initial_behaviour_cls
    synchronized_data: SynchronizedData
    done_event = Event.TERMINATE

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Fast-forward on initialization"""

        data = data if data is not None else {}
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

    def complete(self) -> None:
        """Complete test"""
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self.end_round(done_event=self.done_event)
        assert (
            self.behaviour.current_behaviour is not None
            and self.behaviour.current_behaviour.behaviour_id
            == self.next_behaviour_class.auto_behaviour_id()
        )


class TestBackgroundBehaviour(BaseTerminationTest):
    """Test the background behaviour."""

    behaviour_class = BackgroundBehaviour
    next_behaviour_class = TransactionSettlementRoundBehaviour.initial_behaviour_cls

    # when the service owner ordered termination
    _ZERO_TRANSFER_EVENTS = [
        {"block_number": 1},
        {"block_number": 10},
        {"block_number": 20},
    ]
    _NUM_ZERO_TRANSFER_EVENTS = len(_ZERO_TRANSFER_EVENTS)
    # when the service owner got removed from being a safe owner
    # this happens when the operators take over the safe again
    _SERVICE_OWNER_REMOVED_EVENTS = [
        {"block_number": 2},
        {"block_number": 11},
    ]
    _NUM_SERVICE_OWNER_REMOVED_EVENTS = len(_SERVICE_OWNER_REMOVED_EVENTS)
    _SAFE_OWNERS = ["0x1", "0x2", "0x3", "0x4"]
    _NUM_SAFE_OWNERS = len(_SAFE_OWNERS)
    _SAFE_THRESHOLD = 1
    _MOCK_TX_RESPONSE = b"0xIrrelevantForTests".hex()
    _MOCK_TX_HASH = "0x" + "0" * 64
    _INITIAL_DATA: Dict[str, Any] = dict(
        safe_contract_address=SAFE_ADDRESS, participants=_SAFE_OWNERS
    )

    _STATE_ERR_LOG = (
        f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
        f"received {ContractApiMessage.Performative.ERROR}."
    )
    _RAW_TRANSACTION_ERR = (
        f"Expected response performative {ContractApiMessage.Performative.RAW_TRANSACTION.value}, "  # type: ignore
        f"received {ContractApiMessage.Performative.ERROR}."
    )
    _SERVICE_OWNER_ERR_LOG = (
        f"Couldn't get the service owner for service with id={SERVICE_ID}. "
        f"{_STATE_ERR_LOG}"
    )
    _ZERO_TRANSFER_EVENTS_ERR_LOG = (
        f"Couldn't get the latest Zero Transfer (`SafeReceived`) event. "
        f"{_STATE_ERR_LOG}"
    )
    _SERVICE_OWNER_REMOVED_EVENTS_ERR_LOG = (
        f"Couldn't get the latest `RemovedOwner` event. " f"{_STATE_ERR_LOG}"
    )
    _SAFE_OWNERS_ERR_LOG = (
        f"Couldn't get the safe owners for safe deployed at {SAFE_ADDRESS}. "
        f"{_STATE_ERR_LOG}"
    )
    _REMOVE_OWNER_ERR_LOG = f"Couldn't get a remove owner tx. " f"{_STATE_ERR_LOG}"
    _SWAP_OWNER_ERR_LOG = f"Couldn't get a swap owner tx. " f"{_STATE_ERR_LOG}"
    _SAFE_HASH_ERR_LOG = f"Couldn't get safe hash. " f"{_STATE_ERR_LOG}"
    _MULTISEND_ERR_LOG = "Couldn't compile the multisend tx. "
    _SUCCESS_LOG = "Successfully prepared termination multisend tx."
    _IS_STOPPED_LOG = "dropping message as behaviour has stopped:"
    _IS_NOT_WAITING_MESSAGE = "could not send message"

    def _mock_get_service_owner_request(
        self,
        error: bool = False,
    ) -> None:
        """Mock a ServiceRegistryContract.get_service_owner() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.STATE
            response_body = dict(service_owner=SERVICE_OWNER_ADDRESS)
        else:
            response_body = dict()
            response_performative = ContractApiMessage.Performative.ERROR

        self.mock_contract_api_request(
            contract_id=str(ServiceRegistryContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=SERVICE_REGISTRY_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                state=State(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_zero_transfer_events_request(
        self,
        error: bool = False,
        num_events: int = _NUM_ZERO_TRANSFER_EVENTS,
    ) -> None:
        """Mock a GnosisSafeContract.get_zero_transfer_events() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.STATE
            response_body = dict(data=self._ZERO_TRANSFER_EVENTS[:num_events])
        else:
            response_body = dict()
            response_performative = ContractApiMessage.Performative.ERROR
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=SAFE_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                state=State(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_removed_owner_events_request(
        self,
        error: bool = False,
        num_events: int = _NUM_SERVICE_OWNER_REMOVED_EVENTS,
    ) -> None:
        """Mock a GnosisSafeContract.get_removed_owner_events() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.STATE
            response_body = dict(data=self._SERVICE_OWNER_REMOVED_EVENTS[:num_events])
        else:
            response_body = dict()
            response_performative = ContractApiMessage.Performative.ERROR

        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=SAFE_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                state=State(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_owners_request(
        self,
        error: bool = False,
    ) -> None:
        """Mock a GnosisSafeContract.get_owners() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.STATE
            response_body = dict(owners=self._SAFE_OWNERS)
        else:
            response_body = dict()
            response_performative = ContractApiMessage.Performative.ERROR
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=SAFE_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                state=State(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_remove_owner_data_request(self, error: bool = False) -> None:
        """Mock a GnosisSafeContract.get_remove_owner_data() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.STATE
            response_body = dict(data=self._MOCK_TX_RESPONSE)
        else:
            response_body = dict()
            response_performative = ContractApiMessage.Performative.ERROR
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=SAFE_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                state=State(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_swap_owner_data_request(
        self,
        error: bool = False,
    ) -> None:
        """Mock a GnosisSafeContract.get_swap_owner_data() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.STATE
            response_body = dict(data=self._MOCK_TX_RESPONSE)
        else:
            response_body = dict()
            response_performative = ContractApiMessage.Performative.ERROR
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=SAFE_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                state=State(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_raw_safe_transaction_hash_request(
        self,
        error: bool = False,
    ) -> None:
        """Mock a GnosisSafeContract.get_raw_safe_transaction_hash() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.STATE
            response_body = dict(tx_hash=self._MOCK_TX_HASH)
        else:
            response_body = dict()
            response_performative = ContractApiMessage.Performative.ERROR
        self.mock_contract_api_request(
            contract_id=str(GnosisSafeContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=SAFE_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                state=State(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_get_tx_data_request(
        self,
        error: bool = False,
    ) -> None:
        """Mock a MultiSendContract.get_tx_data() request."""
        if not error:
            response_performative = ContractApiMessage.Performative.RAW_TRANSACTION
            response_body = dict(data=self._MOCK_TX_RESPONSE)
        else:
            response_body = dict()
            response_performative = ContractApiMessage.Performative.ERROR
        self.mock_contract_api_request(
            contract_id=str(MultiSendContract.contract_id),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=MULTISEND_ADDRESS,
            ),
            response_kwargs=dict(
                performative=response_performative,
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body=response_body,
                ),
            ),
        )

    def _mock_is_stopped(  # pylint: disable=unused-argument, disable=protected-access
        self,
        error: bool = False,
    ) -> None:
        """Mock a MultiSendContract.get_tx_data() request."""
        assert self.behaviour.current_behaviour is not None
        self.behaviour.current_behaviour._AsyncBehaviour__stopped = True

    def _mock_state_is_not_waiting_message(  # pylint: disable=unused-argument, disable=protected-access
        self,
        error: bool = False,
    ) -> None:
        """Mock a MultiSendContract.get_tx_data() request."""
        assert self.behaviour.current_behaviour is not None
        self.behaviour.current_behaviour._AsyncBehaviour__state = (
            AsyncBehaviour.AsyncState.RUNNING
        )

    @pytest.mark.parametrize(
        "test_case",
        [
            BehaviourTestCase(
                name="agent fails to get the service owner",
                initial_data=_INITIAL_DATA,
                ok_reqs=[],
                err_reqs=[_mock_get_service_owner_request],
                expected_logs=[_SERVICE_OWNER_ERR_LOG],
            ),
            BehaviourTestCase(
                name="agent fails to get zero transfer event",
                initial_data=_INITIAL_DATA,
                ok_reqs=[_mock_get_service_owner_request],
                err_reqs=[_mock_get_zero_transfer_events_request],
                expected_logs=[_ZERO_TRANSFER_EVENTS_ERR_LOG],
            ),
            BehaviourTestCase(
                name="agent fails to get owner removal event",
                initial_data=_INITIAL_DATA,
                ok_reqs=[
                    _mock_get_service_owner_request,
                    _mock_get_zero_transfer_events_request,
                ],
                err_reqs=[_mock_get_removed_owner_events_request],
                expected_logs=[_SERVICE_OWNER_REMOVED_EVENTS_ERR_LOG],
            ),
            BehaviourTestCase(
                name="agent fails to get the safe owners",
                initial_data=_INITIAL_DATA,
                ok_reqs=[
                    _mock_get_service_owner_request,
                    _mock_get_zero_transfer_events_request,
                    _mock_get_removed_owner_events_request,
                ],
                err_reqs=[_mock_get_owners_request],
                expected_logs=[_SAFE_OWNERS_ERR_LOG],
            ),
            BehaviourTestCase(
                name="agent fails to get a remove safe owner tx",
                initial_data=_INITIAL_DATA,
                ok_reqs=[
                    _mock_get_service_owner_request,
                    _mock_get_zero_transfer_events_request,
                    _mock_get_removed_owner_events_request,
                    _mock_get_owners_request,
                ],
                err_reqs=[_mock_get_remove_owner_data_request],
                expected_logs=[_REMOVE_OWNER_ERR_LOG],
            ),
            BehaviourTestCase(
                name="agent fails to get a swap safe owner tx",
                initial_data=_INITIAL_DATA,
                ok_reqs=[
                    _mock_get_service_owner_request,
                    _mock_get_zero_transfer_events_request,
                    _mock_get_removed_owner_events_request,
                    _mock_get_owners_request,
                    *[_mock_get_remove_owner_data_request] * (_NUM_SAFE_OWNERS - 1),
                ],
                err_reqs=[_mock_get_swap_owner_data_request],
                expected_logs=[_SWAP_OWNER_ERR_LOG],
            ),
            BehaviourTestCase(
                name="agent fails to prepare multisend tx",
                initial_data=_INITIAL_DATA,
                ok_reqs=[
                    _mock_get_service_owner_request,
                    _mock_get_zero_transfer_events_request,
                    _mock_get_removed_owner_events_request,
                    _mock_get_owners_request,
                    *[_mock_get_remove_owner_data_request] * (_NUM_SAFE_OWNERS - 1),
                    _mock_get_swap_owner_data_request,
                ],
                err_reqs=[_mock_get_tx_data_request],
                expected_logs=[_MULTISEND_ERR_LOG],
            ),
            BehaviourTestCase(
                name="agent fails to get a hash for the multisend tx",
                initial_data=_INITIAL_DATA,
                ok_reqs=[
                    _mock_get_service_owner_request,
                    _mock_get_zero_transfer_events_request,
                    _mock_get_removed_owner_events_request,
                    _mock_get_owners_request,
                    *[_mock_get_remove_owner_data_request] * (_NUM_SAFE_OWNERS - 1),
                    _mock_get_swap_owner_data_request,
                    _mock_get_tx_data_request,
                ],
                err_reqs=[_mock_get_raw_safe_transaction_hash_request],
                expected_logs=[_SAFE_HASH_ERR_LOG],
            ),
            BehaviourTestCase(
                name="agent completes the whole flow",
                initial_data=_INITIAL_DATA,
                ok_reqs=[
                    _mock_get_service_owner_request,
                    _mock_get_zero_transfer_events_request,
                    _mock_get_removed_owner_events_request,
                    _mock_get_owners_request,
                    *[_mock_get_remove_owner_data_request] * (_NUM_SAFE_OWNERS - 1),
                    _mock_get_swap_owner_data_request,
                    _mock_get_tx_data_request,
                    _mock_get_raw_safe_transaction_hash_request,
                ],
                err_reqs=[],
                expected_logs=[_SUCCESS_LOG],
            ),
            BehaviourTestCase(
                name="agent drops message because app already stopped",
                initial_data=_INITIAL_DATA,
                ok_reqs=[],
                err_reqs=[
                    _mock_is_stopped,
                    _mock_get_service_owner_request,
                ],
                expected_logs=[_IS_STOPPED_LOG],
            ),
            BehaviourTestCase(
                name="agent could not send message because state != WAITING_MESSAGE",
                initial_data=_INITIAL_DATA,
                ok_reqs=[],
                err_reqs=[
                    _mock_state_is_not_waiting_message,
                    _mock_get_service_owner_request,
                ],
                expected_logs=[_IS_NOT_WAITING_MESSAGE],
            ),
        ],
    )
    @pytest.mark.skip  # Needs to be investigated, fails in CI only. look at #1710
    def test_run(self, test_case: BehaviourTestCase, caplog: LogCaptureFixture) -> None:
        """Test multiple paths of termination."""
        self.fast_forward(data=test_case.initial_data)
        self.behaviour.act_wrapper()

        # apply the OK mocks first
        for ok_req in test_case.ok_reqs:
            ok_req(self)

        # apply the failing mocks
        for err_req in test_case.err_reqs:
            err_req(self, error=True)

        # check that the expected logs appear
        for expected_log in test_case.expected_logs:
            assert expected_log in caplog.text

        if len(test_case.err_reqs) == 0:
            # no mocked requests fail,
            # the behaviour should complete
            self.complete()

    def test_termination_majority_already_reached(self) -> None:
        """Tests the background behaviour when the termination is already reached."""
        self.fast_forward(
            data=dict(termination_majority_reached=True, participants=["a"])
        )
        with mock.patch.object(
            self.behaviour_class, "check_for_signal"
        ) as check_for_signal:
            self.behaviour.act_wrapper()
            check_for_signal.assert_not_called()

    def test_no_termination_signal_is_present(self) -> None:
        """Tests the background behaviour when no termination signal is present."""
        self.fast_forward(self._INITIAL_DATA)
        with mock.patch.object(AsyncBehaviour, "sleep") as sleep:
            self.behaviour.act_wrapper()
            self._mock_get_service_owner_request()
            self._mock_get_zero_transfer_events_request(num_events=0)
            sleep.assert_called()

    def test_no_remove_owner_event_is_present(self) -> None:
        """Tests the background behaviour when the safe owner hasn't been removed."""
        self.fast_forward(self._INITIAL_DATA)
        self.behaviour.act_wrapper()
        self._mock_get_service_owner_request()
        self._mock_get_zero_transfer_events_request()
        self._mock_get_removed_owner_events_request(num_events=0)
        self._mock_get_owners_request()
        for _ in range(self._NUM_SAFE_OWNERS - 1):
            self._mock_get_remove_owner_data_request()
        self._mock_get_swap_owner_data_request()
        self._mock_get_tx_data_request()
        self._mock_get_raw_safe_transaction_hash_request()
        self.complete()


class TestTerminationBehaviour(BaseTerminationTest):
    """Test termination behaviour."""

    behaviour_class = TerminationBehaviour

    def test_run(self) -> None:
        """Test that the Termination Behaviour exits the app."""
        self.fast_forward()
        with mock.patch("sys.exit") as sys_exit:
            self.behaviour.act_wrapper()
            sys_exit.assert_called()
