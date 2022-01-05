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

"""Script to experiment with different tendermint block time settings."""

from glob import glob
from typing import List

TIMEOUT_SETTING_MATCH = """# How long we wait for a proposal block before prevoting nil
timeout_propose = "3s"
# How much timeout_propose increases with each round
timeout_propose_delta = "500ms"
# How long we wait after receiving +2/3 prevotes for “anything” (ie. not a single block or nil)
timeout_prevote = "1s"
# How much the timeout_prevote increases with each round
timeout_prevote_delta = "500ms"
# How long we wait after receiving +2/3 precommits for “anything” (ie. not a single block or nil)
timeout_precommit = "1s"
# How much the timeout_precommit increases with each round
timeout_precommit_delta = "500ms"
# How long we wait after committing a block, before starting on the new
# height (this gives us a chance to receive some more precommits, even
# though we already have +2/3).
timeout_commit = "1s"
"""

TIMEOUT_SETTING_TEMPLATE = """
timeout_propose = "{timeout_propose}ms"
timeout_propose_delta = "{timeout_propose_delta}ms"
timeout_prevote = "{timeout_prevote}ms"
timeout_prevote_delta = "{timeout_prevote_delta}ms"
timeout_precommit = "{timeout_precommit}ms"
timeout_precommit_delta = "{timeout_precommit_delta}ms"
timeout_commit = "{timeout_commit}ms"
"""

timeout_config_data = {
    "timeout_propose": 3000,  # default: 3000
    "timeout_propose_delta": 500,  # default: 500
    "timeout_prevote": 1000,  # default: 1000
    "timeout_prevote_delta": 500,  # default: 500
    "timeout_precommit": 1000,  # default: 1000
    "timeout_precommit_delta": 500,  # default: 500
    "timeout_commit": 2000,  # default: 1000
}


def get_file_list() -> List[str]:
    """Returns a list of files containing config for tendermint validator nodes."""
    return glob("./build/*/config/config.toml")


def main():
    """Main function."""

    config_files = get_file_list()
    timeout_config = TIMEOUT_SETTING_TEMPLATE.format(**timeout_config_data)

    for file_path in config_files:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()

        file_content = file_content.replace(TIMEOUT_SETTING_MATCH, timeout_config)
        with open(file_path, "w+", encoding="utf-8") as file:
            file.write(file_content)


if __name__ == "__main__":
    main()
