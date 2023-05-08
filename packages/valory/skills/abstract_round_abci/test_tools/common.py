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

"""Test common classes."""
import binascii
import json
import time
from pathlib import Path
from typing import Any, Set, Type, cast
from unittest import mock

import pytest
from aea.exceptions import AEAActException
from aea.skills.base import SkillContext

from packages.valory.protocols.contract_api.custom_types import State
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    BaseSynchronizedData,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import BaseBehaviour
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)


PACKAGE_DIR = Path(__file__).parent.parent
DRAND_VALUE = {
    "round": 1416669,
    "randomness": "f6be4bf1fa229f22340c1a5b258f809ac4af558200775a67dacb05f0cb258a11",
    "signature": (
        "b44d00516f46da3a503f9559a634869b6dc2e5d839e46ec61a090e3032172954929a5"
        "d9bd7197d7739fe55db770543c71182562bd0ad20922eb4fe6b8a1062ed21df3b68de"
        "44694eb4f20b35262fa9d63aa80ad3f6172dd4d33a663f21179604"
    ),
    "previous_signature": (
        "903c60a4b937a804001032499a855025573040cb86017c38e2b1c3725286756ce8f33"
        "61188789c17336beaf3f9dbf84b0ad3c86add187987a9a0685bc5a303e37b008fba8c"
        "44f02a416480dd117a3ff8b8075b1b7362c58af195573623187463"
    ),
}


class CommonBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = PACKAGE_DIR = Path(__file__).parent.parent


