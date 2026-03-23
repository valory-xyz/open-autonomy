# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Tests for IdentifyServiceOwnerBehaviour."""

# pylint: disable=protected-access,too-few-public-methods,attribute-defined-outside-init

from typing import Any, Optional
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import BaseBehaviour
from packages.valory.skills.identify_service_owner_abci.behaviours import (
    IdentifyServiceOwnerBehaviour,
    IdentifyServiceOwnerRoundBehaviour,
)
from packages.valory.skills.identify_service_owner_abci.rounds import (
    IdentifyServiceOwnerAbciApp,
    IdentifyServiceOwnerRound,
)

AGENT_ADDRESS = "0x1234567890123456789012345678901234567890"
REGISTRY_ADDRESS = "0x9338b5153AE39BB89f50468E608eD9d764B755fD"
OWNER_ADDRESS = "0xOwner567890123456789012345678901234567890"
STAKING_ADDRESS = "0xStaking890123456789012345678901234567890"
SAFE_ADDRESS = "0xSafe5678901234567890123456789012345678901"
SERVICE_ID = 42


def _make_gen(return_value: Any) -> Any:
    """Create a no-yield generator returning the given value."""

    def gen(*_args: Any, **_kwargs: Any) -> Any:
        return return_value
        yield  # noqa: unreachable

    return gen


def _exhaust_gen(gen: Any) -> Any:
    """Exhaust a generator and return its value."""
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value


def _make_behaviour() -> IdentifyServiceOwnerBehaviour:
    """Create an IdentifyServiceOwnerBehaviour with mocked context."""
    context_mock = MagicMock()
    context_mock.logger = MagicMock()
    context_mock.params = MagicMock()
    context_mock.state.round_sequence = MagicMock()
    context_mock.benchmark_tool = MagicMock()
    context_mock.agent_address = AGENT_ADDRESS
    context_mock.params.on_chain_service_id = SERVICE_ID
    context_mock.params.service_registry_address = REGISTRY_ADDRESS
    return IdentifyServiceOwnerBehaviour(name="test", skill_context=context_mock)


