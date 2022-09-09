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

"""Tests for valory/simple_abci skill's behaviours."""

# pylint: skip-file

import json
import time
from copy import copy
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional, Type, cast
from unittest import mock

from aea.helpers.transaction.base import SignedMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.valory.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    AbstractRound,
    BaseSynchronizedData,
    BaseTxPayload,
    OK_CODE,
    _MetaPayload,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.behaviours import AbstractRoundBehaviour
from packages.valory.skills.simple_abci.behaviours import (
    RandomnessAtStartupBehaviour,
    RegistrationBehaviour,
    ResetAndPauseBehaviour,
    SelectKeeperAtStartupBehaviour,
    SimpleAbciConsensusBehaviour,
)
from packages.valory.skills.simple_abci.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.valory.skills.simple_abci.rounds import Event, SynchronizedData


PACKAGE_DIR = Path(__file__).parent.parent


class DummyRoundId:
    """Dummy class for setting round_id for exit condition."""

    round_id: str

    def __init__(self, round_id: str) -> None:
        """Dummy class for setting round_id for exit condition."""
        self.round_id = round_id


class SimpleAbciFSMBehaviourBaseCase(BaseSkillTestCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = PACKAGE_DIR

    abci_behaviour: AbstractRoundBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]
    synchronized_data: BaseSynchronizedData
    benchmark_dir: TemporaryDirectory
    done_event: Enum = Event.DONE

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
        cls.abci_behaviour = cast(
            SimpleAbciConsensusBehaviour,
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

        cls.abci_behaviour.setup()
        cls._skill.skill_context.state.setup()
        cls._skill.skill_context.state.round_sequence.end_sync()

        cls.benchmark_dir = TemporaryDirectory()
        cls._skill.skill_context.benchmark_tool.log_dir = Path(cls.benchmark_dir.name)

        assert (
            cast(BaseBehaviour, cls.abci_behaviour.current_behaviour).behaviour_id
            == cls.abci_behaviour.initial_behaviour_cls.behaviour_id
        )
        cls.synchronized_data = SynchronizedData(AbciAppDB(setup_data={}))

    def fast_forward_to_behaviour(
        self,
        behaviour: AbstractRoundBehaviour,
        behaviour_id: str,
        synchronized_data: BaseSynchronizedData,
    ) -> None:
        """Fast forward the FSM to a behaviour."""
        next_behaviour = {s.behaviour_id: s for s in behaviour.behaviours}[behaviour_id]
        assert next_behaviour is not None, f"Behaviour {behaviour_id} not found"
        next_behaviour = cast(Type[BaseBehaviour], next_behaviour)
        behaviour.current_behaviour = next_behaviour(
            name=next_behaviour.behaviour_id, skill_context=behaviour.context
        )
        self.skill.skill_context.state.round_sequence.abci_app._round_results.append(
            synchronized_data
        )
        self.skill.skill_context.state.round_sequence.abci_app._extend_previous_rounds_with_current_round()
        self.skill.skill_context.behaviours.main._last_round_height = (
            self.skill.skill_context.state.round_sequence.abci_app.current_round_height
        )
        self.skill.skill_context.state.round_sequence.abci_app._current_round = (
            next_behaviour.matching_round(
                synchronized_data, self.skill.skill_context.params.consensus_params
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
        self.abci_behaviour.act_wrapper()

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
        self.abci_behaviour.act_wrapper()

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
            contract_id=contract_id,
            **response_kwargs,
        )
        self.contract_handler.handle(incoming_message)
        self.abci_behaviour.act_wrapper()

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
        self.abci_behaviour.act_wrapper()
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
        self.abci_behaviour.act_wrapper()

    def mock_signing_request(self, request_kwargs: Dict, response_kwargs: Dict) -> None:
        """Mock signing request."""
        self.assert_quantity_in_decision_making_queue(1)
        actual_signing_message = self.get_message_from_decision_maker_inbox()
        assert actual_signing_message is not None, "No message in outbox."
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_signing_message,
            message_type=SigningMessage,
            to="dummy_decision_maker_address",
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
            sender="dummy_decision_maker_address",
            **response_kwargs,
        )
        self.signing_handler.handle(incoming_message)
        self.abci_behaviour.act_wrapper()

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
                body=json.dumps({"result": {"hash": "", "code": OK_CODE}}).encode(
                    "utf-8"
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
                body=json.dumps({"result": {"tx_result": {"code": OK_CODE}}}).encode(
                    "utf-8"
                ),
            ),
        )

    def end_round(
        self,
        event: Optional[Enum] = None,
    ) -> None:
        """Ends round early to cover `wait_for_end` generator."""
        current_behaviour = cast(BaseBehaviour, self.abci_behaviour.current_behaviour)
        if current_behaviour is None:
            return
        current_behaviour = cast(BaseBehaviour, current_behaviour)
        abci_app = current_behaviour.context.state.round_sequence.abci_app
        old_round = abci_app._current_round
        abci_app._last_round = old_round
        abci_app._current_round = abci_app.transition_function[
            current_behaviour.matching_round
        ][event if event else self.done_event](
            abci_app.synchronized_data, abci_app.consensus_params
        )
        abci_app._previous_rounds.append(old_round)
        abci_app._current_round_height += 1
        self.abci_behaviour._process_current_round()

    def _test_done_flag_set(self) -> None:
        """Test that, when round ends, the 'done' flag is set."""
        current_behaviour = cast(BaseBehaviour, self.abci_behaviour.current_behaviour)
        assert not current_behaviour.is_done()
        with mock.patch.object(
            self.abci_behaviour.context.state, "_round_sequence"
        ) as mock_round_sequence:
            mock_round_sequence.last_round_id = cast(
                AbstractRound, current_behaviour.matching_round
            ).round_id
            current_behaviour.act_wrapper()
            assert current_behaviour.is_done()

    @classmethod
    def teardown(cls) -> None:
        """Teardown the test class."""
        _MetaPayload.transaction_type_to_payload_cls = cls.old_tx_type_to_payload_cls  # type: ignore
        cls.benchmark_dir.cleanup()


