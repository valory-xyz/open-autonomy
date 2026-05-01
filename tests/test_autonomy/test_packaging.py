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

"""Test wheel/sdist packaging guarantees for ejected contracts."""

import re
import shutil
import subprocess  # nosec
import sys
import zipfile
from pathlib import Path
from typing import List

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from tests.conftest import ROOT_DIR

EJECT_CONTRACTS_PATTERN = re.compile(
    r"^eject-contracts:\s*\n\s*@for contract in ([^;]+);", re.MULTILINE
)
CONTRACTS_INCLUDE_PATH = "autonomy/data/contracts/**/*"


def _parse_eject_contracts() -> List[str]:
    """Return the contract list ejected by ``make eject-contracts``."""
    makefile = (ROOT_DIR / "Makefile").read_text()
    match = EJECT_CONTRACTS_PATTERN.search(makefile)
    assert match is not None, (
        "Could not find the `eject-contracts:` recipe in Makefile. If the "
        "recipe was renamed, update EJECT_CONTRACTS_PATTERN here too."
    )
    return match.group(1).split()


def test_pyproject_includes_ejected_contracts() -> None:
    """``pyproject.toml`` must keep ejected contracts in the wheel/sdist.

    Poetry-core (the current PEP 517 backend) excludes anything matching
    ``.gitignore`` by default. The ejected copies of contracts under
    ``autonomy/data/contracts/`` are gitignored to keep the working tree
    free of duplicates, so without an explicit ``[tool.poetry] include``
    they silently drop from the published wheel/sdist — which is what
    happened between v0.21.17 and v0.21.19. This test is the structural
    guard that the include directive stays in place.
    """
    pyproject = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text())
    includes = pyproject.get("tool", {}).get("poetry", {}).get("include", [])
    matching = [
        entry
        for entry in includes
        if isinstance(entry, dict) and entry.get("path") == CONTRACTS_INCLUDE_PATH
    ]
    assert matching, (
        f"Expected `[tool.poetry] include` entry with path "
        f"{CONTRACTS_INCLUDE_PATH!r} in pyproject.toml. Without it, "
        "poetry-core drops the gitignored ejected contract copies from "
        "the wheel/sdist (regression seen in v0.21.17–v0.21.19)."
    )
    formats = set(matching[0].get("format", []))
    assert {"sdist", "wheel"} <= formats, (
        f"`[tool.poetry] include` for {CONTRACTS_INCLUDE_PATH!r} must "
        f"declare both 'sdist' and 'wheel' formats; found {sorted(formats)}."
    )


def test_eject_contracts_sources_exist() -> None:
    """Every contract listed in ``make eject-contracts`` must be ejectable.

    ``make dist`` runs ``eject-contracts`` and then builds the wheel, so a
    typo or stale name here breaks ``make dist`` only at release time. This
    catches the divergence at PR time.
    """
    contracts = _parse_eject_contracts()
    assert contracts, "Parsed empty contract list from `eject-contracts:` recipe."
    missing = [
        name
        for name in contracts
        if not (ROOT_DIR / "packages" / "valory" / "contracts" / name).is_dir()
    ]
    assert not missing, (
        f"`make eject-contracts` lists contracts that do not exist under "
        f"packages/valory/contracts/: {missing}"
    )


def test_ejected_contracts_match_gitignore() -> None:
    """Every ejected contract must be gitignored.

    The working-tree copy created by ``make eject-contracts`` would
    otherwise show up as untracked clutter on every dev machine. This is
    a soft guard — the wheel bundling is now driven by the explicit
    ``[tool.poetry] include`` (see test above), not by ``.gitignore``,
    so the only consequence of a miss here is local-tree noise.
    """
    contracts = _parse_eject_contracts()
    gitignore = (ROOT_DIR / ".gitignore").read_text().splitlines()
    ignored = {
        line.strip()
        for line in gitignore
        if line.strip().startswith("autonomy/data/contracts/")
    }
    missing = [
        name for name in contracts if f"autonomy/data/contracts/{name}" not in ignored
    ]
    assert not missing, (
        f"Contracts ejected by `make eject-contracts` but not listed in "
        f".gitignore: {missing}. Add `autonomy/data/contracts/<name>` "
        "entries so the post-eject working tree stays clean."
    )


def _eject_contracts_in_python(contracts: List[str]) -> None:
    """Replicate ``make eject-contracts`` cross-platform (no ``make`` dep)."""
    contracts_root = ROOT_DIR / "autonomy" / "data" / "contracts"
    contracts_root.mkdir(parents=True, exist_ok=True)
    for name in contracts:
        src = ROOT_DIR / "packages" / "valory" / "contracts" / name
        dst = contracts_root / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


@pytest.mark.skipif(
    sys.platform != "linux" or sys.version_info[:2] != (3, 14),
    reason=(
        "Behavioral build-and-inspect runs once per push on the canonical "
        "release env (linux + py3.14). Wheel content is platform-independent, "
        "so coverage on a single matrix cell is sufficient; the structural "
        "tests above run everywhere."
    ),
)
def test_built_wheel_ships_ejected_contracts(tmp_path: Path) -> None:
    """Build the wheel and assert every ejected contract is bundled.

    The structural tests above guard the ``[tool.poetry] include`` directive
    in source. This test is the behavioral guard that the *built artifact*
    actually ships the contracts — the only thing that catches a future
    build-backend change that ignores the include directive (which is the
    class of regression that bit v0.21.17–v0.21.19 in the first place).
    """
    pytest.importorskip(
        "build", reason="install the `build` distribution to run this test"
    )

    contracts = _parse_eject_contracts()
    assert len(contracts) >= 15, (
        f"Sanity floor: expected at least 15 contracts in the eject list, "
        f"found {len(contracts)}. The list shrinking unexpectedly likely "
        "means a contract was dropped from `make eject-contracts`."
    )

    _eject_contracts_in_python(contracts)

    dist = tmp_path / "dist"
    proc = subprocess.run(  # nosec - inputs are repo-local, no shell
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"`python -m build --wheel` failed:\nstdout:\n{proc.stdout}"
        f"\nstderr:\n{proc.stderr}"
    )

    wheels = list(dist.glob("open_autonomy-*.whl")) + list(dist.glob("autonomy-*.whl"))
    assert len(wheels) == 1, f"Expected exactly one wheel; found {wheels}"

    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())

    missing = [
        f"{name}/{fname}"
        for name in contracts
        for fname in ("contract.py", "contract.yaml")
        if f"autonomy/data/contracts/{name}/{fname}" not in names
    ]
    assert not missing, (
        f"Built wheel {wheels[0].name} is missing {len(missing)} contract "
        f"file(s): {missing}. This is the regression that silently dropped "
        "11 contracts from PyPI artifacts in v0.21.17–v0.21.19."
    )
