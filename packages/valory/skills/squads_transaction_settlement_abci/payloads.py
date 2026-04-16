# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2024 Valory AG
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

"""This module contains the transaction payloads for common apps."""

from dataclasses import dataclass

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


@dataclass(frozen=True)
class RandomnessPayload(BaseTxPayload):
    """Represent a transaction payload of type 'randomness'."""

    round_id: int
    randomness: str


@dataclass(frozen=True)
class SelectKeeperPayload(BaseTxPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    keepers: str


@dataclass(frozen=True)
class CreateTxPayload(BaseTxPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    tx_pda: str
    tx_digest: str


@dataclass(frozen=True)
class ApproveTxPayload(BaseTxPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    tx_pda: str
    tx_digest: str


@dataclass(frozen=True)
class ExecuteTxPayload(BaseTxPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    tx_pda: str
    tx_digest: str


@dataclass(frozen=True)
class VerifyTxPayload(BaseTxPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    tx_pda: str
    verified: bool


@dataclass(frozen=True)
class ResetPayload(BaseTxPayload):
    """Represent a transaction payload of type 'reset'."""

    period_count: int
