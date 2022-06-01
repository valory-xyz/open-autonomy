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
from eth_account import Account


@click.command()
@click.option(
    "-o", "--output-file", "--output_file", type=str, default="encrypted_keys.json"
)
@click.option(
    "-i", "--input-file", "--input_file", type=str, default="generated_keys.json"
)
@click.option("-p", "--password", "--password", type=str, required=True)
def encrypt_keys(output_file, input_file, password):
    """Encrypt keys from input path to output path using the password provided."""
    with open(input_file, "r", encoding="utf8") as fp:
        keys = json.load(fp)

    encrypted_keys = []
    for key in keys:
        print(f"Encrypting address: {key['address']}")
        account = Account.from_key(  # pylint: disable=E1120
            private_key=key["private_key"]
        )
        encrypted = account.encrypt(password=password)
        encrypted_keys.append({"address": account.address, "encrypted_key": encrypted})

    with open(output_file, "w", encoding="utf8") as f:
        json.dump(encrypted_keys, f, indent=4)
    print(f"Encryption complete. Keys save to {output_file}")


if __name__ == "__main__":
    encrypt_keys()  # pylint: disable=no-value-for-parameter
