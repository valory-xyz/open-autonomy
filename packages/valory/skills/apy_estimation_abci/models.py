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

"""Custom objects for the APY estimation ABCI application."""
from typing import Any, Dict, List, Optional, Set, Union, ValuesView, cast

from aea.skills.base import SkillContext

from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.apy_estimation_abci.rounds import APYEstimationAbciApp


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=APYEstimationAbciApp, **kwargs)


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""


class FantomSubgraph(ApiSpecs):
    """A model that wraps ApiSpecs for Fantom subgraph specifications."""


class ETHSubgraph(ApiSpecs):
    """A model that wraps ApiSpecs for ETH subgraph specifications."""


class DEXSubgraph(ApiSpecs):
    """A model that wraps ApiSpecs for DEX subgraph specifications."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize DEX Subgraph."""
        self.bundle_id: int = self.ensure("bundle_id", kwargs)
        self.chain_subgraph_name = self.ensure("chain_subgraph", kwargs)
        self.non_indexed_error_key = kwargs.pop("non_indexed_error_key", "errors")
        self.non_indexed_error_type = kwargs.pop("non_indexed_error_type", "list")
        super().__init__(*args, **kwargs)

    def process_non_indexed_error(self, response: HttpMessage) -> Any:
        """Process a non-indexed block error response from the subgraph."""
        return self._get_response_data(
            response, self.non_indexed_error_key, self.non_indexed_error_type
        )


class UniswapSubgraph(DEXSubgraph):
    """A model that wraps DEXSubgraph for Uniswap subgraph specifications."""


class SpookySwapSubgraph(DEXSubgraph):
    """A model that wraps DEXSubgraph for SpookySwap subgraph specifications."""


# This is a `List` that contains `List`s, which contain two items.
# The first one is the DEX name and the second one is a `List` with the corresponding DEX's id `str`s.
# This is a temporary hack until we fix the limitation with the dict override in the agent config.
# This type should be removed when https://github.com/valory-xyz/open-aea/issues/270 is closed.
HackyPairIdsType = List[List[Union[str, List[str]]]]
PairIdsType = Dict[str, List[str]]
ValidatedSubgraphType = Union[DEXSubgraph, ApiSpecs]
ValidatedSubgraphsType = ValuesView[ValidatedSubgraphType]
ValidatedSubgraphsMappingType = Dict[str, ValidatedSubgraphType]
UnvalidatedSubgraphType = Optional[ValidatedSubgraphType]
UnvalidatedSubgraphsMappingType = Dict[str, UnvalidatedSubgraphType]


class SubgraphsMixin:
    """A mixin to handle the subgraphs' information."""

    _necessary_attributes = {"context.params.pair_ids"}
    context: SkillContext

    def __init__(self) -> None:
        """Initialize the mixin object."""
        self._check_attributes()
        utilized_dex_names = set(self.context.params.pair_ids.keys())
        utilized_dex_subgraphs = self._get_subgraphs_mapping(utilized_dex_names)
        utilized_block_names = {
            dex.chain_subgraph_name
            for dex in utilized_dex_subgraphs.values()
            if dex is not None
        }
        utilized_block_subgraphs = self._get_subgraphs_mapping(utilized_block_names)
        self._utilized_subgraphs = {
            **utilized_dex_subgraphs,
            **utilized_block_subgraphs,
        }
        self._validate_utilized_subgraphs()

    def _check_attributes(self) -> None:
        """Checks that the Mixin is subclassed by a class which has the necessary attributes."""
        missing_attrs = []
        for attr in self._necessary_attributes:
            part_checked_so_far, path_so_far = self, ""
            for part in attr.split("."):
                try:
                    path_so_far += f"{part}"
                    part_checked_so_far = getattr(part_checked_so_far, part)
                except AttributeError:
                    missing_attrs.append(path_so_far)
                finally:
                    path_so_far += "."

        if missing_attrs:
            raise AttributeError(
                f"`SubgraphsMixin` is missing attribute(s): {missing_attrs}."
            )

    def _validate_utilized_subgraphs(self) -> None:
        """Check that the utilized subgraphs are valid, i.e., they are defined in the `skill.yaml` config file."""
        unknown_subgraphs = {
            name
            for name, subgraph in self._utilized_subgraphs.items()
            if subgraph is None
        }
        if unknown_subgraphs:
            raise ValueError(
                f"Subgraph(s) {unknown_subgraphs} not recognized. "
                "Please specify them in the `skill.yaml` config file and `models.py`."
            )

    def _get_subgraphs_mapping(
        self, names: Set[str]
    ) -> UnvalidatedSubgraphsMappingType:
        """Get subgraphs mapped to their names."""
        return {name: self._try_get_subgraph(name) for name in names}

    def _try_get_subgraph(self, name: str) -> UnvalidatedSubgraphType:
        """Try to get a subgraph by its name. If it does not exist, return `None`"""
        return getattr(self.context, name, None)

    def get_subgraph(self, name: str) -> ValidatedSubgraphType:
        """Get a subgraph by its name. If it does not exist, an `AttributeError` is raised."""
        return getattr(self.context, name)

    @property
    def utilized_subgraphs(self) -> ValidatedSubgraphsType:
        """Get the utilized Subgraphs."""
        return cast(ValidatedSubgraphsMappingType, self._utilized_subgraphs).values()


