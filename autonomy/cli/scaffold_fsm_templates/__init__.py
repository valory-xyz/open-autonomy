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

"""Scaffolding templates for FSM"""

from datetime import datetime

from .components import (  # noqa: F401
    BEHAVIOURS,
    DIALOGUES,
    HANDLERS,
    MODELS,
    PAYLOADS,
    ROUNDS,
)
from .tests import (  # noqa: F401
    TEST_BEHAVIOURS,
    TEST_DIALOGUES,
    TEST_HANDLERS,
    TEST_MODELS,
    TEST_PAYLOADS,
    TEST_ROUNDS,
)


COPYRIGHT_HEADER = """\
    # -*- coding: utf-8 -*-
    # ------------------------------------------------------------------------------
    #
    #   Copyright {year} Valory AG
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
    """.format(
    year=datetime.now().year
)
