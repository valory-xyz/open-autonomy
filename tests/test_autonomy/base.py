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

import yaml

from tests.conftest import ROOT_DIR


def get_dummy_service_config(file_number: int = 0) -> List[Dict]:
    """Returns a dummy service config."""

    with (
        ROOT_DIR
        / "tests"
        / "data"
        / "dummy_service_config_files"
        / f"service_{file_number}.yaml"
    ).open("r") as fp:
        return list(yaml.safe_load_all(fp))
