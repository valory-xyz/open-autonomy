#! /usr/bin/python3
import hashlib
import os
import signal
import time
from argparse import ArgumentParser
from glob import glob
from pathlib import Path


parser = ArgumentParser()
parser.add_argument(
    "-p", "--path_to_monitor", help="path to monitor for changes.", default="/app"
)
parser.add_argument(
    "-dp",
    "--destination_path",
    help="path for the configuration to be copied to",
    default="./out",
)
parser.add_argument("-i", "--interval", default=1)


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def restart_host():
    # This is a little inelegant, but ... effective.
    data = [x.rstrip().strip() for x in os.popen("ps h -eo pid")][2:]
    [os.kill(int(i), signal.SIGINT) for i in data]


def hash_files(files):
    return "".join([md5(file) for file in files])


def main():
    args = parser.parse_args()
    files = glob(args.path_to_monitor + "/*")
    state = hash_files(files)

    print(f"Starting to track config folder. {args.path_to_monitor}")
    print(f"Initial State: {state}")
    while True:
        files = glob(args.path_to_monitor + "/*")
        new_state = hash_files(files)
        if state != new_state:
            print("new config detected")
            restart_host()
        time.sleep(1)
        state = new_state


if __name__ == "__main__":
    main()
