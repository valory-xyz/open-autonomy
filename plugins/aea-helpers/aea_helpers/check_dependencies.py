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
from typing import Tuple, cast

import click
import toml
from aea.configurations.data_types import Dependency
from aea.package_manager.base import load_configuration
from aea.package_manager.v1 import PackageManagerV1

ANY_SPECIFIER = "*"


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
        "open-aea-flashbots",
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
    ) -> None:
        """Initialize object."""
        self.dependencies = dependencies
        self.config = config
        self.file = file
        self.ignore = list(set(self.ignore + (exclude or [])))

    def __iter__(self) -> Iterator[Dependency]:
        """Iterate dependencies."""
        for dependency in self.dependencies.values():
            if dependency.name not in self.ignore:
                yield dependency

    def update(self, dependency: Dependency) -> None:
        """Update dependency specifier."""
        if dependency.name in self.ignore:
            return
        if dependency.name in self.dependencies and dependency.version == "":
            return
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

    @classmethod
    def load(
        cls, pyproject_path: Path, exclude: Optional[List[str]] = None
    ) -> Optional["PyProjectTomlConfig"]:
        """Load pyproject.toml dependencies."""
        config = toml.load(pyproject_path)
        dependencies: OrderedDictType[str, Dependency] = OrderedDict()
        try:
            config["tool"]["poetry"]["dependencies"]
        except KeyError:
            return None
        for name, version in config["tool"]["poetry"]["dependencies"].items():
            if isinstance(version, str):
                dependencies[name] = Dependency(
                    name=name,
                    version=version.replace("^", "==") if version != "*" else "",
                )
                continue
            data = cast(Dict, version)
            if "extras" in data:
                version = data["version"]
                if re.match(r"^\d", version):
                    version = f"=={version}"
                dependencies[name] = Dependency(
                    name=name,
                    version=version,
                    extras=data["extras"],
                )
                continue

        return cls(
            dependencies=dependencies,
            config=config,
            file=pyproject_path,
            exclude=exclude,
        )

    def dump(self) -> None:
        """Dump to file."""
        update = ""
        content = self.file.read_text(encoding="utf-8")
        for line in content.split("\n"):
            if " = " not in line:
                update += f"{line}\n"
                continue
            package, *_ = line.split(" = ")
            dep = self.dependencies.get(package)
            if dep is None:
                update += f"{line}\n"
                continue
            update += f"{dep.to_pipfile_string()}\n"
        self.file.write_text(update[:-1], encoding="utf-8")


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
) -> None:
    """Check dependencies for consistency."""

    fail_check = 0

    if pipfile is not None:
        print("Comparing dependencies from Pipfile and packages")
        for dependency in packages_dependencies:
            error, level = pipfile.check(dependency=dependency)
            if error is not None:
                logging.log(level=level, msg=error)
                fail_check = level or fail_check

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
        print("Comparing dependencies from pyproject.toml and packages")
        for dependency in packages_dependencies:
            error, level = pyproject.check(dependency=dependency)
            if error is not None:
                logging.log(level=level, msg=error)
                fail_check = level or fail_check

        print("Comparing dependencies from pyproject.toml and tox")
        for dependency in pyproject:
            error, level = tox.check(dependency=dependency)
            if error is not None:
                logging.log(level=level, msg=error)
                fail_check = level or fail_check

        print("Comparing dependencies from tox and pyproject.toml")
        for dependency in tox:
            error, level = pyproject.check(dependency=dependency)
            if error is not None:
                logging.log(level=level, msg=error)
                fail_check = level or fail_check

    print("Comparing dependencies from tox and packages")
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

    pipfile_path = pipfile_path or Path.cwd() / "Pipfile"
    pipfile = (
        PipfileConfig.load(pipfile_path, exclude=exclude_list)
        if pipfile_path.exists()
        else None
    )

    pyproject_path = pyproject_path or Path.cwd() / "pyproject.toml"
    pyproject = (
        PyProjectTomlConfig.load(pyproject_path, exclude=exclude_list)
        if pyproject_path.exists()
        else None
    )

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
        )

    return _update(
        tox=tox,
        pipfile=pipfile,
        pyproject=pyproject,
        packages_dependencies=packages_dependencies,
    )
