"""Script for bumping core dependencies."""

import typing as t
from pathlib import Path

import click
import requests
from aea.cli.utils.click_utils import PyPiDependency
from aea.configurations.constants import PACKAGES, PACKAGE_TYPE_TO_CONFIG_FILE
from aea.configurations.data_types import Dependency
from aea.helpers.logging import setup_logger
from aea.helpers.yaml_utils import yaml_dump_all, yaml_load_all
from aea.package_manager.v1 import PackageManagerV1

from autonomy.cli.helpers.ipfs_hash import load_configuration


BUMP_BRANCH = "chore/bump"
PIPFILE = Path.cwd() / "Pipfile"
PYPROJECT_TOML = Path.cwd() / "pyproject.toml"
TOX_INI = Path.cwd() / "tox.ini"
TAGS_URL = "https://api.github.com/repos/{repo}/tags"
OPEN_AEA_REPO = "valory-xyz/open-aea"
OPEN_AUTONOMY_REPO = "valory-xyz/open-autonomy"

_repo_version_cache = {}

_logger = setup_logger("bump")


def get_latest_tag(repo: str) -> str:
    """Fetch latest git tag."""
    response = requests.get(url=TAGS_URL.format(repo=repo))
    if response.status_code != 200:
        raise ValueError(
            f"Fetching tags from `{repo}` failed with message '"
            + response.json()["message"]
            + "'"
        )
    latest_tag_data, *_ = response.json()
    _repo_version_cache[repo] = latest_tag_data["name"]
    return _repo_version_cache[repo]


def get_open_aea_dependencies() -> t.Dict[str, str]:
    """Get open-aea dependencies."""
    version = get_latest_tag(OPEN_AEA_REPO).replace("v", "")
    return {
        "open-aea": f"=={version}",
        "open-aea-ledger-ethereum": f"=={version}",
        "open-aea-ledger-ethereum-flashbots": f"=={version}",
        "open-aea-ledger-ethereum-hwi": f"=={version}",
        "open-aea-ledger-cosmos": f"=={version}",
        "open-aea-ledger-solana": f"=={version}",
        "open-aea-cli-ipfs": f"=={version}",
    }


def get_open_autonomy_dependencies() -> t.Dict[str, str]:
    """Get open-autonomy dependencies."""
    version = get_latest_tag(OPEN_AUTONOMY_REPO).replace("v", "")
    return {
        "open-autonomy": f"=={version}",
        "open-aea-test-autonomy": f"=={version}",
    }


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
@click.option("--sync", "sync", is_flag=True, help="Perform sync.")
def main(extra: t.List[Dependency], sync: bool) -> None:
    """Run the bump script."""
    dependencies = {}
    dependencies.update(get_open_aea_dependencies())
    dependencies.update(get_open_autonomy_dependencies())
    dependencies.update({dep.name: dep.version for dep in extra or []})

    bump_pipfile_or_pyproject(PIPFILE, dependencies=dependencies)
    bump_pipfile_or_pyproject(PYPROJECT_TOML, dependencies=dependencies)
    bump_tox(dependencies=dependencies)
    bump_packages(dependencies=dependencies)

    if sync:
        pm = PackageManagerV1.from_dir(
            Path.cwd() / PACKAGES, config_loader=load_configuration
        )
        pm.sync(
            sources=[
                f"{OPEN_AEA_REPO}:{_repo_version_cache[OPEN_AEA_REPO]}",
                f"{OPEN_AUTONOMY_REPO}:{_repo_version_cache[OPEN_AUTONOMY_REPO]}",
            ]
        )
        pm.update_package_hashes()
        pm.dump()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
