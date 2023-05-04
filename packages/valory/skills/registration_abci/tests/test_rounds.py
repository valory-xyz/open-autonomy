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

"""Test the rounds.py module of the skill."""

import json
from typing import Any, Dict, Optional, cast
from unittest import mock
from unittest.mock import MagicMock, PropertyMock

import pytest

from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.base import (
    BaseSynchronizedData as SynchronizedData,
)
from packages.valory.skills.abstract_round_abci.base import (
    CollectSameUntilAllRound,
    SlashingNotConfiguredError,
)
from packages.valory.skills.abstract_round_abci.test_tools.rounds import (
    BaseCollectSameUntilAllRoundTest,
    BaseCollectSameUntilThresholdRoundTest,
)
from packages.valory.skills.registration_abci.payloads import RegistrationPayload
from packages.valory.skills.registration_abci.rounds import Event as RegistrationEvent
from packages.valory.skills.registration_abci.rounds import (
    RegistrationRound,
    RegistrationStartupRound,
)


# pylint: skip-file


class TestRegistrationStartupRound(BaseCollectSameUntilAllRoundTest):
    """Test RegistrationStartupRound."""

    _synchronized_data_class = SynchronizedData
    _event_class = RegistrationEvent

    @pytest.mark.parametrize("slashing_config", ("", json.dumps({"valid": "config"})))
    def test_run_default(
        self,
        slashing_config: str,
    ) -> None:
        """Run test."""

        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )

        test_round = RegistrationStartupRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        self.synchronized_data.slashing_config = slashing_config

        if not slashing_config:
            seq = test_round.context.state.round_sequence
            type(seq).offence_status = PropertyMock(
                side_effect=SlashingNotConfiguredError
            )

        most_voted_payload = self.synchronized_data.db.serialize()
        round_payloads = {
            participant: RegistrationPayload(
                sender=participant,
                initialisation=most_voted_payload,
            )
            for participant in self.participants
        }

        self._run_with_round(
            test_round,
            round_payloads,
            most_voted_payload,
            RegistrationEvent.DONE,
        )

        assert all(
            (
                self.synchronized_data.all_participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.safe_contract_address
                == "stub_safe_contract_address",
                self.synchronized_data.db.get("oracle_contract_address")
                == "stub_oracle_contract_address",
            )
        )

        test_round.context.state.round_sequence.sync_db_and_slashing.assert_called_once_with(
            most_voted_payload
        )

        if slashing_config:
            test_round.context.state.round_sequence.enable_slashing.assert_called_once()
        else:
            test_round.context.state.round_sequence.enable_slashing.assert_not_called()

    def test_run_default_not_finished(
        self,
    ) -> None:
        """Run test."""

        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )
        test_round = RegistrationStartupRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        with mock.patch.object(
            CollectSameUntilAllRound,
            "collection_threshold_reached",
            new_callable=mock.PropertyMock,
        ) as threshold_mock:
            threshold_mock.return_value = False
            self._run_with_round(
                test_round,
                finished=False,
                most_voted_payload="none",
            )

        assert all(
            (
                self.synchronized_data.all_participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.safe_contract_address
                == "stub_safe_contract_address",
                self.synchronized_data.db.get("oracle_contract_address")
                == "stub_oracle_contract_address",
            )
        )

    def _run_with_round(
        self,
        test_round: RegistrationStartupRound,
        round_payloads: Optional[Dict[str, RegistrationPayload]] = None,
        most_voted_payload: Optional[Any] = None,
        expected_event: Optional[RegistrationEvent] = None,
        finished: bool = True,
    ) -> None:
        """Run with given round."""

        round_payloads = round_payloads or {
            p: RegistrationPayload(sender=p, initialisation="none")
            for p in self.participants
        }

        test_runner = self._test_round(
            test_round=test_round,
            round_payloads=round_payloads,
            synchronized_data_update_fn=(
                lambda *x: SynchronizedData(
                    AbciAppDB(
                        setup_data=dict(participants=[tuple(self.participants)]),
                    )
                )
            ),
            synchronized_data_attr_checks=[
                lambda _synchronized_data: _synchronized_data.participants
            ],
            most_voted_payload=most_voted_payload,
            exit_event=expected_event,
            finished=finished,
        )

        next(test_runner)
        next(test_runner)
        next(test_runner)
        if finished:
            next(test_runner)


