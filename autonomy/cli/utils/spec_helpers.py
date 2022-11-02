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
"""FSM spec helpers."""

import importlib
from pathlib import Path
from types import ModuleType
from typing import Optional, cast

import click

from autonomy.analyse.abci.app_spec import (
    DFA,
    DFASpecificationError,
    FSMSpecificationLoader,
    check_unreferenced_events,
)


def import_and_validate_app_class(module_path: Path, app_class: str) -> ModuleType:
    """Import and validate rounds.py module."""

    module_to_look_for = "rounds"
    if not (module_path / "rounds.py").exists():
        module_to_look_for = "composition"

    module_name = ".".join(
        (
            *module_path.parts,
            module_to_look_for,
        )
    )

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise click.ClickException(
            f'Failed to load "{module_name}". Please, verify that AbciApps and classes are correctly defined within the module.'
        ) from e

    if not hasattr(module, app_class):
        raise click.ClickException(f'Class "{app_class}" is not in "{module_name}".')

    return module


def _get_app_class_from_spec_file(
    file: Path,
    spec_format: str,
) -> Optional[str]:
    """Get app class name from spec file."""
    data = FSMSpecificationLoader.load(file=file, spec_format=spec_format)
    return data.get("label")


def update_one(
    package_path: Path,
    app_class: Optional[str] = None,
    spec_format: str = FSMSpecificationLoader.OutputFormats.YAML,
) -> None:
    """Update FSM specification for one package."""

    spec_file = package_path / cast(
        Path, FSMSpecificationLoader.OutputFormats.default_output_files.get(spec_format)
    )

    try:
        if app_class is None:
            if not spec_file.exists():
                raise click.ClickException(
                    f"FSM specification file {spec_file} does not exist, please provide app class name to continue."
                )
            app_class = _get_app_class_from_spec_file(spec_file, spec_format)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Specification file {spec_file} does not exist, please provide the name for app class to continue."
        ) from e

    if app_class is None:
        raise ValueError(
            "Please provide name for the app class or make sure FSM specification file is properly defined."
        )

    module = import_and_validate_app_class(package_path, app_class)
    abci_app_class = getattr(module, app_class)

    dfa = DFA.abci_to_dfa(abci_app_class, app_class)
    FSMSpecificationLoader.dump(
        dfa,
        spec_file,
        spec_format,
    )


def check_one(
    package_path: Path,
    app_class: Optional[str] = None,
    spec_format: str = FSMSpecificationLoader.OutputFormats.YAML,
) -> None:
    """Check for one."""

    spec_file = package_path / cast(
        Path, FSMSpecificationLoader.OutputFormats.default_output_files.get(spec_format)
    )

    if app_class is None:
        app_class = _get_app_class_from_spec_file(spec_file, spec_format)

    if app_class is None:
        raise ValueError(
            "Please provide name for the app class or make sure FSM specification file is properly defined."
        )

    module = import_and_validate_app_class(package_path, app_class)
    if not hasattr(module, app_class):
        raise Exception(f'Class "{app_class}" is not in "{module}".')

    abci_app_class = getattr(module, app_class)
    dfa_from_object = DFA.abci_to_dfa(abci_app_class, app_class)
    dfa_from_file = DFA.load(spec_file, spec_format)
    error_strings = check_unreferenced_events(abci_app_class)

    dfa_check = dfa_from_file != dfa_from_object
    if len(error_strings) > 0:
        errors = "\n".join(error_strings)
        raise DFASpecificationError(f"Event reference check failed with \n{errors}")

    if dfa_check:
        raise DFASpecificationError(
            "FSM Spec definition does not match in specification file and class definitions."
        )


def check_all(
    packages_dir: Path, spec_format: str = FSMSpecificationLoader.OutputFormats.YAML
) -> None:
    """Check all the available definitions."""

    spec_check_failed = []
    fsm_specifications = sorted(
        [
            *packages_dir.glob(
                f"*/skills/*/{FSMSpecificationLoader.OutputFormats.default_output_files.get(spec_format)}"
            ),
        ]
    )
    # TODO: fix this implementation:
    # - above file names should be constant and explained in helper text
    # - investigate: either a) we need to do this in the order of the inverse dependency tree, so that
    # dependencies are already loaded. Otherwise dependencies might not be present. Or b)
    # we need to ensure relative modules are loaded too (https://docs.python.org/3/library/importlib.html#importlib.import_module)?
    for spec_file in fsm_specifications:
        package_path = spec_file.parent.relative_to(Path.cwd().resolve())
        click.echo(f"Checking {package_path}")
        try:
            check_one(package_path=package_path, spec_format=spec_format)
        except DFASpecificationError:
            spec_check_failed.append(str(package_path))

    if len(spec_check_failed) > 0:
        error_message = "Specifications check for following packages.\n" + "\n".join(
            spec_check_failed
        )
        raise DFASpecificationError(error_message)
