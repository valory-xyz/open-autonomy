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
"""Configurations for APY skill's tools tests."""

from typing import List, Union

import pandas as pd
import pytest

from packages.valory.skills.apy_estimation_abci.tools.io import TRANSFORMED_HIST_DTYPES


@pytest.fixture
def transformed_history() -> pd.DataFrame:
    """Generate a test transformed history.

    :return: a test transformed history.
    """
    hist_li: List[Union[int, float, str]] = [10] * 21
    hist_li.extend(["x"] * 4)
    hist_li.insert(23, "X")
    hist_li.append("X")
    hist_li.append("x - x")
    hist_li.append(10.0)
    hist_li.append(100.0)
    hist_li.extend([0.0] * 2)

    transformed = pd.DataFrame([hist_li], [1], TRANSFORMED_HIST_DTYPES.keys())

    return transformed
