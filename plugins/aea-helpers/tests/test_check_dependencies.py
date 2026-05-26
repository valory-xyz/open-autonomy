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

import logging
import sys
import textwrap
from collections import OrderedDict
from pathlib import Path

import pytest
from aea.configurations.data_types import Dependency
from aea_helpers.check_dependencies import PyProjectTomlConfig
from packaging.specifiers import SpecifierSet

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

SAMPLE_PYPROJECT = textwrap.dedent("""\
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
    pywin32 = { version = ">=304", markers = "sys_platform == 'win32'" }

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
    """)


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


def test_main_deps_win_over_group_deps_on_name_collision(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """If the same package appears in both main and a group, main wins."""
    content = textwrap.dedent("""\
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
        """)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    with caplog.at_level(logging.WARNING):
        config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    assert SpecifierSet(config.dependencies["protobuf"].version) == SpecifierSet(
        "==4.25.0"
    )
    msg = next(r.getMessage() for r in caplog.records if "protobuf" in r.getMessage())
    # Names the dep, says main wins, and logs both colliding versions.
    assert "main wins" in msg
    assert "==4.25.0" in msg and "*" in msg


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
    assert "requests" in names


def test_exclude_argument_filters_iteration(tmp_path: Path) -> None:
    """User-provided exclusions hide deps from iteration."""
    config = PyProjectTomlConfig.load(
        _write_pyproject(tmp_path), exclude=["mkdocs", "docker"]
    )
    assert config is not None
    names = {dep.name for dep in config}
    assert "mkdocs" not in names
    assert "docker" not in names


def test_iter_scopes_to_main_deps(tmp_path: Path) -> None:
    """`__iter__` yields main-deps only; group entries are reserved for lookups.

    Group deps live in `self.dependencies` so package-YAML ->
    pyproject `check()` lookups succeed, but they must not be surfaced
    when cross-comparing pyproject against `tox.ini` (which only carries
    main runtime deps).

    :param tmp_path: pytest-provided temp dir for the sample pyproject.
    """
    config = PyProjectTomlConfig.load(_write_pyproject(tmp_path))
    assert config is not None
    iterated = {dep.name for dep in config}
    # Main-deps present:
    assert "open-aea" in iterated
    assert "docker" in iterated
    # Group-only deps absent from iteration but still accessible via check():
    assert "pytest-asyncio" not in iterated
    assert "Flask" not in iterated
    assert "mkdocs" not in iterated
    assert "pytest-asyncio" in config.dependencies
    assert "Flask" in config.dependencies


def test_dump_does_not_hoist_group_deps_to_main(tmp_path: Path) -> None:
    """`dump()` rewrites only string-form main deps; everything else is preserved.

    Regression guard for the `--update` mode corruption described in
    the review: dict-form main deps must keep ``optional`` / ``path`` /
    ``develop`` / ``markers``, and ``[tool.poetry.extras]`` lists must
    survive.  Group lines pass through verbatim.

    :param tmp_path: pytest-provided temp dir for the sample pyproject.
    """
    pyproject = _write_pyproject(tmp_path)
    config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    config.dump()
    # Parse the rewritten file structurally — substring matches would be
    # brittle against inline-table whitespace reformatting.
    parsed = tomllib.loads(pyproject.read_text())
    poetry = parsed["tool"]["poetry"]
    main_deps = poetry["dependencies"]

    # --- Main dict-form deps keep their metadata (not flattened) ---
    assert main_deps["docker"] == {"version": "==7.1.0", "optional": True}
    assert main_deps["open-aea-ledger-ethereum-hwi"] == {
        "version": "==2.2.1",
        "optional": True,
    }
    # Environment markers survive (would install on every OS if dropped).
    assert main_deps["pywin32"].get("markers") == "sys_platform == 'win32'"

    # --- [tool.poetry.extras] lists survive ---
    assert poetry["extras"]["docker"] == ["docker"]
    assert poetry["extras"]["hwi"] == ["open-aea-ledger-ethereum-hwi"]

    # --- Group deps stay in their group tables, not hoisted into main ---
    for group_name in ("pytest-asyncio", "Flask", "open-aea-helpers", "mkdocs"):
        assert (
            group_name not in main_deps
        ), f"Group dep {group_name!r} hoisted into main"
    assert "pytest-asyncio" in poetry["group"]["dev"]["dependencies"]
    assert "mkdocs" in poetry["group"]["docs"]["dependencies"]


def test_load_skips_list_form_spec(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """List-form specs (multi-constraint with markers) are skipped, not crashed on."""
    content = textwrap.dedent("""\
        [tool.poetry]
        name = "demo"
        version = "0.1.0"
        description = ""
        authors = ["demo"]

        [tool.poetry.dependencies]
        python = ">=3.10,<3.15"
        requests = "*"

        [[tool.poetry.dependencies.weird]]
        version = "==1.0"
        python = "<3.12"
        """)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    with caplog.at_level(logging.WARNING):
        config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    # `requests` parses normally; the list-form `weird` entry is skipped.
    assert "requests" in config.dependencies
    assert "weird" not in config.dependencies
    assert any(
        "'weird'" in r.getMessage() and "expected str or dict" in r.getMessage()
        for r in caplog.records
    ), "expected skip-warning for list-form 'weird'"


def test_load_handles_malformed_group_table(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A `[tool.poetry.group]` whose entries lack `dependencies` is tolerated."""
    content = textwrap.dedent("""\
        [tool.poetry]
        name = "demo"
        version = "0.1.0"
        description = ""
        authors = ["demo"]

        [tool.poetry.dependencies]
        python = ">=3.10,<3.15"
        requests = "*"

        [tool.poetry.group.dev]
        optional = true
        """)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    with caplog.at_level(logging.WARNING):
        config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    assert "requests" in config.dependencies
    assert any(
        "dev" in r.getMessage() and "not a table or is missing" in r.getMessage()
        for r in caplog.records
    ), "expected warning for malformed group 'dev'"


def test_load_handles_no_group_table(tmp_path: Path) -> None:
    """A pyproject.toml with `[tool.poetry.dependencies]` but no groups loads cleanly."""
    content = textwrap.dedent("""\
        [tool.poetry]
        name = "demo"
        version = "0.1.0"
        description = ""
        authors = ["demo"]

        [tool.poetry.dependencies]
        python = ">=3.10,<3.15"
        requests = "*"
        """)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    assert {dep.name for dep in config} == {"requests"}


def test_load_normalizes_bare_numeric_string(tmp_path: Path) -> None:
    """Bare-numeric string entries (`"7.0.0"`) get `==` prefixed."""
    content = textwrap.dedent("""\
        [tool.poetry]
        name = "demo"
        version = "0.1.0"
        description = ""
        authors = ["demo"]

        [tool.poetry.dependencies]
        python = ">=3.10,<3.15"
        somepkg = "7.0.0"
        """)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    assert SpecifierSet(config.dependencies["somepkg"].version) == SpecifierSet(
        "==7.0.0"
    )


def test_load_normalizes_flask_range_specifier(tmp_path: Path) -> None:
    """Range specifiers (`>=3.1.0,<4.0.0`) survive normalization unchanged."""
    config = PyProjectTomlConfig.load(_write_pyproject(tmp_path))
    assert config is not None
    assert SpecifierSet(config.dependencies["Flask"].version) == SpecifierSet(
        ">=3.1.0,<4.0.0"
    )


def test_direct_constructor_without_main_dep_names(tmp_path: Path) -> None:
    """Constructing directly with `main_dep_names=None` iterates everything."""
    deps: "OrderedDict[str, Dependency]" = OrderedDict()
    deps["requests"] = Dependency(name="requests", version="")
    deps["pytest-asyncio"] = Dependency(name="pytest-asyncio", version="")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.poetry]\n")

    config = PyProjectTomlConfig(
        dependencies=deps,
        config={},
        file=pyproject,
        main_dep_names=None,
    )
    names = {dep.name for dep in config}
    assert "requests" in names
    assert "pytest-asyncio" in names


def test_dump_preserves_main_dict_form_and_extras_collision(
    tmp_path: Path,
) -> None:
    """dump() must not corrupt main dict-form deps or extras lists.

    Regression test: when a dep name appears both in
    `[tool.poetry.dependencies]` (dict-form) and
    `[tool.poetry.extras]` (list-form), dump() must leave both
    lines intact.

    :param tmp_path: pytest-provided temp dir for the sample pyproject.
    """
    content = textwrap.dedent("""\
        [tool.poetry]
        name = "demo"
        version = "0.1.0"
        description = ""
        authors = ["demo"]

        [tool.poetry.dependencies]
        python = ">=3.10,<3.15"
        requests = "*"
        docker = { version = "==7.1.0", optional = true }
        pywin32 = { version = ">=304", markers = "sys_platform == 'win32'" }

        [tool.poetry.extras]
        docker = ["docker"]

        [tool.poetry.group.dev.dependencies]
        protobuf = "*"
        """)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    config.dump()
    # Structural assertions (robust to inline-table whitespace reformatting).
    parsed = tomllib.loads(pyproject.read_text())
    main_deps = parsed["tool"]["poetry"]["dependencies"]
    # Main dict-form dep keeps optional=true (not flattened to a string).
    assert main_deps["docker"] == {"version": "==7.1.0", "optional": True}
    # Environment markers survive.
    assert main_deps["pywin32"].get("markers") == "sys_platform == 'win32'"
    # Extras list (name collides with the dict-form dep) survives intact.
    assert parsed["tool"]["poetry"]["extras"]["docker"] == ["docker"]
    # Group dep is not hoisted into main.
    assert "protobuf" not in main_deps


def test_group_vs_group_collision_keeps_first_group(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Two groups declaring the same dep: first wins, warning must not say 'main wins'.

    :param tmp_path: pytest-provided temp dir for the sample pyproject.
    :param caplog: pytest log-capture fixture for the collision warning.
    """
    content = textwrap.dedent("""\
        [tool.poetry]
        name = "demo"
        version = "0.1.0"
        description = ""
        authors = ["demo"]

        [tool.poetry.dependencies]
        python = ">=3.10,<3.15"

        [tool.poetry.group.dev.dependencies]
        requests = "==1.0.0"

        [tool.poetry.group.docs.dependencies]
        requests = "==2.0.0"
        """)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    with caplog.at_level(logging.WARNING):
        config = PyProjectTomlConfig.load(pyproject)
    assert config is not None
    assert SpecifierSet(config.dependencies["requests"].version) == SpecifierSet(
        "==1.0.0"
    )
    msg = next(r.getMessage() for r in caplog.records if "requests" in r.getMessage())
    assert "main wins" not in msg
    assert "multiple groups" in msg
