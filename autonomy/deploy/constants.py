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

from string import Template
from typing import Any, Dict


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
Build Length          $size\n\n
"""
)

DEPLOYMENT_KEY_DIRECTORY = "agent_keys"
DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA = "agent_{agent_n}"
KUBERNETES_AGENT_KEY_NAME = DEPLOYMENT_AGENT_KEY_DIRECTORY_SCHEMA + "_private_key.yaml"

DEFAULT_ENCODING = "utf-8"

KEY_SCHEMA_ADDRESS = "address"
KEY_SCHEMA_PRIVATE_KEY = "private_key"


DEFAULT_ABCI_BUILD_DIR = "abci_build"
PERSISTENT_DATA_DIR = "persistent_data"
LOG_DIR = "logs"
TM_STATE_DIR = "tm_state"
BENCHMARKS_DIR = "benchmarks"
VENVS_DIR = "venvs"
AGENT_KEYS_DIR = "agent_keys"
DOCKERFILES = "Dockerfiles"


INFO = "INFO"
DEBUG = "DEBUG"
WARNING = "WARNING"
ERROR = "ERROR"
CRITICAL = "CRITICAL"

LOGGING_LEVELS = (
    INFO,
    DEBUG,
    WARNING,
    ERROR,
    CRITICAL,
)
