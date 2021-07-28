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
from copy import copy
from typing import List

from packages.valory.protocols.abci import abci_pb2


class BlockParams:
    """This class represents an instance of BlockParams."""

    __slots__ = ["max_bytes", "max_gas"]

    def __init__(self, max_bytes: int, max_gas: int):
        """Initialise an instance of BlockParams."""
        self.max_bytes = max_bytes
        self.max_gas = max_gas

    @staticmethod
    def encode(
        block_params_protobuf_object, block_params_object: "BlockParams"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the block_params_protobuf_object argument is matched with the instance of this class in the 'block_params_object' argument.

        :param block_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param block_params_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        block_params_protobuf_object.max_bytes = block_params_object.max_bytes
        block_params_protobuf_object.max_gas = block_params_object.max_gas

    @classmethod
    def decode(cls, block_params_protobuf_object) -> "BlockParams":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'block_params_protobuf_object' argument.

        :param block_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'block_params_protobuf_object' argument.
        """
        return BlockParams(
            block_params_protobuf_object.max_bytes, block_params_protobuf_object.max_gas
        )

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, BlockParams)
            and self.max_bytes == other.max_bytes
            and self.max_gas == other.max_gas
        )


class Duration:
    """This class represents an instance of Duration."""

    __slots__ = ["seconds", "nanos"]

    def __init__(self, seconds: int, nanos: int):
        """
        Initialise an instance of Duration.

        :param seconds: Signed seconds of the span of time.
            Must be from -315,576,000,000 to +315,576,000,000 inclusive.
        :param nanos: Signed fractions of a second at nanosecond resolution of the span of time.
            Durations less than one second are represented with a 0 seconds field and
            a positive or negative nanos field. For durations of one second or more,
            a non-zero value for the nanos field must be of the same sign as the seconds field.
            Must be from -999,999,999 to +999,999,999 inclusive.
        """
        self.seconds = seconds
        self.nanos = nanos

    @staticmethod
    def encode(duration_protobuf_object, duration_object: "Duration") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the duration_protobuf_object argument is matched with the instance of this class in the 'duration_object' argument.

        :param duration_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param duration_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        duration_protobuf_object.seconds = duration_object.seconds
        duration_protobuf_object.nanos = duration_object.nanos

    @classmethod
    def decode(cls, duration_protobuf_object) -> "Duration":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'duration_protobuf_object' argument.

        :param duration_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'duration_protobuf_object' argument.
        """
        return Duration(
            duration_protobuf_object.seconds, duration_protobuf_object.nanos
        )

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Duration)
            and self.seconds == other.seconds
            and self.nanos == other.nanos
        )


