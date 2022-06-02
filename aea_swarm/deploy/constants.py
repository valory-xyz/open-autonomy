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

"""Constants for generating deployments environment."""
import socket
from string import Template
from typing import Any, Dict


def get_ip() -> str:
    """Get local IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:  # pylint: disable=broad-except
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


NETWORKS = {
    "docker-compose": {
        "hardhat": {
            "LEDGER_ADDRESS": f"http://{get_ip()}:8545",
            "LEDGER_CHAIN_ID": 31337,
        },
        "ropsten": {
            "LEDGER_ADDRESS": "https://ropsten.infura.io/v3/2980beeca3544c9fbace4f24218afcd4",
            "LEDGER_CHAIN_ID": 3,
        },
    },
    "kubernetes": {
        "hardhat": {
            "LEDGER_ADDRESS": "http://hardhat:8545",
            "LEDGER_CHAIN_ID": 31337,
        },
        "ropsten": {
            "LEDGER_ADDRESS": "https://ropsten.infura.io/v3/2980beeca3544c9fbace4f24218afcd4",
            "LEDGER_CHAIN_ID": 3,
        },
    },
}

TENDERMINT_CONFIGURATION_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "kubernetes": {
        "TENDERMINT_URL": "http://localhost:26657",
        "TENDERMINT_COM_URL": "http://localhost:8080",
        "ABCI_HOST": "localhost",
    }
}

DEPLOYMENT_REPORT: Template = Template(
    """
Generated Deployment!\n\n
Type:                 $type
Agents:               $agents
Network:              $network
Build Length          $size\n\n
"""
)
