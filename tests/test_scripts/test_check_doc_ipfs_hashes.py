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

"""This module contains tests for the documentation tools."""

import re

from scripts.check_doc_ipfs_hashes import AEA_COMMAND_REGEX, FULL_PACKAGE_REGEX


def test_cmd_regex() -> None:
    """Test the command regex"""

    lines = [
        "aea fetch --remote open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
        "aea fetch open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
        "aea fetch --remote --other_flag open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
        "autonomy fetch --remote open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
        "autonomy fetch open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
        "autonomy fetch --remote --other_flag open_aea/my_first_aea:bafybeibnjfr3sdg57ggyxbcfkh42yqkj6a3gftp55l26aaw2z2jvvc3tny",
        "autonomy fetch valory/hello_world:0.1.0:bafybeihh6fz5xti3vmzd4ktihcvhqknnijmnc5vgbbqjcanqlfimqis6zy --remote --service",
    ]

    for line in lines:
        assert re.match(
            AEA_COMMAND_REGEX, line
        ), f"line '{line}' does not match AEA_COMMAND_REGEX"


def test_package_regex() -> None:
    """Test the command regex"""

    lines = [
        "valory/abstract_round_abci:0.1.0:bafybeibmwz5b7khd2efbegr7djknjdtwfrm6ufmsyiyhoxwz6r6p5cljv4",
        "open_aea/signing:bafybeid6f5ceool4evgaxdegs5pkjoivqjk3mo3ehctalswngb5m5c32wm",
    ]

    for line in lines:
        assert re.match(
            FULL_PACKAGE_REGEX, line
        ), f"line '{line}' does not match FULL_PACKAGE_REGEX"
