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
"""Tests for `aea_helpers.check_dependencies.PyProjectTomlConfig.load`."""

import textwrap
from pathlib import Path

from packaging.specifiers import SpecifierSet

from aea_helpers.check_dependencies import PyProjectTomlConfig


SAMPLE_PYPROJECT = textwrap.dedent(
    """\
    [tool.poetry]
    name = "demo"
    version = "0.1.0"
    description = ""
    authors = ["demo"]

    [tool.poetry.dependencies]
    python = ">=3.10,<3.15"
    requests = "*"
    web3 = "^7.0.0"
    open-aea = { version = "==2.2.1", extras = ["all"] }
    docker = { version = "==7.1.0", optional = true }
    open-aea-ledger-ethereum-hwi = { version = "==2.2.1", optional = true }
    open-aea-ledger-ethereum = { version = "==2.2.1", optional = true, extras = [] }

    [tool.poetry.extras]
    docker = ["docker"]
    hwi = ["open-aea-ledger-ethereum-hwi"]

    [tool.poetry.group.dev.dependencies]
    tomte = { extras = ["tox"], version = "==0.6.5" }
    pytest-asyncio = "*"
    Flask = ">=3.1.0,<4.0.0"
    open-aea-helpers = { path = "plugins/aea-helpers", develop = true }

    [tool.poetry.group.docs.dependencies]
    mkdocs = "==1.6.0"
    """
)


def _write_pyproject(tmp_path: Path) -> Path:
    """Write the sample pyproject.toml to a temp file and return its path."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(SAMPLE_PYPROJECT)
    return pyproject


def test_load_includes_main_dict_entries_without_extras(tmp_path: Path) -> None:
    """Dict entries with `optional = true` and no `extras` key are declared."""
    config = PyProjectTomlConfig.load(_write_pyproject(tmp_path))
    assert config is not None
    assert "docker" in config.dependencies
    assert "open-aea-ledger-ethereum-hwi" in config.dependencies


def test_load_includes_main_dict_entries_with_extras(tmp_path: Path) -> None:
    """Dict entries that already carry `extras` keep working."""
    config = PyProjectTomlConfig.load(_write_pyproject(tmp_path))
    assert config is not None
    assert config.dependencies["open-aea"].extras == ["all"]
    assert config.dependencies["open-aea-ledger-ethereum"].extras == []


def test_load_includes_string_entries(tmp_path: Path) -> None:
    """Plain-string entries are picked up with normalized versions."""
    config = PyProjectTomlConfig.load(_write_pyproject(tmp_path))
    assert config is not None
    assert config.dependencies["requests"].version == ""
    assert SpecifierSet(config.dependencies["web3"].version) == SpecifierSet("==7.0.0")


def test_load_includes_dev_group(tmp_path: Path) -> None:
    """`[tool.poetry.group.dev.dependencies]` entries are visible."""
    config = PyProjectTomlConfig.load(_write_pyproject(tmp_path))
    assert config is not None
    assert "pytest-asyncio" in config.dependencies
    assert "Flask" in config.dependencies
    assert "tomte" in config.dependencies
    assert "open-aea-helpers" in config.dependencies
    assert config.dependencies["tomte"].extras == ["tox"]
    assert config.dependencies["open-aea-helpers"].version == ""


def test_load_includes_other_groups(tmp_path: Path) -> None:
    """Non-dev groups (e.g. `docs`) are also ingested."""
    config = PyProjectTomlConfig.load(_write_pyproject(tmp_path))
    assert config is not None
    assert "mkdocs" in config.dependencies


def test_main_deps_win_over_group_deps_on_name_collision(tmp_path: Path) -> None:
    """If the same package appears in both main and a group, main wins."""
    content = textwrap.dedent(
        """\
        [tool.poetry]
        name = "demo"
        version = "0.1.0"
        description = ""
        authors = ["demo"]

        [tool.poetry.dependencies]
        python = ">=3.10,<3.15"
        protobuf = "==4.25.0"

        [tool.poetry.group.dev.dependencies]
        protobuf = "*"
        """
    )
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    assert SpecifierSet(config.dependencies["protobuf"].version) == SpecifierSet(
        "==4.25.0"
    )


def test_load_returns_none_when_no_poetry_table(tmp_path: Path) -> None:
    """A pyproject.toml without `[tool.poetry.dependencies]` returns None."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[build-system]\nrequires = ['setuptools']\n")
    assert PyProjectTomlConfig.load(pyproject) is None


def test_iter_excludes_python_marker(tmp_path: Path) -> None:
    """The `python` constraint is filtered out by the default ignore list."""
    config = PyProjectTomlConfig.load(_write_pyproject(tmp_path))
    assert config is not None
    names = {dep.name for dep in config}
    assert "python" not in names


def test_exclude_argument_filters_iteration(tmp_path: Path) -> None:
    """User-provided exclusions hide deps from iteration."""
    config = PyProjectTomlConfig.load(
        _write_pyproject(tmp_path), exclude=["mkdocs", "docker"]
    )
    assert config is not None
    names = {dep.name for dep in config}
    assert "mkdocs" not in names
    assert "docker" not in names