class BaseRandomnessBehaviourTest(CommonBaseCase):
    """Test RandomnessBehaviour."""

    randomness_behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[BaseBehaviour]
    done_event: Any

    def test_randomness_behaviour(
        self,
    ) -> None:
        """Test RandomnessBehaviour."""

        self.fast_forward_to_behaviour(
            self.behaviour,
            self.randomness_behaviour_class.auto_behaviour_id(),
            BaseSynchronizedData(AbciAppDB(setup_data={})),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()
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
                body=json.dumps(DRAND_VALUE).encode("utf-8"),
            ),
        )

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(self.done_event)

        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.auto_behaviour_id()

    def test_invalid_drand_value(
        self,
    ) -> None:
        """Test invalid drand values."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.randomness_behaviour_class.auto_behaviour_id(),
            BaseSynchronizedData(AbciAppDB(setup_data={})),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()

        drand_value = DRAND_VALUE.copy()
        drand_value["randomness"] = binascii.hexlify(b"randomness_hex").decode()
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
                body=json.dumps(drand_value).encode(),
            ),
        )

    def test_invalid_response(
        self,
    ) -> None:
        """Test invalid json response."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.randomness_behaviour_class.auto_behaviour_id(),
            BaseSynchronizedData(AbciAppDB(setup_data={})),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()

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
        self.behaviour.act_wrapper()
        time.sleep(1)
        self.behaviour.act_wrapper()

    def test_max_retries_reached_fallback(
        self,
    ) -> None:
        """Test with max retries reached."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.randomness_behaviour_class.auto_behaviour_id(),
            BaseSynchronizedData(AbciAppDB(setup_data={})),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.context.randomness_api.__dict__["_frozen"] = False
        with mock.patch.object(
            self.behaviour.context.randomness_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.behaviour.act_wrapper()
            self.mock_ledger_api_request(
                request_kwargs=dict(
                    performative=LedgerApiMessage.Performative.GET_STATE
                ),
                response_kwargs=dict(
                    performative=LedgerApiMessage.Performative.STATE,
                    state=State(ledger_id="ethereum", body={"hash": "0xa"}),
                ),
            )

            self.behaviour.act_wrapper()
            self.mock_a2a_transaction()
            self._test_done_flag_set()
            self.end_round(self.done_event)

            behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
            assert (
                behaviour.behaviour_id == self.next_behaviour_class.auto_behaviour_id()
            )
        self.behaviour.context.randomness_api.__dict__["_frozen"] = True

    def test_max_retries_reached_fallback_fail(
        self,
    ) -> None:
        """Test with max retries reached."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.randomness_behaviour_class.auto_behaviour_id(),
            BaseSynchronizedData(AbciAppDB(setup_data={})),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.context.randomness_api.__dict__["_frozen"] = False
        with mock.patch.object(
            self.behaviour.context.randomness_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.behaviour.act_wrapper()
            self.mock_ledger_api_request(
                request_kwargs=dict(
                    performative=LedgerApiMessage.Performative.GET_STATE
                ),
                response_kwargs=dict(
                    performative=LedgerApiMessage.Performative.ERROR,
                    state=State(ledger_id="ethereum", body={}),
                ),
            )

            self.behaviour.act_wrapper()
        self.behaviour.context.randomness_api.__dict__["_frozen"] = True

    def test_max_retries_reached_fallback_fail_case_2(
        self,
    ) -> None:
        """Test with max retries reached."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.randomness_behaviour_class.auto_behaviour_id(),
            BaseSynchronizedData(AbciAppDB(setup_data={})),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.context.randomness_api.__dict__["_frozen"] = False
        with mock.patch.object(
            self.behaviour.context.randomness_api,
            "is_retries_exceeded",
            return_value=True,
        ):
            self.behaviour.act_wrapper()
            self.mock_ledger_api_request(
                request_kwargs=dict(
                    performative=LedgerApiMessage.Performative.GET_STATE
                ),
                response_kwargs=dict(
                    performative=LedgerApiMessage.Performative.STATE,
                    state=State(ledger_id="ethereum", body={}),
                ),
            )

            self.behaviour.act_wrapper()
        self.behaviour.context.randomness_api.__dict__["_frozen"] = True

    def test_clean_up(
        self,
    ) -> None:
        """Test when `observed` value is none."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.randomness_behaviour_class.auto_behaviour_id(),
            BaseSynchronizedData(AbciAppDB(setup_data={})),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.randomness_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.context.randomness_api.retries_info.retries_attempted = (  # pylint: disable=protected-access
            1
        )
        assert self.behaviour.current_behaviour is not None
        self.behaviour.current_behaviour.clean_up()
        assert (
            self.behaviour.context.randomness_api.retries_info.retries_attempted  # pylint: disable=protected-access
            == 0
        )


class BaseSelectKeeperBehaviourTest(CommonBaseCase):
    """Test SelectKeeperBehaviour."""

    select_keeper_behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[BaseBehaviour]
    done_event: Any
    _synchronized_data: Type[BaseSynchronizedData] = BaseSynchronizedData

    @mock.patch.object(SkillContext, "agent_address", new_callable=mock.PropertyMock)
    @pytest.mark.parametrize(
        "blacklisted_keepers",
        (
            set(),
            {"a_1"},
            {"test_agent_address" + "t" * 24},
            {"a_1" + "t" * 39, "a_2" + "t" * 39, "test_agent_address" + "t" * 24},
        ),
    )
    def test_select_keeper(
        self, agent_address_mock: mock.Mock, blacklisted_keepers: Set[str]
    ) -> None:
        """Test select keeper agent."""
        agent_address_mock.return_value = "test_agent_address" + "t" * 24
        participants = (
            self.skill.skill_context.agent_address,
            "a_1" + "t" * 39,
            "a_2" + "t" * 39,
        )
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.select_keeper_behaviour_class.auto_behaviour_id(),
            synchronized_data=self._synchronized_data(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            participants=participants,
                            most_voted_randomness="56cbde9e9bbcbdcaf92f183c678eaa5288581f06b1c9c7f884ce911776727688",
                            blacklisted_keepers="".join(blacklisted_keepers),
                        )
                    ),
                )
            ),
        )
        assert self.behaviour.current_behaviour is not None
        assert (
            self.behaviour.current_behaviour.behaviour_id
            == self.select_keeper_behaviour_class.auto_behaviour_id()
        )

        if (
            self.behaviour.current_behaviour.synchronized_data.participants
            - self.behaviour.current_behaviour.synchronized_data.blacklisted_keepers
        ):
            self.behaviour.act_wrapper()
            self.mock_a2a_transaction()
            self._test_done_flag_set()
            self.end_round(self.done_event)
            assert (
                self.behaviour.current_behaviour.behaviour_id
                == self.next_behaviour_class.auto_behaviour_id()
            )
        else:
            with pytest.raises(
                AEAActException,
                match="Cannot continue if all the keepers have been blacklisted!",
            ):
                self.behaviour.act_wrapper()

    def test_select_keeper_preexisting_keeper(
        self,
    ) -> None:
        """Test select keeper agent."""
        participants = (self.skill.skill_context.agent_address, "a_1", "a_2")
        preexisting_keeper = next(iter(participants))
        self.fast_forward_to_behaviour(
            behaviour=self.behaviour,
            behaviour_id=self.select_keeper_behaviour_class.auto_behaviour_id(),
            synchronized_data=self._synchronized_data(
                AbciAppDB(
                    setup_data=dict(
                        participants=[participants],
                        most_voted_randomness=[
                            "56cbde9e9bbcbdcaf92f183c678eaa5288581f06b1c9c7f884ce911776727688"
                        ],
                        most_voted_keeper_address=[preexisting_keeper],
                    ),
                )
            ),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.select_keeper_behaviour_class.auto_behaviour_id()
        )
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(self.done_event)
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.auto_behaviour_id()
