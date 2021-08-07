# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Wrappers to Tendermint RPC messages (via HTTP)."""
from aea.skills.base import SkillContext

from packages.valory.skills.price_estimation_abci.utils import (
    _send_http_request_message,
)


def _send_broadcast_tx_commit(context: SkillContext, tx_bytes: bytes):
    """Send a broadcast_tx_commit request."""
    _send_http_request_message(
        context,
        "GET",
        context.params.tendermint_url + f"/broadcast_tx_commit?tx=0x{tx_bytes.hex()}",
        handler_callback="broadcast_tx_commit",
    )
