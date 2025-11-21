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
from importlib.util import source_from_cache
from pathlib import Path
from types import ModuleType
from typing import Optional


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


def _get_module_file(module: ModuleType) -> Optional[Path]:
    """Resolve module file path if available."""

    file_path = getattr(module, "__file__", None)
    if file_path is None:
        return None

    try:
        resolved = Path(file_path).resolve()
    except (FileNotFoundError, RuntimeError):
        return None

    if resolved.suffix == ".pyc":
        try:
            resolved = Path(source_from_cache(str(resolved))).resolve()
        except (NotImplementedError, ValueError):
            return None

    return resolved


def import_module_from_path(
    module_name: str,
    module_file: Path,
    *,
    strict_origin: bool = True,
) -> ModuleType:
    """Import a module ensuring it originates from the expected file path."""

    module_file = module_file.resolve()
    existing = sys.modules.get(module_name)
    if existing is not None:
        existing_path = _get_module_file(existing)
        if existing_path == module_file:
            return existing
        purge_module_cache(module_name)

    module = importlib.import_module(module_name)
    module_path = _get_module_file(module)
    if strict_origin and module_path != module_file:
        raise ModuleNotFoundError(
            f"Module '{module_name}' was loaded from an unexpected location. Expected {module_file}"
        )

    return module
