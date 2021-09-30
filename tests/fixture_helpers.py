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

"""This module contains helper classes/functions for fixtures."""
import secrets
from typing import List, Optional, Tuple

import pytest

from tests.helpers.constants import KEY_PAIRS
from tests.helpers.docker.ganache import DEFAULT_GANACHE_PORT


@pytest.mark.integration
class UseTendermint:
    """Inherit from this class to use Tendermint."""

    @pytest.fixture(autouse=True)
    def _start_tendermint(self, tendermint, tendermint_port):
        """Start a Tendermint image."""
        self.tendermint_port = tendermint_port


@pytest.mark.integration
class UseGnosisSafeHardHatNet:
    """Inherit from this class to use HardHat local net with Gnosis-Safe deployed."""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1
    SALT_NONCE: Optional[int] = None

    hardhat_port: int
    hardhat_key_pairs: List[Tuple[str, str]]
    proxy_contract_address: str

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_hardhat(cls, gnosis_safe_hardhat, hardhat_port, key_pairs) -> None:
        """Start an HardHat instance."""
        cls.hardhat_port = hardhat_port
        cls.hardhat_key_pairs = key_pairs

    @classmethod
    def owners(cls) -> List[Tuple[str, str]]:
        """Get the owners."""
        return cls.hardhat_key_pairs[: cls.NB_OWNERS]

    @classmethod
    def deployer(cls) -> Tuple[str, str]:
        """Get the key pair of the deployer."""
        # for simplicity, get the first owner
        return cls.owners()[0]

    @classmethod
    def get_nonce(cls) -> int:
        """Get the nonce."""
        if cls.SALT_NONCE is not None:
            return cls.SALT_NONCE
        return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


@pytest.mark.integration
class UseGanache:
    """Inherit from this class to use Ganache."""

    NB_OWNERS: int = 4
    THRESHOLD: int = 1

    ganache_port: int = DEFAULT_GANACHE_PORT
    key_pairs: List[Tuple[str, str]] = KEY_PAIRS

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_ganache(cls, ganache_safenet, ganache_configuration) -> None:
        """Start Ganache instance."""
        cls.key_pairs = [
            key for key, _ in ganache_configuration.get("accounts_balances", [])
        ]

    @property
    def owners(
        self,
    ) -> List[Tuple[str, str]]:
        """Returns list of key pairs for owners."""
        return self.key_pairs

    @property
    def threshold(
        self,
    ) -> int:
        """Returns the amount of threshold."""
        return self.THRESHOLD
