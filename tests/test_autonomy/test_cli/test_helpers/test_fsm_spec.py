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

"""Tests for cli/helpers/fsm_spec.py"""

from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture  # type: ignore

from autonomy.cli.helpers.fsm_spec import (
    check_all,
    check_one,
    import_and_validate_app_class,
    update_one,
)

from packages.valory.skills import test_abci

from tests.conftest import ROOT_DIR


@pytest.mark.parametrize("relative_path", [True, False])
def test_import_and_validate_app_class(relative_path: bool) -> None:
    """Test import_and_validate_app_class"""

    module_path = Path(test_abci.__file__).parent
    if relative_path:
        module_path = module_path.relative_to(ROOT_DIR)
    module = import_and_validate_app_class(module_path, "TestAbciApp")
    assert module.__name__ == f"{test_abci.__name__}.rounds"