class EvidenceParams:
    """This class represents an instance of EvidenceParams."""

    __slots__ = [
        "max_age_num_blocks",
        "max_age_duration",
        "max_bytes",
    ]

    def __init__(
        self, max_age_num_blocks: int, max_age_duration: Duration, max_bytes: int
    ):
        """Initialise an instance of BlockParams."""
        self.max_age_num_blocks = max_age_num_blocks
        self.max_age_duration = max_age_duration
        self.max_bytes = max_bytes

    @staticmethod
    def encode(
        evidence_params_protobuf_object, evidence_params_object: "EvidenceParams"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the evidence_params_protobuf_object argument is matched with the instance of this class in the 'evidence_params_object' argument.

        :param evidence_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param evidence_params_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        evidence_params_protobuf_object.max_age_num_blocks = (
            evidence_params_object.max_age_num_blocks
        )
        Duration.encode(
            evidence_params_object.max_age_duration,
            evidence_params_object.max_age_duration,
        )
        evidence_params_protobuf_object.max_bytes = evidence_params_object.max_bytes

    @classmethod
    def decode(cls, evidence_params_protobuf_object) -> "EvidenceParams":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'evidence_params_protobuf_object' argument.

        :param evidence_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'evidence_params_protobuf_object' argument.
        """
        duration = Duration.decode(evidence_params_protobuf_object.max_age_duration)
        return EvidenceParams(
            evidence_params_protobuf_object.max_age_num_blocks,
            duration,
            evidence_params_protobuf_object.max_bytes,
        )

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, EvidenceParams)
            and self.max_age_num_blocks == other.max_age_num_blocks
            and self.max_age_duration == other.max_age_duration
            and self.max_bytes == other.max_bytes
        )


class ValidatorParams:
    """This class represents an instance of ValidatorParams."""

    __slots__ = [
        "pub_key_types",
    ]

    def __init__(self, pub_key_types: List[str]):
        """Initialise an instance of BlockParams."""
        self.pub_key_types = copy(pub_key_types)

    @staticmethod
    def encode(
        validator_params_protobuf_object, validator_params_object: "ValidatorParams"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the validator_params_protobuf_object argument is matched with the instance of this class in the 'validator_params_object' argument.

        :param validator_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param validator_params_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        validator_params_protobuf_object.pub_key_types.extend(
            validator_params_object.pub_key_types
        )

    @classmethod
    def decode(cls, validator_params_protobuf_object) -> "ValidatorParams":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'validator_params_protobuf_object' argument.

        :param validator_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'validator_params_protobuf_object' argument.
        """
        pub_key_types = list(validator_params_protobuf_object.pub_key_types)
        return ValidatorParams(
            pub_key_types,
        )

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, ValidatorParams)
            and self.pub_key_types == other.pub_key_types
        )


class VersionParams:
    """This class represents an instance of VersionParams."""

    __slots__ = [
        "app_version",
    ]

    def __init__(self, app_version: int):
        """Initialise an instance of BlockParams."""
        self.app_version = app_version

    @staticmethod
    def encode(
        version_params_protobuf_object, version_params_object: "VersionParams"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the version_params_protobuf_object argument is matched with the instance of this class in the 'version_params_object' argument.

        :param version_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param version_params_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        version_params_protobuf_object.app_version = version_params_object.app_version

    @classmethod
    def decode(cls, version_params_protobuf_object) -> "VersionParams":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'version_params_protobuf_object' argument.

        :param version_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'version_params_protobuf_object' argument.
        """
        app_version = version_params_protobuf_object.app_version
        return VersionParams(
            app_version,
        )

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, VersionParams) and self.app_version == other.app_version
        )


class ConsensusParams:
    """This class represents an instance of ConsensusParams."""

    def __init__(
        self,
        block: "BlockParams",
        evidence_params: "EvidenceParams",
        validator_params: "ValidatorParams",
        version_params: "VersionParams",
    ):
        """Initialise an instance of ConsensusParams."""
        self.block = block
        self.evidence_params = evidence_params
        self.validator_params = validator_params
        self.version_params = version_params

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
        BlockParams.encode(
            consensus_params_protobuf_object.block, consensus_params_object.block
        )
        EvidenceParams.encode(
            consensus_params_protobuf_object.evidence,
            consensus_params_object.evidence_params,
        )
        ValidatorParams.encode(
            consensus_params_protobuf_object.validator,
            consensus_params_object.validator_params,
        )
        VersionParams.encode(
            consensus_params_protobuf_object.version,
            consensus_params_object.version_params,
        )

    @classmethod
    def decode(cls, consensus_params_protobuf_object) -> "ConsensusParams":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'consensus_params_protobuf_object' argument.

        :param consensus_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'consensus_params_protobuf_object' argument.
        """
        block_params = BlockParams.decode(consensus_params_protobuf_object.block)
        evidence_params = EvidenceParams.decode(
            consensus_params_protobuf_object.evidence
        )
        validator_params = ValidatorParams.decode(
            consensus_params_protobuf_object.validator
        )
        version_params = VersionParams.decode(consensus_params_protobuf_object.version)
        return ConsensusParams(
            block_params, evidence_params, validator_params, version_params
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, ConsensusParams)
            and self.block == other.block
            and self.evidence_params == other.evidence_params
            and self.validator_params == other.validator_params
            and self.version_params == other.version_params
        )


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


