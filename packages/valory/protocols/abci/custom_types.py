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
import datetime
from enum import Enum
from typing import List, Optional

from aea.exceptions import enforce

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
        """
        evidence_params_protobuf_object.max_age_num_blocks = (
            evidence_params_object.max_age_num_blocks
        )
        Duration.encode(
            evidence_params_protobuf_object.max_age_duration,
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
        self.pub_key_types = pub_key_types

    @staticmethod
    def encode(
        validator_params_protobuf_object, validator_params_object: "ValidatorParams"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the validator_params_protobuf_object argument is matched with the instance of this class in the 'validator_params_object' argument.

        :param validator_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param validator_params_object: an instance of this class to be encoded in the protocol buffer object.
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
        consensus_params_protobuf_object,
        consensus_params_object: Optional["ConsensusParams"],
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the consensus_params_protobuf_object argument is matched with the instance of this class in the 'consensus_params_object' argument.

        :param consensus_params_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param consensus_params_object: an instance of this class to be encoded in the protocol buffer object.
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


class EventAttribute:
    """This class represents an instance of EventAttribute."""

    def __init__(self, key: bytes, value: bytes, index: bool):
        """Initialise an instance of EventAttribute."""
        self.key = key
        self.value = value
        self.index = index

    @staticmethod
    def encode(
        event_attribute_protobuf_object, event_attribute_object: "EventAttribute"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the event_attribute_protobuf_object argument is matched with the instance of this class in the 'event_attribute_object' argument.

        :param event_attribute_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param event_attribute_object: an instance of this class to be encoded in the protocol buffer object.
        """
        event_attribute_protobuf_object.key = event_attribute_object.key
        event_attribute_protobuf_object.value = event_attribute_object.value
        event_attribute_protobuf_object.index = event_attribute_object.index

    @classmethod
    def decode(cls, event_attribute_protobuf_object) -> "EventAttribute":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'event_attribute_protobuf_object' argument.

        :param event_attribute_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'event_attribute_protobuf_object' argument.
        """
        return EventAttribute(
            event_attribute_protobuf_object.key,
            event_attribute_protobuf_object.value,
            event_attribute_protobuf_object.index,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, EventAttribute)
            and self.key == other.key
            and self.value == other.value
            and self.index == other.index
        )


class Event:
    """This class represents an instance of Event."""

    def __init__(self, type_: str, attributes: List[EventAttribute]):
        """Initialise an instance of Event."""
        self.type_ = type_
        self.attributes = attributes

    @staticmethod
    def encode(event_protobuf_object, event_object: "Event") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the event_protobuf_object argument is matched with the instance of this class in the 'event_object' argument.

        :param event_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param event_object: an instance of this class to be encoded in the protocol buffer object.
        """
        event_protobuf_object.type = event_object.type_

        event_attribute_protobuf_objects = []
        for event_attribute_object in event_object.attributes:
            event_attribute_protobuf_object = (
                abci_pb2.AbciMessage.Events.EventAttribute()
            )
            EventAttribute.encode(
                event_attribute_protobuf_object, event_attribute_object
            )
            event_attribute_protobuf_objects.append(event_attribute_protobuf_object)

        event_protobuf_object.attributes.extend(event_attribute_protobuf_objects)

    @classmethod
    def decode(cls, event_protobuf_object) -> "Event":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'event_protobuf_object' argument.

        :param event_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'event_protobuf_object' argument.
        """
        attributes = []
        for event_attribute_protobuf_object in list(event_protobuf_object.attributes):
            attribute = EventAttribute.decode(event_attribute_protobuf_object)
            attributes.append(attribute)
        return Event(event_protobuf_object.type, attributes)

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Event)
            and self.type_ == other.type_
            and self.attributes == other.attributes
        )


class Events:
    """This class represents an instance of Events."""

    def __init__(self, events: List[Event]):
        """Initialise an instance of Events."""
        self.events = events

    @staticmethod
    def encode(events_protobuf_object, events_object: "Events") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the events_protobuf_object argument is matched with the instance of this class in the 'events_object' argument.

        :param events_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param events_object: an instance of this class to be encoded in the protocol buffer object.
        """
        event_protobuf_objects = []
        for event_object in events_object.events:
            event_protobuf_object = abci_pb2.AbciMessage.Events.Event()
            Event.encode(event_protobuf_object, event_object)
            event_protobuf_objects.append(event_protobuf_object)
        events_protobuf_object.events.extend(event_protobuf_objects)

    @classmethod
    def decode(cls, events_protobuf_object) -> "Events":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'events_protobuf_object' argument.

        :param events_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'events_protobuf_object' argument.
        """
        event_objects = []
        for event_protobuf_object in list(events_protobuf_object.events):
            event_object = Event.decode(event_protobuf_object)
            event_objects.append(event_object)
        return Events(event_objects)

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, Events) and self.events == other.events


class EvidenceType(Enum):
    """This class represent an instance of EvidenceType."""

    UNKNOWN = 0
    DUPLICATE_VOTE = 1
    LIGHT_CLIENT_ATTACK = 2


class Evidence:
    """This class represent an instance of Evidence."""

    def __init__(
        self,
        evidence_type: EvidenceType,
        validator: "Validator",
        height: int,
        time: "Timestamp",
        total_voting_power: int,
    ):
        """Initialise an instance of Evidences."""
        self.evidence_type = evidence_type
        self.validator = validator
        self.height = height
        self.time = time
        self.total_voting_power = total_voting_power

    @staticmethod
    def encode(evidence_protobuf_object, evidence_object: "Evidence") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the evidence_protobuf_object argument is matched with the instance of this class in the 'evidence_object' argument.

        :param evidence_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param evidence_object: an instance of this class to be encoded in the protocol buffer object.
        """
        evidence_protobuf_object.type = evidence_object.evidence_type.value

        validator_protobuf_object = abci_pb2.AbciMessage.LastCommitInfo.Validator()
        Validator.encode(validator_protobuf_object, evidence_object.validator)
        evidence_protobuf_object.validator.CopyFrom(validator_protobuf_object)

        evidence_protobuf_object.height = evidence_object.height

        timestamp_protobuf_object = abci_pb2.AbciMessage.Timestamp()
        Timestamp.encode(timestamp_protobuf_object, evidence_object.time)
        evidence_protobuf_object.time.CopyFrom(timestamp_protobuf_object)

        evidence_protobuf_object.total_voting_power = evidence_object.total_voting_power

    @classmethod
    def decode(cls, evidence_protobuf_object) -> "Evidence":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'evidence_protobuf_object' argument.

        :param evidence_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'evidence_protobuf_object' argument.
        """
        evidence_type = EvidenceType(evidence_protobuf_object.type)
        validator = Validator.decode(evidence_protobuf_object.validator)
        height = evidence_protobuf_object.height
        time = Timestamp.decode(evidence_protobuf_object.time)
        total_voting_power = evidence_protobuf_object.total_voting_power
        return Evidence(evidence_type, validator, height, time, total_voting_power)

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Evidence)
            and self.evidence_type == other.evidence_type
            and self.validator == other.validator
            and self.height == other.height
            and self.time == other.time
            and self.total_voting_power == other.total_voting_power
        )


class Evidences:
    """This class represents an instance of Evidences."""

    def __init__(self, byzantine_validators: List[Evidence]):
        """Initialise an instance of Evidences."""
        self.byzantine_validators = byzantine_validators

    @staticmethod
    def encode(evidences_protobuf_object, evidences_object: "Evidences") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the evidences_protobuf_object argument is matched with the instance of this class in the 'evidences_object' argument.

        :param evidences_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param evidences_object: an instance of this class to be encoded in the protocol buffer object.
        """
        validators_protobuf_objects = []
        for validator in evidences_object.byzantine_validators:
            evidence_protobuf_object = abci_pb2.AbciMessage.Evidences.Evidence()
            Evidence.encode(evidence_protobuf_object, validator)
            validators_protobuf_objects.append(evidence_protobuf_object)
        evidences_protobuf_object.byzantine_validators.extend(
            validators_protobuf_objects
        )

    @classmethod
    def decode(cls, evidences_protobuf_object) -> "Evidences":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'evidences_protobuf_object' argument.

        :param evidences_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'evidences_protobuf_object' argument.
        """
        validator_objects = []
        for validator_protobuf_object in list(
            evidences_protobuf_object.byzantine_validators
        ):
            validator_object = Evidence.decode(validator_protobuf_object)
            validator_objects.append(validator_object)
        return Evidences(validator_objects)

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Evidences)
            and self.byzantine_validators == other.byzantine_validators
        )


class CheckTxTypeEnum(Enum):
    """CheckTxTypeEnum for tx check."""

    NEW = 0
    RECHECK = 1


class CheckTxType:
    """This class represents an instance of CheckTxType."""

    def __init__(self, check_tx_type: CheckTxTypeEnum):
        """Initialise an instance of CheckTxType."""
        self.check_tx_type = check_tx_type

    @staticmethod
    def encode(
        check_tx_type_protobuf_object, check_tx_type_object: "CheckTxType"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the check_tx_type_protobuf_object argument is matched with the instance of this class in the 'check_tx_type_object' argument.

        :param check_tx_type_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param check_tx_type_object: an instance of this class to be encoded in the protocol buffer object.
        """
        check_tx_type_protobuf_object.type = check_tx_type_object.check_tx_type.value

    @classmethod
    def decode(cls, check_tx_type_protobuf_object) -> "CheckTxType":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'check_tx_type_protobuf_object' argument.

        :param check_tx_type_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'check_tx_type_protobuf_object' argument.
        """
        return CheckTxType(CheckTxTypeEnum(check_tx_type_protobuf_object.type))

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, CheckTxType) and self.check_tx_type == other.check_tx_type
        )


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
        """
        consensus_version_protobuf_object.block = consensus_version_object.block
        consensus_version_protobuf_object.app = consensus_version_object.app

    @classmethod
    def decode(cls, consensus_version_protobuf_object) -> "ConsensusVersion":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'consensus_version_protobuf_object' argument.

        :param consensus_version_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'consensus_version_protobuf_object' argument.
        """
        return ConsensusVersion(
            consensus_version_protobuf_object.block,
            consensus_version_protobuf_object.app,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, ConsensusVersion)
            and self.block == other.block
            and self.app == other.app
        )


class PartSetHeader:
    """This class represents an instance of PartSetHeader."""

    def __init__(self, total: int, hash_: bytes):
        """Initialise an instance of PartSetHeader."""
        self.total = total
        self.hash_ = hash_

    @staticmethod
    def encode(
        part_set_header_protobuf_object, part_set_header_object: "PartSetHeader"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the part_set_header_protobuf_object argument is matched with the instance of this class in the 'part_set_header_object' argument.

        :param part_set_header_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param part_set_header_object: an instance of this class to be encoded in the protocol buffer object.
        """
        part_set_header_protobuf_object.total = part_set_header_object.total
        part_set_header_protobuf_object.hash = part_set_header_object.hash_

    @classmethod
    def decode(cls, part_set_header_protobuf_object) -> "PartSetHeader":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'part_set_header_protobuf_object' argument.

        :param part_set_header_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'part_set_header_protobuf_object' argument.
        """
        return PartSetHeader(
            part_set_header_protobuf_object.total,
            part_set_header_protobuf_object.hash,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, PartSetHeader)
            and self.total == other.total
            and self.hash_ == other.hash_
        )


class BlockID:
    """This class represents an instance of BlockID."""

    def __init__(self, hash_: bytes, part_set_header: PartSetHeader):
        """Initialise an instance of BlockID."""
        self.hash_ = hash_
        self.part_set_header = part_set_header

    @staticmethod
    def encode(block_id_protobuf_object, block_id_object: "BlockID") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the block_id_protobuf_object argument is matched with the instance of this class in the 'block_id_object' argument.

        :param block_id_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param block_id_object: an instance of this class to be encoded in the protocol buffer object.
        """
        block_id_protobuf_object.hash = block_id_object.hash_
        part_set_header_protobuf_object = abci_pb2.AbciMessage.Header.PartSetHeader()
        PartSetHeader.encode(
            part_set_header_protobuf_object, block_id_object.part_set_header
        )
        block_id_protobuf_object.part_set_header.CopyFrom(
            part_set_header_protobuf_object
        )

    @classmethod
    def decode(cls, block_id_protobuf_object) -> "BlockID":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'block_id_protobuf_object' argument.

        :param block_id_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'block_id_protobuf_object' argument.
        """
        part_set_header = PartSetHeader.decode(block_id_protobuf_object.part_set_header)
        return BlockID(
            block_id_protobuf_object.hash,
            part_set_header,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, BlockID)
            and self.hash_ == other.hash_
            and self.part_set_header == other.part_set_header
        )


class Header:  # pylint: disable=too-many-instance-attributes
    """This class represents an instance of Header."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        version: ConsensusVersion,
        chain_id: str,
        height: int,
        time: "Timestamp",
        last_block_id: BlockID,
        last_commit_hash: bytes,
        data_hash: bytes,
        validators_hash: bytes,
        next_validators_hash: bytes,
        consensus_hash: bytes,
        app_hash: bytes,
        last_results_hash: bytes,
        evidence_hash: bytes,
        proposer_address: bytes,
    ):
        """Initialise an instance of Header."""
        self.version = version
        self.chain_id = chain_id
        self.height = height
        self.time = time
        self.last_block_id = last_block_id
        self.last_commit_hash = last_commit_hash
        self.data_hash = data_hash
        self.validators_hash = validators_hash
        self.next_validators_hash = next_validators_hash
        self.consensus_hash = consensus_hash
        self.app_hash = app_hash
        self.last_results_hash = last_results_hash
        self.evidence_hash = evidence_hash
        self.proposer_address = proposer_address

    @property
    def timestamp(self) -> datetime.datetime:
        """Get the block timestamp."""
        timestamp: Timestamp = self.time
        nanoseconds = timestamp.nanos / 10**9
        seconds = timestamp.seconds
        return datetime.datetime.fromtimestamp(seconds + nanoseconds)

    @staticmethod
    def encode(header_protobuf_object, header_object: "Header") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the header_protobuf_object argument is matched with the instance of this class in the 'header_object' argument.

        :param header_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param header_object: an instance of this class to be encoded in the protocol buffer object.
        """
        consensus_version_protobuf_obj = abci_pb2.AbciMessage.Header.ConsensusVersion()
        ConsensusVersion.encode(consensus_version_protobuf_obj, header_object.version)
        header_protobuf_object.version.CopyFrom(consensus_version_protobuf_obj)

        header_protobuf_object.chain_id = header_object.chain_id
        header_protobuf_object.height = header_object.height

        timestamp_protobuf_obj = abci_pb2.AbciMessage.Timestamp()
        Timestamp.encode(timestamp_protobuf_obj, header_object.time)
        header_protobuf_object.time.CopyFrom(timestamp_protobuf_obj)

        last_block_id_protobuf_obj = abci_pb2.AbciMessage.Header.BlockID()
        BlockID.encode(last_block_id_protobuf_obj, header_object.last_block_id)
        header_protobuf_object.last_block_id.CopyFrom(last_block_id_protobuf_obj)

        header_protobuf_object.last_commit_hash = header_object.last_commit_hash
        header_protobuf_object.data_hash = header_object.data_hash
        header_protobuf_object.validators_hash = header_object.validators_hash
        header_protobuf_object.next_validators_hash = header_object.next_validators_hash
        header_protobuf_object.consensus_hash = header_object.consensus_hash
        header_protobuf_object.app_hash = header_object.app_hash
        header_protobuf_object.last_results_hash = header_object.last_results_hash
        header_protobuf_object.evidence_hash = header_object.evidence_hash
        header_protobuf_object.proposer_address = header_object.proposer_address

    @classmethod
    def decode(  # pylint: disable=too-many-locals
        cls, header_protobuf_object
    ) -> "Header":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'header_protobuf_object' argument.

        :param header_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'header_protobuf_object' argument.
        """
        consensus_version_obj = ConsensusVersion.decode(header_protobuf_object.version)
        chain_id = header_protobuf_object.chain_id
        height = header_protobuf_object.height
        time = Timestamp.decode(header_protobuf_object.time)

        last_block_id = BlockID.decode(header_protobuf_object.last_block_id)

        last_commit_hash = header_protobuf_object.last_commit_hash
        data_hash = header_protobuf_object.data_hash
        validators_hash = header_protobuf_object.validators_hash
        next_validators_hash = header_protobuf_object.next_validators_hash
        consensus_hash = header_protobuf_object.consensus_hash
        app_hash = header_protobuf_object.app_hash
        last_results_hash = header_protobuf_object.last_results_hash
        evidence_hash = header_protobuf_object.evidence_hash
        proposer_address = header_protobuf_object.proposer_address
        return Header(
            consensus_version_obj,
            chain_id,
            height,
            time,
            last_block_id,
            last_commit_hash,
            data_hash,
            validators_hash,
            next_validators_hash,
            consensus_hash,
            app_hash,
            last_results_hash,
            evidence_hash,
            proposer_address,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Header)
            and self.version == other.version
            and self.chain_id == other.chain_id
            and self.height == other.height
            and self.time == other.time
            and self.last_block_id == other.last_block_id
            and self.last_commit_hash == other.last_commit_hash
            and self.data_hash == other.data_hash
            and self.validators_hash == other.validators_hash
            and self.next_validators_hash == other.next_validators_hash
            and self.consensus_hash == other.consensus_hash
            and self.app_hash == other.app_hash
            and self.last_results_hash == other.last_results_hash
            and self.evidence_hash == other.evidence_hash
            and self.proposer_address == other.proposer_address
        )


