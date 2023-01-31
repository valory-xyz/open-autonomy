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

"""Analyse dialogue definitions."""


import importlib
import importlib.machinery
import importlib.util
import types
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Dict, List, cast

import yaml

from autonomy.analyse.constants import CLASS_NAME, DIALOGUES, DIALOGUES_FILE, MODELS


def load_dialogues_module_from_skill_path(skill_path: Path) -> types.ModuleType:
    """Load `dialogues.py` module for the given skill."""

    loader = importlib.machinery.SourceFileLoader(
        DIALOGUES, str(skill_path / DIALOGUES_FILE)
    )
    spec = cast(ModuleSpec, importlib.util.spec_from_loader(DIALOGUES, loader))
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)

    return module


def validate_and_get_dialogues(
    models_configuration: Dict[str, Dict[str, str]]
) -> Dict[str, str]:
    """Returns dialogue names to class name mappings"""
    mapping = {}
    for name, info in models_configuration.items():
        name_ends_with_dialogue = name.endswith(DIALOGUES)

        class_name = info[CLASS_NAME]
        class_ends_with_dialogue = class_name.lower().endswith(DIALOGUES)

        if not class_ends_with_dialogue and not name_ends_with_dialogue:
            continue  # pragma: nocover

        if name_ends_with_dialogue and not class_ends_with_dialogue:
            raise ValueError(
                f"Class name for a dialogue should end with `Dialogues`; dialogue={name}; class={class_name}"
            )

        if class_ends_with_dialogue and not name_ends_with_dialogue:
            raise ValueError(
                f"Dialogue name should end with `dialogues`; dialogue={name}; class={class_name}"
            )

        mapping[name] = class_name

    return mapping


def check_dialogues_in_a_skill_package(config_file: Path, dialogues: List[str]) -> None:
    """Check dialogue definitions."""

    if not (config_file.parent / DIALOGUES_FILE).exists():
        raise FileNotFoundError(f"dialogue file does not exist in {config_file.parent}")

    module = load_dialogues_module_from_skill_path(skill_path=config_file.parent)
    module_attributes = dir(module)

    with open(str(config_file), mode="r", encoding="utf-8") as fp:
        config = yaml.safe_load(fp)
        dialogue_to_class = validate_and_get_dialogues(
            models_configuration=cast(Dict[str, Dict[str, str]], config[MODELS])
        )

        for dialogue_name in dialogues:
            if not dialogue_name.endswith(DIALOGUES):
                dialogue_name = f"{dialogue_name}_{DIALOGUES}"

            if dialogue_name not in dialogue_to_class:
                raise ValueError(
                    f"Common dialogue '{dialogue_name}' is not defined in {config_file}"
                )

            if dialogue_to_class[dialogue_name] not in module_attributes:
                raise ValueError(
                    f"dialogue {dialogue_to_class[dialogue_name]} declared in {config_file} "
                    f"is missing from {config_file.parent / DIALOGUES}.py"
                )
