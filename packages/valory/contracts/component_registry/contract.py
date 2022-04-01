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

"""This module contains the class to connect to the Service Registry contract."""

import logging
from typing import Dict, List, Tuple, cast

import hashlib
from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import LedgerApi, EthereumApi

Address = hex
ConfigHash = Tuple[bytes, int, int]
AgentParams = Tuple[int, int]

PUBLIC_ID = PublicId.from_str("valory/component_registry:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class ComponentRegistryContract(Contract):
    """The Service Registry contract."""

    contract_id = PUBLIC_ID
