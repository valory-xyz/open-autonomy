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

"""The module contains test_helpers for module tests."""

import json
import os
import random
import string
import tempfile
from pathlib import Path
from unittest import mock

from aea.configurations.constants import DEFAULT_ENV_DOTFILE

from autonomy.cli.helpers.env import load_env_file


class TestLoadEnvFile:
    """Test `load_env_file` file."""

    _t: tempfile.TemporaryDirectory
    t: Path
    cwd: Path

    env_var = "ENV_VAR"

    @staticmethod
    def generate_random_value(n: int = 6) -> str:
        """Generate random string."""
        return "".join([random.choice(string.ascii_letters) for i in range(n)])  # nosec

    def setup(self) -> None:
        """Setup test"""

        self._t = tempfile.TemporaryDirectory()
        self.t = Path(self._t.name)
        self.cwd = Path.cwd()

        os.chdir(self.t)

    def test_load_dot_env(self) -> None:
        """Test `.env` file."""
        env_var_value = self.generate_random_value()
        dotenv_file = self.t / DEFAULT_ENV_DOTFILE
        dotenv_file.write_text(f"{self.env_var}={env_var_value}")
        with mock.patch.dict(os.environ):
            load_env_file(file=dotenv_file)
            assert os.environ[self.env_var] == env_var_value

    def test_load_json(self) -> None:
        """Test `.json` file."""

        env_var_value = self.generate_random_value()
        json_file = self.t / "env.json"
        json_file.write_text(json.dumps({self.env_var: env_var_value}))
        with mock.patch.dict(os.environ):
            load_env_file(file=json_file)
            assert os.environ[self.env_var] == env_var_value

    def test_load_json_serialize(self) -> None:
        """Test `.json` file with serialize values."""

        env_var_value = [self.generate_random_value(), self.generate_random_value()]
        json_file = self.t / "env.json"
        json_file.write_text(json.dumps({self.env_var: env_var_value}))

        with mock.patch.dict(os.environ):
            load_env_file(file=json_file, serialize_json=True)
            assert json.loads(os.environ[self.env_var]) == env_var_value

    def teardown(self) -> None:
        """Test teardown"""
        os.chdir(self.cwd)
        self._t.cleanup()
