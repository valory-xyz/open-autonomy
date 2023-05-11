# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Environment variable helpers."""


import json
import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv


def load_json(file: Path, serialize: bool = False) -> None:
    """Load json."""
    env_vars: Dict = json.load(file.open(mode="r", encoding="utf-8"))
    if serialize:
        for key, val in env_vars.items():
            if isinstance(val, str):
                continue  # pragma: nocover
            env_vars[key] = json.dumps(val)
    os.environ.update(env_vars)


def load_env_file(file: Path, serialize_json: bool = False) -> None:
    """Load env file."""

    if file.name.endswith(".json"):
        load_json(file=file, serialize=serialize_json)
    else:
        load_dotenv(dotenv_path=file)
