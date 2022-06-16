import re
from pathlib import Path
from typing import Dict


FETCH_COMMAND_REGEX = r"aea fetch valory\/hello_world:(?P<hash>Q.*) \-\-remote"


def read_file(filepath: str) -> str:
    """Loads a file into a string"""
    with open(filepath, "r", encoding="utf-8") as file_:
        file_str = file_.read()
    return file_str


def get_hashes() -> Dict[str, str]:
    """Get a dictionary with all packages and their hashes"""
    CSV_HASH_REGEX = r"(?P<vendor>.*)\/(?P<type>.*)\/(?P<name>.*),(?P<hash>.*)\n"
    hashes_file = Path("packages", "hashes.csv").relative_to(".")
    hashes_content = read_file(str(hashes_file))
    hashes = {}
    for match in re.findall(CSV_HASH_REGEX, hashes_content):
        hashes[f"{match[0]}/{match[1]}/{match[2]}"] = match[3]
    return hashes


def fix_ipfs_hashes() -> None:
    """Fix ipfs hashes in the docs"""
    hashes = get_hashes()
    # Find and check (and optionally fix) hashes in the docs


if __name__ == "__main__":
    fix_ipfs_hashes()
