# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Analyse handlers."""


import importlib
import importlib.machinery
import importlib.util
import types
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import List, cast

import yaml

from autonomy.configurations.constants import CLASS_NAME, HANDLERS


HANDLERS_FILE = f"{HANDLERS}.py"


def load_handler_module_from_skill_path(skill_path: Path) -> types.ModuleType:
    """Resolve handler path to current workind directory."""

    loader = importlib.machinery.SourceFileLoader(
        HANDLERS, str(skill_path / "handlers.py")
    )
    spec = cast(ModuleSpec, importlib.util.spec_from_loader(HANDLERS, loader))
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)

    return module


def check_handlers(config_file: Path, common_handlers: List[str]) -> None:
    """Check handlers"""

    if not (config_file.parent / HANDLERS_FILE).exists():
        raise FileNotFoundError(f"Handler file does not exist in {config_file.parent}")

    module = load_handler_module_from_skill_path(config_file.parent)
    module_attributes = dir(module)

    with open(str(config_file), mode="r", encoding="utf-8") as fp:
        config = yaml.safe_load(fp)
        for common_handler in common_handlers:
            if common_handler not in config[HANDLERS]:
                raise ValueError(
                    f"Common handler '{common_handler}' is not defined in {config_file}"
                )

        for handler_info in config[HANDLERS].values():
            if handler_info["class_name"] not in module_attributes:
                raise ValueError(
                    f"Handler {handler_info[CLASS_NAME]} declared in {config_file} is missing from {config_file.parent / HANDLERS}.py"
                )