class ConsensusVersion:
    """This class represents an instance of ConsensusVersion."""

    def __init__(self, block: int, app: int):
        """Initialise an instance of ConsensusVersion."""
        self.block = block
        self.app = app

    @staticmethod
    def encode(
        consensus_version_protobuf_object, consensus_version_object: "ConsensusVersion"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the consensus_version_protobuf_object argument is matched with the instance of this class in the 'consensus_version_object' argument.

        :param consensus_version_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param consensus_version_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, consensus_version_protobuf_object) -> "ConsensusVersion":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'consensus_version_protobuf_object' argument.

        :param consensus_version_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'consensus_version_protobuf_object' argument.
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


class ProofOp:
    """This class represents an instance of ProofOp."""

    def __init__(self, type_: str, key: bytes, data: bytes):
        """
        Initialise an instance of ProofOp.

        ProofOp defines an operation used for calculating Merkle root
        The data could be arbitrary format, providing necessary data
        for example neighbouring node hash.

        :param type_: the type
        :param key: the key
        :param data: the data
        """
        self.type_ = type_
        self.key = key
        self.data = data

    @staticmethod
    def encode(proof_op_protobuf_object, proof_op_object: "ProofOp") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the proof_op_protobuf_object argument is matched with the instance of this class in the 'proof_op_object' argument.

        :param proof_op_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param proof_op_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        proof_op_protobuf_object.type = proof_op_object.type_
        proof_op_protobuf_object.key = proof_op_object.key
        proof_op_protobuf_object.data = proof_op_object.data

    @classmethod
    def decode(cls, proof_op_protobuf_object) -> "ProofOp":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'proof_op_protobuf_object' argument.

        :param proof_op_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'proof_op_protobuf_object' argument.
        """
        return ProofOp(
            proof_op_protobuf_object.type,
            proof_op_protobuf_object.key,
            proof_op_protobuf_object.data,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, ProofOp)
            and self.type_ == other.type_
            and self.key == other.key
            and self.data == other.data
        )


class ProofOps:
    """This class represents an instance of ProofOps."""

    def __init__(self, proof_ops: List[ProofOp]):
        """
        Initialise an instance of ProofOps.

        :param proof_ops: a list of ProofOp instances.
        """
        self.proof_ops = proof_ops

    @staticmethod
    def encode(proof_ops_protobuf_object, proof_ops_object: "ProofOps") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the proof_ops_protobuf_object argument is matched with the instance of this class in the 'proof_ops_object' argument.

        :param proof_ops_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param proof_ops_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        proof_ops_protobuf_objects = []
        for proof_op in proof_ops_object.proof_ops:
            proof_op_protobuf_object = abci_pb2.AbciMessage.ProofOps.ProofOp()
            ProofOp.encode(proof_op_protobuf_object, proof_op)
            proof_ops_protobuf_objects.append(proof_op_protobuf_object)
        proof_ops_protobuf_object.ops.extend(proof_ops_protobuf_objects)

    @classmethod
    def decode(cls, proof_ops_protobuf_object) -> "ProofOps":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'proof_ops_protobuf_object' argument.

        :param proof_ops_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'proof_ops_protobuf_object' argument.
        """
        proof_ops_objects = []
        for proof_op_protobuf_object in list(proof_ops_protobuf_object.ops):
            proof_ops_objects.append(ProofOp.decode(proof_op_protobuf_object))
        return ProofOps(proof_ops_objects)

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, ProofOps) and self.proof_ops == other.proof_ops


