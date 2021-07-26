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


class Events:
    """This class represents an instance of Events."""

    def __init__(self):
        """Initialise an instance of Events."""
        raise NotImplementedError

    @staticmethod
    def encode(events_protobuf_object, events_object: "Events") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the events_protobuf_object argument is matched with the instance of this class in the 'events_object' argument.

        :param events_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param events_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, events_protobuf_object) -> "Events":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'events_protobuf_object' argument.

        :param events_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'events_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class Evidences:
    """This class represents an instance of Evidences."""

    def __init__(self):
        """Initialise an instance of Evidences."""
        raise NotImplementedError

    @staticmethod
    def encode(evidences_protobuf_object, evidences_object: "Evidences") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the evidences_protobuf_object argument is matched with the instance of this class in the 'evidences_object' argument.

        :param evidences_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param evidences_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, evidences_protobuf_object) -> "Evidences":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'evidences_protobuf_object' argument.

        :param evidences_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'evidences_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class Header:
    """This class represents an instance of Header."""

    def __init__(self):
        """Initialise an instance of Header."""
        raise NotImplementedError

    @staticmethod
    def encode(header_protobuf_object, header_object: "Header") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the header_protobuf_object argument is matched with the instance of this class in the 'header_object' argument.

        :param header_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param header_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, header_protobuf_object) -> "Header":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'header_protobuf_object' argument.

        :param header_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'header_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class LastCommitInfo:
    """This class represents an instance of LastCommitInfo."""

    def __init__(self):
        """Initialise an instance of LastCommitInfo."""
        raise NotImplementedError

    @staticmethod
    def encode(
        last_commit_info_protobuf_object, last_commit_info_object: "LastCommitInfo"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the last_commit_info_protobuf_object argument is matched with the instance of this class in the 'last_commit_info_object' argument.

        :param last_commit_info_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param last_commit_info_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, last_commit_info_protobuf_object) -> "LastCommitInfo":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'last_commit_info_protobuf_object' argument.

        :param last_commit_info_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'last_commit_info_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class ProofOps:
    """This class represents an instance of ProofOps."""

    def __init__(self):
        """Initialise an instance of ProofOps."""
        raise NotImplementedError

    @staticmethod
    def encode(proof_ops_protobuf_object, proof_ops_object: "ProofOps") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the proof_ops_protobuf_object argument is matched with the instance of this class in the 'proof_ops_object' argument.

        :param proof_ops_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param proof_ops_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, proof_ops_protobuf_object) -> "ProofOps":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'proof_ops_protobuf_object' argument.

        :param proof_ops_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'proof_ops_protobuf_object' argument.
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
