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

# pylint: skip-file

import ast
import logging  # noqa: F401
import re
import time
from typing import Dict, List, Tuple, Type, cast

import pytest
import requests
from _pytest.fixtures import FixtureRequest

from packages.valory.protocols.http import HttpMessage
from packages.valory.skills.abstract_round_abci.models import ApiSpecs
from packages.valory.skills.abstract_round_abci.test_tools.apis import DummyMessage
from packages.valory.skills.apy_estimation_abci.behaviours import NON_INDEXED_BLOCK_RE
from packages.valory.skills.apy_estimation_abci.models import (
    DEXSubgraph,
    ETHSubgraph,
    FantomSubgraph,
    SpookySwapSubgraph,
    UniswapSubgraph,
)
from packages.valory.skills.apy_estimation_abci.tests.conftest import (
    SpecsType,
    is_list_of_strings,
)


ResponseItemType = List[Dict[str, str]]
SubgraphResponseType = Dict[str, ResponseItemType]


def __make_request_no_retries(
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


def make_request(
    api_specs: Dict,
    query: str,
    raise_on_error: bool = True,
    allowed_retries: int = 5,
    backoff_factor: int = 1,
) -> requests.Response:
    """Make a request using retries."""
    for i in range(allowed_retries):
        n_tries = i + 1
        try:
            return __make_request_no_retries(api_specs, query, raise_on_error)
        except (ValueError, ConnectionError) as e:
            retry_in = backoff_factor * n_tries
            print(
                f"Trial {n_tries}/{allowed_retries} failed. Retrying the request in {retry_in} secs. "
                f"Received an exception:\n{e}"
            )
            time.sleep(retry_in)


class TestSubgraphs:
    """Test for subgraphs."""

    @staticmethod
    @pytest.mark.parametrize(
        "dex_subgraph, specs_fixture, expected_res_fixture",
        (
            (
                SpookySwapSubgraph,
                "spooky_specs_price_extended",
                "spooky_expected_eth_price_usd",
            ),
            (
                UniswapSubgraph,
                "uni_specs_price_extended",
                "uni_expected_eth_price_usd",
            ),
        ),
    )
    def test_eth_price(
        dex_subgraph: Type[ApiSpecs],
        specs_fixture: str,
        expected_res_fixture: str,
        eth_price_usd_q: str,
        request: FixtureRequest,
    ) -> None:
        """Test SpookySwap's eth price request from subgraph."""
        specs: SpecsType = request.getfixturevalue(specs_fixture)
        expected_res: float = request.getfixturevalue(expected_res_fixture)
        api = dex_subgraph(**specs)

        res = make_request(api.get_spec(), eth_price_usd_q)
        eth_price = ast.literal_eval(api.process_response(DummyMessage(res.content))[0]["ethPrice"])  # type: ignore

        assert eth_price == expected_res

    @staticmethod
    @pytest.mark.parametrize(
        "dex_subgraph, specs_fixture",
        (
            (
                SpookySwapSubgraph,
                "spooky_specs_price_extended",
            ),
            (
                UniswapSubgraph,
                "uni_specs_price_extended",
            ),
        ),
    )
    def test_eth_price_non_indexed_block(
        dex_subgraph: Type[DEXSubgraph],
        specs_fixture: str,
        eth_price_usd_raising_q: str,
        largest_acceptable_block_number: int,
        request: FixtureRequest,
    ) -> None:
        """Test SpookySwap's eth price request from subgraph, when the requesting block has not been indexed yet."""
        specs: SpecsType = request.getfixturevalue(specs_fixture)
        specs["response_key"] = "errors"
        api = dex_subgraph(**specs)

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
    @pytest.mark.parametrize("from_", ("timestamp", "number"))
    @pytest.mark.parametrize(
        "block_subgraph, specs_fixture, expected_res_fixture",
        (
            (
                FantomSubgraph,
                "fantom_specs_blocks_extended",
                "expected_fantom_block",
            ),
            (
                ETHSubgraph,
                "eth_specs_blocks_extended",
                "expected_eth_block",
            ),
        ),
    )
    def test_block_qs(
        from_: str,
        block_subgraph: Type[ApiSpecs],
        specs_fixture: str,
        expected_res_fixture: str,
        expected_block_q_res_keys: List[str],
        request: FixtureRequest,
    ) -> None:
        """Test Fantom's block from timestamp request from subgraph."""
        block_query_fixture = f"block_from_{from_}_q"
        query: str = request.getfixturevalue(block_query_fixture)
        specs: SpecsType = request.getfixturevalue(specs_fixture)
        expected_res_fixture += f"_from_{from_}"
        expected_res: Dict[str, str] = request.getfixturevalue(expected_res_fixture)

        api = block_subgraph(**specs)
        res = make_request(api.get_spec(), query)
        block = api.process_response(DummyMessage(res.content))[0]  # type: ignore

        assert isinstance(block, dict)
        assert all((key in block for key in expected_block_q_res_keys))
        assert all(
            isinstance(ast.literal_eval(block[key]), int)
            for key in expected_block_q_res_keys
        )
        assert block == expected_res

    @staticmethod
    @pytest.mark.parametrize(
        "dex_subgraph, specs_fixture",
        (
            (
                SpookySwapSubgraph,
                "spooky_specs_pairs_extended",
            ),
            (
                UniswapSubgraph,
                "uni_specs_pairs_extended",
            ),
        ),
    )
    def test_top_n_pairs(
        dex_subgraph: Type[ApiSpecs],
        specs_fixture: str,
        top_n_pairs_q: str,
        request: FixtureRequest,
    ) -> None:
        """Test SpookySwap's top n pairs request from subgraph."""
        specs: SpecsType = request.getfixturevalue(specs_fixture)
        api = dex_subgraph(**specs)

        res = make_request(specs, top_n_pairs_q)
        pair_ids = [pair["id"] for pair in api.process_response(DummyMessage(res.content))]  # type: ignore

        assert is_list_of_strings(pair_ids)

    @staticmethod
    @pytest.mark.parametrize(
        "dex_subgraph, query_fixture, specs_fixture",
        (
            (
                SpookySwapSubgraph,
                "spooky_pairs_q",
                "spooky_specs_pairs_extended",
            ),
            (
                SpookySwapSubgraph,
                "spooky_existing_pairs_q",
                "spooky_specs_pairs_extended",
            ),
            (
                UniswapSubgraph,
                "uni_pairs_q",
                "uni_specs_pairs_extended",
            ),
            (
                UniswapSubgraph,
                "uni_existing_pairs_q",
                "uni_specs_pairs_extended",
            ),
        ),
    )
    def test_pairs(
        dex_subgraph: Type[ApiSpecs],
        specs_fixture: str,
        query_fixture: str,
        pool_fields: Tuple[str, ...],
        pairs_ids: Dict[str, List[str]],
        request: FixtureRequest,
    ) -> None:
        """Test SpookySwap's pairs request from subgraph."""
        specs: SpecsType = request.getfixturevalue(specs_fixture)
        query: str = request.getfixturevalue(query_fixture)
        api = dex_subgraph(**specs)

        res = make_request(api.get_spec(), query)
        pairs = api.process_response(DummyMessage(res.content))  # type: ignore

        assert isinstance(pairs, list)
        assert len(pairs) > 0
        assert isinstance(pairs[0], dict)

        if "existing" in query_fixture:
            assert pairs == [{"id": id_} for id_ in pairs_ids[api.name]]
            return

        for pair in pairs:
            assert all((key in pair for key in pool_fields))
