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

"""Tests package for the 'valory/abci' protocol."""
from abc import abstractmethod

from packages.valory.protocols.abci import AbciMessage
from packages.valory.protocols.abci.custom_types import (
    BlockParams,
    ConsensusParams,
    Duration,
    EvidenceParams,
    Timestamp,
    ValidatorParams,
    ValidatorUpdate,
    ValidatorUpdates,
    VersionParams,
)


class BaseTestMessageConstruction:
    """Base class to test message construction for the ABCI protocol."""

    @abstractmethod
    def build_message(self) -> AbciMessage:
        """Build the message to be used for testing."""

    def test_run(self):
        """Run the test."""
        actual_message = self.build_message()
        expected_message = actual_message.decode(actual_message.encode())
        assert expected_message == actual_message


class TestRequestEcho(BaseTestMessageConstruction):
    """Test ABCI request echo."""

    def build_message(self):
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_ECHO, message="hello"
        )


class TestResponseEcho(BaseTestMessageConstruction):
    """Test ABCI response echo."""

    def build_message(self):
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_ECHO, message="hello"
        )


class TestRequestFlush(BaseTestMessageConstruction):
    """Test ABCI request flush."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_FLUSH,
        )


class TestResponseFlush(BaseTestMessageConstruction):
    """Test ABCI response flush."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_FLUSH,
        )


class TestRequestInfo(BaseTestMessageConstruction):
    """Test ABCI request info."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_INFO,
            version="0.1.0",
            block_version=1,
            p2p_version=1,
        )


class TestResponseInfo(BaseTestMessageConstruction):
    """Test ABCI response info."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_INFO,
            info_data="info",
            version="0.1.0",
            app_version=1,
            last_block_height=1,
            last_block_app_hash=b"bytes",
        )


class TestRequestInitChain(BaseTestMessageConstruction):
    """Test ABCI request init chain."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        consensus_params = ConsensusParams(
            BlockParams(0, 0),
            EvidenceParams(0, Duration(0, 0), 0),
            ValidatorParams(["pub_key"]),
            VersionParams(0),
        )

        validators = ValidatorUpdates(
            [
                ValidatorUpdate(b"pub_key_bytes", 1),
                ValidatorUpdate(b"pub_key_bytes", 2),
            ]
        )

        return AbciMessage(
            performative=AbciMessage.Performative.REQUEST_INIT_CHAIN,
            time=Timestamp(0, 0),
            chain_id="1",
            consensus_params=consensus_params,
            validators=validators,
            app_state_bytes=b"bytes",
            initial_height="height",
        )


class TestResponseInitChain(BaseTestMessageConstruction):
    """Test ABCI response init chain."""

    def build_message(self) -> AbciMessage:
        """Build the message."""
        consensus_params = ConsensusParams(
            BlockParams(0, 0),
            EvidenceParams(0, Duration(0, 0), 0),
            ValidatorParams(["pub_key"]),
            VersionParams(0),
        )

        validators = ValidatorUpdates(
            [
                ValidatorUpdate(b"pub_key_bytes", 1),
                ValidatorUpdate(b"pub_key_bytes", 2),
            ]
        )

        return AbciMessage(
            performative=AbciMessage.Performative.RESPONSE_INIT_CHAIN,
            consensus_params=consensus_params,
            validators=validators,
            app_hash=b"app_hash",
        )
