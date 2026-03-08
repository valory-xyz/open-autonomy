#!/usr/bin/env python3
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

"""Check that third-party package hashes match the open-aea repository."""

import json
import re
import sys
from pathlib import Path

import requests

ROOT_DIR = Path(__file__).parent.parent
SETUP_PY = ROOT_DIR / "setup.py"
PACKAGES_JSON = ROOT_DIR / "packages" / "packages.json"
OPEN_AEA_REPO = "valory-xyz/open-aea"


def get_open_aea_version() -> str:
    """Extract the pinned open-aea version from setup.py."""
    content = SETUP_PY.read_text(encoding="utf-8")
    match = re.search(r'"open-aea\[all\]==(\S+)"', content)
    if not match:
        print("ERROR: Could not find open-aea version in setup.py")
        sys.exit(1)
    return match.group(1)


def get_remote_packages(version: str) -> dict:
    """Fetch packages.json from open-aea repo at the tag matching version."""
    tag = f"v{version}"
    url = f"https://raw.githubusercontent.com/{OPEN_AEA_REPO}/{tag}/packages/packages.json"
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        print(
            f"ERROR: Failed to fetch packages.json from {url} (status {response.status_code})"
        )
        sys.exit(1)
    data = response.json()
    if "dev" in data:
        return {**data["dev"], **data.get("third_party", {})}
    return data


def get_local_third_party() -> dict:
    """Read third-party packages from local packages.json."""
    with open(PACKAGES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("third_party", {})


def main() -> None:
    """Run the check."""
    version = get_open_aea_version()
    print(f"open-aea version from setup.py: {version}")

    remote_packages = get_remote_packages(version)
    local_third_party = get_local_third_party()

    mismatches = []
    missing_remote = []

    for package_id, local_hash in sorted(local_third_party.items()):
        if package_id not in remote_packages:
            missing_remote.append(package_id)
            continue
        remote_hash = remote_packages[package_id]
        if local_hash != remote_hash:
            mismatches.append((package_id, local_hash, remote_hash))

    if missing_remote:
        print(
            f"\nWARNING: {len(missing_remote)} third-party package(s) not found in remote:"
        )
        for pkg in missing_remote:
            print(f"  - {pkg}")

    if mismatches:
        print(f"\nERROR: {len(mismatches)} hash mismatch(es) found:")
        for pkg, local_h, remote_h in mismatches:
            print(f"  {pkg}")
            print(f"    local:  {local_h}")
            print(f"    remote: {remote_h}")
        sys.exit(1)

    print(
        f"\nAll {len(local_third_party)} third-party hashes match remote (open-aea v{version})."
    )


if __name__ == "__main__":
    main()
