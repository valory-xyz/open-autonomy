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
    """Update address books in data dump to use them in replays.

    Malformed individual peer entries (missing ``addr``/``ip`` keys or
    a non-dotted IP) are skipped with a warning so a single bad entry
    does not leave the addrbook half-rewritten and abort the sweep of
    the remaining files.

    :param build_dir: build directory containing the tendermint state dump.
    """
    for addr_file in sorted(
        (build_dir / PERSISTENT_DATA_DIR / TM_STATE_DIR).glob("**/addrbook.json")
    ):
        addr_data = json.loads(addr_file.read_text())
        for entry in addr_data.get("addrs") or []:
            addr = entry.get("addr") if isinstance(entry, dict) else None
            if not isinstance(addr, dict):
                print(f"Skipping malformed peer entry in {addr_file}: {entry!r}")
                continue
            ip = addr.get("ip")
            if not isinstance(ip, str) or "." not in ip:
                print(f"Skipping peer with non-dotted IP in {addr_file}: {ip!r}")
                continue
            *_, post_fix = ip.split(".")
            try:
                new_port = int(f"2663{int(post_fix) - 3}")
            except ValueError:
                print(
                    f"Skipping peer with non-numeric IP suffix in {addr_file}: {ip!r}"
                )
                continue
            addr["ip"] = "127.0.0.1"
            addr["port"] = new_port

        addr_file.write_text(json.dumps(addr_data, indent=4))
        print(f"Updated {addr_file}")


def fix_config_files(build_dir: Path) -> None:
    """Update config.toml in data dump to use them in replays.

    :param build_dir: build directory containing the tendermint state dump.
    """
    for config_file in sorted(
        (build_dir / PERSISTENT_DATA_DIR / TM_STATE_DIR).glob("**/config.toml")
    ):
        config = config_file.read_text()
        config = config.replace("persistent_peers =", "# persistent_peers =")
        config_file.write_text(config)
        print(f"Updated {config_file}")


def load_docker_config(file_path: Path) -> Dict[str, Any]:  # pragma: nocover
    """Load docker config.

    :param file_path: docker-compose YAML path.
    :return: parsed mapping.
    :raises ValueError: if the top-level YAML node is not a mapping.
    """
    with open(str(file_path), "r", encoding="utf-8") as fp:
        docker_compose_config = yaml.safe_load(fp)

    if not isinstance(docker_compose_config, dict):
        raise ValueError(
            f"Expected a mapping at the top of {file_path}, got "
            f"{type(docker_compose_config).__name__}"
        )

    return docker_compose_config
