"""
Script for bumping core dependencies.

This script

- Fetches the latest core dependency versions from github
- Updates the tox.ini, packages and Pipfile/pyproject.toml files
- Performs the packages sync
"""

import os
import re
import typing as t
from pathlib import Path

import click
import requests
from aea.cli.utils.click_utils import PackagesSource, PyPiDependency
from aea.configurations.constants import PACKAGES, PACKAGE_TYPE_TO_CONFIG_FILE
from aea.configurations.data_types import Dependency
from aea.helpers.logging import setup_logger
from aea.helpers.yaml_utils import yaml_dump, yaml_dump_all, yaml_load, yaml_load_all
from aea.package_manager.v1 import PackageManagerV1

from autonomy.cli.helpers.ipfs_hash import load_configuration


BUMP_BRANCH = "chore/bump"
PIPFILE = Path.cwd() / "Pipfile"
PYPROJECT_TOML = Path.cwd() / "pyproject.toml"
TOX_INI = Path.cwd() / "tox.ini"

TAGS_URL = "https://api.github.com/repos/{repo}/tags"
FILE_URL = "https://raw.githubusercontent.com/{repo}/{tag}/{file}"

VERISON_RE = re.compile(r"(__version__|version)( )?=( )?\"(?P<version>[0-9a-z\.]+)\"")

OPEN_AEA_REPO = "valory-xyz/open-aea"
OPEN_AUTONOMY_REPO = "valory-xyz/open-autonomy"

DEPENDENCY_SPECS = {
    "open-aea": {
        "repo": OPEN_AEA_REPO,
        "file": "aea/__version__.py",
    },
    "open-aea-ledger-ethereum": {
        "repo": OPEN_AEA_REPO,
        "file": "plugins/aea-ledger-ethereum/setup.py",
    },
    "open-aea-ledger-ethereum-flashbots": {
        "repo": OPEN_AEA_REPO,
        "file": "plugins/aea-ledger-ethereum-flashbots/setup.py",
    },
    "open-aea-ledger-ethereum-hwi": {
        "repo": OPEN_AEA_REPO,
        "file": "plugins/aea-ledger-ethereum-hwi/setup.py",
    },
    "open-aea-ledger-cosmos": {
        "repo": OPEN_AEA_REPO,
        "file": "plugins/aea-ledger-cosmos/setup.py",
    },
    "open-aea-ledger-solana": {
        "repo": OPEN_AEA_REPO,
        "file": "plugins/aea-ledger-solana/setup.py",
    },
    "open-aea-cli-ipfs": {
        "repo": OPEN_AEA_REPO,
        "file": "plugins/aea-cli-ipfs/setup.py",
    },
    "open-autonomy": {
        "repo": OPEN_AUTONOMY_REPO,
        "file": "autonomy/__version__.py",
    },
    "open-aea-test-autonomy": {
        "repo": OPEN_AUTONOMY_REPO,
        "file": "plugins/aea-test-autonomy/setup.py",
    },
}

_cache_file = Path.home() / ".aea" / ".gitcache"
_version_cache = {}
_logger = setup_logger("bump")


def load_git_cache() -> None:
    """Load versions cache."""
    if not _cache_file.exists():
        return
    with _cache_file.open("r", encoding="utf-8") as stream:
        _version_cache.update(yaml_load(stream=stream))


def dump_git_cache() -> None:
    """Dump versions cache."""
    with _cache_file.open("w", encoding="utf-8") as stream:
        yaml_dump(data=_version_cache, stream=stream)


def make_git_request(url: str) -> requests.Response:
    """Make git request"""
    auth = os.environ.get("GITHUB_AUTH")
    if auth is None:
        return requests.get(url=url)
    return requests.get(url=url, headers={"Authorization": f"Bearer {auth}"})


def get_latest_tag(repo: str) -> str:
    """Fetch latest git tag."""
    if repo in _version_cache:
        return _version_cache[repo]

    response = make_git_request(url=TAGS_URL.format(repo=repo))
    if response.status_code != 200:
        raise ValueError(
            f"Fetching tags from `{repo}` failed with message '"
            + response.json()["message"]
            + "'"
        )
    latest_tag_data, *_ = response.json()
    _version_cache[repo] = latest_tag_data["name"]
    return _version_cache[repo]


def get_dependency_version(repo: str, file: str) -> str:
    """Get version spec ."""
    response = make_git_request(
        FILE_URL.format(
            repo=repo,
            tag=get_latest_tag(repo=repo),
            file=file,
        )
    )
    if response.status_code != 200:
        raise ValueError(
            f"Fetching packages from `{repo}` failed with message '"
            + response.text
            + "'"
        )
    ((*_, version),) = VERISON_RE.findall(response.content.decode())
    return f"=={version}"


