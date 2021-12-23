# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This module contains the the price estimation ABCI application."""

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.common_apps.rounds import (
    AgentRegistrationAbciApp,
    FailedRound,
    FinishedRegistrationFFWRound,
    FinishedRegistrationRound,
    FinishedTransactionSubmissionRound,
    RandomnessTransactionSubmissionRound,
    RegistrationRound,
    TransactionSubmissionAbciApp,
)
from packages.valory.skills.oracle_deployment_abci.rounds import (
    FinishedOracleRound,
    OracleDeploymentAbciApp,
    RandomnessOracleRound,
)
from packages.valory.skills.price_estimation_abci.rounds import (
    CollectObservationRound,
    FinishedPriceAggregationRound,
    PriceAggregationAbciApp,
)
from packages.valory.skills.safe_deployment_abci.rounds import (
    FinishedSafeRound,
    RandomnessSafeRound,
    SafeDeploymentAbciApp,
)


abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: RandomnessSafeRound,
    FinishedSafeRound: RandomnessOracleRound,
    FinishedOracleRound: CollectObservationRound,
    FinishedRegistrationFFWRound: CollectObservationRound,
    FinishedPriceAggregationRound: RandomnessTransactionSubmissionRound,
    FinishedTransactionSubmissionRound: CollectObservationRound,
    FailedRound: RegistrationRound,
}

PriceEstimationAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        SafeDeploymentAbciApp,
        OracleDeploymentAbciApp,
        PriceAggregationAbciApp,
        TransactionSubmissionAbciApp,
    ),
    abci_app_transition_mapping,
)
