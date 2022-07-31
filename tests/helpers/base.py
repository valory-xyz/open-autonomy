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

"""Base helpers."""
import contextlib
import os
from os import PathLike
from typing import Any, Generator, Tuple, Type

from packages.valory.skills.abstract_round_abci.base import AbstractRound


@contextlib.contextmanager
def cd(path: PathLike) -> Generator:  # pragma: nocover
    """Change working directory temporarily."""
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)


def try_send(gen: Generator, obj: Any = None) -> None:
    """
    Try to send an object to a generator.

    :param gen: the generator.
    :param obj: the object.
    """
    with contextlib.suppress(StopIteration):
        gen.send(obj)


def make_round_class(name: str, bases: Tuple = (AbstractRound,)) -> Type[AbstractRound]:
    """Make a round class."""
    new_round_cls = type(name, bases, {})
    setattr(new_round_cls, "round_id", name)  # noqa: B010
    assert issubclass(new_round_cls, AbstractRound)
    return new_round_cls
