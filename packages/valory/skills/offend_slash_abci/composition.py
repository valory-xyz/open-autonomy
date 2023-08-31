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

"""This module contains the offend_slash_abci application."""

import packages.valory.skills.offend_abci.rounds as OffendAbci
import packages.valory.skills.registration_abci.rounds as RegistrationAbci
import packages.valory.skills.reset_pause_abci.rounds as ResetAndPauseAbci
from packages.valory.skills.abstract_round_abci.abci_app_chain import (
    AbciAppTransitionMapping,
    chain,
)
from packages.valory.skills.abstract_round_abci.base import BackgroundAppConfig
from packages.valory.skills.slashing_abci.composition import SlashingAbciApp
from packages.valory.skills.slashing_abci.rounds import Event, SlashingCheckRound


abci_app_transition_mapping: AbciAppTransitionMapping = {
    RegistrationAbci.FinishedRegistrationRound: OffendAbci.OffendRound,
    OffendAbci.FinishedOffendRound: ResetAndPauseAbci.ResetAndPauseRound,
    ResetAndPauseAbci.FinishedResetAndPauseRound: OffendAbci.OffendRound,
    ResetAndPauseAbci.FinishedResetAndPauseErrorRound: ResetAndPauseAbci.ResetAndPauseRound,
}

slashing_config = BackgroundAppConfig(
    round_cls=SlashingCheckRound,
    start_event=Event.SLASH_START,
    end_event=Event.SLASH_END,
    abci_app=SlashingAbciApp,
)

OffendSlashAbciApp = chain(
    (
        RegistrationAbci.AgentRegistrationAbciApp,
        OffendAbci.OffendAbciApp,
        ResetAndPauseAbci.ResetPauseAbciApp,
    ),
    abci_app_transition_mapping,
).add_background_app(slashing_config)