class BaseRandomnessBehaviourTest(SimpleAbciFSMBehaviourBaseCase):
    """Test RandomnessBehaviour."""

    randomness_behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[BaseBehaviour]

    def test_randomness_behaviour(
        self,
    ) -> None:
        """Test RandomnessBehaviour."""

        self.fast_forward_to_behaviour(
            self.abci_behaviour,
            self.randomness_behaviour_class.behaviour_id,
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.abci_behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.behaviour_id
        )
        self.abci_behaviour.act_wrapper()
        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="",
                status_code=200,
                status_text="",
                headers="",
                body=json.dumps(
                    {
                        "round": 1283255,
                        "randomness": "04d4866c26e03347d2431caa82ab2d7b7bdbec8b58bca9460c96f5265d878feb",
                    }
                ).encode("utf-8"),
            ),
        )

        self.abci_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()

        behaviour = cast(BaseBehaviour, self.abci_behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id

    def test_invalid_response(
        self,
    ) -> None:
        """Test invalid json response."""
        self.fast_forward_to_behaviour(
            self.abci_behaviour,
            self.randomness_behaviour_class.behaviour_id,
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.abci_behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.behaviour_id
        )
        self.abci_behaviour.act_wrapper()

        self.mock_http_request(
            request_kwargs=dict(
                method="GET",
                headers="",
                version="",
                body=b"",
                url="https://drand.cloudflare.com/public/latest",
            ),
            response_kwargs=dict(
                version="", status_code=200, status_text="", headers="", body=b""
            ),
        )
        self.abci_behaviour.act_wrapper()
        time.sleep(1)
        self.abci_behaviour.act_wrapper()

    def test_max_retries_reached(
        self,
    ) -> None:
        """Test with max retries reached."""
        self.fast_forward_to_behaviour(
            self.abci_behaviour,
            self.randomness_behaviour_class.behaviour_id,
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.abci_behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.behaviour_id
        )
        with mock.patch.object(
            self.abci_behaviour.context.randomness_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.abci_behaviour.act_wrapper()
            behaviour = cast(BaseBehaviour, self.abci_behaviour.current_behaviour)
            assert (
                behaviour.behaviour_id == self.randomness_behaviour_class.behaviour_id
            )
            self._test_done_flag_set()

    def test_clean_up(
        self,
    ) -> None:
        """Test when `observed` value is none."""
        self.fast_forward_to_behaviour(
            self.abci_behaviour,
            self.randomness_behaviour_class.behaviour_id,
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.abci_behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.behaviour_id
        )
        self.abci_behaviour.context.randomness_api._retries_attempted = 1
        assert self.abci_behaviour.current_behaviour is not None
        self.abci_behaviour.current_behaviour.clean_up()
        assert self.abci_behaviour.context.randomness_api._retries_attempted == 0


class BaseSelectKeeperBehaviourTest(SimpleAbciFSMBehaviourBaseCase):
    """Test SelectKeeperBehaviour."""

    select_keeper_behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[BaseBehaviour]

    def test_select_keeper(
        self,
    ) -> None:
        """Test select keeper agent."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        self.fast_forward_to_behaviour(
            behaviour=self.abci_behaviour,
            behaviour_id=self.select_keeper_behaviour_class.behaviour_id,
            synchronized_data=SynchronizedData(
                AbciAppDB(
                    setup_data=dict(
                        participants=[participants],
                        most_voted_randomness=[
                            "56cbde9e9bbcbdcaf92f183c678eaa5288581f06b1c9c7f884ce911776727688"
                        ],
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.abci_behaviour.current_behaviour),
            ).behaviour_id
            == self.select_keeper_behaviour_class.behaviour_id
        )
        self.abci_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        behaviour = cast(BaseBehaviour, self.abci_behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id


class TestRegistrationBehaviour(SimpleAbciFSMBehaviourBaseCase):
    """Test case to test RegistrationBehaviour."""

    def test_registration(self) -> None:
        """Test registration."""
        self.fast_forward_to_behaviour(
            self.abci_behaviour,
            RegistrationBehaviour.behaviour_id,
            self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.abci_behaviour.current_behaviour),
            ).behaviour_id
            == RegistrationBehaviour.behaviour_id
        )
        self.abci_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()

        self.end_round()
        behaviour = cast(BaseBehaviour, self.abci_behaviour.current_behaviour)
        assert behaviour.behaviour_id == RandomnessAtStartupBehaviour.behaviour_id


class TestRandomnessAtStartup(BaseRandomnessBehaviourTest):
    """Test randomness at startup."""

    randomness_behaviour_class = RandomnessAtStartupBehaviour
    next_behaviour_class = SelectKeeperAtStartupBehaviour


class TestSelectKeeperAtStartupBehaviour(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    select_keeper_behaviour_class = SelectKeeperAtStartupBehaviour
    next_behaviour_class = ResetAndPauseBehaviour


class TestResetAndPauseBehaviour(SimpleAbciFSMBehaviourBaseCase):
    """Test ResetBehaviour."""

    behaviour_class = ResetAndPauseBehaviour
    next_behaviour_class = RandomnessAtStartupBehaviour

    def test_pause_and_reset_behaviour(
        self,
    ) -> None:
        """Test pause and reset behaviour."""
        self.fast_forward_to_behaviour(
            behaviour=self.abci_behaviour,
            behaviour_id=self.behaviour_class.behaviour_id,
            synchronized_data=self.synchronized_data,
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.abci_behaviour.current_behaviour),
            ).behaviour_id
            == self.behaviour_class.behaviour_id
        )
        self.abci_behaviour.context.params.observation_interval = 0.1
        self.abci_behaviour.act_wrapper()
        time.sleep(0.3)
        self.abci_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        behaviour = cast(BaseBehaviour, self.abci_behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id

    def test_reset_behaviour(
        self,
    ) -> None:
        """Test reset behaviour."""
        self.fast_forward_to_behaviour(
            behaviour=self.abci_behaviour,
            behaviour_id=self.behaviour_class.behaviour_id,
            synchronized_data=self.synchronized_data,
        )
        self.abci_behaviour.current_behaviour.pause = False  # type: ignore
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.abci_behaviour.current_behaviour),
            ).behaviour_id
            == self.behaviour_class.behaviour_id
        )
        self.abci_behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        behaviour = cast(BaseBehaviour, self.abci_behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id
