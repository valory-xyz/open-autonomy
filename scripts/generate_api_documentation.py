#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This tool generates the API docs."""
import argparse
import re
import shutil
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Set

from aea.configurations.base import ComponentType, PublicId
from aea.configurations.constants import PACKAGES


DOCS_DIR = Path("docs/")
API_DIR = DOCS_DIR / "api/"
AEA_DIR = Path("autonomy")
PACKAGES_DIR = Path(PACKAGES)
PLUGIN_DIR = Path("plugins")
DEFAULT_PACKAGES = {
    (ComponentType.CONNECTION, "valory/abci:latest"),
    (ComponentType.CONTRACT, "valory/gnosis_safe:latest"),
    (ComponentType.CONTRACT, "valory/gnosis_safe_proxy_factory:latest"),
    (ComponentType.PROTOCOL, "valory/abci:latest"),
    (ComponentType.SKILL, "valory/abstract_abci:latest"),
    (ComponentType.SKILL, "valory/abstract_round_abci:latest"),
    (ComponentType.SKILL, "valory/oracle_abci:latest"),
    (ComponentType.SKILL, "valory/oracle_deployment_abci:latest"),
    (ComponentType.SKILL, "valory/price_estimation_abci:latest"),
    (ComponentType.SKILL, "valory/registration_abci:latest"),
    (ComponentType.SKILL, "valory/safe_deployment_abci:latest"),
    (ComponentType.SKILL, "valory/transaction_settlement_abci:latest"),
}

IGNORE_NAMES = {
    r"^__init__\.py$",
    r"^__main__\.py$",
    r"^__version__\.py$",
    r"^py\.typed$",
    r"^.*_pb2.py$",
    r"^..*_pb2_grpc.py$",
    r"^test_.*\.py$",
    r"^conftest\.py$",
}
IGNORE_PREFIXES: Set[Path] = set()


def check_working_tree_is_dirty() -> None:
    """Check if the current Git working tree is dirty."""
    print("Checking if there are any newly generated doc file...")
    result = subprocess.check_output(["git", "status"])  # nosec
    if len(result) > 0:
        files = [
            file.replace("modified:", "").strip()
            for file in result.decode("utf-8").split("\n")
            if "modified:" in file
        ]
        filterd_md_files = [
            file for file in files if file.endswith(".md") and file.startswith("docs")
        ]
        if len(filterd_md_files) > 0:
            print("\nNewly generated doc files:\n")
            print("\n".join(filterd_md_files))
            sys.exit(1)

    print("All good!")


def create_subdir(path: str) -> None:
    """
    Create a subdirectory.

    :param path: the directory path
    """
    directory = "/".join(path.split("/")[:-1])
    Path(directory).mkdir(parents=True, exist_ok=True)


def replace_underscores(text: str) -> str:
    """
    Replace escaped underscores in a text.

    :param text: the text
    :return: the processed text
    """
    text_a = text.replace("\\_\\_", "`__`")
    text_b = text_a.replace("\\_", "`_`")
    return text_b


def is_relative_to(path_one: Path, path_two: Path) -> bool:
    """Check if a path is relative to another path."""
    return str(path_one).startswith(str(path_two))


def is_not_dir(path: Path) -> bool:
    """Call p.is_dir() method and negate the result."""
    return not path.is_dir()


def should_skip(module_path: Path) -> bool:
    """Return true if the file should be skipped."""
    if any(re.search(pattern, module_path.name) for pattern in IGNORE_NAMES):
        print("Skipping, it's in ignore patterns")
        return True
    if module_path.suffix != ".py":
        print("Skipping, it's not a Python module.")
        return True
    if any(is_relative_to(module_path, prefix) for prefix in IGNORE_PREFIXES):
        print(f"Ignoring prefix {module_path}")
        return True
    return False


