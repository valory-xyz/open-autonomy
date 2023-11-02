# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""This module contains the transaction payloads for the slashing background skill."""

from dataclasses import dataclass, field

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


@dataclass(frozen=True)
class SlashingTxPayload(BaseTxPayload):
    """Represent a transaction payload for slashing."""

    # normal payload field
    tx_hex: str
    # these two fields are present in order to simplify the `end_block` method implementation of the corresponding round
    in_progress: bool = field(default=True)
    sent: bool = field(default=True)


@dataclass(frozen=True)
class StatusResetPayload(BaseTxPayload):
    """Represent a transaction payload for resetting the offence status."""

    # normal payload fields
    operators_mapping: str
    slash_timestamps: str
    # these two fields are present in order to simplify the `end_block` method implementation of the corresponding round
    slashing_in_flight: bool = field(default=False)
    slash_tx_sent: bool = field(default=False)
