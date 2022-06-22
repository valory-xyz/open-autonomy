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

"""Push all available packages to a registry."""


from pathlib import Path
from typing import Optional

import click
from aea.cli.push_all import push_all_packages
from aea.cli.utils.click_utils import registry_flag

from autonomy.configurations.base import PACKAGE_TYPE_TO_CONFIG_CLASS


@click.command("push-all")
@click.option(
    "--packages-dir", type=click.Path(file_okay=False, dir_okay=True, exists=True)
)
@registry_flag()
def push_all(packages_dir: Optional[Path], registry: str) -> None:
    """Push all available packages to a registry."""
    push_all_packages(
        registry,
        packages_dir,
        package_type_config_class=PACKAGE_TYPE_TO_CONFIG_CLASS,
    )
