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
from pathlib import Path
from typing import Any, Dict, Type, cast

from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    TransactionDigest,
    TransactionReceipt,
)

from packages.open_aea.protocols.signing import SigningMessage
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import AbciAppDB
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseBehaviour,
    make_degenerate_behaviour,
)
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)
from packages.valory.skills.abstract_round_abci.test_tools.common import (
    BaseRandomnessBehaviourTest,
    BaseSelectKeeperBehaviourTest,
)
from packages.valory.skills.safe_deployment_abci.behaviours import (
    DeploySafeBehaviour,
    RandomnessSafeBehaviour,
    SelectKeeperSafeBehaviour,
)
from packages.valory.skills.safe_deployment_abci.behaviours import (
    SynchronizedData as SafeDeploymentSynchronizedData,
)
from packages.valory.skills.safe_deployment_abci.behaviours import ValidateSafeBehaviour
from packages.valory.skills.safe_deployment_abci.rounds import (
    Event as SafeDeploymentEvent,
)
from packages.valory.skills.safe_deployment_abci.rounds import FinishedSafeRound


PACKAGE_DIR = Path(__file__).parent.parent


class BaseValidateBehaviourTest(FSMBehaviourBaseCase):
    """Test ValidateSafeBehaviour."""

    behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[BaseBehaviour]
    synchronized_data_kwargs: Dict
    contract_id: str
    done_event: Any

    def test_validate_behaviour(self) -> None:
        """Run test."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            SafeDeploymentSynchronizedData(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(self.synchronized_data_kwargs)
                ),
            ),
        )
        assert (
            cast(
                BaseBehaviour,
                cast(BaseBehaviour, self.behaviour.current_behaviour),
            ).behaviour_id
            == self.behaviour_class.behaviour_id
        )
        self.behaviour.act_wrapper()
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
            ),
            contract_id=self.contract_id,
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="verify_contract",
                state=ContractApiMessage.State(
                    ledger_id="ethereum", body={"verified": True}
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(self.done_event)
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id


class BaseDeployBehaviourTest(FSMBehaviourBaseCase):
    """Base DeployBehaviourTest."""

    behaviour_class: Type[BaseBehaviour]
    next_behaviour_class: Type[BaseBehaviour]
    synchronized_data_kwargs: Dict
    contract_id: str
    done_event: Any

    def test_deployer_act(
        self,
    ) -> None:
        """Run tests."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        most_voted_keeper_address = self.skill.skill_context.agent_address
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            SafeDeploymentSynchronizedData(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            participants=participants,
                            most_voted_keeper_address=most_voted_keeper_address,
                            **self.synchronized_data_kwargs,
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
            == self.behaviour_class.behaviour_id
        )
        self.behaviour.act_wrapper()

        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ),
            contract_id=self.contract_id,
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_deploy_transaction",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={"contract_address": "safe_contract_address"},
                ),
            ),
        )

        self.mock_signing_request(
            request_kwargs=dict(
                performative=SigningMessage.Performative.SIGN_TRANSACTION,
            ),
            response_kwargs=dict(
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=SignedTransaction(
                    ledger_id="ethereum", body={"hash": "tx_hash"}
                ),
            ),
        )

        self.mock_ledger_api_request(
            request_kwargs=dict(
                performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            ),
            response_kwargs=dict(
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                transaction_digest=TransactionDigest(
                    ledger_id="ethereum", body="tx_hash"
                ),
            ),
        )

        self.mock_ledger_api_request(
            request_kwargs=dict(
                performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                transaction_digest=TransactionDigest(
                    ledger_id="ethereum", body="tx_hash"
                ),
            ),
            response_kwargs=dict(
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=TransactionReceipt(
                    ledger_id="ethereum",
                    receipt={"contractAddress": "stub"},
                    transaction={},
                ),
            ),
        )

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(self.done_event)
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id

    def test_not_deployer_act(
        self,
    ) -> None:
        """Run tests."""
        participants = frozenset({self.skill.skill_context.agent_address, "a_1", "a_2"})
        most_voted_keeper_address = "a_1"
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            SafeDeploymentSynchronizedData(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            participants=participants,
                            most_voted_keeper_address=most_voted_keeper_address,
                            **self.synchronized_data_kwargs,
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
            == self.behaviour_class.behaviour_id
        )
        self.behaviour.act_wrapper()
        self._test_done_flag_set()
        self.end_round(self.done_event)
        time.sleep(1)
        self.behaviour.act_wrapper()
        behaviour = cast(BaseBehaviour, self.behaviour.current_behaviour)
        assert behaviour.behaviour_id == self.next_behaviour_class.behaviour_id


class SafeDeploymentAbciBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = PACKAGE_DIR


class TestRandomnessSafe(BaseRandomnessBehaviourTest):
    """Test randomness safe."""

    path_to_skill = PACKAGE_DIR

    randomness_behaviour_class = RandomnessSafeBehaviour
    next_behaviour_class = SelectKeeperSafeBehaviour
    done_event = SafeDeploymentEvent.DONE


class TestSelectKeeperSafeBehaviour(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    path_to_skill = PACKAGE_DIR

    select_keeper_behaviour_class = SelectKeeperSafeBehaviour
    next_behaviour_class = DeploySafeBehaviour
    done_event = SafeDeploymentEvent.DONE


class TestDeploySafeBehaviour(BaseDeployBehaviourTest, SafeDeploymentAbciBaseCase):
    """Test DeploySafeBehaviour."""

    behaviour_class = DeploySafeBehaviour
    next_behaviour_class = ValidateSafeBehaviour
    synchronized_data_kwargs = dict(safe_contract_address="safe_contract_address")
    contract_id = str(GNOSIS_SAFE_CONTRACT_ID)
    done_event = SafeDeploymentEvent.DONE


class TestValidateSafeBehaviour(BaseValidateBehaviourTest, SafeDeploymentAbciBaseCase):
    """Test ValidateSafeBehaviour."""

    behaviour_class = ValidateSafeBehaviour
    next_behaviour_class = make_degenerate_behaviour(FinishedSafeRound.round_id)
    synchronized_data_kwargs = dict(safe_contract_address="safe_contract_address")
    contract_id = str(GNOSIS_SAFE_CONTRACT_ID)
    done_event = SafeDeploymentEvent.DONE