class TestIdentifyServiceOwnerBehaviour:
    """Test IdentifyServiceOwnerBehaviour."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.behaviour = _make_behaviour()

    def test_matching_round(self) -> None:
        """Test matching_round is correctly set."""
        assert self.behaviour.matching_round == IdentifyServiceOwnerRound

    @pytest.mark.parametrize(
        "service_id,registry_address",
        [
            (None, REGISTRY_ADDRESS),
            (SERVICE_ID, None),
        ],
    )
    def test_resolve_not_configured(
        self, service_id: Any, registry_address: Any
    ) -> None:
        """Test _resolve_service_owner when service_id or registry is None."""
        self.behaviour.context.params.on_chain_service_id = service_id
        self.behaviour.context.params.service_registry_address = registry_address
        gen = self.behaviour._resolve_service_owner()
        result = _exhaust_gen(gen)
        assert result is None

    def test_resolve_agent_not_registered(self) -> None:
        """Test _resolve_service_owner when agent is not registered."""
        with patch.object(
            self.behaviour,
            "_verify_agent_registration",
            new=_make_gen(False),
        ):
            gen = self.behaviour._resolve_service_owner()
            result = _exhaust_gen(gen)
        assert result is None

    def test_resolve_registry_owner_none(self) -> None:
        """Test _resolve_service_owner when registry owner call fails."""
        with patch.object(
            self.behaviour,
            "_verify_agent_registration",
            new=_make_gen(True),
        ), patch.object(self.behaviour, "_get_registry_owner", new=_make_gen(None)):
            gen = self.behaviour._resolve_service_owner()
            result = _exhaust_gen(gen)
        assert result is None

    @pytest.mark.parametrize(
        "staking_result,expected",
        [
            (OWNER_ADDRESS, OWNER_ADDRESS),
            (None, OWNER_ADDRESS),
        ],
    )
    def test_resolve_service_owner(
        self, staking_result: Optional[str], expected: str
    ) -> None:
        """Test _resolve_service_owner for staked and non-staked services."""
        registry_owner = STAKING_ADDRESS if staking_result else OWNER_ADDRESS
        with patch.object(
            self.behaviour,
            "_verify_agent_registration",
            new=_make_gen(True),
        ), patch.object(
            self.behaviour,
            "_get_registry_owner",
            new=_make_gen(registry_owner),
        ), patch.object(
            self.behaviour,
            "_get_owner_from_staking",
            new=_make_gen(staking_result),
        ):
            gen = self.behaviour._resolve_service_owner()
            result = _exhaust_gen(gen)
        assert result == expected

    @pytest.mark.parametrize(
        "performative,body,expected",
        [
            (
                ContractApiMessage.Performative.STATE,
                {
                    "agentInstances": [AGENT_ADDRESS],
                    "numAgentInstances": 1,
                },
                True,
            ),
            (
                ContractApiMessage.Performative.STATE,
                {
                    "agentInstances": ["0xOtherAgent"],
                    "numAgentInstances": 1,
                },
                False,
            ),
            (ContractApiMessage.Performative.ERROR, None, False),
        ],
    )
    def test_verify_agent_registration(
        self, performative: Any, body: Any, expected: bool
    ) -> None:
        """Test _verify_agent_registration for success, not registered, and error."""
        mock_response = MagicMock()
        mock_response.performative = performative
        if body is not None:
            mock_response.state.body = body

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._verify_agent_registration(
                SERVICE_ID, REGISTRY_ADDRESS
            )
            result = _exhaust_gen(gen)
        assert result is expected

    @pytest.mark.parametrize(
        "performative,body,expected",
        [
            (
                ContractApiMessage.Performative.STATE,
                {"service_owner": OWNER_ADDRESS},
                OWNER_ADDRESS,
            ),
            (ContractApiMessage.Performative.ERROR, None, None),
        ],
    )
    def test_get_registry_owner(
        self, performative: Any, body: Any, expected: Any
    ) -> None:
        """Test _get_registry_owner for success and error cases."""
        mock_response = MagicMock()
        mock_response.performative = performative
        if body is not None:
            mock_response.state.body = body

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._get_registry_owner(SERVICE_ID, REGISTRY_ADDRESS)
            result = _exhaust_gen(gen)
        assert result == expected

    @pytest.mark.parametrize(
        "performative,body,address,expected",
        [
            (
                ContractApiMessage.Performative.STATE,
                {"data": ["0xMultisig", OWNER_ADDRESS, [], 0, 0, 0]},
                STAKING_ADDRESS,
                OWNER_ADDRESS,
            ),
            (
                ContractApiMessage.Performative.ERROR,
                None,
                OWNER_ADDRESS,
                None,
            ),
        ],
    )
    def test_get_owner_from_staking(
        self, performative: Any, body: Any, address: str, expected: Any
    ) -> None:
        """Test _get_owner_from_staking for staking and non-staking cases."""
        mock_response = MagicMock()
        mock_response.performative = performative
        if body is not None:
            mock_response.state.body = body

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._get_owner_from_staking(address, SERVICE_ID)
            result = _exhaust_gen(gen)
        assert result == expected

    @pytest.mark.parametrize(
        "owner",
        [OWNER_ADDRESS, None],
    )
    def test_async_act(self, owner: Optional[str]) -> None:
        """Test async_act when owner is resolved or resolution fails."""
        with patch.object(
            self.behaviour,
            "_resolve_service_owner",
            new=_make_gen(owner),
        ), patch.object(
            type(self.behaviour),
            "synchronized_data",
            new_callable=lambda: property(
                lambda self: MagicMock(safe_contract_address=SAFE_ADDRESS)
            ),
        ), patch.object(
            self.behaviour, "send_a2a_transaction", new=_make_gen(None)
        ), patch.object(
            self.behaviour, "wait_until_round_end", new=_make_gen(None)
        ), patch.object(
            self.behaviour, "set_done"
        ) as mock_set_done:
            gen = self.behaviour.async_act()
            _exhaust_gen(gen)
            mock_set_done.assert_called_once()


class TestIdentifyServiceOwnerBaseBehaviour:
    """Test base behaviour properties."""

    def test_synchronized_data_property(self) -> None:
        """Test synchronized_data property returns cast SynchronizedData."""
        b = _make_behaviour()
        mock_sync = MagicMock()
        with patch.object(
            BaseBehaviour,
            "synchronized_data",
            new_callable=PropertyMock,
            return_value=mock_sync,
        ):
            result = b.synchronized_data
        assert result == mock_sync


class TestIdentifyServiceOwnerRoundBehaviour:
    """Test IdentifyServiceOwnerRoundBehaviour."""

    def test_initial_behaviour_cls(self) -> None:
        """Test initial_behaviour_cls."""
        assert (
            IdentifyServiceOwnerRoundBehaviour.initial_behaviour_cls
            is IdentifyServiceOwnerBehaviour
        )

    def test_abci_app_cls(self) -> None:
        """Test abci_app_cls."""
        assert (
            IdentifyServiceOwnerRoundBehaviour.abci_app_cls
            is IdentifyServiceOwnerAbciApp
        )

    def test_behaviours(self) -> None:
        """Test behaviours set."""
        assert IdentifyServiceOwnerBehaviour in (
            IdentifyServiceOwnerRoundBehaviour.behaviours
        )
