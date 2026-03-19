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

from typing import Any
from unittest.mock import MagicMock, patch

from packages.valory.protocols.contract_api import ContractApiMessage
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

    def gen(*args: Any, **kwargs: Any) -> Any:
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
    return IdentifyServiceOwnerBehaviour(
        name="test", skill_context=context_mock
    )


class TestIdentifyServiceOwnerBehaviour:
    """Test IdentifyServiceOwnerBehaviour."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.behaviour = _make_behaviour()

    def test_matching_round(self) -> None:
        """Test matching_round is correctly set."""
        assert self.behaviour.matching_round == IdentifyServiceOwnerRound

    def test_resolve_not_configured(self) -> None:
        """Test _resolve_service_owner when service_id is None."""
        self.behaviour.context.params.on_chain_service_id = None
        gen = self.behaviour._resolve_service_owner()
        result = _exhaust_gen(gen)
        assert result is None

    def test_resolve_registry_address_none(self) -> None:
        """Test _resolve_service_owner when registry_address is None."""
        self.behaviour.context.params.service_registry_address = None
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
        ), patch.object(
            self.behaviour, "_get_registry_owner", new=_make_gen(None)
        ):
            gen = self.behaviour._resolve_service_owner()
            result = _exhaust_gen(gen)
        assert result is None

    def test_resolve_staked_service(self) -> None:
        """Test _resolve_service_owner for a staked service."""
        with patch.object(
            self.behaviour,
            "_verify_agent_registration",
            new=_make_gen(True),
        ), patch.object(
            self.behaviour,
            "_get_registry_owner",
            new=_make_gen(STAKING_ADDRESS),
        ), patch.object(
            self.behaviour,
            "_get_owner_from_staking",
            new=_make_gen(OWNER_ADDRESS),
        ):
            gen = self.behaviour._resolve_service_owner()
            result = _exhaust_gen(gen)
        assert result == OWNER_ADDRESS

    def test_resolve_non_staked_service(self) -> None:
        """Test _resolve_service_owner for a non-staked service."""
        with patch.object(
            self.behaviour,
            "_verify_agent_registration",
            new=_make_gen(True),
        ), patch.object(
            self.behaviour,
            "_get_registry_owner",
            new=_make_gen(OWNER_ADDRESS),
        ), patch.object(
            self.behaviour,
            "_get_owner_from_staking",
            new=_make_gen(None),
        ):
            gen = self.behaviour._resolve_service_owner()
            result = _exhaust_gen(gen)
        assert result == OWNER_ADDRESS

    def test_verify_agent_registration_success(self) -> None:
        """Test _verify_agent_registration when agent is registered."""
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.STATE
        mock_response.state.body = {
            "agentInstances": [AGENT_ADDRESS],
            "numAgentInstances": 1,
        }

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._verify_agent_registration(
                SERVICE_ID, REGISTRY_ADDRESS
            )
            result = _exhaust_gen(gen)
        assert result is True

    def test_verify_agent_registration_not_registered(self) -> None:
        """Test _verify_agent_registration when agent is not in the list."""
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.STATE
        mock_response.state.body = {
            "agentInstances": ["0xOtherAgent"],
            "numAgentInstances": 1,
        }

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._verify_agent_registration(
                SERVICE_ID, REGISTRY_ADDRESS
            )
            result = _exhaust_gen(gen)
        assert result is False

    def test_verify_agent_registration_error(self) -> None:
        """Test _verify_agent_registration when contract call fails."""
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.ERROR

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._verify_agent_registration(
                SERVICE_ID, REGISTRY_ADDRESS
            )
            result = _exhaust_gen(gen)
        assert result is False

    def test_get_registry_owner_success(self) -> None:
        """Test _get_registry_owner success."""
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.STATE
        mock_response.state.body = {"service_owner": OWNER_ADDRESS}

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._get_registry_owner(
                SERVICE_ID, REGISTRY_ADDRESS
            )
            result = _exhaust_gen(gen)
        assert result == OWNER_ADDRESS

    def test_get_registry_owner_error(self) -> None:
        """Test _get_registry_owner when contract call fails."""
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.ERROR

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._get_registry_owner(
                SERVICE_ID, REGISTRY_ADDRESS
            )
            result = _exhaust_gen(gen)
        assert result is None

    def test_get_owner_from_staking_success(self) -> None:
        """Test _get_owner_from_staking when address is a staking contract."""
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.STATE
        mock_response.state.body = {
            "data": ["0xMultisig", OWNER_ADDRESS, [], 0, 0, 0]
        }

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._get_owner_from_staking(
                STAKING_ADDRESS, SERVICE_ID
            )
            result = _exhaust_gen(gen)
        assert result == OWNER_ADDRESS

    def test_get_owner_from_staking_not_staking(self) -> None:
        """Test _get_owner_from_staking when address is not a staking contract."""
        mock_response = MagicMock()
        mock_response.performative = ContractApiMessage.Performative.ERROR

        with patch.object(
            self.behaviour,
            "get_contract_api_response",
            new=_make_gen(mock_response),
        ):
            gen = self.behaviour._get_owner_from_staking(
                OWNER_ADDRESS, SERVICE_ID
            )
            result = _exhaust_gen(gen)
        assert result is None

    def test_async_act_with_owner(self) -> None:
        """Test async_act when owner is resolved."""
        with patch.object(
            self.behaviour,
            "_resolve_service_owner",
            new=_make_gen(OWNER_ADDRESS),
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

    def test_async_act_without_owner(self) -> None:
        """Test async_act when owner resolution fails."""
        with patch.object(
            self.behaviour,
            "_resolve_service_owner",
            new=_make_gen(None),
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
        with patch(
            "packages.valory.skills.abstract_round_abci.behaviours.BaseBehaviour.synchronized_data",
            new_callable=lambda: property(lambda self: mock_sync),
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
