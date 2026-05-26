# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2026 Valory AG
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

"""Constants for the replay module."""

# Tendermint addresses used by the replay runner. The trailing digit slot is
# filled with the node id so the per-node ports do not collide.
P2P_LADDR_TEMPLATE = "tcp://127.0.0.1:2663{node_id}"
RPC_LADDR_TEMPLATE = "tcp://localhost:2664{node_id}"
PROXY_APP_TEMPLATE = "tcp://localhost:2665{node_id}"
