# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Test image build helpers."""

from aea.configurations.data_types import Dependency

from autonomy.deploy.image import generate_dependency_flag_var


def test_generate_dependency_flag_var() -> None:
    """Test generate_dependency_flag_var method."""

    dependencies = (
        Dependency(name="some-package", version="==1.0.0"),
        Dependency(
            name="other-package",
            git="https://github.com/author/some_package",
            ref="79342a93079648ef03ab5aaf14978068fc96587a",
        ),
    )

    assert generate_dependency_flag_var(dependencies=dependencies) == (
        "-e some-package==1.0.0 "
        "-e git+https://github.com/author/some_package@79342a93079648ef03ab5aaf14978068fc96587a#egg=other-package"
    )