class Validator:
    """This class represents an instance of Validator."""

    def __init__(self, address: bytes, power: int):
        """Initialise an instance of Validator."""
        self.address = address
        self.power = power

    @staticmethod
    def encode(validator_protobuf_object, validator_object: "Validator") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the validator_protobuf_object argument is matched with the instance of this class in the 'validator_object' argument.

        :param validator_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param validator_object: an instance of this class to be encoded in the protocol buffer object.
        """
        validator_protobuf_object.address = validator_object.address
        validator_protobuf_object.power = validator_object.power

    @classmethod
    def decode(cls, validator_protobuf_object) -> "Validator":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'validator_protobuf_object' argument.

        :param validator_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'validator_protobuf_object' argument.
        """
        return Validator(
            validator_protobuf_object.address,
            validator_protobuf_object.power,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Validator)
            and self.address == other.address
            and self.power == other.power
        )


class VoteInfo:
    """This class represents an instance of VoteInfo."""

    def __init__(self, validator: Validator, signed_last_block: bool):
        """Initialise an instance of Validator."""
        self.validator = validator
        self.signed_last_block = signed_last_block

    @staticmethod
    def encode(vote_info_protobuf_object, vote_info_object: "VoteInfo") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the vote_info_protobuf_object argument is matched with the instance of this class in the 'vote_info_object' argument.

        :param vote_info_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param vote_info_object: an instance of this class to be encoded in the protocol buffer object.
        """
        validator_protobuf_object = abci_pb2.AbciMessage.LastCommitInfo.Validator()
        Validator.encode(validator_protobuf_object, vote_info_object.validator)
        vote_info_protobuf_object.validator.CopyFrom(validator_protobuf_object)

        vote_info_protobuf_object.signed_last_block = vote_info_object.signed_last_block

    @classmethod
    def decode(cls, vote_info_protobuf_object) -> "VoteInfo":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'vote_info_protobuf_object' argument.

        :param vote_info_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'vote_info_protobuf_object' argument.
        """
        validator = Validator.decode(vote_info_protobuf_object.validator)
        return VoteInfo(
            validator,
            vote_info_protobuf_object.signed_last_block,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, VoteInfo)
            and self.validator == other.validator
            and self.signed_last_block == other.signed_last_block
        )


