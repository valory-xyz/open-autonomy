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
"""Test to ensure that tendermint classes used for deployment stay in sync"""

import difflib
import inspect
import logging
from typing import List, Type

import pytest

from deployments.Dockerfiles.tendermint import tendermint  # type: ignore

from packages.valory.connections.abci import connection


@pytest.mark.parametrize(
    "deployment_cls, package_cls",
    [
        (connection.StoppableThread, tendermint.StoppableThread),
        (connection.TendermintParams, tendermint.TendermintParams),
        (connection.TendermintNode, tendermint.TendermintNode),
    ],
)
def test_deployment_class_identical(deployment_cls: Type, package_cls: Type) -> None:
    """Assert Tendermint deployment and package code is identical"""

    def get_lines(cls: Type) -> List[str]:
        return inspect.getsource(cls).splitlines(keepends=False)

    p_code, d_code = map(get_lines, (deployment_cls, package_cls))
    differences = "\n".join(difflib.unified_diff(p_code, d_code, lineterm=""))
    if differences:
        logging.error(differences)
    assert not differences
