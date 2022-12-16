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

"""Test importing all modules"""
import importlib
import pkgutil
import sys
from importlib import reload
from importlib.machinery import FileFinder, SourceFileLoader
from typing import cast

import autonomy

import packages


def test_import_all_modules() -> None:
    """Test importing all modules."""

    old_path = sys.path.copy()
    old_meta_path = sys.meta_path.copy()
    old_modules = sys.modules.copy()
    try:
        package_names = [autonomy.__name__, packages.__name__]
        for file_finder, module_name, _ in pkgutil.walk_packages(package_names):
            loader = cast(FileFinder, file_finder).find_module(module_name)
            cast(SourceFileLoader, loader).load_module(module_name)
            cast(FileFinder, file_finder).invalidate_caches()
    finally:
        sys.path = old_path
        sys.meta_path = old_meta_path
        sys.modules = old_modules
        importlib.invalidate_caches()
