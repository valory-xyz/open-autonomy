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

import pkgutil

import autonomy
import packages


def test_import_all_modules() -> None:
    """Test importing all modules."""

    package_names = [autonomy.__name__, packages.__name__]
    for loader, module_name, c in pkgutil.walk_packages(package_names):
        loader.find_module(module_name).load_module(module_name)