class LastCommitInfo:
    """This class represents an instance of LastCommitInfo."""

    def __init__(self, round_: int, votes: List[VoteInfo]):
        """Initialise an instance of LastCommitInfo."""
        self.round_ = round_
        self.votes = votes

    @staticmethod
    def encode(
        last_commit_info_protobuf_object, last_commit_info_object: "LastCommitInfo"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the last_commit_info_protobuf_object argument is matched with the instance of this class in the 'last_commit_info_object' argument.

        :param last_commit_info_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param last_commit_info_object: an instance of this class to be encoded in the protocol buffer object.
        """
        last_commit_info_protobuf_object.round = last_commit_info_object.round_

        votes_protobuf_objects = []
        for vote_info in last_commit_info_object.votes:
            vote_info_protobuf_object = abci_pb2.AbciMessage.LastCommitInfo.VoteInfo()
            VoteInfo.encode(vote_info_protobuf_object, vote_info)
            votes_protobuf_objects.append(vote_info_protobuf_object)
        last_commit_info_protobuf_object.votes.extend(votes_protobuf_objects)

    @classmethod
    def decode(cls, last_commit_info_protobuf_object) -> "LastCommitInfo":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'last_commit_info_protobuf_object' argument.

        :param last_commit_info_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'last_commit_info_protobuf_object' argument.
        """
        vote_info_objects = []
        for vote_info_protobuf_object in list(last_commit_info_protobuf_object.votes):
            vote_info = VoteInfo.decode(vote_info_protobuf_object)
            vote_info_objects.append(vote_info)

        return LastCommitInfo(last_commit_info_protobuf_object.round, vote_info_objects)

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, LastCommitInfo)
            and self.round_ == other.round_
            and self.votes == other.votes
        )


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


