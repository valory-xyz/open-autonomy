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

"""Tests for valory/abstract_round_abci skill's behaviours."""
import json
from abc import ABC
from copy import copy
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Type, cast
from unittest import mock
from unittest.mock import MagicMock

from aea.helpers.transaction.base import SignedMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.valory.connections.ledger.connection import (
    PUBLIC_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.http import HttpMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    BaseSynchronizedData,
    BaseTxPayload,
    OK_CODE,
    _MetaPayload,
)
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.abstract_round_abci.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
    TendermintHandler,
)


# pylint: disable=protected-access,too-few-public-methods,consider-using-with


class FSMBehaviourBaseCase(BaseSkillTestCase, ABC):
    """Base case for testing FSMBehaviour classes."""

    path_to_skill: Path
    behaviour: AbstractRoundBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    tendermint_handler: TendermintHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]
    benchmark_dir: TemporaryDirectory
    default_ledger: str = "ethereum"

    @classmethod
    def setup_class(cls, **kwargs: Any) -> None:
        """Setup the test class."""
        if not hasattr(cls, "path_to_skill"):
            raise ValueError(f"No `path_to_skill` set on {cls}")  # pragma: nocover
            # works once https://github.com/valory-xyz/open-aea/issues/492 is fixed
        # we need to store the current value of the meta-class attribute
        # _MetaPayload.transaction_type_to_payload_cls, and restore it
        # in the teardown function. We do a shallow copy so we avoid
        # to modify the old mapping during the execution of the tests.
        cls.old_tx_type_to_payload_cls = copy(_MetaPayload.registry)
        _MetaPayload.registry = {}
        super().setup_class(**kwargs)  # pylint: disable=no-value-for-parameter
        assert (
            cls._skill.skill_context._agent_context is not None
        ), "Agent context not set"  # nosec
        cls._skill.skill_context._agent_context.identity._default_address_key = (
            cls.default_ledger
        )
        cls._skill.skill_context._agent_context._default_ledger_id = cls.default_ledger
        behaviour = cls._skill.skill_context.behaviours.main
        assert isinstance(
            behaviour, AbstractRoundBehaviour
        ), f"{behaviour} is not of type {AbstractRoundBehaviour}"
        cls.behaviour = behaviour
        for attr, handler, handler_type in [
            ("http_handler", cls._skill.skill_context.handlers.http, HttpHandler),
            (
                "signing_handler",
                cls._skill.skill_context.handlers.signing,
                SigningHandler,
            ),
            (
                "contract_handler",
                cls._skill.skill_context.handlers.contract_api,
                ContractApiHandler,
            ),
            (
                "ledger_handler",
                cls._skill.skill_context.handlers.ledger_api,
                LedgerApiHandler,
            ),
            (
                "tendermint_handler",
                cls._skill.skill_context.handlers.tendermint,
                TendermintHandler,
            ),
        ]:
            assert isinstance(
                handler, handler_type
            ), f"{handler} is not of type {handler_type}"
            setattr(cls, attr, handler)

        if kwargs.get("param_overrides") is not None:
            for param_name, param_value in kwargs["param_overrides"].items():
                cls.behaviour.context.params.__dict__[param_name] = param_value

    def setup(self, **kwargs: Any) -> None:
        """
        Set up the test method.

        Called each time before a test method is called.

        :param kwargs: the keyword arguments passed to _prepare_skill
        """
        super().setup(**kwargs)
        self.behaviour.setup()
        self._skill.skill_context.state.setup()
        self._skill.skill_context.state.round_sequence.end_sync()

        self.benchmark_dir = TemporaryDirectory()
        self._skill.skill_context.benchmark_tool.__dict__["log_dir"] = Path(
            self.benchmark_dir.name
        )
        assert (  # nosec
            cast(BaseBehaviour, self.behaviour.current_behaviour).behaviour_id
            == self.behaviour.initial_behaviour_cls.auto_behaviour_id()
        )

    def fast_forward_to_behaviour(
        self,
        behaviour: AbstractRoundBehaviour,
        behaviour_id: str,
        synchronized_data: BaseSynchronizedData,
    ) -> None:
        """Fast forward the FSM to a behaviour."""
        next_behaviour = {s.auto_behaviour_id(): s for s in behaviour.behaviours}[
            behaviour_id
        ]
        next_behaviour = cast(Type[BaseBehaviour], next_behaviour)
        behaviour.current_behaviour = next_behaviour(
            name=next_behaviour.auto_behaviour_id(), skill_context=behaviour.context
        )
        self.skill.skill_context.state.round_sequence.abci_app._round_results.append(
            synchronized_data
        )
        self.skill.skill_context.state.round_sequence.abci_app._extend_previous_rounds_with_current_round()
        self.skill.skill_context.behaviours.main._last_round_height = (
            self.skill.skill_context.state.round_sequence.abci_app.current_round_height
        )
        self.skill.skill_context.state.round_sequence.abci_app._current_round_cls = (
            next_behaviour.matching_round
        )
        # consensus parameters will not be available if the current skill is abstract
        consensus_params = getattr(
            self.skill.skill_context.params, "consensus_params", None
        )
        self.skill.skill_context.state.round_sequence.abci_app._current_round = (
            next_behaviour.matching_round(synchronized_data, consensus_params)
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
        assert actual_ledger_api_message is not None, "No message in outbox."  # nosec
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_ledger_api_message,
            message_type=LedgerApiMessage,
            to=str(LEDGER_CONNECTION_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            **request_kwargs,
        )

        assert has_attributes, error_str  # nosec
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
        self.behaviour.act_wrapper()

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
        assert (  # nosec
            actual_contract_ledger_message is not None
        ), "No message in outbox."
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
        assert has_attributes, error_str  # nosec
        self.behaviour.act_wrapper()

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
            contract_id="mock_contract_id",
            **response_kwargs,
        )
        self.contract_handler.handle(incoming_message)
        self.behaviour.act_wrapper()

    def mock_http_request(self, request_kwargs: Dict, response_kwargs: Dict) -> None:
        """
        Mock http request.

        :param request_kwargs: keyword arguments for request check.
        :param response_kwargs: keyword arguments for mock response.
        """

        self.assert_quantity_in_outbox(1)
        actual_http_message = self.get_message_from_outbox()
        assert actual_http_message is not None, "No message in outbox."  # nosec
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_http_message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            **request_kwargs,
        )
        assert has_attributes, error_str  # nosec
        self.behaviour.act_wrapper()
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
        self.behaviour.act_wrapper()

    def mock_signing_request(self, request_kwargs: Dict, response_kwargs: Dict) -> None:
        """Mock signing request."""
        self.assert_quantity_in_decision_making_queue(1)
        actual_signing_message = self.get_message_from_decision_maker_inbox()
        assert actual_signing_message is not None, "No message in outbox."  # nosec
        has_attributes, error_str = self.message_has_attributes(
            actual_message=actual_signing_message,
            message_type=SigningMessage,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            **request_kwargs,
        )
        assert has_attributes, error_str  # nosec
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
        self.behaviour.act_wrapper()

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

    def end_round(self, done_event: Enum) -> None:
        """Ends round early to cover `wait_for_end` generator."""
        current_behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        if current_behaviour is None:
            return
        current_behaviour = cast(BaseBehaviour, current_behaviour)
        abci_app = current_behaviour.context.state.round_sequence.abci_app
        old_round = abci_app._current_round
        abci_app._last_round = old_round
        abci_app._current_round = abci_app.transition_function[
            current_behaviour.matching_round
        ][done_event](abci_app.synchronized_data, context=MagicMock())
        abci_app._previous_rounds.append(old_round)
        abci_app._current_round_height += 1
        self.behaviour._process_current_round()

    def _test_done_flag_set(self) -> None:
        """Test that, when round ends, the 'done' flag is set."""
        current_behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert not current_behaviour.is_done()  # nosec
        with mock.patch.object(
            self.behaviour.context.state, "_round_sequence"
        ) as mock_round_sequence:
            mock_round_sequence.last_round_id = cast(
                AbstractRound, current_behaviour.matching_round
            ).auto_round_id()
            current_behaviour.act_wrapper()
            assert current_behaviour.is_done()  # nosec

    @classmethod
    def teardown_class(cls) -> None:
        """Teardown the test class."""
        if getattr(cls, "old_tx_type_to_payload_cls", False):
            _MetaPayload.registry = cls.old_tx_type_to_payload_cls

    def teardown(self, **kwargs: Any) -> None:
        """Teardown."""
        super().teardown(**kwargs)
        self.benchmark_dir.cleanup()


class DummyContext:
    """Dummy Context class for testing shared state initialization."""

    class params:
        """Dummy param variable."""

        round_timeout_seconds: float = 1.0

    _skill: MagicMock = MagicMock()
    logger: MagicMock = MagicMock()
    skill_id = "dummy_skill_id"

    @property
    def is_abstract_component(self) -> bool:
        """Mock for is_abstract."""
        return True
