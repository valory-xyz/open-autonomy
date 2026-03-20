# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Tests for the identify_service_owner_abci handlers."""

import pytest

from packages.valory.skills.abstract_round_abci import handlers as base_handlers
from packages.valory.skills.identify_service_owner_abci import (
    handlers as skill_handlers,
)


@pytest.mark.parametrize(
    "skill_attr,base_attr",
    [
        ("ABCIHandler", "ABCIRoundHandler"),
        ("HttpHandler", "HttpHandler"),
        ("SigningHandler", "SigningHandler"),
        ("LedgerApiHandler", "LedgerApiHandler"),
        ("ContractApiHandler", "ContractApiHandler"),
        ("TendermintHandler", "TendermintHandler"),
        ("IpfsHandler", "IpfsHandler"),
    ],
)
def test_handler_alias(skill_attr: str, base_attr: str) -> None:
    """Test that each handler class is a direct alias of the base class."""
    assert getattr(skill_handlers, skill_attr) is getattr(base_handlers, base_attr)
