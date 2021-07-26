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
from packages.valory.protocols.abci import AbciMessage


def test_request_echo():
    """Test ABCI request echo."""
    actual_message = AbciMessage(
        performative=AbciMessage.Performative.REQUEST_ECHO, message="hello"
    )
    expected_message = actual_message.decode(actual_message.encode())
    assert expected_message == actual_message


def test_response_echo():
    """Test ABCI response echo."""
    actual_message = AbciMessage(
        performative=AbciMessage.Performative.RESPONSE_ECHO, message="hello"
    )
    expected_message = actual_message.decode(actual_message.encode())
    assert expected_message == actual_message


def test_request_flush():
    """Test ABCI request flush."""
    actual_message = AbciMessage(
        performative=AbciMessage.Performative.REQUEST_FLUSH,
    )
    expected_message = actual_message.decode(actual_message.encode())
    assert expected_message == actual_message


def test_response_flush():
    """Test ABCI response flush."""
    actual_message = AbciMessage(
        performative=AbciMessage.Performative.RESPONSE_FLUSH,
    )
    expected_message = actual_message.decode(actual_message.encode())
    assert expected_message == actual_message
