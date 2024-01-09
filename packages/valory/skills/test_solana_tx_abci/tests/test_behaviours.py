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

# pylint: disable=unused-argument,no-self-use

"""Tests for valory/test_solana_abci skill's behaviours."""

import json
import sys
from typing import Any, Callable, Generator, Optional
from unittest import mock
from unittest.mock import MagicMock

from aea_test_autonomy.helpers.base import try_send

from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.io_.store import SupportedObjectType
from packages.valory.skills.test_solana_tx_abci.behaviours import SolanaTransferBehaviour


class TestSolanaTransferBehaviour:
    """Test for SolanaTransferBehaviour."""

    def wrap_dummy_get_from_solana(
        self, return_value: Optional[SupportedObjectType]
    ) -> Callable:
        """Wrap dummy_get_from_solana."""

        def dummy_get_from_solana(
            *args: Any, **kwargs: Any
        ) -> Generator[None, None, Optional[SupportedObjectType]]:
            """A mock get_from_solana."""
            return return_value
            yield

        return dummy_get_from_solana

    def wrap_dummy_send_to_solana(self, return_value: Optional[str]) -> Callable:
        """Wrap dummy_send_to_solana."""

        def dummy_send_to_solana(
            *args: Any, **kwargs: Any
        ) -> Generator[None, None, Optional[str]]:
            """A mock send_to_solana."""
            return return_value
            yield

        return dummy_send_to_solana

    def wrap_dummy_sleep(self) -> Callable:
        """Dummy sleep wrapper."""

        def dummy_sleep(*args: Any, **kwargs: Any) -> Generator:
            return
            yield

        return dummy_sleep

    def test_async_act(self) -> None:
        """Test SolanaTransferBehaviour.async_act"""
        behaviour = SolanaTransferBehaviour(name="", skill_context=MagicMock())
        gen = behaviour.async_act()
        dummy_object = {
            "dummy_k1": "dummy_v1",
            "dummy_k2": "dummy_v2",
            "dummy_k3": "dummy_v3",
        }
        with mock.patch.object(
            BaseBehaviour,
            "get_from_solana",
            side_effect=self.wrap_dummy_get_from_solana(dummy_object),
        ), mock.patch.object(
            BaseBehaviour,
            "send_to_solana",
            side_effect=self.wrap_dummy_send_to_solana(json.dumps(dummy_object)),
        ), mock.patch.object(
            BaseBehaviour, "sleep", side_effect=self.wrap_dummy_sleep()
        ), mock.patch.object(
            sys, "exit"
        ):
            try_send(gen)

    def test_async_act_multiple(self) -> None:
        """Test SolanaTransferBehaviour.async_act"""
        behaviour = SolanaTransferBehaviour(name="", skill_context=MagicMock())
        gen = behaviour.async_act()
        dummy_object = {
            "dummy_k1": "dummy_v1",
            "dummy_k2": "dummy_v2",
            "dummy_k3": "dummy_v3",
        }
        multiple_objects = {
            "test1.json": dummy_object,
            "test2.json": dummy_object,
            "test3.json": dummy_object,
        }
        with mock.patch.object(
            BaseBehaviour,
            "get_from_solana",
            side_effect=self.wrap_dummy_get_from_solana(multiple_objects),
        ), mock.patch.object(
            BaseBehaviour,
            "send_to_solana",
            side_effect=self.wrap_dummy_get_from_solana(multiple_objects),
        ), mock.patch.object(
            BaseBehaviour, "sleep", side_effect=self.wrap_dummy_sleep()
        ), mock.patch.object(
            sys, "exit"
        ):
            try_send(gen)
