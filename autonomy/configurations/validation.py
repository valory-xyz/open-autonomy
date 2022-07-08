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

"""Config validators."""

import json

import jsonschema
from aea.configurations import validation
from aea.helpers.io import open_file

from autonomy.configurations.constants import SCHEMAS_DIR


class ConfigValidator(validation.ConfigValidator):
    """Configuration validator implementation."""

    def __init__(  # pylint: disable=super-init-not-called
        self, schema_filename: str, env_vars_friendly: bool = False
    ) -> None:
        """
        Initialize the parser for configuration files.

        :param schema_filename: the path to the JSON-schema file in 'aea/configurations/schemas'.
        :param env_vars_friendly: whether or not it is env var friendly.
        """

        with open_file(SCHEMAS_DIR / schema_filename) as fp:
            self._schema = json.load(fp)

        root_path = validation.make_jsonschema_base_uri(SCHEMAS_DIR)
        self._resolver = jsonschema.RefResolver(root_path, self._schema)
        self.env_vars_friendly = env_vars_friendly

        if env_vars_friendly:  # pragma: nocover
            self._validator = validation.EnvVarsFriendlyDraft4Validator(
                self._schema, resolver=self._resolver
            )
        else:
            self._validator = validation.OwnDraft4Validator(
                self._schema, resolver=self._resolver
            )
