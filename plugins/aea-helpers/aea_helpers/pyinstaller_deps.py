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

"""Generate PyInstaller hidden-import and collect-all flags from agent dependencies."""

import os
from importlib.metadata import distributions
from pathlib import Path
from typing import List

import click

BLACKLIST_MODULES = {
    "pytest",
    "pytest_asyncio",
    "_pytest",
    "py",
    "hypothesis",
    "Crypto",
    "_yaml",
}


def get_modules_from_dist(dist) -> List[str]:  # type: ignore
    """Get top-level modules from dist metadata, fallback to directory names.

    :param dist: an importlib.metadata Distribution object.
    :return: sorted list of unique module names.
    """
    modules: List[str] = []

    try:
        top_level = dist.read_text("top_level.txt")
        if top_level:
            modules.extend(m.strip() for m in top_level.splitlines() if m.strip())
    except FileNotFoundError:
        pass

    if not modules:
        for path in dist.files or []:
            if ".dist-info" in str(path):
                continue
            parts = Path(path).parts
            if len(parts) == 1 and parts[0].endswith(".py"):
                modules.append(parts[0][:-3])
            if len(parts) == 2 and parts[1] == "__init__.py":
                modules.append(parts[0])

    return sorted(set(modules))


def get_agent_dependency_modules(agent_dir: str) -> List[str]:
    """Read agent config and resolve installed modules for all dependencies.

    :param agent_dir: path to the agent directory.
    :return: sorted list of module names.
    """
    from aea.cli.utils.config import try_to_load_agent_config  # type: ignore
    from aea.cli.utils.context import Context  # type: ignore

    original_dir = os.getcwd()
    try:
        os.chdir(agent_dir)
        ctx = Context(cwd=".", verbosity="debug", registry_path=".")
        try_to_load_agent_config(ctx)
        deps = {name.replace("-", "_") for name in ctx.get_dependencies()}
        all_modules: List[str] = []
        for dist in distributions():
            dist_name = dist.metadata["Name"].lower().replace("-", "_")
            if dist_name in deps:
                all_modules.extend(get_modules_from_dist(dist))
        return sorted(all_modules)
    finally:
        os.chdir(original_dir)


def filter_modules(modules: List[str]) -> List[str]:
    """Remove test-related and problematic modules.

    :param modules: list of module names.
    :return: filtered list.
    """
    return [m for m in modules if m not in BLACKLIST_MODULES]


def build_pyinstaller_flags(modules: List[str]) -> str:
    """Build --hidden-import and --collect-all flags for PyInstaller.

    :param modules: list of module names.
    :return: space-separated flag string.
    """
    return " ".join(f"--hidden-import {m} --collect-all {m}" for m in modules)


@click.command(name="build-binary-deps")
@click.argument("agent_dir", type=click.Path(exists=True), default="agent")
def build_binary_deps(agent_dir: str) -> None:
    """Print PyInstaller dependency flags for an agent.

    Reads the agent's aea-config.yaml, resolves all installed dependencies,
    and outputs --hidden-import and --collect-all flags for PyInstaller.
    """
    modules = filter_modules(get_agent_dependency_modules(agent_dir))
    click.echo(build_pyinstaller_flags(modules), nl=False)
