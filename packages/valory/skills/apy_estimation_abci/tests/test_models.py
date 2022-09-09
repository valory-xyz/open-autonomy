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

# pylint: skip-file

import re
from copy import deepcopy
from typing import Any, Dict, List, Tuple, Type, Union
from unittest.mock import MagicMock

import pytest

from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.apy_estimation_abci.models import (
    APYParams,
    SharedState,
    SpookySwapSubgraph,
    SubgraphsMixin,
)
from packages.valory.skills.apy_estimation_abci.rounds import APYEstimationAbciApp


try:
    from typing import TypedDict  # >=3.8
except ImportError:
    from mypy_extensions import TypedDict  # <=3.7

APYParamsArgsType = Tuple[str, MagicMock]


class APYParamsKwargsType(TypedDict):
    """Typed dict for the APY kwargs."""

    tendermint_url: str
    tendermint_com_url: str
    tendermint_check_sleep_delay: str
    tendermint_max_retries: str
    reset_tendermint_after: str
    ipfs_domain_name: str
    consensus: Dict[str, int]
    max_healthcheck: str
    round_timeout_seconds: str
    sleep_time: str
    retry_attempts: str
    retry_timeout: str
    observation_interval: str
    drand_public_key: str
    history_interval_in_unix: int
    history_start: int
    optimizer: Dict[str, Union[None, str, int]]
    testing: str
    estimation: str
    pair_ids: Dict[str, List[str]]
    service_id: str
    service_registry_address: str
    keeper_timeout: float
    cleanup_history_depth: int
    backwards_compatible: bool
    decimals: int


APY_PARAMS_ARGS: APYParamsArgsType = ("test", MagicMock())
APY_PARAMS_KWARGS = APYParamsKwargsType(
    tendermint_url="test",
    tendermint_com_url="test",
    tendermint_check_sleep_delay="test",
    tendermint_max_retries="test",
    reset_tendermint_after="test",
    ipfs_domain_name="test",
    consensus={"max_participants": 0},
    max_healthcheck="test",
    round_timeout_seconds="test",
    sleep_time="test",
    retry_attempts="test",
    retry_timeout="test",
    observation_interval="test",
    drand_public_key="test",
    history_interval_in_unix=86400,
    history_start=1652544875,
    optimizer={"timeout": 0, "window_size": 0},
    testing="test",
    estimation="test",
    pair_ids={"test": ["not_supported"], "spooky_subgraph": ["supported"]},
    service_id="apy_estimation",
    service_registry_address="0xa51c1fc2f0d1a1b8494ed1fe312d7c3a78ed91c0",
    keeper_timeout=30.0,
    cleanup_history_depth=0,
    backwards_compatible=False,
    decimals=5,
)


class TestSharedState:
    """Test SharedState(Model) class."""

    def test_setup(
        self,
        shared_state: SharedState,
    ) -> None:
        """Test setup."""
        shared_state.context.params.setup_params = {"test": []}
        shared_state.context.params.consensus_params = MagicMock()
        shared_state.setup()
        assert shared_state.abci_app_cls == APYEstimationAbciApp


class TestAPYParams:
    """Test `APYParams`"""

    @staticmethod
    @pytest.mark.parametrize("param_value", (None, "not_an_int", 0))
    def test__validate_params(param_value: Union[None, str, int]) -> None:
        """Test `__validate_params`."""
        args = APY_PARAMS_ARGS
        # TypedDict can’t be used for specifying the type of a **kwargs argument: https://peps.python.org/pep-0589/
        kwargs: dict = deepcopy(APY_PARAMS_KWARGS)  # type: ignore
        kwargs["optimizer"]["timeout"] = param_value
        kwargs["optimizer"]["window_size"] = param_value

        if param_value is not None and not isinstance(param_value, int):
            with pytest.raises(ValueError):
                APYParams(*args, **kwargs)

            kwargs["optimizer"]["timeout"] = "None"  # type: ignore

            with pytest.raises(ValueError):
                APYParams(*args, **kwargs)

            return

        apy_params = APYParams(*args, **kwargs)
        assert apy_params.optimizer_params["timeout"] is param_value
        assert apy_params.optimizer_params["window_size"] is param_value


