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

"""Test various price apis."""
import logging  # noqa: F401
from typing import Dict, List

import requests

from packages.valory.skills.apy_estimation.models import SpookySwapSubgraph, FantomSubgraph
from tests.test_skills.test_abstract_round_abci.test_models import DummyMessage
from tests.test_skills.test_apy_estimation.conftest import SpecsType, is_list_of_strings

ResponseItemType = List[Dict[str, str]]
SubgraphResponseType = Dict[str, ResponseItemType]


def make_request(api_specs: Dict, query: str) -> requests.Response:
    """Make a request to a subgraph.

    Args:
        api_specs: the subgraph's api_specs.
        query: the query.

    Returns:
        a response dictionary.
    """
    if api_specs["method"] == "POST":
        r = requests.post(url=api_specs["url"], headers=api_specs["headers"], json={'query': query})

        if r.status_code == 200:
            res = r.json()

            if 'errors' in res.keys():
                message = res['errors'][0]['message']
                location = res['errors'][0]['locations'][0]
                line = location['line']
                column = location['column']

                raise ValueError(f'The given query is not correct.\nError in line {line}, column {column}: {message}')

            elif 'data' not in res.keys():
                raise ValueError(f'Unknown error encountered!\nRaw response: {res}')

        else:
            raise ConnectionError('Something went wrong while trying to communicate with the subgraph '
                                  f'(Error: {r.status_code})!\n{r.text}')

    else:
        raise ValueError(f"Unknown method {api_specs['method']} for {api_specs['api_id']}")

    return r


class TestSubgraphs:
    @staticmethod
    def test_eth_price(spooky_specs: SpecsType, eth_price_usd_q: str) -> None:
        """Test SpookySwap's eth price request from subgraph."""
        spooky_specs['response_key'] += ':bundles'
        api = SpookySwapSubgraph(**spooky_specs)

        res = make_request(api.get_spec(), eth_price_usd_q)
        eth_price = eval(api.process_response(DummyMessage(res.content))[0]['ethPrice'])  # type: ignore

        assert isinstance(eth_price, float)

    @staticmethod
    def test_block_from_timestamp(fantom_specs: SpecsType, block_from_timestamp_q: str) -> None:
        """Test Fantom's block from timestamp request from subgraph."""
        fantom_specs['response_key'] += ':blocks'
        api = FantomSubgraph(**fantom_specs)

        res = make_request(api.get_spec(), block_from_timestamp_q)
        block = api.process_response(DummyMessage(res.content))[0]  # type: ignore

        assert isinstance(block, dict)
        keys = ['number', 'timestamp']
        assert all((key in block for key in keys))
        assert all(isinstance(eval(block[key]), int) for key in keys)

    @staticmethod
    def test_top_n_pairs(spooky_specs: SpecsType, top_n_pairs_q: str) -> None:
        """Test SpookySwap's top n pairs request from subgraph."""
        spooky_specs['response_key'] += ':pairs'
        api = SpookySwapSubgraph(**spooky_specs)

        res = make_request(api.get_spec(), top_n_pairs_q)
        pair_ids = [pair['id'] for pair in api.process_response(DummyMessage(res.content))]  # type: ignore

        assert is_list_of_strings(pair_ids)

    @staticmethod
    def test_pairs(spooky_specs: SpecsType, pairs_q: str) -> None:
        """Test SpookySwap's pairs request from subgraph."""
        spooky_specs['response_key'] += ':pairs'
        api = SpookySwapSubgraph(**spooky_specs)

        res = make_request(api.get_spec(), pairs_q)
        pairs = api.process_response(DummyMessage(res.content))  # type: ignore

        assert isinstance(pairs, list)
        assert len(pairs) > 0
        assert isinstance(pairs[0], dict)

        keys = (
            'createdAtBlockNumber',
            'createdAtTimestamp',
            'id',
            'liquidityProviderCount',
            'reserve0',
            'reserve1',
            'reserveETH',
            'reserveUSD',
            'token0Price',
            'token1Price',
            'totalSupply',
            'trackedReserveETH',
            'untrackedVolumeUSD',
            'txCount',
            'volumeToken0',
            'volumeToken1',
            'volumeUSD',
            'token0',
            'token1'
        )

        for pair in pairs:
            assert all((key in pair for key in keys))
