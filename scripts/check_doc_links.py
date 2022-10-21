#!/usr/bin/env python3
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
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List

import requests
from requests.adapters import HTTPAdapter  # type: ignore
from requests.packages.urllib3.util.retry import (  # type: ignore # pylint: disable=import-error
    Retry,
)


MAX_WORKERS = 10
URL_REGEX = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s)"]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s)"]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s)"]{2,}|www\.[a-zA-Z0-9]+\.[^\s)"]{2,})'
REQUEST_TIMEOUT = 5  # seconds


def read_file(filepath: str) -> str:
    """Loads a file into a string"""
    with open(filepath, "r", encoding="utf-8") as file_:
        file_str = file_.read()
    return file_str


def check_file(
    session: Any, md_file: str, http_skips: List[str], url_skips: List[str]
) -> Dict:
    """Check for broken or HTTP links in a specific file"""

    text = read_file(md_file)
    m = re.findall(URL_REGEX, text)
    http_links = []
    broken_links = []

    for url in m:

        # Add the closing parenthesis if it is missing, as the REGEX is too strict sometimes
        if "(" in url and ")" not in url:
            url += ")"

        # Check for HTTP urls
        if not url.startswith("https") and url not in http_skips:
            http_links.append((md_file, url))

        # Check for broken links: 200 and 403 codes are admitted
        if url in url_skips + http_skips:
            continue
        try:
            status_code = session.get(url, timeout=REQUEST_TIMEOUT).status_code
            if status_code not in (200, 403):
                broken_links.append((md_file, url, status_code))
        except (
            requests.exceptions.RetryError,
            requests.exceptions.ConnectionError,
        ) as e:
            broken_links.append((md_file, url, e))

    return {
        "file": str(md_file),
        "http_links": http_links,
        "broken_links": broken_links,
    }


def main() -> None:  # pylint: disable=too-many-locals
    """Check for broken or HTTP links"""
    all_md_files = [str(p.relative_to(".")) for p in Path("docs").rglob("*.md")]

    broken_links: Dict[str, List[str]] = {}
    http_links: Dict[str, List[str]] = {}

    http_skips = [
        "http://www.fipa.org/repository/ips.php3",
        "http://host.docker.internal:8545```",
        "http://host.docker.internal:8545",
    ]
    url_skips = [
        "https://github.com/valory-xyz/open-autonomy/trunk/packages",
        "https://github.com/valory-xyz/open-autonomy/trunk/infrastructure",
        "https://gateway.autonolas.tech/ipfs/`<hash>`,",
        "https://gateway.autonolas.tech/ipfs/Qmbh9SQLbNRawh9Km3PMEDSxo77k1wib8fYZUdZkhPBiev",
        "https://encyclopedia.pub/entry/2959",
    ]

    # Configure request retries
    retry_strategy = Retry(
        total=3,  # number of retries
        status_forcelist=[404, 429, 500, 502, 503, 504],  # codes to retry on
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Run all file checks in a thread pool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for md_file in all_md_files:
            print(f"Checking {str(md_file)}...")
            futures.append(
                executor.submit(check_file, session, md_file, http_skips, url_skips)
            )

        # Awaiting for results is blocking
        print("Awaiting for results...")
        future_results = [future.result() for future in futures]

        # Get errors
        for i in future_results:
            if i["http_links"]:
                http_links[i["file"]] = i["http_links"]
            if i["broken_links"]:
                broken_links[i["file"]] = i["broken_links"]

        # Check errors
        if broken_links:
            broken_links_str = "\n".join(
                [
                    f"{file_name}: {[url[1] for url in urls]}"
                    for file_name, urls in broken_links.items()
                ]
            )
            print(f"Found broken url in the docs:\n{broken_links_str}")

        if http_links:
            http_links_str = "\n".join(
                [
                    f"{file_name}: {[url[1] for url in urls]}"
                    for file_name, urls in http_links.items()
                ]
            )
            print(
                f"Found HTTP urls in the docs:\n{http_links_str}\nTry to use HTTPS equivalent urls or add them to 'http_skips' if not possible"
            )

        if broken_links or http_links:
            sys.exit(1)

        print("OK")
        sys.exit(0)


if __name__ == "__main__":
    main()
