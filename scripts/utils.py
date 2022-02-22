#!/usr/bin/env python3
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

"""Utilities"""
# flake8: noqa

import abc
import importlib
import inspect
import itertools
import pkgutil
from types import ModuleType
from typing import Dict, List, Set, Type, Union


def import_submodules(
    package: Union[str, ModuleType], recursive: bool = False
) -> Dict[str, ModuleType]:
    """Import submodules from a package."""

    if isinstance(package, str):
        package = importlib.import_module(package)

    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):  # type: ignore
        if loader.path not in package.__path__:  # type: ignore
            continue
        full_name = package.__name__ + "." + name
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name, recursive))

    return results


def get_inheritors(cls: Type) -> Set[Type]:
    """Get all subclasses."""

    subclasses, stack = set(), [cls]
    while stack:
        parent = stack.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                stack.append(child)
    return subclasses


def get_all_classes(package: str) -> Dict[str, Set[Type]]:
    """Get all newly defined classes from a package."""

    modules = import_submodules(package, True)

    classes: Dict[str, Set[Type]] = {}
    for _, module in modules.items():
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if inspect.isclass(attribute) and attribute.__module__.startswith(package):
                classes.setdefault(attribute_name, set()).add(attribute)

    return classes


def get_concrete_inheritors(package: str, cls_name: str) -> List[Type]:
    """Get concrete subclasses of a base class from a package."""

    def is_concrete(cls: Type) -> bool:
        return not inspect.isabstract(cls) and abc.ABC not in cls.__bases__

    classes = get_all_classes(package)
    base_classes = classes[cls_name]  # could be more than one class with the same name
    inheritors = itertools.chain.from_iterable(map(get_inheritors, base_classes))
    concrete_inheritors = list(filter(is_concrete, inheritors))
    return concrete_inheritors


def your_code() -> None:
    """Your code here"""

    package = "packages.valory"
    cls_name = "AbciApp"
    abci_apps = get_concrete_inheritors(package, cls_name)

    for abci_app in abci_apps:
        doc_string = abci_app.__doc__
        source_code, line_no = inspect.findsource(abci_app)
        file_path = inspect.getfile(abci_app)

        assert (doc_string, source_code, line_no, file_path)  # type: ignore