class ResultType(Enum):
    """This class represents an instance of ResultType."""

    UNKNOWN = 0  # Unknown result, abort all snapshot restoration
    ACCEPT = 1  # Snapshot accepted, apply chunks
    ABORT = 2  # Abort all snapshot restoration
    REJECT = 3  # Reject this specific snapshot, try others
    REJECT_FORMAT = 4  # Reject all snapshots of this format, try others
    REJECT_SENDER = 5  # Reject all snapshots from the sender(s), try others


class Result:
    """This class represents an instance of Result."""

    def __init__(self, result_type: ResultType):
        """Initialise an instance of Result."""
        self.result_type = result_type

    @staticmethod
    def encode(result_protobuf_object, result_object: "Result") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the result_protobuf_object argument is matched with the instance of this class in the 'result_object' argument.

        :param result_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param result_object: an instance of this class to be encoded in the protocol buffer object.
        """
        result_protobuf_object.result_type = result_object.result_type.value

    @classmethod
    def decode(cls, result_protobuf_object) -> "Result":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'result_protobuf_object' argument.

        :param result_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'result_protobuf_object' argument.
        """
        return Result(ResultType(result_protobuf_object.result_type))

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, Result) and self.result_type == other.result_type


class Snapshot:
    """This class represents an instance of Snapshot."""

    def __init__(
        self, height: int, format_: int, chunks: int, hash_: bytes, metadata: bytes
    ):
        """Initialise an instance of Snapshot."""
        self.height = height
        self.format_ = format_
        self.chunks = chunks
        self.hash_ = hash_
        self.metadata = metadata

    @staticmethod
    def encode(snapshot_protobuf_object, snapshot_object: "Snapshot") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the snapshot_protobuf_object argument is matched with the instance of this class in the 'snapshot_object' argument.

        :param snapshot_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param snapshot_object: an instance of this class to be encoded in the protocol buffer object.
        """
        snapshot_protobuf_object.height = snapshot_object.height
        snapshot_protobuf_object.format = snapshot_object.format_
        snapshot_protobuf_object.chunks = snapshot_object.chunks
        snapshot_protobuf_object.hash = snapshot_object.hash_
        snapshot_protobuf_object.metadata = snapshot_object.metadata

    @classmethod
    def decode(cls, snapshot_protobuf_object) -> "Snapshot":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'snapshot_protobuf_object' argument.

        :param snapshot_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'snapshot_protobuf_object' argument.
        """
        return Snapshot(
            snapshot_protobuf_object.height,
            snapshot_protobuf_object.format,
            snapshot_protobuf_object.chunks,
            snapshot_protobuf_object.hash,
            snapshot_protobuf_object.metadata,
        )

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Snapshot)
            and self.height == other.height
            and self.format_ == other.format_
            and self.chunks == other.chunks
            and self.hash_ == other.hash_
            and self.metadata == other.metadata
        )


