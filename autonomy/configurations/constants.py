# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

"""Configuration constants."""


from pathlib import Path


CONFIG_PATH = Path(__file__).absolute().parent
SCHEMAS_DIR = CONFIG_PATH / "schemas"
DEFAULT_SERVICE_CONFIG_FILE = "service.yaml"
SERVICE = "service"
SERVICES = "services"
INIT_PY = "__init__.py"
PYCACHE = "__pycache__"

DEFAULT_FSM_SPEC_YAML = "fsm_specification.yaml"
DEFAULT_FSM_SPEC_JSON = "fsm_specification.json"
DEFAULT_FSM_SPEC_MERMAID = "fsm_specification.md"
