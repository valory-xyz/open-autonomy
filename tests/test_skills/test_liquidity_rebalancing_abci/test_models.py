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

"""Test the models.py module of the skill."""

from packages.valory.skills.liquidity_rebalancing_abci.models import Params, SharedState

from tests.test_skills.base import DummyContext


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_initialization(
        self,
    ) -> None:
        """Test initialization."""
        SharedState(name="", skill_context=DummyContext())


class TestParams:
    """Test params."""

    def test_initialization(
        self,
    ) -> None:
        """Test initialization."""
        Params(
            name="",
            skill_context=DummyContext(),
            consensus={"max_participants": 1},
            max_healthcheck=10,
            round_timeout_seconds=1,
            sleep_time=1,
            retry_timeout=1,
            retry_attempts=1,
            validate_timeout=1,
            finalize_timeout=1,
            history_check_timeout=1,
            drand_public_key="868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784a9402801af31",
            observation_interval=10,
            setup={},
            reset_tendermint_after=2,
            tendermint_com_url="http://localhost:8080",
            tendermint_url="http://localhost:26657",
            tendermint_max_retries=5,
            tendermint_check_sleep_delay=3,
            service_id="liquidity_rebalancing",
            service_registry_address="0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0",
            keeper_timeout=1.0,
            keeper_allowed_retries=3,
            rebalancing={
                "chain": "Ethereum",
                "token_base_address": "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9",
                "token_base_ticker": "WETH",
                "token_a_address": "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82",
                "token_a_ticker": "TKA",
                "token_b_address": "0x9A676e781A523b5d0C0e43731313A708CB607508",
                "token_b_ticker": "TKB",
                "lp_token_address": "0x50CD56fb094F8f06063066a619D898475dD3EedE",
                "default_minter": "0x0000000000000000000000000000000000000000",
                "ab_pool_address": "0x86A6C37D3E868580a65C723AAd7E0a945E170416",
                "max_allowance": 1.1579209e77,  # 2**256 - 1
                "deadline": 300,  # 5 min into the future"
                "sleep_seconds": 60,
            },
            cleanup_history_depth=0,
        )
