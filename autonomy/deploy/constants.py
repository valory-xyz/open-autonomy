# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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

from pathlib import Path
from string import Template


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
TENDERMINT_BIN_UNIX = "tendermint"
TENDERMINT_BIN_WINDOWS = "tendermint.exe"
TENDERMINT_VARS_CONFIG_FILE = "tendermint.json"
AGENT_VARS_CONFIG_FILE = "agent.json"
TENDERMINT_FLASK_APP_PATH = (
    Path("autonomy") / "deploy" / "generators" / "localhost" / "tendermint" / "app.py"
)
DEATTACH_WINDOWS_FLAG = 0x00000008

TM_ENV_TMHOME = "TMHOME"
TM_ENV_TMSTATE = "TMSTATE"
TM_ENV_PROXY_APP = "PROXY_APP"
TM_ENV_P2P_LADDR = "P2P_LADDR"
TM_ENV_RPC_LADDR = "RPC_LADDR"
TM_ENV_PROXY_APP = "PROXY_APP"
TM_ENV_CREATE_EMPTY_BLOCKS = "CREATE_EMPTY_BLOCKS"
TM_ENV_USE_GRPC = "USE_GRPC"

DEFAULT_ENCODING = "utf-8"

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
