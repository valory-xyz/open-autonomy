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
"""Script to generate bulk ethereum keys for use with the 'aea build_deployment' subcommand."""
import json

import click
from aea.cli.utils.click_utils import password_option
from aea.crypto.registries import make_crypto


@click.command()
@click.option("-n", "--number-of-keys", "--number_of_keys", type=int, default=4)
@click.option(
    "-o", "--output-file", "--output_file", type=str, default="generated_keys.json"
)
@password_option(confirmation_prompt=True, required=True)
def generate_keys(number_of_keys: int, output_file: str, password: str) -> None:
    """Generates n number of keys to be used by deployment generator."""
    keys = []
    for x in range(number_of_keys):
        account = make_crypto("ethereum")
        keys.append(
            {"address": account.address, "private_key": account.encrypt(password)}
        )
        print(f"Processed key generation {x}")
    with open(output_file, "w", encoding="utf8") as f:
        json.dump(keys, f, indent=4)


if __name__ == "__main__":
    generate_keys()  # pylint: disable=no-value-for-parameter
