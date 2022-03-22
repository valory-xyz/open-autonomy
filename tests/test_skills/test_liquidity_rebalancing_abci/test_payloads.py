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

"""Test the payloads.py module of the skill."""

from packages.valory.skills.liquidity_rebalancing_abci.payloads import (
    StrategyEvaluationPayload,
    StrategyType,
    TransactionType,
)


def test_strategy_evaluation_payload() -> None:
    """Test `StrategyEvaluationPayload`."""

    strategy = {
        "action": StrategyType.ENTER.value,
        "pair": ["FTM", "BOO"],
        "pool": "0x0000000000000000000000000000",
        "amountETH": 0.1,  # Be careful with floats and determinism here
    }
    payload = StrategyEvaluationPayload(sender="sender", strategy=str(strategy))

    assert payload.sender == "sender"
    assert payload.data == {"strategy": str(strategy)}
    assert payload.transaction_type == TransactionType.STRATEGY_EVALUATION
