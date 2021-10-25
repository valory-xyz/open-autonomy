# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Script for aggregating results."""


import json
from glob import glob
from typing import Dict, List


def get_file_list() -> List[str]:
    """Returns file list."""
    return glob("./logs/*.json")


def get_logs() -> List[Dict]:
    """Returns logs."""
    return [json.load(open(file, "r", encoding="utf-8")) for file in get_file_list()]


def main() -> None:
    """Run main function."""

    benchmarks = get_logs()
    cols = [c_name for c_name, _ in max(
        benchmarks, key=lambda x: len(x['logs'])).get("logs")]

    header = f"address | " + " | ".join([f"{col[:8]}..." for col in cols])
    print(f"{'-'*len(header)}\n{header}\n{'-'*len(header)}")
    for benchmark in benchmarks:
        time_values = [f"{t_value:.9f}" for _, t_value in benchmark["logs"]]
        print(f"{benchmark['agent_address'][:4]}... |" + " | ".join(time_values))


if __name__ == "__main__":
    main()