class SnapShots:
    """This class represents an instance of SnapShots."""

    def __init__(self, snapshots: List[Snapshot]):
        """Initialise an instance of SnapShots."""
        self.snapshots = snapshots

    @staticmethod
    def encode(snapshots_protobuf_object, snapshots_object: "SnapShots") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the snapshots_protobuf_object argument is matched with the instance of this class in the 'snapshots_object' argument.

        :param snapshots_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param snapshots_object: an instance of this class to be encoded in the protocol buffer object.
        """
        snapshot_protobuf_objects = []
        for snapshot_object in snapshots_object.snapshots:
            snapshot_protobuf_object = abci_pb2.AbciMessage.Snapshot()
            Snapshot.encode(snapshot_protobuf_object, snapshot_object)
            snapshot_protobuf_objects.append(snapshot_protobuf_object)
        snapshots_protobuf_object.snapshots.extend(snapshot_protobuf_objects)

    @classmethod
    def decode(cls, snapshots_protobuf_object) -> "SnapShots":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'snapshots_protobuf_object' argument.

        :param snapshots_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'snapshots_protobuf_object' argument.
        """
        snapshot_objects = []
        for snapshot_protobuf_object in list(snapshots_protobuf_object.snapshots):
            snapshot_objects.append(Snapshot.decode(snapshot_protobuf_object))
        return SnapShots(snapshot_objects)

    def __eq__(self, other):
        """Compare with another object."""
        return isinstance(other, SnapShots) and self.snapshots == other.snapshots


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
        enforce(
            0 <= nanos < 10**9,
            "nanos argument must be from 0 to 999,999,999 inclusive",
            exception_class=ValueError,
        )

    @staticmethod
    def encode(timestamp_protobuf_object, timestamp_object: "Timestamp") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the timestamp_protobuf_object argument is matched with the instance of this class in the 'timestamp_object' argument.

        :param timestamp_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param timestamp_object: an instance of this class to be encoded in the protocol buffer object.
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


