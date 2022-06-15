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

"""This module contains the tests for the links in the documentation."""


import re
from pathlib import Path

import requests

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import read_file  # type: ignore


URL_REGEX = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s)"]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s)"]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s)"]{2,}|www\.[a-zA-Z0-9]+\.[^\s)"]{2,})'


def test_links() -> None:
    """Check for broken or HTTP links"""
    all_md_files = [
        str(p.relative_to(ROOT_DIR)) for p in Path(ROOT_DIR, "docs").rglob("*.md")
    ]

    broken_links = []
    http_links = []
    http_skips = ["http://www.fipa.org/repository/ips.php3"]
    url_skips = ["https://github.com/valory-xyz/open-autonomy/trunk/packages"]

    for md_file in all_md_files:
        text = read_file(md_file)
        m = re.findall(URL_REGEX, text)
        for url in m:

            # Add the closing parenthesis if it is msising, as the REGEX is too strict sometimes
            if "(" in url and ")" not in url:
                url += ")"

            # Check for HTTP urls
            if not url.startswith("https") and url not in http_skips:
                http_links.append((md_file, url))

            # Check for broken links: 200 and 403 codes are admitted
            if url in url_skips:
                continue
            try:
                status_code = requests.get(url).status_code
                if status_code not in (200, 403):
                    broken_links.append((md_file, url, status_code))
            except Exception as e:
                broken_links.append((md_file, url, e))

    broken_links_str = "\n".join(
        [f"{url[0]}: {url[1]} ({url[2]})" for url in broken_links]
    )
    http_links_str = "\n".join([f"{url[0]}: {url[1]} ({url[2]})" for url in http_links])
    assert not broken_links, f"Found broken url in the docs:\n{broken_links_str}"
    assert not http_links, f"Found HTTP urls in the docs:\n{http_links_str}"
