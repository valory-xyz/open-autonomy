# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2026 Valory AG
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
"""
Check that project dependency files are consistent.

Validates that dependencies declared in packages/ match those in
pyproject.toml (or Pipfile) and tox.ini. Supports both check-only
and update modes.
"""

import itertools
import logging
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple, cast

import click
from aea.configurations.data_types import Dependency
from aea.package_manager.base import load_configuration
from aea.package_manager.v1 import PackageManagerV1

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # pytest (via open-aea[all]) supplies `tomli`

ANY_SPECIFIER = "*"

# Matches a top-level TOML key assignment at the very start of a line
# (no leading whitespace, so indented inner lines of a multi-line inline
# table are not matched). Tolerant of the no-space form (`pkg="*"`).
_DEP_LINE_RE = re.compile(r"^([A-Za-z0-9_.\-]+)\s*=")


def _split_inline_comment(text: str) -> Tuple[str, str]:
    """Split a TOML line into ``(code, trailing_comment)``.

    Quote-aware so a ``#`` inside a quoted version specifier is not
    mistaken for a comment. The returned comment includes the whitespace
    that preceded the ``#``, so re-assembly preserves the original gap;
    it is ``""`` when there is no trailing comment.

    :param text: the line body (without its trailing newline).
    :return: a ``(code, comment)`` tuple.
    """
    in_str: Optional[str] = None
    for i, char in enumerate(text):
        if in_str is not None:
            if char == in_str:
                in_str = None
        elif char in ('"', "'"):
            in_str = char
        elif char == "#":
            code = text[:i].rstrip()
            return code, text[len(code) :]
    return text, ""


