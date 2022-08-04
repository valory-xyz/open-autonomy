#!/usr/bin/env python3
import argparse
import os
import ipfshttpclient
from subprocess import PIPE, run


def main(file: str):
    addr = os.environ.get("OPEN_AEA_IPFS_ADDR")
    ipfs_tool = ipfshttpclient.Client(addr=addr)
    print(f"Connected to {addr}. Now Attemping Pin.")
    res = ipfs_tool.add(f"./mints/{file}")
    hash_ = res.as_json()['Hash']
    print("Done!", hash_)
    command = ["ipfs", "cid", "format", "-v", "1", "-b", "base32", hash_]
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    print("base32:", result.stdout)
    print("link:", f"ipfs://{result.stdout}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-f",
        "--file",
        type=str,
        help="File name.",
    )
    args = parser.parse_args()
    main(file=args.file)