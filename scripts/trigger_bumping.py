# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 Valory AG
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

"""Trigger automated bumping flow."""

import json
import os
import sys
import typing as t

import requests
from aea import __version__ as aea_version

from autonomy import __version__ as autonomy_version


def get_dependencies() -> t.Dict:
    """Get dependencies."""
    return {
        "open-aea": f"=={aea_version}",
        "open-aea-ledger-ethereum": f"=={aea_version}",
        "open-aea-ledger-ethereum-flashbots": f"=={aea_version}",
        "open-aea-ledger-ethereum-hwi": f"=={aea_version}",
        "open-aea-ledger-cosmos": f"=={aea_version}",
        "open-aea-ledger-solana": f"=={aea_version}",
        "open-aea-cli-ipfs": f"=={aea_version}",
        "open-autonomy": f"=={autonomy_version}",
        "open-aea-test-autonomy": f"=={autonomy_version}",
    }


def get_sources() -> t.Dict:
    """Get sources."""
    return {
        "open-aea": f"v{aea_version}",
        "open-autonomy": f"v{autonomy_version}",
    }


dependencies = get_dependencies()

sources = get_sources()

repositories = [
    dict(name="price-oracle", owners=["Adamantios Zaras", "David Vilela Freire"]),
    dict(name="apy-oracle", owners=["Adamantios Zaras", "David Vilela Freire"]),
    dict(name="agent-academy-1", owners=["Ardian", "Adamantios Zaras"]),
    dict(name="agent-academy-2", owners=["Ardian", "Adamantios Zaras"]),
    dict(name="autonomous-fund", owners=["Ardian", "Adamantios Zaras"]),
    dict(name="IEKit", owners=["David Vilela Freire", "Ardian"]),
    dict(name="mech", owners=["Ardian", "Adamantios Zaras"]),
    dict(name="market-creator", owners=["José Moreira Sánchez", "Adamantios Zaras"]),
    dict(name="trader", owners=["Adamantios Zaras", "Ardian"]),
    dict(name="generatooorr", owners=["Ardian", "Adamantios Zaras"]),
    dict(name="contribution-service", owners=["David Vilela Freire", "Ardian"]),
    dict(name="governatooorr", owners=["David Vilela Freire", "Ardian"]),
    dict(name="centaurs", owners=["David Vilela Freire", "José Moreira Sánchez"]),
]

request = dict(
    repositories=repositories,
    dependencies=dependencies,
    sources=sources,
)

url = os.environ.get("CHARLIE_API")
if url is None:
    print("Please provide URL for charlie API using environment variable 'CHARLIE_API'")
    sys.exit(1)

token = os.environ.get("CHARLIE_TOKEN")
if token is None:
    print(
        "Please provide authorization token for charlie API using environment variable 'CHARLIE_TOKEN'"
    )
    sys.exit(1)

response = requests.post(
    url=url,
    json=dict(
        repositories=repositories,
        dependencies=dependencies,
        sources=sources,
    ),
    headers={
        "Authorization": token,
    },
)

print(
    json.dumps(
        response.json(),
        indent=2,
    )
)
