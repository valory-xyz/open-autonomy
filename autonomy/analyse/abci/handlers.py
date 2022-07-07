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

"""Analyse handlers."""


import importlib
from pathlib import Path
from typing import List

import yaml


def check_handlers(
    config_file: Path, common_handlers: List[str], skip_skills: List[str]
) -> None:
    """Check handlers"""

    handler_file_path = (config_file.parent / "handlers.py").relative_to(
        Path.cwd().resolve()
    )
    module_name = str(handler_file_path).replace(".py", "").replace("/", ".")
    if config_file.parent.name in skip_skills:
        return

    try:
        module = importlib.import_module(module_name)
        module_attributes = dir(module)
    except ModuleNotFoundError as exc:
        raise FileNotFoundError(f"Handler file {module_name} does not exist") from exc

    with open(str(config_file), mode="r", encoding="utf-8") as fp:
        config = yaml.safe_load(fp)
        for common_handler in common_handlers:
            if common_handler not in config["handlers"]:
                raise ValueError(
                    f"Common handler '{common_handler}' is not defined in {config_file}"
                )

        for handler_info in config["handlers"].values():
            if handler_info["class_name"] not in module_attributes:
                raise ValueError(
                    f"Handler {handler_info['class_name']} declared in {config_file} is missing from {handler_file_path}"
                )
