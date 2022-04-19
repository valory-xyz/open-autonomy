#!/usr/bin/env python3
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

"""
Update Python modules from Tendermint Protobuf files.

NOTE: This code is adapted from the google protobuf Python library. Specifically from the setup.py file.
"""

import os
import re
import subprocess  # nosec
import sys
from distutils.spawn import find_executable
from pathlib import Path
from typing import cast


PACKAGE_IMPORT_PATH_PREFIX = "packages.valory.connections.abci"


def _find_protoc() -> str:
    """Find protoc binary."""
    if "PROTOC" in os.environ and os.path.exists(os.environ["PROTOC"]):
        protoc_bin = os.environ["PROTOC"]
    elif os.path.exists("../src/protoc"):
        protoc_bin = "../src/protoc"
    elif os.path.exists("../src/protoc.exe"):
        protoc_bin = "../src/protoc.exe"
    elif os.path.exists("../vsprojects/Debug/protoc.exe"):
        protoc_bin = "../vsprojects/Debug/protoc.exe"
    elif os.path.exists("../vsprojects/Release/protoc.exe"):
        protoc_bin = "../vsprojects/Release/protoc.exe"
    else:
        which_protoc = find_executable("protoc")
        if which_protoc is None:
            raise ValueError("cannot find 'protoc' binary on the system.")
        protoc_bin = which_protoc
    return cast(str, protoc_bin)


protoc = _find_protoc()


def generate_proto(source: str) -> None:
    """
    Generate a protobuf file.

    Invokes the Protocol Compiler to generate a _pb2.py from the given
    .proto file.  Does nothing if the output already exists and is newer than
    the input.

    :param source: path to the source.
    """

    if not os.path.exists(source):
        return

    output = source.replace(".proto", "_pb2.py").replace("./protos/", "./")

    if not os.path.exists(output) or (
        os.path.exists(source) and os.path.getmtime(source) > os.path.getmtime(output)
    ):
        print("Generating %s..." % output)

        if not os.path.exists(source):
            sys.stderr.write("Can't find required file: %s\n" % source)
            sys.exit(-1)

        if protoc is None:
            sys.stderr.write("protoc is not installed!\n")
            sys.exit(-1)

        protoc_cross_platform = protoc.replace("/", os.path.sep)
        protoc_command = [
            protoc_cross_platform,
            "-I./protos",
            "-I.",
            "--python_out=.",
            source,
        ]
        if subprocess.call(protoc_command) != 0:  # nosec
            sys.exit(-1)

        # prepend to all imports statement the AEA package import prefix path
        output_path = Path(output)
        output_content = output_path.read_text()
        output_content = re.sub(
            "from tendermint",
            f"from {PACKAGE_IMPORT_PATH_PREFIX}.tendermint",
            output_content,
        )
        output_content = re.sub(
            "from gogoproto",
            f"from {PACKAGE_IMPORT_PATH_PREFIX}.gogoproto",
            output_content,
        )
        output_path.write_text(output_content)


if __name__ == "__main__":
    # Build all the protobuf files and put into their directory
    generate_proto("./protos/gogoproto/gogo.proto")
    generate_proto("./protos/tendermint/crypto/keys.proto")
    generate_proto("./protos/tendermint/crypto/proof.proto")
    generate_proto("./protos/tendermint/types/params.proto")
    generate_proto("./protos/tendermint/types/types.proto")
    generate_proto("./protos/tendermint/types/validator.proto")
    generate_proto("./protos/tendermint/version/types.proto")
    generate_proto("./protos/tendermint/abci/types.proto")
