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

"""Check that ``[tool.isort]`` in ``pyproject.toml`` matches the cfg rendered by ``tomte render-isort-config``.

``aea generate-all-protocols`` reads ``[tool.isort]`` from ``pyproject.toml`` directly;
``[testenv:isort]`` / ``[testenv:isort-check]`` use the cfg rendered by tomte. If the two
diverge — e.g. a tomte canonical bump changes section ordering — IDE/aea-generated
formatting silently disagrees with CI. This script parses both files (without going
through ``isort.Config``, which auto-discovers ``pyproject.toml`` from cwd and would
mask the very drift we want to catch) and reports any setting that differs.
"""

import configparser
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


# Settings that must match across both sources. The cfg uses snake_case and
# comma-separated strings; pyproject uses snake_case and TOML arrays. Both are
# normalised below before comparison.
_KEYS: Tuple[str, ...] = (
    "profile",
    "multi_line_output",
    "include_trailing_comma",
    "force_grid_wrap",
    "use_parentheses",
    "ensure_newline_before_comments",
    "line_length",
    "order_by_type",
    "case_sensitive",
    "lines_after_imports",
    "known_first_party",
    "known_packages",
    "known_local_folder",
    "sections",
)

_LIST_KEYS = {"known_first_party", "known_packages", "known_local_folder", "sections"}
_BOOL_KEYS = {
    "include_trailing_comma",
    "use_parentheses",
    "ensure_newline_before_comments",
    "order_by_type",
    "case_sensitive",
}
_INT_KEYS = {
    "multi_line_output",
    "force_grid_wrap",
    "line_length",
    "lines_after_imports",
}


def _normalise(key: str, value: Any) -> Any:
    """Coerce a value into the canonical representation for comparison."""
    if value is None:
        return None
    if key in _LIST_KEYS:
        if isinstance(value, str):
            items = [v.strip() for v in value.split(",") if v.strip()]
        else:
            items = list(value)
        # `sections` is order-sensitive (it determines block ordering); the
        # other list-valued keys are unordered group memberships.
        return tuple(items) if key == "sections" else frozenset(items)
    if key in _BOOL_KEYS:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "on"}
    if key in _INT_KEYS:
        return int(value)
    return value


def _load_pyproject(path: Path) -> Dict[str, Any]:
    """Read ``[tool.isort]`` out of pyproject.toml."""
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return data.get("tool", {}).get("isort", {}) or {}


def _load_cfg(path: Path) -> Dict[str, Any]:
    """Read the ``[isort]`` section of an isort cfg file."""
    parser = configparser.ConfigParser()
    parser.read(path)
    if "isort" not in parser:
        return {}
    return dict(parser["isort"])


def _diff(pyproject: Dict[str, Any], rendered: Dict[str, Any]) -> List[str]:
    """Return human-readable diff lines for any setting that differs."""
    out: List[str] = []
    for key in _KEYS:
        a = _normalise(key, pyproject.get(key))
        b = _normalise(key, rendered.get(key))
        if a != b:
            out.append(
                f"  {key}:\n    pyproject.toml: {a!r}\n    tomte rendered: {b!r}"
            )
    return out


def main(rendered_cfg: str) -> int:
    """Compare effective isort settings; exit 1 if they differ.

    :param rendered_cfg: Path to the cfg produced by `tomte render-isort-config`.
    :return: 0 on match, 1 on drift.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.is_file():
        print(f"error: {pyproject} not found in cwd", file=sys.stderr)
        return 1
    rendered = Path(rendered_cfg)
    if not rendered.is_file():
        print(f"error: rendered cfg not found at {rendered}", file=sys.stderr)
        return 1

    diff = _diff(_load_pyproject(pyproject), _load_cfg(rendered))
    if diff:
        print(
            "isort config drift detected between pyproject.toml [tool.isort] "
            "and the cfg rendered by `tomte render-isort-config`:"
        )
        print("\n".join(diff))
        print(
            "\nFix: edit `[tool.isort]` in pyproject.toml to match the rendered "
            "values (or update the `tomte render-isort-config` flags in tox.ini)."
        )
        return 1
    print("isort configs in sync")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "usage: python scripts/check_isort_config.py <path-to-rendered-isort.cfg>",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
