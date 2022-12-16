# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the register-reset ABCI application."""

from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.register_reset_recovery_abci.rounds import (
    RoundCountAbciApp,
    RoundCountRound,
)
from packages.valory.skills.registration_abci.rounds import (
    AgentRegistrationAbciApp,
    FinishedRegistrationFFWRound,
    FinishedRegistrationRound,
)


abci_app_transition_mapping: AbciAppTransitionMapping = {
    FinishedRegistrationRound: RoundCountRound,
    FinishedRegistrationFFWRound: RoundCountRound,
}

RegisterResetRecoveryAbciApp = chain(
    (
        AgentRegistrationAbciApp,
        RoundCountAbciApp,
    ),
    abci_app_transition_mapping,
)