class Timestamp:
    """This class represents an instance of Timestamp."""

    __slots__ = ["seconds", "nanos"]

    def __init__(self, seconds: int, nanos: int):
        """
        Initialise an instance of Timestamp.

        :param seconds: Represents seconds of UTC time since Unix epoch
            1970-01-01T00:00:00Z. Must be from 0001-01-01T00:00:00Z to
            9999-12-31T23:59:59Z inclusive.
        :param nanos: Non-negative fractions of a second at nanosecond resolution.
            Negative second values with fractions must still have non-negative nanos values
            that count forward in time. Must be from 0 to 999,999,999 inclusive.
        """
        self.seconds = seconds
        self.nanos = nanos

    @staticmethod
    def encode(timestamp_protobuf_object, timestamp_object: "Timestamp") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the timestamp_protobuf_object argument is matched with the instance of this class in the 'timestamp_object' argument.

        :param timestamp_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param timestamp_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        timestamp_protobuf_object.seconds = timestamp_object.seconds
        timestamp_protobuf_object.nanos = timestamp_object.nanos

    @classmethod
    def decode(cls, timestamp_protobuf_object) -> "Timestamp":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'timestamp_protobuf_object' argument.

        :param timestamp_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'timestamp_protobuf_object' argument.
        """
        return Timestamp(
            timestamp_protobuf_object.seconds, timestamp_protobuf_object.nanos
        )

    def __eq__(self, other) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Timestamp)
            and self.seconds == other.seconds
            and self.nanos == other.nanos
        )


class ValidatorUpdate:
    """This class represents an instance of ValidatorUpdate."""

    def __init__(self, pub_key: bytes, power: int):
        """Initialise an instance of ValidatorUpdate."""
        self.pub_key = pub_key
        self.power = power

    @staticmethod
    def encode(
        validator_update_protobuf_object, validator_update_object: "ValidatorUpdate"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the validator_update_protobuf_object argument is matched with the instance of this class in the 'validator_update_object' argument.

        :param validator_update_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param validator_update_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        validator_update_protobuf_object.pub_key = validator_update_object.pub_key
        validator_update_protobuf_object.power = validator_update_object.power

    @classmethod
    def decode(cls, validator_update_protobuf_object) -> "ValidatorUpdate":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'validator_update_protobuf_object' argument.

        :param validator_update_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'validator_update_protobuf_object' argument.
        """
        return ValidatorUpdate(
            validator_update_protobuf_object.pub_key,
            validator_update_protobuf_object.power,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, ValidatorUpdate)
            and self.pub_key == other.pub_key
            and self.power == other.power
        )


class ValidatorUpdates:
    """This class represents an instance of ValidatorUpdates."""

    def __init__(self, validator_updates: List[ValidatorUpdate]):
        """Initialise an instance of ValidatorUpdates."""
        self.validator_updates = copy(validator_updates)

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
        validator_updates = []
        for validator_update_object in validator_updates_object.validator_updates:
            validator_update_protobuf_object = (
                abci_pb2.AbciMessage.ValidatorUpdates.ValidatorUpdate()
            )
            ValidatorUpdate.encode(
                validator_update_protobuf_object, validator_update_object
            )
            validator_updates.append(validator_update_protobuf_object)
        validator_updates_protobuf_object.validators.extend(validator_updates)

    @classmethod
    def decode(cls, validator_updates_protobuf_object) -> "ValidatorUpdates":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'validator_updates_protobuf_object' argument.

        :param validator_updates_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'validator_updates_protobuf_object' argument.
        """
        validator_updates_objects = []
        validator_updates_protobuf_objects = list(
            validator_updates_protobuf_object.validators
        )
        for validator_update_protobuf_object in validator_updates_protobuf_objects:
            validator_update = ValidatorUpdate.decode(validator_update_protobuf_object)
            validator_updates_objects.append(validator_update)
        return ValidatorUpdates(validator_updates_objects)

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, ValidatorUpdates)
            and self.validator_updates == other.validator_updates
        )
