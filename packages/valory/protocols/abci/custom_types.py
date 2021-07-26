# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 valory
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

"""This module contains class representations corresponding to every custom type in the protocol specification."""


class ConsensusParams:
    """This class represents an instance of ConsensusParams."""

    def __init__(self):
        """Initialise an instance of ConsensusParams."""
        raise NotImplementedError

    @staticmethod
    def encode(
        consensus_params_protobuf_object, consensus_params_object: "ConsensusParams"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the consensus_params_protobuf_object argument is matched with the instance of this class in the 'consensus_params_object' argument.

        :param consensus_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param consensus_params_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, consensus_params_protobuf_object) -> "ConsensusParams":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'consensus_params_protobuf_object' argument.

        :param consensus_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'consensus_params_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class Timestamp:
    """This class represents an instance of Timestamp."""

    def __init__(self):
        """Initialise an instance of Timestamp."""
        raise NotImplementedError

    @staticmethod
    def encode(timestamp_protobuf_object, timestamp_object: "Timestamp") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the timestamp_protobuf_object argument is matched with the instance of this class in the 'timestamp_object' argument.

        :param timestamp_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param timestamp_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, timestamp_protobuf_object) -> "Timestamp":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'timestamp_protobuf_object' argument.

        :param timestamp_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'timestamp_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class ValidatorUpdates:
    """This class represents an instance of ValidatorUpdates."""

    def __init__(self):
        """Initialise an instance of ValidatorUpdates."""
        raise NotImplementedError

    @staticmethod
    def encode(
        validator_updates_protobuf_object, validator_updates_object: "ValidatorUpdates"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the validator_updates_protobuf_object argument is matched with the instance of this class in the 'validator_updates_object' argument.

        :param validator_updates_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param validator_updates_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, validator_updates_protobuf_object) -> "ValidatorUpdates":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'validator_updates_protobuf_object' argument.

        :param validator_updates_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'validator_updates_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError
