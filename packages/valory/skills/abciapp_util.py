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

"""No flaky"""

from typing import Callable, Type

from packages.valory.skills.abstract_round_abci.base import AbciApp
from packages.valory.skills.apy_estimation_abci.rounds import APYEstimationAbciApp
from packages.valory.skills.liquidity_provision.rounds import LiquidityProvisionAbciApp
from packages.valory.skills.price_estimation_abci.composition import (
    AgentRegistrationAbciApp,
    OracleDeploymentAbciApp,
    PriceAggregationAbciApp,
    PriceEstimationAbciApp,
    SafeDeploymentAbciApp,
    TransactionSubmissionAbciApp,
)
from packages.valory.skills.simple_abci.rounds import SimpleAbciApp


def add_docstring(func: Callable) -> Callable:
    """A decorator for dynamically generating doc strings"""

    def wrapped(cls: Type) -> Type:
        cls.__doc__ = func(cls)
        return cls

    return wrapped


def docstring_abci_app(abci_app: AbciApp) -> str:  # pylint: disable-msg=too-many-locals
    """Generate a docstring for an ABCI app

    This ensures that documentation aligns with the actual implementation
    """

    indent, newline, comma = "    ", "\n", ", "

    states = {state: i for i, state in enumerate(abci_app.transition_function)}

    initial_round = abci_app.initial_round_cls.__name__

    initial_states = [state.__name__ for state in abci_app.initial_states]
    initial_states = initial_states if initial_states else [initial_round]

    final_states = [state.__name__ for state in abci_app.final_states]

    transition_states = []
    for state, transitions in abci_app.transition_function.items():
        transition_states.append(f"{states[state]}. {state.__name__}")
        for event, next_state in transitions.items():
            name = event.value.replace("_", " ")
            transition_states.append(f"{indent}- {name}: {states[next_state]}.")

    timeouts = []
    for event, seconds in abci_app.event_to_timeout.items():
        timeouts.append(f"{indent}{event.value.replace('_', ' ')}: {seconds}")

    docstring = (
        f"{abci_app.__name__}\n\n"  # type: ignore
        f"Initial round: {initial_round}\n\n"
        f"Initial states: {{{comma.join(initial_states)}}}\n\n"
        f"Transition states: \n{newline.join(transition_states)}\n\n"
        f"Final states: {{{comma.join(final_states)}}}\n\n"
        f"Timeouts: \n{newline.join(timeouts)}"
    )

    return docstring


def show_docstring_abci_apps() -> None:
    """No flaky"""

    abci_apps = [
        APYEstimationAbciApp,
        LiquidityProvisionAbciApp,
        OracleDeploymentAbciApp,
        PriceAggregationAbciApp,
        AgentRegistrationAbciApp,
        SafeDeploymentAbciApp,
        SimpleAbciApp,
        TransactionSubmissionAbciApp,
    ]

    for abci_app in abci_apps:
        print(docstring_abci_app(abci_app))  # type: ignore


def show_decorating_chained_FSM() -> None:
    """No flaky"""

    @add_docstring(docstring_abci_app)
    class ShowCase(PriceEstimationAbciApp):  # type: ignore
        """Showcase decorator"""

    help(ShowCase)
