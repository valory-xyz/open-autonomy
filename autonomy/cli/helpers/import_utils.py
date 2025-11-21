# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2025 Valory AG
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
"""Utilities for importing modules from the local packages registry."""

import importlib
import sys
from pathlib import Path


def compute_sys_path_root(module_path: Path, module_name: str) -> Path:
    """Determine the directory that should be injected into sys.path."""

    resolved = module_path.resolve()
    top_level = module_name.split(".", 1)[0]

    current = resolved
    while current != current.parent:
        if current.name == top_level:
            return current.parent
        current = current.parent

    return resolved.parent


def purge_module_cache(module_name: str) -> None:
    """Remove cached modules so they can be re-imported from the registry."""

    prefix = module_name.split(".", 1)[0]
    keys = [key for key in sys.modules if key == prefix or key.startswith(prefix + ".")]
    for key in keys:
        sys.modules.pop(key, None)

    importlib.invalidate_caches()
