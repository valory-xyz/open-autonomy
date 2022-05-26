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

from pathlib import Path

from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    make_degenerate_behaviour,
)
from packages.valory.skills.safe_deployment_abci.behaviours import (
    DeploySafeBehaviour,
    RandomnessSafeBehaviour,
    SelectKeeperSafeBehaviour,
    ValidateSafeBehaviour,
)
from packages.valory.skills.safe_deployment_abci.rounds import (
    Event as SafeDeploymentEvent,
)
from packages.valory.skills.safe_deployment_abci.rounds import FinishedSafeRound

from tests.conftest import ROOT_DIR
from tests.test_skills.base import FSMBehaviourBaseCase
from tests.test_skills.test_abstract_round_abci.test_common import (
    BaseRandomnessBehaviourTest,
    BaseSelectKeeperBehaviourTest,
)
from tests.test_skills.test_oracle_deployment_abci.test_behaviours import (
    BaseDeployBehaviourTest,
    BaseValidateBehaviourTest,
)


class SafeDeploymentAbciBaseCase(FSMBehaviourBaseCase):
    """Base case for testing PriceEstimation FSMBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "safe_deployment_abci"
    )


class TestRandomnessSafe(BaseRandomnessBehaviourTest):
    """Test randomness safe."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "safe_deployment_abci"
    )

    randomness_behaviour_class = RandomnessSafeBehaviour
    next_behaviour_class = SelectKeeperSafeBehaviour
    done_event = SafeDeploymentEvent.DONE


class TestSelectKeeperSafeBehaviour(BaseSelectKeeperBehaviourTest):
    """Test SelectKeeperBehaviour."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "valory", "skills", "safe_deployment_abci"
    )

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
