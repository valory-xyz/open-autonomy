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

"""Helpers for autonomy tests."""

from typing import Dict, List


def get_dummy_service_config() -> List[Dict]:
    """Returns a dummy service config."""
    return [
        {
            "name": "dummy_service",
            "author": "valory",
            "version": "0.1.0",
            "description": "A set of agents implementing a dummy oracle",
            "aea_version": ">=1.0.0, <2.0.0",
            "license": "Apache-2.0",
            "fingerprint": {
                "README.md": "QmY4bupJmk4BKkFefNCWNEkj3kUtgmraSDNbWFDx4qgbZf"
            },
            "fingerprint_ignore_patterns": [],
            "agent": "valory/oracle:0.1.0:QmXuaeUagpuJ4cRiBHTX9ydSnibPyEbdL23zmGyUuWwMYr",
            "number_of_agents": 1,
        },
        {
            "public_id": "valory/oracle_abci:0.1.0",
            "type": "skill",
            "models": {
                0: [
                    {
                        "price_api": {
                            "args": {
                                "url": "url",
                                "api_id": "api_id",
                                "parameters": None,
                                "response_key": None,
                                "headers": None,
                            }
                        }
                    },
                    {
                        "randomness_api": {
                            "args": {
                                "url": "https://drand.cloudflare.com/public/latest",
                                "api_id": "cloudflare",
                            }
                        }
                    },
                    {
                        "params": {
                            "args": {
                                "observation_interval": 30,
                                "broadcast_to_server": False,
                                "service_registry_address": "address",
                                "on_chain_service_id": 1,
                            }
                        }
                    },
                    {"server_api": {"args": {"url": "url"}}},
                    {"benchmark_tool": {"args": {"log_dir": "/benchmarks"}}},
                ]
            },
        },
    ]