class TestRegistrationRound(BaseCollectSameUntilThresholdRoundTest):
    """Test RegistrationRound."""

    _synchronized_data_class = SynchronizedData
    _event_class = RegistrationEvent

    def test_run_default(
        self,
    ) -> None:
        """Run test."""
        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )
        test_round = RegistrationRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        payload_data = self.synchronized_data.db.serialize()

        round_payloads = {
            participant: RegistrationPayload(
                sender=participant,
                initialisation=payload_data,
            )
            for participant in self.participants
        }

        self._run_with_round(
            test_round=test_round,
            expected_event=RegistrationEvent.DONE,
            confirmations=11,
            most_voted_payload=payload_data,
            round_payloads=round_payloads,
        )

        assert all(
            (
                self.synchronized_data.all_participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.safe_contract_address
                == "stub_safe_contract_address",
                self.synchronized_data.db.get("oracle_contract_address")
                == "stub_oracle_contract_address",
            )
        )

    def test_run_default_not_finished(
        self,
    ) -> None:
        """Run test."""
        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )
        test_round = RegistrationRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )
        self._run_with_round(
            test_round,
            confirmations=None,
        )

        assert all(
            (
                self.synchronized_data.all_participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.safe_contract_address
                == "stub_safe_contract_address",
                self.synchronized_data.db.get("oracle_contract_address")
                == "stub_oracle_contract_address",
            )
        )

    def _run_with_round(
        self,
        test_round: RegistrationRound,
        round_payloads: Optional[Dict[str, RegistrationPayload]] = None,
        most_voted_payload: Optional[Any] = None,
        expected_event: Optional[RegistrationEvent] = None,
        confirmations: Optional[int] = None,
        finished: bool = True,
    ) -> None:
        """Run with given round."""

        round_payloads = round_payloads or {
            p: RegistrationPayload(sender=p, initialisation="none")
            for p in self.participants
        }

        test_runner = self._test_round(
            test_round=test_round,
            round_payloads=round_payloads,
            synchronized_data_update_fn=(
                lambda *x: SynchronizedData(
                    AbciAppDB(
                        setup_data=dict(participants=[tuple(self.participants)]),
                    )
                )
            ),
            synchronized_data_attr_checks=[
                lambda _synchronized_data: _synchronized_data.participants
            ],
            most_voted_payload=most_voted_payload,
            exit_event=expected_event,
        )

        next(test_runner)
        if confirmations is None:
            assert (
                test_round.block_confirmations
                <= test_round.required_block_confirmations
            )

        else:
            test_round.block_confirmations = confirmations
            test_round = next(test_runner)
            prior_confirmations = test_round.block_confirmations
            next(test_runner)
            assert test_round.block_confirmations == prior_confirmations + 1
            if finished:
                next(test_runner)

    def test_no_majority(self) -> None:
        """Test the NO_MAJORITY event."""
        self.synchronized_data = cast(
            SynchronizedData,
            self.synchronized_data.update(
                safe_contract_address="stub_safe_contract_address",
                oracle_contract_address="stub_oracle_contract_address",
            ),
        )

        test_round = RegistrationRound(
            synchronized_data=self.synchronized_data,
            context=MagicMock(),
        )

        with mock.patch.object(test_round, "is_majority_possible", return_value=False):
            with mock.patch.object(test_round, "block_confirmations", 11):
                self._test_no_majority_event(test_round)

        assert all(
            (
                self.synchronized_data.all_participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.participants
                == frozenset({"agent_2", "agent_0", "agent_1", "agent_3"}),
                self.synchronized_data.safe_contract_address
                == "stub_safe_contract_address",
                self.synchronized_data.db.get("oracle_contract_address")
                == "stub_oracle_contract_address",
            )
        )