class PathArgument(click.Path):
    """Path parameter for CLI."""

    def convert(
        self,
        value: Any,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Optional[Path]:
        """Convert path string to `pathlib.Path`"""
        path_string = super().convert(value, param, ctx)
        return None if path_string is None else Path(path_string)


class PipfileConfig:
    """Class to represent Pipfile config."""

    ignore = [
        "open-aea-ledger-cosmos",
        "open-aea-ledger-ethereum",
        "open-aea-ledger-fetchai",
        "tomte",
    ]

    def __init__(
        self,
        sources: List[str],
        packages: OrderedDictType[str, Dependency],
        dev_packages: OrderedDictType[str, Dependency],
        file: Path,
        exclude: Optional[List[str]] = None,
    ) -> None:
        """Initialize object."""
        self.sources = sources
        self.packages = packages
        self.dev_packages = dev_packages
        self.file = file
        self.ignore = list(set(self.ignore + (exclude or [])))

    def __iter__(self) -> Iterator[Dependency]:
        """Iterate dependencies."""
        for name, dependency in itertools.chain(
            self.packages.items(), self.dev_packages.items()
        ):
            if name.startswith("comment_") or name in self.ignore:
                continue
            yield dependency

    def update(self, dependency: Dependency) -> None:
        """Update dependency specifier."""
        if dependency.name in self.ignore:
            return
        if dependency.name in self.packages:
            if dependency.version == "":
                return
            self.packages[dependency.name] = dependency
        else:
            self.dev_packages[dependency.name] = dependency

    def check(self, dependency: Dependency) -> Tuple[Optional[str], int]:
        """Check dependency specifier."""
        if dependency.name in self.ignore:
            return None, 0

        if dependency.name in self.packages:
            expected = self.packages[dependency.name]
            if expected != dependency:
                return (
                    f"in Pipfile {expected.get_pip_install_args()[0]}; "
                    f"got {dependency.get_pip_install_args()[0]}"
                ), logging.WARNING
            return None, 0

        if dependency.name not in self.dev_packages:
            return f"{dependency.name} not found in Pipfile", logging.ERROR

        expected = self.dev_packages[dependency.name]
        if expected != dependency:
            return (
                f"in Pipfile {expected.get_pip_install_args()[0]}; "
                f"got {dependency.get_pip_install_args()[0]}"
            ), logging.WARNING

        return None, 0

    @classmethod
    def parse(
        cls, content: str
    ) -> Tuple[List[str], OrderedDictType[str, OrderedDictType[str, Dependency]]]:
        """Parse from string."""
        sources: List[str] = []
        sections: OrderedDictType = OrderedDict()
        lines = content.split("\n")
        comments = 0
        while len(lines) > 0:
            line = lines.pop(0)
            if "[[source]]" in line:
                source = line + "\n"
                while True:
                    line = lines.pop(0)
                    if line == "":
                        break
                    source += line + "\n"
                sources.append(source)
            if "[dev-packages]" in line or "[packages]" in line:
                section = line
                sections[section] = OrderedDict()
                while len(lines) > 0:
                    line = lines.pop(0).strip()
                    if line == "":
                        break
                    if line.startswith("#"):
                        sections[section][f"comment_{comments}"] = line
                        comments += 1
                    else:
                        # Normalize spacing: 'pkg ="ver"' → 'pkg = "ver"'
                        normalized = re.sub(r'(\S)\s*=\s*"', r'\1 = "', line)
                        try:
                            dep = Dependency.from_pipfile_string(normalized)
                            sections[section][dep.name] = dep
                        except ValueError:
                            logging.warning(f"Could not parse Pipfile line: {line!r}")
                            continue
        return sources, sections

    def compile(self) -> str:
        """Compile to Pipfile string."""
        content = ""
        for source in self.sources:
            content += source + "\n"

        content += "[packages]\n"
        for package, dep in self.packages.items():
            if package.startswith("comment"):
                content += str(dep) + "\n"
            else:
                content += dep.to_pipfile_string() + "\n"

        content += "\n[dev-packages]\n"
        for package, dep in self.dev_packages.items():
            if package.startswith("comment"):
                content += str(dep) + "\n"
            else:
                content += dep.to_pipfile_string() + "\n"
        return content

    @classmethod
    def load(cls, file: Path, exclude: Optional[List[str]] = None) -> "PipfileConfig":
        """Load from file."""
        sources, sections = cls.parse(
            content=file.read_text(encoding="utf-8"),
        )
        return cls(
            sources=sources,
            packages=sections.get("[packages]", OrderedDict()),
            dev_packages=sections.get("[dev-packages]", OrderedDict()),
            file=file,
            exclude=exclude,
        )

    def dump(self) -> None:
        """Write to Pipfile."""
        self.file.write_text(self.compile(), encoding="utf-8")


class ToxConfig:
    """Class to represent tox.ini file."""

    skip = [
        "open-aea-ledger-cosmos",
        "open-aea-ledger-ethereum",
        "open-aea-ledger-fetchai",
    ]

    def __init__(
        self,
        dependencies: Dict[str, Dict[str, Any]],
        file: Path,
        exclude: Optional[List[str]] = None,
    ) -> None:
        """Initialize object."""
        self.dependencies = dependencies
        self.file = file
        self.extra: Dict[str, Dependency] = {}
        self.skip = list(set(self.skip + (exclude or [])))

    def __iter__(self) -> Iterator[Dependency]:
        """Iter dependencies."""
        for obj in self.dependencies.values():
            yield obj["dep"]

    def update(self, dependency: Dependency) -> None:
        """Update dependency specifier."""
        if dependency.name in self.skip:
            return
        if dependency.name in self.dependencies:
            if dependency.version == "":
                return
            self.dependencies[dependency.name]["dep"] = dependency
            return
        self.extra[dependency.name] = dependency

    def check(self, dependency: Dependency) -> Tuple[Optional[str], int]:
        """Check dependency specifier."""
        if dependency.name in self.skip:
            return None, 0

        if dependency.name in self.dependencies:
            expected = self.dependencies[dependency.name]["dep"]
            if (
                expected.name != dependency.name
                and expected.version != dependency.version
            ):
                return (
                    f"in tox.ini {expected.get_pip_install_args()[0]}; "
                    f"got {dependency.get_pip_install_args()[0]}"
                ), logging.WARNING
            return None, 0
        return f"{dependency.name} not found in tox.ini", logging.ERROR

    @classmethod
    def parse(cls, content: str) -> Dict[str, Dict[str, Any]]:
        """Parse file content."""
        deps: Dict[str, Dict[str, Any]] = {}
        lines = content.split("\n")
        while len(lines) > 0:
            line = lines.pop(0)
            if line.startswith("deps"):
                while True:
                    line = lines.pop(0)
                    if not line.startswith("    "):
                        break
                    stripped = line.lstrip()
                    if (
                        stripped.startswith("{")
                        or stripped.startswith(";")
                        or stripped.startswith("#")
                        or stripped == ""
                    ):
                        continue
                    # Strip inline comments (e.g. "pkg==1.0  # comment")
                    dep_str = stripped.split("  #")[0].split("\t#")[0].strip()
                    if not dep_str:
                        continue
                    try:
                        dep = Dependency.from_string(dep_str)
                    except (ValueError, TypeError):
                        continue
                    deps[dep.name] = {
                        "original": line,
                        "dep": dep,
                    }
        return deps

    @classmethod
    def load(cls, file: Path, exclude: Optional[List[str]] = None) -> "ToxConfig":
        """Load tox.ini file."""
        content = file.read_text(encoding="utf-8")
        dependencies = cls.parse(content=content)
        return cls(
            dependencies=dependencies,
            file=file,
            exclude=exclude,
        )

    def _include_extra(self, content: str) -> str:
        """Include extra dependencies."""
        lines = content.split("\n")
        extra = []
        for dep in self.extra.values():
            extra.append(f"    {dep.get_pip_install_args()[0]}")

        if "[extra-deps]" in lines:
            start_idx = lines.index("[extra-deps]") + 2
            end_idx = lines.index("; end-extra")
            extra = list(sorted(set(extra + lines[start_idx:end_idx])))
            lines = lines[:start_idx] + extra + lines[end_idx:]
        else:
            idx = lines.index("[testenv]")
            lines = [
                *lines[:idx],
                "[extra-deps]",
                "deps = ",
                *list(sorted(extra)),
                "; end-extra\n",
                *lines[idx:],
            ]

        return "\n".join(lines)

    def write(self) -> None:
        """Dump config."""
        content = self.file.read_text(encoding="utf-8")
        for obj in self.dependencies.values():
            replace = "    " + cast(Dependency, obj["dep"]).get_pip_install_args()[0]
            content = re.sub(obj["original"], replace, content)

        if len(self.extra) > 0:
            content = self._include_extra(content=content)

        self.file.write_text(content, encoding="utf-8")


class PyProjectTomlConfig:
    """Class to represent pyproject.toml file."""

    ignore = [
        "python",
    ]

    def __init__(
        self,
        dependencies: OrderedDictType[str, Dependency],
        config: Dict[str, Dict],
        file: Path,
        exclude: Optional[List[str]] = None,
        main_dep_names: Optional[Set[str]] = None,
        string_dep_names: Optional[Set[str]] = None,
        group_dep_names: Optional[Set[str]] = None,
    ) -> None:
        """Initialize object."""
        self.dependencies = dependencies
        self.config = config
        self.file = file
        self.ignore = list(set(self.ignore + (exclude or [])))
        # When `main_dep_names` is provided, `__iter__` is scoped to
        # those entries.  Group-only entries still live in
        # `self.dependencies` so `check()` lookups succeed, but they
        # don't get cross-compared against `tox.ini`.  `None` is the
        # documented "unset" value, so plain assignment.
        self._main_dep_names = main_dep_names
        # Names of deps that originated from a plain-string spec in
        # pyproject.toml (e.g. `requests = "*"`).  Only these are safe
        # to rewrite via `Dependency.to_pipfile_string()` in `dump()`;
        # dict-form entries carry metadata (`optional`, `path`,
        # `develop`, `markers`) that the serializer would strip.
        self._string_dep_names = string_dep_names
        # Names declared in any `[tool.poetry.group.*.dependencies]`,
        # captured at load so `dump()` doesn't re-walk `self.config` and
        # doesn't hoist group deps into the main table.
        self._group_dep_names = group_dep_names or set()

    def __iter__(self) -> Iterator[Dependency]:
        """Iterate dependencies."""
        for name, dependency in self.dependencies.items():
            if dependency.name in self.ignore:
                continue
            if self._main_dep_names is not None and name not in self._main_dep_names:
                continue
            yield dependency

    def update(self, dependency: Dependency) -> None:
        """Update dependency specifier."""
        if dependency.name in self.ignore:
            return
        if dependency.name in self.dependencies and dependency.version == "":
            return
        # `dump()` only rewrites string-form deps, so an update to a
        # dict-form main dep (with `optional`/`markers`/etc.) is a no-op
        # on write — warn so a `--update` that appears to do nothing is
        # not silent.
        if (
            dependency.name in self.dependencies
            and self._string_dep_names is not None
            and dependency.name not in self._string_dep_names
            and dependency.name in (self._main_dep_names or set())
        ):
            logging.warning(
                "Update to dict-form dependency %r will not be written by "
                "dump(); bump it manually in pyproject.toml.",
                dependency.name,
            )
        self.dependencies[dependency.name] = dependency

    def check(self, dependency: Dependency) -> Tuple[Optional[str], int]:
        """Check dependency specifier."""
        if dependency.name in self.ignore:
            return None, 0

        if dependency.name not in self.dependencies:
            return f"{dependency.name} not found in pyproject.toml", logging.ERROR

        expected = self.dependencies[dependency.name]
        if expected.name != dependency.name and expected.version != dependency.version:
            return (
                f"in pyproject.toml {expected.get_pip_install_args()[0]}; "
                f"got {dependency.get_pip_install_args()[0]}"
            ), logging.WARNING

        return None, 0

    @staticmethod
    def _normalize_version(version: Any) -> str:
        """Normalize a poetry version constraint to a pip-style specifier."""
        # TOML can legally produce a non-string `version` (e.g.
        # `version = 7` -> int). The type hint promises str, but the
        # caller passes `spec.get("version", "")` straight from parsed
        # TOML, so guard rather than trust.
        if not isinstance(version, str):
            return ""
        if version in ("", "*"):
            return ""
        if version.startswith("^"):
            # Deliberately lossy: PEP 440 has no caret, and the checker
            # compares specifiers as plain strings against package YAMLs
            # which use `==X.Y.Z`. Collapsing `^X.Y.Z` to `==X.Y.Z`
            # matches that convention; the upper bound (`<(X+1).0.0`)
            # implied by Poetry's caret semantics is dropped here.
            return version.replace("^", "==", 1)
        if version[0].isdigit():
            return f"=={version}"
        return version

    @classmethod
    def _dependency_from_spec(
        cls, name: str, spec: Any, pyproject_path: Path
    ) -> Optional[Dependency]:
        """Build a Dependency from a poetry dep spec (string or dict)."""
        if isinstance(spec, str):
            return Dependency(name=name, version=cls._normalize_version(spec))
        if isinstance(spec, dict):
            raw_version = spec.get("version", "")
            if not isinstance(raw_version, str):
                logging.warning(
                    "Non-string version %r for %r in %s; treating as unconstrained.",
                    raw_version,
                    name,
                    pyproject_path,
                )
            return Dependency(
                name=name,
                version=cls._normalize_version(raw_version),
                extras=spec.get("extras"),
            )
        # Lists (multiple constraints with markers) and other shapes are
        # rare in our repos; surface them as a warning so a future
        # contributor knows the entry was skipped rather than silently
        # treated as declared.
        logging.warning(
            "Skipping unrecognized dependency spec for %r in %s: "
            "expected str or dict, got %s.",
            name,
            pyproject_path,
            type(spec).__name__,
        )
        return None

    @classmethod
    def load(
        cls, pyproject_path: Path, exclude: Optional[List[str]] = None
    ) -> Optional["PyProjectTomlConfig"]:
        """Load pyproject.toml dependencies.

        Reads `[tool.poetry.dependencies]` plus every
        `[tool.poetry.group.*.dependencies]` table. Dict-form entries are
        treated as declared even when they omit the `extras` key (so
        `optional = true` deps are visible), and dev/test-only entries
        (e.g. `pytest-asyncio` in the `dev` group) no longer need to be
        duplicated into main deps to satisfy the check.

        Group-origin entries enter `self.dependencies` for `check()`
        lookups but are excluded from `__iter__` / `dump()` so that
        cross-validation against `tox.ini` and `--update` rewrites stay
        scoped to main runtime deps. See `__init__` for the rationale.

        A malformed/unreadable file is logged and propagated (the
        ``TOMLDecodeError`` / ``OSError`` is re-raised) so a corrupt
        pyproject fails the check rather than being silently treated as
        "no deps to verify".

        :param pyproject_path: path to the pyproject.toml file.
        :param exclude: package names to omit from iteration / check.
        :return: a `PyProjectTomlConfig` instance, or `None` if the file
            has no `[tool.poetry.dependencies]` table (the `except
            KeyError` also triggers on a missing `[tool]` /
            `[tool.poetry]` parent).
        """
        try:
            with open(pyproject_path, "rb") as _pyproject_fp:
                config = tomllib.load(_pyproject_fp)
        except (tomllib.TOMLDecodeError, OSError) as exc:
            # Log a readable one-liner, then re-raise: a corrupt file must
            # fail the check (non-zero exit) rather than be silently
            # treated as "no deps to verify" by the caller.
            logging.error("Failed to parse %s: %s", pyproject_path, exc)
            raise
        dependencies: OrderedDictType[str, Dependency] = OrderedDict()
        string_dep_names: Set[str] = set()
        group_dep_names: Set[str] = set()
        try:
            main_deps = config["tool"]["poetry"]["dependencies"]
        except KeyError:
            return None

        # Populated after the main ingest so `_ingest` (closure) can tell
        # a main-vs-group collision from a group-vs-group one.
        main_dep_names: Set[str] = set()

        def _dropped(spec: Any) -> str:
            # Render a colliding spec's version the same way `kept` is
            # rendered, so the warning isn't "==2.0.0" vs a raw dict.
            if isinstance(spec, str):
                return spec or "*"
            if isinstance(spec, dict):
                return str(spec.get("version", spec))
            return repr(spec)

        def _ingest(table: Dict[str, Any]) -> None:
            for name, spec in table.items():
                if name in dependencies:
                    # `_ingest` runs once for main then once per group, so
                    # a collision is either main-vs-group or group-vs-group.
                    # The kept value is whatever landed first; only call it
                    # "main wins" when main is actually involved.
                    kept = dependencies[name].version or "*"
                    if name in main_dep_names:
                        logging.warning(
                            "Dependency %r appears in both main and a group "
                            "in %s; main wins (kept %r, dropped %r).",
                            name,
                            pyproject_path,
                            kept,
                            _dropped(spec),
                        )
                    else:
                        logging.warning(
                            "Dependency %r appears in multiple groups in %s; "
                            "first occurrence wins (kept %r, dropped %r).",
                            name,
                            pyproject_path,
                            kept,
                            _dropped(spec),
                        )
                    continue
                dep = cls._dependency_from_spec(name, spec, pyproject_path)
                if dep is None:
                    continue
                dependencies[name] = dep
                if isinstance(spec, str):
                    string_dep_names.add(name)

        _ingest(main_deps)
        main_dep_names.update(dependencies)

        group_tables = config["tool"]["poetry"].get("group", {})
        if not isinstance(group_tables, dict):
            logging.warning(
                "[tool.poetry.group] in %s is not a table; ignoring.",
                pyproject_path,
            )
            group_tables = {}
        for group_name, group in group_tables.items():
            group_deps = group.get("dependencies") if isinstance(group, dict) else None
            if isinstance(group_deps, dict):
                group_dep_names.update(group_deps)
                _ingest(group_deps)
            else:
                logging.warning(
                    "[tool.poetry.group.%s.dependencies] in %s is not a "
                    "table or is missing; skipping group.",
                    group_name,
                    pyproject_path,
                )

        return cls(
            dependencies=dependencies,
            config=config,
            file=pyproject_path,
            exclude=exclude,
            main_dep_names=main_dep_names,
            string_dep_names=string_dep_names,
            group_dep_names=group_dep_names,
        )

    def dump(self) -> None:
        """Dump to file (line-based, preserving comments and formatting).

        Rewrites string-form main deps in place inside
        ``[tool.poetry.dependencies]`` and appends any newly-added deps
        (e.g. introduced by ``update()`` in ``--update`` mode, which adds
        package-/tox-discovered names not yet in pyproject) at the end of
        that table.  Dict-form entries
        (``docker = { version = "==7.1.0", optional = true }``) carry
        metadata the ``name = version`` form can't represent, so they
        pass through verbatim — which also means an ``update()`` to a
        dict-form dep is not re-emitted (`update()` warns about that).
        Every other section, plus comments (including trailing in-line
        comments on rewritten lines), inline-table formatting and the
        original newline style, is left untouched.
        """
        content = self.file.read_text(encoding="utf-8")
        eol = "\r\n" if "\r\n" in content else "\n"
        out: List[str] = []
        in_main_deps = False
        seen: Set[str] = set()

        def _append_new_main_deps() -> None:
            # Deps in `self.dependencies` that never appeared as a line in
            # the main table and aren't group-origin are newly added (via
            # `update()`); emit them as plain-string form (`update()`
            # never carries dict-form metadata). Group-origin deps stay
            # in their own tables.
            pending = [
                (name, dep)
                for name, dep in self.dependencies.items()
                if name not in seen
                and name not in self._group_dep_names
                and name not in self.ignore
            ]
            if pending and out and not out[-1].endswith(("\n", "\r")):
                out[-1] = out[-1] + eol
            for name, dep in pending:
                out.append(dep.to_pipfile_string() + eol)
                seen.add(name)

        for raw in content.splitlines(keepends=True):
            body = raw.rstrip("\r\n")
            line_eol = raw[len(body) :]
            stripped = body.strip()
            if stripped.startswith("["):
                # Leaving the main-deps table — flush newly-added deps
                # before the next section header (they still belong to
                # the table per TOML, since only a header ends a table).
                if in_main_deps:
                    _append_new_main_deps()
                in_main_deps = stripped == "[tool.poetry.dependencies]"
                out.append(raw)
                continue
            if in_main_deps:
                match = _DEP_LINE_RE.match(body)
                if match:
                    # Mark every top-level key as seen *before* deciding to
                    # rewrite, so a key in no-space form (`pkg="*"`) isn't
                    # re-appended as a duplicate by `_append_new_main_deps`.
                    package = match.group(1)
                    seen.add(package)
                    # Only rewrite plain-string deps; dict-form lines (and
                    # the `python = ...` marker) pass through verbatim so
                    # `optional` / `path` / `develop` / `markers` survive.
                    if package in self.dependencies and (
                        self._string_dep_names is None
                        or package in self._string_dep_names
                    ):
                        _, comment = _split_inline_comment(body)
                        out.append(
                            self.dependencies[package].to_pipfile_string()
                            + comment
                            + line_eol
                        )
                        continue
            out.append(raw)
        if in_main_deps:  # file ended while still inside the table
            _append_new_main_deps()
        self.file.write_text("".join(out), encoding="utf-8")


def load_packages_dependencies(
    packages_dir: Path, exclude: Optional[List[str]] = None
) -> List[Dependency]:
    """Returns a list of package dependencies."""
    exclude = exclude or []
    package_manager = PackageManagerV1.from_dir(packages_dir=packages_dir)
    dependencies: Dict[str, Dependency] = {}
    for package in package_manager.iter_dependency_tree():
        if package.package_type.value == "service":
            continue
        _dependencies = load_configuration(  # type: ignore
            package_type=package.package_type,
            package_path=package_manager.package_path_from_package_id(
                package_id=package
            ),
        ).dependencies
        for key, value in _dependencies.items():
            if key in exclude:
                continue
            if key not in dependencies:
                dependencies[key] = value
            else:
                if value.version == "":
                    continue
                if dependencies[key].version == "":
                    dependencies[key] = value
                if value == dependencies[key]:
                    continue
                print(
                    f"Non-matching dependency versions for {key}: {value} vs {dependencies[key]}"
                )

    return list(dependencies.values())


def _update(
    packages_dependencies: List[Dependency],
    tox: ToxConfig,
    pipfile: Optional[PipfileConfig] = None,
    pyproject: Optional[PyProjectTomlConfig] = None,
) -> None:
    """Update dependencies."""

    if pipfile is not None:
        for dependency in packages_dependencies:
            pipfile.update(dependency=dependency)

        for dependency in pipfile:
            tox.update(dependency=dependency)

        for dependency in tox:
            pipfile.update(dependency=dependency)

        pipfile.dump()

    if pyproject is not None:
        for dependency in packages_dependencies:
            pyproject.update(dependency=dependency)

        for dependency in pyproject:
            tox.update(dependency=dependency)

        for dependency in tox:
            pyproject.update(dependency=dependency)

        pyproject.dump()

    tox.write()


def _check(
    packages_dependencies: List[Dependency],
    tox: ToxConfig,
    pipfile: Optional[PipfileConfig] = None,
    pyproject: Optional[PyProjectTomlConfig] = None,
    strict: bool = False,
) -> None:
    """Check dependencies for consistency."""

    fail_check = 0

    if pipfile is not None:
        print("Comparing dependencies from packages and Pipfile")
        for dependency in packages_dependencies:
            error, level = pipfile.check(dependency=dependency)
            if error is not None:
                logging.log(level=level, msg=error)
                fail_check = level or fail_check

        if strict:
            print("Comparing dependencies from tox and Pipfile")
            for dependency in pipfile:
                error, level = tox.check(dependency=dependency)
                if error is not None:
                    logging.log(level=level, msg=error)
                    fail_check = level or fail_check

            print("Comparing dependencies from Pipfile and tox")
            for dependency in tox:
                error, level = pipfile.check(dependency=dependency)
                if error is not None:
                    logging.log(level=level, msg=error)
                    fail_check = level or fail_check

    if pyproject is not None:
        print("Comparing dependencies from packages and pyproject.toml")
        for dependency in packages_dependencies:
            error, level = pyproject.check(dependency=dependency)
            if error is not None:
                logging.log(level=level, msg=error)
                fail_check = level or fail_check

        if strict:
            print("Comparing dependencies from pyproject.toml and tox")
            for dependency in pyproject:
                error, level = tox.check(dependency=dependency)
                if error is not None:
                    logging.log(level=level, msg=error)
                    fail_check = level or fail_check

        if strict:
            print("Comparing dependencies from tox and pyproject.toml")
            for dependency in tox:
                error, level = pyproject.check(dependency=dependency)
                if error is not None:
                    logging.log(level=level, msg=error)
                    fail_check = level or fail_check

    print("Comparing dependencies from packages and tox")
    for dependency in packages_dependencies:
        error, level = tox.check(dependency=dependency)
        if error is not None:
            logging.log(level=level, msg=error)
            fail_check = level or fail_check

    if fail_check == logging.ERROR:
        print("Dependencies check failed")
        sys.exit(1)

    if fail_check == logging.WARNING:
        print("Please address warnings to avoid errors")
        sys.exit(0)

    print("No issues found")


@click.command(name="check-dependencies")
@click.option(
    "--check",
    "check_only",
    is_flag=True,
    help="Validate only, do not update files.",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Enable full cross-validation between all dependency files.",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Package names to exclude from checks (repeatable).",
)
@click.option(
    "--packages",
    "packages_dir",
    type=PathArgument(exists=True, file_okay=False, dir_okay=True),
    help="Path of the packages directory.",
)
@click.option(
    "--tox",
    "tox_path",
    type=PathArgument(exists=True, file_okay=True, dir_okay=False),
    help="tox.ini path.",
)
@click.option(
    "--pipfile",
    "pipfile_path",
    type=PathArgument(exists=True, file_okay=True, dir_okay=False),
    help="Pipfile path.",
)
@click.option(
    "--pyproject",
    "pyproject_path",
    type=PathArgument(exists=True, file_okay=True, dir_okay=False),
    help="pyproject.toml path.",
)
def check_dependencies(
    check_only: bool = False,
    strict: bool = False,
    exclude: tuple = (),
    packages_dir: Optional[Path] = None,
    tox_path: Optional[Path] = None,
    pipfile_path: Optional[Path] = None,
    pyproject_path: Optional[Path] = None,
) -> None:
    """Check dependencies across packages, tox.ini, pyproject.toml and Pipfile."""

    logging.basicConfig(format="- %(levelname)s: %(message)s")
    exclude_list = list(exclude)

    tox_path = tox_path or Path.cwd() / "tox.ini"
    tox = ToxConfig.load(tox_path, exclude=exclude_list)

    # If user explicitly passed --pipfile or --pyproject, use what they asked for.
    # Otherwise auto-detect: prefer Pipfile if it exists, fall back to pyproject.toml.
    # Only use one — not both — to match the original per-repo behavior.
    user_specified_pipfile = pipfile_path is not None
    user_specified_pyproject = pyproject_path is not None

    pipfile_path = pipfile_path or Path.cwd() / "Pipfile"
    pyproject_path = pyproject_path or Path.cwd() / "pyproject.toml"

    if user_specified_pipfile or user_specified_pyproject:
        # Explicit: load only what was requested
        pipfile = (
            PipfileConfig.load(pipfile_path, exclude=exclude_list)
            if user_specified_pipfile and pipfile_path.exists()
            else None
        )
        pyproject = (
            PyProjectTomlConfig.load(pyproject_path, exclude=exclude_list)
            if user_specified_pyproject and pyproject_path.exists()
            else None
        )
    elif pipfile_path.exists():
        # Auto-detect: Pipfile takes precedence
        pipfile = PipfileConfig.load(pipfile_path, exclude=exclude_list)
        pyproject = None
    elif pyproject_path.exists():
        # Auto-detect: fall back to pyproject.toml
        pipfile = None
        pyproject = PyProjectTomlConfig.load(pyproject_path, exclude=exclude_list)
    else:
        pipfile = None
        pyproject = None

    packages_dir = packages_dir or Path.cwd() / "packages"
    packages_dependencies = load_packages_dependencies(
        packages_dir=packages_dir, exclude=exclude_list
    )

    if check_only:
        return _check(
            tox=tox,
            pipfile=pipfile,
            pyproject=pyproject,
            packages_dependencies=packages_dependencies,
            strict=strict,
        )

    return _update(
        tox=tox,
        pipfile=pipfile,
        pyproject=pyproject,
        packages_dependencies=packages_dependencies,
    )