class TestSubgraphsMixin:
    """Test `SubgraphsMixin`."""

    class DummyMixinUsage(APYParams, SubgraphsMixin):
        """Dummy class that utilizes the `SubgraphsMixin`."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Initialize `APYEstimationBaseBehaviour`."""
            super().__init__(*args, **kwargs)
            subgraph_args = ["spooky_name", MagicMock()]
            subgraph_kwargs = {
                "url": "url",
                "api_id": "spooky_api_id",
                "method": "method",
                "bundle_id": 0,
                "chain_subgraph": "chain_subgraph",
            }
            self.context.test = None
            self.context.spooky_subgraph = SpookySwapSubgraph(
                *subgraph_args, **subgraph_kwargs
            )
            subgraph_args[0] = "chain_name"
            subgraph_kwargs["api_id"] = "chain_api_id"
            self.context.chain_subgraph = ApiSpecs(*subgraph_args, **subgraph_kwargs)
            self.context.params = MagicMock(pair_ids=self.pair_ids)
            SubgraphsMixin.__init__(self)

    dummy_mixin_usage: DummyMixinUsage

    @classmethod
    def setup_class(cls) -> None:
        """Initialize a `TestSubgraphsMixin`."""
        # TypedDict can’t be used for specifying the type of a **kwargs argument: https://peps.python.org/pep-0589/
        kwargs: dict = deepcopy(APY_PARAMS_KWARGS)  # type: ignore
        del kwargs["pair_ids"]["test"]
        cls.dummy_mixin_usage = TestSubgraphsMixin.DummyMixinUsage(
            *APY_PARAMS_ARGS, **kwargs
        )

    @staticmethod
    def test_incorrect_initialization() -> None:
        """Test `SubgraphsMixin`'s `__init__` when not subclassed properly."""
        with pytest.raises(
            AttributeError,
            match=re.escape(
                "`SubgraphsMixin` is missing attribute(s): "
                "['context', 'context.params', 'context.params.pair_ids']."
            ),
        ):
            SubgraphsMixin()

    @staticmethod
    def test_initialization_unsupported_subgraph() -> None:
        """Test `SubgraphsMixin`'s `__init__` when subclassed properly, but an unsupported subgraph is given."""
        # TypedDict can’t be used for specifying the type of a **kwargs argument: https://peps.python.org/pep-0589/
        kwargs: dict = deepcopy(APY_PARAMS_KWARGS)  # type: ignore

        with pytest.raises(
            ValueError,
            match=re.escape(
                "Subgraph(s) {'test'} not recognized. "
                "Please specify them in the `skill.yaml` config file and `models.py`."
            ),
        ):
            TestSubgraphsMixin.DummyMixinUsage(*APY_PARAMS_ARGS, **kwargs)

    @pytest.mark.parametrize(
        "subgraph, name, id_",
        (
            ("spooky_subgraph", "spooky_name", "spooky_api_id"),
            ("chain_subgraph", "chain_name", "chain_api_id"),
        ),
    )
    def test_initialization(self, subgraph: str, name: str, id_: str) -> None:
        """Test `SubgraphsMixin`'s `__init__` when subclassed properly, and only unsupported subgraphs are given."""
        assert subgraph in self.dummy_mixin_usage._utilized_subgraphs.keys()
        subgraph_instance = getattr(self.dummy_mixin_usage.context, subgraph)
        assert isinstance(subgraph_instance, ApiSpecs)
        assert subgraph_instance.name == name
        assert subgraph_instance.api_id == id_

    def test_utilized_subgraphs(self) -> None:
        """Test `utilized_subgraphs` property."""
        assert [
            subgraph.name for subgraph in self.dummy_mixin_usage.utilized_subgraphs
        ] == ["spooky_name", "chain_name"]

    @pytest.mark.parametrize(
        "subgraph, name, type_, id_",
        (
            ("spooky_subgraph", "spooky_name", SpookySwapSubgraph, "spooky_api_id"),
            ("chain_subgraph", "chain_name", ApiSpecs, "chain_api_id"),
        ),
    )
    def test_get_subgraph(
        self, subgraph: str, name: str, type_: Type[ApiSpecs], id_: str
    ) -> None:
        """Test `get_subgraph` method."""
        subgraph_instance = self.dummy_mixin_usage.get_subgraph(subgraph)
        assert subgraph_instance == getattr(self.dummy_mixin_usage.context, subgraph)
        assert type(subgraph_instance) == type_
        assert subgraph_instance.name == name
        assert subgraph_instance.api_id == id_