def _generate_apidocs_aea_modules() -> None:
    """Generate API docs for aea.* modules."""
    for module_path in filter(is_not_dir, Path(AEA_DIR).rglob("*")):
        print(f"Processing {module_path}... ", end="")
        if should_skip(module_path):
            continue
        parents = module_path.parts[:-1]
        parents_without_root = module_path.parts[1:-1]
        last = module_path.stem
        doc_file = API_DIR / Path(*parents_without_root) / f"{last}.md"
        dotted_path = ".".join(parents) + "." + last
        make_pydoc(dotted_path, doc_file)


def _generate_apidocs_packages() -> None:
    """Generate API docs for default packages."""
    for component_type, default_package in DEFAULT_PACKAGES:
        public_id = PublicId.from_str(default_package)
        author = public_id.author
        name = public_id.name
        type_plural = component_type.to_plural()
        package_dir = PACKAGES_DIR / author / type_plural / name
        for module_path in package_dir.rglob("*.py"):
            print(f"Processing {module_path}...", end="")
            if should_skip(module_path):
                continue
            suffix = Path(str(module_path.relative_to(package_dir))[:-3] + ".md")
            dotted_path = ".".join(module_path.parts)[:-3]
            doc_file = API_DIR / type_plural / name / suffix
            make_pydoc(dotted_path, doc_file)


def _generate_apidocs_plugins() -> None:
    """Generate API docs for cyrpto plugins."""
    for plugin in PLUGIN_DIR.iterdir():
        plugin_name = plugin.name
        plugin_module_name = plugin_name.replace("-", "_")
        python_package_root = plugin / plugin_module_name
        for module_path in python_package_root.rglob("*.py"):
            print(f"Processing {module_path}...", end="")
            if should_skip(module_path):
                continue
            # remove ".py"
            relative_module_path = module_path.relative_to(python_package_root)
            suffix = Path(str(relative_module_path)[:-3] + ".md")
            dotted_path = ".".join(module_path.parts)[:-3]
            doc_file = API_DIR / "plugins" / plugin_module_name / suffix
            make_pydoc(dotted_path, doc_file)


def make_pydoc(dotted_path: str, dest_file: Path) -> None:
    """Make a PyDoc file."""
    print(
        f"Running with dotted path={dotted_path} and dest_file={dest_file}... ", end=""
    )
    try:
        api_doc_content = run_pydoc_markdown(dotted_path)
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        dest_file.write_text(api_doc_content)
    except Exception as e:  # pylint: disable=broad-except,invalid-name
        print(f"Error: {str(e)}")
        return
    print("Done!")


def run_pydoc_markdown(module: str) -> str:
    """
    Run pydoc-markdown.

    :param module: the dotted path.
    :return: the PyDoc content (pre-processed).
    """
    pydoc = subprocess.Popen(  # nosec # pylint: disable=consider-using-with
        ["pydoc-markdown", "-m", module, "-I", "."], stdout=subprocess.PIPE
    )
    stdout, _ = pydoc.communicate()
    pydoc.wait()
    stdout_text = stdout.decode("utf-8")
    text = replace_underscores(stdout_text)
    return text


def generate_api_docs() -> None:
    """Generate the api docs."""
    shutil.rmtree(API_DIR, ignore_errors=True)
    API_DIR.mkdir()
    _generate_apidocs_packages()
    _generate_apidocs_aea_modules()
    _generate_apidocs_plugins()


def install(package: str) -> int:
    """
    Install a PyPI package by calling pip.

    :param package: the package name and version specifier.
    :return: the return code.
    """
    return subprocess.check_call(  # nosec
        [sys.executable, "-m", "pip", "install", package]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("generate_api_docs")
    parser.add_argument(
        "--check-clean", action="store_true", help="Check if the working tree is clean."
    )
    arguments = parser.parse_args()

    res = shutil.which("pydoc-markdown")
    if res is None:
        install("pydoc-markdown==3.3.0")
        sys.exit(1)

    generate_api_docs()
    if arguments.check_clean:
        check_working_tree_is_dirty()
