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

"""
A module that holds a tendermint server that is slow in response to /hard_reset requests.

In order for hard reset to work, the following steps must be strictly followed:
    1. Tendermint server receives /hard_reset request from the agent.
    2. Tendermint server stops tendermint.
    3. Tendermint server performs unsafe-reset-all.
    4. Tendermint server restarts tendermint.
    5. Agent receives success response, and resets local blockchain.
    6. Tendermint sends a handshake info request to the agent.

This module contains a special implementation of the Tendermint Server that forces step 6 to happen before step 5.
It does that by performing steps 2, 3 and 4 but sleeping for 5 seconds before sending a response to the agent.
"""
