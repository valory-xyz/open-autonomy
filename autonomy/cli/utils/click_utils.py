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

"""Usefule click utils."""
import contextlib
import copy
import sys
from pathlib import Path
from typing import Any, Callable, Generator, Optional

import click

from autonomy.analyse.abci.app_spec import FSMSpecificationLoader
from autonomy.deploy.chain import CHAIN_CONFIG
from autonomy.deploy.image import ImageProfiles


def image_profile_flag(
    default: str = ImageProfiles.PRODUCTION, mark_default: bool = True
) -> Callable:
    """Choice of one flag between: '--local/--remote'."""

    def wrapper(f: Callable) -> Callable:
        for profile in ImageProfiles.ALL:
            f = click.option(
                f"--{profile}",
                "profile",
                flag_value=profile,
                help=f"To use the {profile} profile.",
                default=(profile == default) and mark_default,
            )(f)

        return f

    return wrapper


def abci_spec_format_flag(
    default: str = FSMSpecificationLoader.OutputFormats.YAML, mark_default: bool = True
) -> Callable:
    """Flags for abci spec outputs formats."""

    def wrapper(f: Callable) -> Callable:
        for of in FSMSpecificationLoader.OutputFormats.ALL:
            f = click.option(
                f"--{of}",
                "spec_format",
                flag_value=of,
                help=f"{of.title()} file.",
                default=(of == default) and mark_default,
            )(f)

        return f

    return wrapper


def chain_selection_flag(
    default: str = "staging", mark_default: bool = True
) -> Callable:
    """Flags for abci spec outputs formats."""

    def wrapper(f: Callable) -> Callable:
        for chain in CHAIN_CONFIG.keys():
            f = click.option(
                f"--use-{chain}",
                "chain_type",
                flag_value=chain,
                help=f"Use {chain} chain to resolve the token id.",
                default=(chain == default) and mark_default,
            )(f)
        return f

    return wrapper


@contextlib.contextmanager
def sys_path_patch(path: Path) -> Generator:
    """Patch sys.path variable with new import path at highest priority."""
    old_sys_path = copy.copy(sys.path)
    sys.path.insert(0, str(path))
    yield
    sys.path = old_sys_path


class PathArgument(click.Path):
    """Path parameter for CLI."""

    def convert(
        self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> Optional[Path]:
        """Convert path string to `pathlib.Path`"""
        path_string = super().convert(value, param, ctx)
        return None if path_string is None else Path(path_string)
