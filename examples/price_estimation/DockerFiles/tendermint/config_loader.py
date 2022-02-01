# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Configuration loader."""

from pathlib import Path
from glob import glob
import time
import os

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('-p', "--path_to_monitor",
                    help='path to monitor for changes.',
                    default="/tendermint")
parser.add_argument('-dp', "--destination_path",
                    help="path for the configuration to be copied to",
                    default="./out")
parser.add_argument('-i', "--interval", default=1)

import hashlib
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def restart_host():
    os.system("shutdown /s /t 1")




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
        print(state)
        print(new_state)
        time.sleep(1)
        state = new_state

if __name__ == '__main__':
    main()

