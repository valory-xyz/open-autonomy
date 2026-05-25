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

"""Utils module."""

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from autonomy.deploy.constants import PERSISTENT_DATA_DIR, TM_STATE_DIR


def fix_address_books(build_dir: Path) -> None:
    """Update address books in data dump to use them in replays."""
    for addr_file in sorted(
        (build_dir / PERSISTENT_DATA_DIR / TM_STATE_DIR).glob("**/addrbook.json")
    ):
        try:
            addr_data = json.loads(addr_file.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in {addr_file}: {exc}") from exc
        for i in range(len(addr_data["addrs"])):
            *_, post_fix = addr_data["addrs"][i]["addr"]["ip"].split(".")
            addr_data["addrs"][i]["addr"]["ip"] = "127.0.0.1"
            addr_data["addrs"][i]["addr"]["port"] = int(f"2663{int(post_fix) - 3}")

        addr_file.write_text(json.dumps(addr_data, indent=4))
        print(f"Updated {addr_file}")


def fix_config_files(build_dir: Path) -> None:
    """Update config.toml in data dump to use them in replays."""
    for config_file in sorted(
        (build_dir / PERSISTENT_DATA_DIR / TM_STATE_DIR).glob("**/config.toml")
    ):
        try:
            config = config_file.read_text()
        except OSError as exc:
            raise FileNotFoundError(
                f"Could not read tendermint config at {config_file}: {exc}"
            ) from exc
        config = config.replace("persistent_peers =", "# persistent_peers =")
        config_file.write_text(config)
        print(f"Updated {config_file}")


def load_docker_config(file_path: Path) -> Dict[str, Any]:  # pragma: nocover
    """Load docker config."""
    try:
        with open(str(file_path), "r", encoding="utf-8") as fp:
            docker_compose_config = yaml.safe_load(fp)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Docker compose config not found at {file_path}"
        ) from exc
    except yaml.YAMLError as exc:
        raise yaml.YAMLError(
            f"Malformed YAML in docker compose config at {file_path}: {exc}"
        ) from exc

    if not isinstance(docker_compose_config, dict):
        raise ValueError(
            f"Expected a mapping at the top of {file_path}, got "
            f"{type(docker_compose_config).__name__}"
        )

    return docker_compose_config
