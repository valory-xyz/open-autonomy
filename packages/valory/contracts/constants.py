# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains the constants for the contracts authored by Valory AG."""

MIN_GAS = MIN_GASPRICE = 1
# see https://github.com/safe-global/safe-eth-py/blob/6c0e0d80448e5f3496d0d94985bca239df6eb399/gnosis/safe/safe_tx.py#L354
GAS_ADJUSTMENT = 75_000
# see https://github.com/valory-xyz/open-autonomy/pull/1209#discussion_r950129886
GAS_ESTIMATE_ADJUSTMENT = 50_000
