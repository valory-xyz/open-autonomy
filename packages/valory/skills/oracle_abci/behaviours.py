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

"""This module contains the behaviours for the 'abci' skill."""

from typing import Set, Type

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.oracle_abci.composition import OracleAbciApp
from packages.valory.skills.oracle_deployment_abci.behaviours import (
    OracleDeploymentRoundBehaviour,
)
from packages.valory.skills.price_estimation_abci.behaviours import (
    ObserverRoundBehaviour,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)
from packages.valory.skills.safe_deployment_abci.behaviours import (
    SafeDeploymentRoundBehaviour,
)
from packages.valory.skills.transaction_settlement_abci.behaviours import (
    TransactionSettlementRoundBehaviour,
)


class OracleAbciAppConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_behaviour_cls = RegistrationStartupBehaviour
    abci_app_cls = OracleAbciApp  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = {
        *OracleDeploymentRoundBehaviour.behaviours,
        *AgentRegistrationRoundBehaviour.behaviours,
        *SafeDeploymentRoundBehaviour.behaviours,
        *TransactionSettlementRoundBehaviour.behaviours,
        *ResetPauseABCIConsensusBehaviour.behaviours,
        *ObserverRoundBehaviour.behaviours,
    }