def get_dependencies() -> t.Dict:
    """Get dependency->version mapping."""
    dependencies = {}
    for dependency, specs in DEPENDENCY_SPECS.items():
        version = _version_cache.get(
            dependency,
            get_dependency_version(
                repo=specs["repo"],
                file=specs["file"],
            ),
        )
        dependencies[dependency] = version
    _version_cache.update(dependencies)
    return dependencies


def bump_pipfile_or_pyproject(file: Path, dependencies: t.Dict[str, str]) -> None:
    """Bump Pipfile."""
    if not file.exists():
        return

    _logger.info(f"Updating {file.name}")
    updated = ""
    content = file.read_text(encoding="utf-8")
    for line in content.split("\n"):
        try:
            spec = Dependency.from_pipfile_string(line)
            update = dependencies.get(spec.name)
            if update is None:
                updated += line + "\n"
                continue
            spec = Dependency(
                name=spec.name,
                version=update,
                extras=spec.extras,
            )
            updated += spec.to_pipfile_string() + "\n"
        except ValueError:
            updated += line + "\n"
    file.write_text(updated[:-1], encoding="utf-8")


def bump_tox(dependencies: t.Dict[str, str]) -> None:
    """Bump tox file."""
    if not TOX_INI.exists():
        return

    _logger.info("Updating tox.ini")
    updated = ""
    content = TOX_INI.read_text(encoding="utf-8")
    for line in content.split("\n"):
        try:
            spec = Dependency.from_string(line.lstrip().rstrip())
            update = dependencies.get(spec.name)
            if update is None:
                updated += line + "\n"
                continue
            spec = Dependency(
                name=spec.name,
                version=update,
                extras=spec.extras,
            )
            updated += "    " + spec.to_pip_string() + "\n"
        except ValueError:
            updated += line + "\n"
    TOX_INI.write_text(updated[:-1], encoding="utf-8")


def bump_packages(dependencies: t.Dict[str, str]) -> None:
    """Bump packages."""
    _logger.info("Updating packages")
    manager = PackageManagerV1.from_dir(Path(PACKAGES))
    for package_id in manager.dev_packages:
        path = (
            manager.package_path_from_package_id(
                package_id=package_id,
            )
            / PACKAGE_TYPE_TO_CONFIG_FILE[package_id.package_type.value]
        )
        with path.open("r", encoding="utf-8") as stream:
            config, *extra = yaml_load_all(stream=stream)

        for name in config.get("dependencies", {}):
            update = dependencies.get(name)
            if update is None:
                continue
            config["dependencies"][name]["version"] = update

        with path.open("w", encoding="utf-8") as stream:
            yaml_dump_all([config, *extra], stream=stream)


@click.command(name="bump")
@click.option(
    "-d",
    "--dependency",
    "extra",
    type=PyPiDependency(),
    multiple=True,
    help="Specify extra dependency.",
)
@click.option(
    "-s",
    "--source",
    "sources",
    type=PackagesSource(),
    multiple=True,
    help="Specify extra sources.",
)
@click.option("--sync", is_flag=True, help="Perform sync.")
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Avoid using cache to bump.",
)
def main(
    extra: t.Tuple[Dependency, ...],
    sources: t.Tuple[str, ...],
    sync: bool,
    no_cache: bool,
) -> None:
    """Run the bump script."""

    if not no_cache:
        load_git_cache()

    dependencies = {}
    dependencies.update(get_dependencies())
    dependencies.update({dep.name: dep.version for dep in extra or []})

    bump_pipfile_or_pyproject(PIPFILE, dependencies=dependencies)
    bump_pipfile_or_pyproject(PYPROJECT_TOML, dependencies=dependencies)
    bump_tox(dependencies=dependencies)
    bump_packages(dependencies=dependencies)
    dump_git_cache()

    if sync:
        pm = PackageManagerV1.from_dir(
            Path.cwd() / PACKAGES, config_loader=load_configuration
        )
        pm.sync(
            sources=[
                f"{OPEN_AEA_REPO}:{_version_cache[OPEN_AEA_REPO]}",
                f"{OPEN_AUTONOMY_REPO}:{_version_cache[OPEN_AUTONOMY_REPO]}",
                *sources,
            ],
            update_packages=True,
        )
        pm.update_package_hashes()
        pm.dump()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
