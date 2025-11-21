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

"""Helper for docstring analyser."""

import importlib
from pathlib import Path
from types import ModuleType
from typing import Optional, cast

import click
from aea.configurations.constants import PACKAGES

from autonomy.analyse.abci.docstrings import (
    ABCIAPP,
    compare_docstring_content,
    docstring_abci_app,
)


def import_rounds_module(
    module_path: Path,
    packages_dir: Optional[Path] = None,
) -> ModuleType:
    """Import module using importlib.import_module"""
    packages_dir = (packages_dir or Path.cwd() / PACKAGES).parent
    module_dir = module_path.parent.resolve().relative_to(packages_dir)
    import_path = ".".join((*module_dir.parts, "rounds"))
    return importlib.import_module(import_path)


def analyse_docstrings(
    module_path: Path,
    update: bool = False,
    packages_dir: Optional[Path] = None,
) -> bool:
    """
    Process module.

    :param module_path: Path to the rounds module
    :param update: whether to update the content if required
    :param packages_dir: Path to packages directory

    :return: boolean specifying whether the update is needed or not
    """

    module = import_rounds_module(module_path=module_path, packages_dir=packages_dir)
    for obj in dir(module):
        if obj.endswith(ABCIAPP) and obj != ABCIAPP:
            App = getattr(module, obj)
            docstring = docstring_abci_app(App)

            original_content = Path(cast(str, module.__file__)).read_text(
                encoding="utf-8"
            )
            has_docstring, expected_content = compare_docstring_content(
                file_content=original_content, docstring=docstring, abci_app_name=obj
            )

            if not has_docstring and update:
                click.echo(
                    f"App definition in {module_path} does not contain well formatted docstring, please update it manually"
                )
                return True

            update_needed = original_content != expected_content

            if update and update_needed:
                module_path.write_text(expected_content, encoding="utf-8")
                return True

            return update_needed

    click.echo(f"WARNING: No AbciApp definition found in: {module.__file__}")
    return True
