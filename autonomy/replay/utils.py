# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

from autonomy.deploy.constants import PERSISTENT_DATA_DIR, TM_STATE_DIR


def fix_address_books(build_dir: Path) -> None:
    """Update address books in data dump to use them in replays."""
    for addr_file in sorted(
        (build_dir / PERSISTENT_DATA_DIR / TM_STATE_DIR).glob("**/addrbook.json")
    ):
        addr_data = json.loads(addr_file.read_text())
        for i in range(len(addr_data["addrs"])):
            *_, post_fix = addr_data["addrs"][i]["addr"]["ip"].split(".")
            addr_data["addrs"][i]["addr"]["ip"] = "127.0.0.1"
            addr_data["addrs"][i]["addr"]["port"] = int(f"2663{int(post_fix)-3}")

        addr_file.write_text(json.dumps(addr_data, indent=4))
        print(f"Updated {addr_file}")


def fix_config_files(build_dir: Path) -> None:
    """Update config.toml in data dump to use them in replays."""
    for config_file in sorted(
        (build_dir / PERSISTENT_DATA_DIR / TM_STATE_DIR).glob("**/config.toml")
    ):
        config = config_file.read_text()
        config = config.replace("persistent_peers =", "# persistent_peers =")
        config_file.write_text(config)
        print(f"Updated {config_file}")
