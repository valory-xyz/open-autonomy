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

"""Test various price apis."""
import ast
import logging  # noqa: F401
import re
from typing import Dict, List, Tuple, cast

import requests

from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.apy_estimation_abci.behaviours import NON_INDEXED_BLOCK_RE
from packages.valory.skills.apy_estimation_abci.models import (
    FantomSubgraph,
    SpookySwapSubgraph,
)

from tests.test_skills.test_abstract_round_abci.test_models import DummyMessage
from tests.test_skills.test_apy_estimation_abci.conftest import (
    SpecsType,
    is_list_of_strings,
)


ResponseItemType = List[Dict[str, str]]
SubgraphResponseType = Dict[str, ResponseItemType]


def make_request(
    api_specs: Dict, query: str, raise_on_error: bool = True
) -> requests.Response:
    """Make a request to a subgraph.

    :param api_specs: the subgraph's api_specs.
    :param query: the query.
    :param raise_on_error: if the method should raise an exception on error.
    :return: a response dictionary.
    """
    if api_specs["method"] != "POST" and raise_on_error:
        raise ValueError(
            f"Unknown method {api_specs['method']} for {api_specs['api_id']}"
        )

    r = requests.post(
        url=api_specs["url"], headers=api_specs["headers"], json={"query": query}
    )

    if r.status_code != 200 and raise_on_error:
        raise ConnectionError(
            "Something went wrong while trying to communicate with the subgraph "
            f"(Error: {r.status_code})!\n{r.text}"
        )

    res = r.json()

    if (
        "errors" in res.keys()
        and res["errors"][0].get("locations", None) is not None
        and raise_on_error
    ):
        message = res["errors"][0]["message"]
        location = res["errors"][0]["locations"][0]
        line = location["line"]
        column = location["column"]

        raise ValueError(
            f"The given query is not correct.\nError in line {line}, column {column}: {message}"
        )

    if ("errors" in res.keys() or "data" not in res.keys()) and raise_on_error:
        raise ValueError(f"Unknown error encountered!\nRaw response: {res}")

    return r


class TestSubgraphs:
    """Test for subgraphs."""

    @staticmethod
    def test_eth_price(
        spooky_specs: SpecsType, eth_price_usd_q: str, expected_eth_price_usd: float
    ) -> None:
        """Test SpookySwap's eth price request from subgraph."""
        spooky_specs["response_key"] += ":bundles"  # type: ignore
        api = SpookySwapSubgraph(**spooky_specs)

        res = make_request(api.get_spec(), eth_price_usd_q)
        eth_price = ast.literal_eval(api.process_response(DummyMessage(res.content))[0]["ethPrice"])  # type: ignore

        assert eth_price == expected_eth_price_usd

    @staticmethod
    def test_eth_price_non_indexed_block(
        spooky_specs: SpecsType,
        eth_price_usd_q: str,
        eth_price_usd_raising_q: str,
        largest_acceptable_block_number: int,
    ) -> None:
        """Test SpookySwap's eth price request from subgraph, when the requesting block has not been indexed yet."""
        spooky_specs["response_key"] = "errors"
        api = SpookySwapSubgraph(**spooky_specs)

        res = make_request(
            api.get_spec(), eth_price_usd_raising_q, raise_on_error=False
        )
        non_indexed_error = api.process_non_indexed_error(
            cast(HttpMessage, DummyMessage(res.content))
        )[0]["message"]
        match = re.match(NON_INDEXED_BLOCK_RE, non_indexed_error)
        assert match is not None
        latest_indexed_block = match.group(1)
        assert int(latest_indexed_block) < largest_acceptable_block_number

    @staticmethod
    def test_regex_for_indexed_block_capture() -> None:
        """Test the regex for capturing the indexed block."""
        error_message = (
            "Failed to decode `block.number` value: `subgraph QmPJbGjktGa7c4UYWXvDRajPxpuJBSZxeQK5siNT3VpthP has only "
            "indexed up to block number 3730367 and data for block number 3830367 is therefore not yet available`"
        )
        match = re.match(NON_INDEXED_BLOCK_RE, error_message)
        assert match is not None
        assert match.groups() == ("3730367",)

        error_message = "new message 3730367"
        assert re.match(NON_INDEXED_BLOCK_RE, error_message) is None

    @staticmethod
    def test_block_from_timestamp(
        fantom_specs: SpecsType, block_from_timestamp_q: str
    ) -> None:
        """Test Fantom's block from timestamp request from subgraph."""
        fantom_specs["response_key"] += ":blocks"  # type: ignore
        api = FantomSubgraph(**fantom_specs)

        res = make_request(api.get_spec(), block_from_timestamp_q)
        block = api.process_response(DummyMessage(res.content))[0]  # type: ignore

        assert isinstance(block, dict)
        keys = ["number", "timestamp"]
        assert all((key in block for key in keys))
        assert all(isinstance(ast.literal_eval(block[key]), int) for key in keys)
        assert block == {"timestamp": "1652544875", "number": "38234191"}

    @staticmethod
    def test_block_from_number_q(
        fantom_specs: SpecsType, block_from_number_q: str
    ) -> None:
        """Test Fantom's block from number request from subgraph."""
        fantom_specs["response_key"] += ":blocks"  # type: ignore
        api = FantomSubgraph(**fantom_specs)

        res = make_request(api.get_spec(), block_from_number_q)
        block = api.process_response(DummyMessage(res.content))[0]  # type: ignore

        assert isinstance(block, dict)
        keys = ["number", "timestamp"]
        assert all((key in block for key in keys))
        assert all(isinstance(ast.literal_eval(block[key]), int) for key in keys)
        assert block == {"timestamp": "1618485988", "number": "3730360"}

    @staticmethod
    def test_top_n_pairs(spooky_specs: SpecsType, top_n_pairs_q: str) -> None:
        """Test SpookySwap's top n pairs request from subgraph."""
        spooky_specs["response_key"] += ":pairs"  # type: ignore
        api = SpookySwapSubgraph(**spooky_specs)
        api_specs = api.get_spec()
        api_specs["top_n_pools"] = 100

        res = make_request(api_specs, top_n_pairs_q)
        pair_ids = [pair["id"] for pair in api.process_response(DummyMessage(res.content))]  # type: ignore

        assert is_list_of_strings(pair_ids)

    @staticmethod
    def test_pairs(
        spooky_specs: SpecsType, pairs_q: str, pool_fields: Tuple[str, ...]
    ) -> None:
        """Test SpookySwap's pairs request from subgraph."""
        spooky_specs["response_key"] += ":pairs"  # type: ignore
        api = SpookySwapSubgraph(**spooky_specs)

        res = make_request(api.get_spec(), pairs_q)
        pairs = api.process_response(DummyMessage(res.content))  # type: ignore

        assert isinstance(pairs, list)
        assert len(pairs) > 0
        assert isinstance(pairs[0], dict)

        for pair in pairs:
            assert all((key in pair for key in pool_fields))