class PublicKey:
    """This class represents an instance of PublicKey."""

    class PublicKeyType(Enum):
        """Enumeration of public key types supported by Tendermint."""

        ed25519 = "ed25519"
        secp256k1 = "secp256k1"

    def __init__(self, data: bytes, key_type: PublicKeyType) -> None:
        """
        Initialize the public key object.

        :param data: the data of the public key.
        :param key_type: the type of the public key.
        """
        self.data = data
        self.key_type = key_type

    @staticmethod
    def encode(public_key_protobuf_object, public_key_object: "PublicKey") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the public_key_protobuf_object argument is matched with the instance of this class in the 'public_key_object' argument.

        :param public_key_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param public_key_object: an instance of this class to be encoded in the protocol buffer object.
        """
        key_type_name = public_key_object.key_type.value
        setattr(public_key_protobuf_object, key_type_name, public_key_object.data)

    @classmethod
    def decode(cls, public_key_protobuf_object) -> "PublicKey":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'public_key_protobuf_object' argument.

        :param public_key_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'public_key_protobuf_object' argument.
        """
        key_type_name = public_key_protobuf_object.WhichOneof("sum")
        key_type = PublicKey.PublicKeyType(key_type_name)
        data = getattr(public_key_protobuf_object, key_type_name)
        return PublicKey(data, key_type)

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, PublicKey)
            and self.data == other.data
            and self.key_type == other.key_type
        )


class ValidatorUpdate:
    """This class represents an instance of ValidatorUpdate."""

    def __init__(self, pub_key: PublicKey, power: int):
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
        """
        PublicKey.encode(
            validator_update_protobuf_object.pub_key, validator_update_object.pub_key
        )
        validator_update_protobuf_object.power = validator_update_object.power

    @classmethod
    def decode(cls, validator_update_protobuf_object) -> "ValidatorUpdate":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'validator_update_protobuf_object' argument.

        :param validator_update_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'validator_update_protobuf_object' argument.
        """
        pub_key = PublicKey.decode(validator_update_protobuf_object.pub_key)
        return ValidatorUpdate(
            pub_key,
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
        self.validator_updates = validator_updates

    @staticmethod
    def encode(
        validator_updates_protobuf_object, validator_updates_object: "ValidatorUpdates"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the validator_updates_protobuf_object argument is matched with the instance of this class in the 'validator_updates_object' argument.

        :param validator_updates_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param validator_updates_object: an instance of this class to be encoded in the protocol buffer object.
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