def _raise_incorrect_hacky_initialization() -> None:
    """
    Raise a `ValueError` when the pair ids hacky initialization is incorrect.

    Please also take a look at the discussion here:
    https://github.com/valory-xyz/open-autonomy/pull/1171#discussion_r938924806
    This method should be removed when https://github.com/valory-xyz/open-aea/issues/270 is closed.
    """
    raise ValueError(
        "Pair ids have been incorrectly configured. Please consider: https://github.com/valory-xyz/open-aea/issues/270."
    )


def _validate_parsed_hacky_pair_ids(pair_ids: PairIdsType) -> None:
    """
    Validate the parsed hacky initialized pair ids.

    Please also take a look at the discussion here:
    https://github.com/valory-xyz/open-autonomy/pull/1171#discussion_r938924806
    This method should be removed when https://github.com/valory-xyz/open-aea/issues/270 is closed.

    :param pair_ids: the parsed hacky pair ids to validate.
    """
    for dex_name, dex_ids in pair_ids.items():
        if not isinstance(dex_name, str) or not isinstance(dex_ids, list):
            _raise_incorrect_hacky_initialization()
        for dex_id in dex_ids:
            if not isinstance(dex_id, str):
                _raise_incorrect_hacky_initialization()


def _hack_around_dict_override_limitation(pair_ids: HackyPairIdsType) -> PairIdsType:
    """
    Temporary hack to overcome the dict override limitation in the agent's config.

    Please also take a look at the discussion here:
    https://github.com/valory-xyz/open-autonomy/pull/1171#discussion_r938924806
    This method should be removed when https://github.com/valory-xyz/open-aea/issues/270 is closed.

    :param pair_ids: the hacky pair ids to parse to their normal dict representation.
    :return: the parsed pair ids.
    """
    ids: Dict[str, List[str]] = {}

    try:
        ids = {
            # here we make the assumption that the first item contains the key and the second the `list` of `str` values
            str(dex_config[i]): cast(List[str], dex_config[i + 1])
            for dex_config in pair_ids
            for i in range(0, len(dex_config), 2)
        }
    except IndexError:
        _raise_incorrect_hacky_initialization()
    else:
        _validate_parsed_hacky_pair_ids(ids)

    return ids


class APYParams(BaseParams):  # pylint: disable=too-many-instance-attributes
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.start: int = self._ensure("history_start", kwargs)
        self.end: Optional[int] = kwargs.pop("history_end", None)
        self.interval: int = self._ensure("history_interval_in_unix", kwargs)
        self.optimizer_params: Dict[
            str, Union[None, bool, int, float, str]
        ] = self._ensure("optimizer", kwargs)
        self.testing = self._ensure("testing", kwargs)
        self.estimation = self._ensure("estimation", kwargs)
        pair_ids: HackyPairIdsType = self._ensure("pair_ids", kwargs)
        self.pair_ids: PairIdsType = _hack_around_dict_override_limitation(pair_ids)
        self.ipfs_domain_name = self._ensure("ipfs_domain_name", kwargs)
        super().__init__(*args, **kwargs)

        self.__validate_params()

    def __validate_params(self) -> None:
        """Validate the given parameters."""
        # Eventually, we should probably validate all the parameters.
        for param_name in ("timeout", "window_size"):
            param_val = self.optimizer_params.get(param_name)
            if param_val is not None and not isinstance(param_val, int):
                raise ValueError(
                    f"Optimizer's parameter `{param_name}` can be either of type `int` or `None`. "
                    f"{type(param_val)} was given."
                )
            # if the value did not exist in the config, then we set it to the default (None) returned from `.get` method
            self.optimizer_params[param_name] = param_val
