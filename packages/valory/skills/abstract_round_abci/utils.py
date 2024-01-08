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

"""This module contains utility functions for the 'abstract_round_abci' skill."""

import builtins
import collections
import dataclasses
import sys
import types
import typing
from hashlib import sha256
from math import ceil
from typing import (
    Any,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from unittest.mock import MagicMock

import typing_extensions
from eth_typing.bls import BLSPubkey, BLSSignature
from py_ecc.bls import G2Basic as bls
from typing_extensions import Literal, TypeGuard, TypedDict


MAX_UINT64 = 2**64 - 1
DEFAULT_TENDERMINT_P2P_PORT = 26656


class VerifyDrand:  # pylint: disable=too-few-public-methods
    """
    Tool to verify Randomness retrieved from various external APIs.

    The ciphersuite used is BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_

    cryptographic-specification section in https://drand.love/docs/specification/
    https://github.com/ethereum/py_ecc
    """

    @classmethod
    def _int_to_bytes_big(cls, value: int) -> bytes:
        """Convert int to bytes."""
        if value < 0 or value > MAX_UINT64:
            raise ValueError(
                "VerifyDrand can only handle positive numbers representable with 8 bytes"
            )
        return int.to_bytes(value, 8, byteorder="big", signed=False)

    @classmethod
    def _verify_randomness_hash(cls, randomness: bytes, signature: bytes) -> bool:
        """Verify randomness hash."""
        return sha256(signature).digest() == randomness

    @classmethod
    def _verify_signature(
        cls,
        pubkey: Union[BLSPubkey, bytes],
        message: bytes,
        signature: Union[BLSSignature, bytes],
    ) -> bool:
        """Verify randomness signature."""
        return bls.Verify(
            cast(BLSPubkey, pubkey), message, cast(BLSSignature, signature)
        )

    def verify(self, data: Dict, pubkey: str) -> Tuple[bool, Optional[str]]:
        """
        Verify drand value retried from external APIs.

        :param data: dictionary containing drand parameters.
        :param pubkey: league of entropy public key
                       public-endpoints section in https://drand.love/developer/http-api/
        :returns: bool, error message
        """

        encoded_pubkey = bytes.fromhex(pubkey)
        try:
            randomness = data["randomness"]
            signature = data["signature"]
            round_value = int(data["round"])
        except KeyError as e:
            return False, f"DRAND dict is missing value for {e}"

        previous_signature = data.pop("previous_signature", "")
        encoded_randomness = bytes.fromhex(randomness)
        encoded_signature = bytes.fromhex(signature)
        int_encoded_round = self._int_to_bytes_big(round_value)
        encoded_previous_signature = bytes.fromhex(previous_signature)

        if not self._verify_randomness_hash(encoded_randomness, encoded_signature):
            return False, "Failed randomness hash check."

        msg_b = encoded_previous_signature + int_encoded_round
        msg_hash_b = sha256(msg_b).digest()

        if not self._verify_signature(encoded_pubkey, msg_hash_b, encoded_signature):
            return False, "Failed bls.Verify check."

        return True, None


def get_data_from_nested_dict(
    nested_dict: Dict, keys: str, separator: str = ":"
) -> Any:
    """Gets content from a nested dictionary, using serialized response keys which are split by a given separator.

    :param nested_dict: the nested dictionary to get the content from
    :param keys: the keys to use on the nested dictionary in order to get the content
    :param separator: the separator to use in order to get the keys list.
    Choose the separator carefully, so that it does not conflict with any character of the keys.

    :returns: the content result
    """
    parsed_keys = keys.split(separator)
    for key in parsed_keys:
        nested_dict = nested_dict[key]
    return nested_dict


def get_value_with_type(value: Any, type_name: str) -> Any:
    """Get the given value as the specified type."""
    return getattr(builtins, type_name)(value)


def parse_tendermint_p2p_url(url: str) -> Tuple[str, int]:
    """Parse tendermint P2P url."""
    hostname, *_port = url.split(":")
    if len(_port) > 0:
        port_str, *_ = _port
        port = int(port_str)
    else:
        port = DEFAULT_TENDERMINT_P2P_PORT

    return hostname, port


##
# Typing utils - to be extracted to open-aea
##


try:
    # Python >=3.8 should have these functions already
    from typing import get_args as _get_args  # pylint: disable=ungrouped-imports
    from typing import get_origin as _get_origin  # pylint: disable=ungrouped-imports
except ImportError:  # pragma: nocover
    # Python 3.7
    def _get_origin(tp):  # type: ignore
        """Copied from the Python 3.8 typing module"""
        if isinstance(tp, typing._GenericAlias):  # pylint: disable=protected-access
            return tp.__origin__
        if tp is typing.Generic:
            return typing.Generic
        return None

    def _get_args(tp):  # type: ignore
        """Copied from the Python 3.8 typing module"""
        if isinstance(tp, typing._GenericAlias):  # pylint: disable=protected-access
            res = tp.__args__
            if get_origin(tp) is collections.abc.Callable and res[0] is not Ellipsis:
                res = (list(res[:-1]), res[-1])
            return res
        return ()


def get_origin(tp):  # type: ignore
    """
    Get the unsubscripted version of a type.

    This supports generic types, Callable, Tuple, Union, Literal, Final and
    ClassVar. Returns None for unsupported types.
    Examples:
        get_origin(Literal[42]) is Literal
        get_origin(int) is None
        get_origin(ClassVar[int]) is ClassVar
        get_origin(Generic) is Generic
        get_origin(Generic[T]) is Generic
        get_origin(Union[T, int]) is Union
        get_origin(List[Tuple[T, T]][int]) == list
    """
    return _get_origin(tp)


def get_args(tp):  # type: ignore
    """
    Get type arguments with all substitutions performed.

    For unions, basic simplifications used by Union constructor are performed.
    Examples:
        get_args(Dict[str, int]) == (str, int)
        get_args(int) == ()
        get_args(Union[int, Union[T, int], str][int]) == (int, str)
        get_args(Union[int, Tuple[T, int]][str]) == (int, Tuple[str, int])
        get_args(Callable[[], T][int]) == ([], int)
    """
    return _get_args(tp)


##
# The following is borrowed from https://github.com/tamuhey/dataclass_utils/blob/81580d2c0c285081db06be02b4ecdd125532bef5/dataclass_utils/type_checker.py#L152
##


def is_pep604_union(ty: Type[Any]) -> bool:
    """Check if a type is a PEP 604 union."""
    return sys.version_info >= (3, 10) and ty is types.UnionType  # type: ignore # noqa: E721 # pylint: disable=no-member


def _path_to_str(path: List[str]) -> str:
    """Convert a path to a string."""
    return " -> ".join(reversed(path))


class AutonomyTypeError(TypeError):
    """Type Error for the Autonomy type check system."""

    def __init__(
        self,
        ty: Type[Any],
        value: Any,
        path: Optional[List[str]] = None,
    ):
        """Initialize AutonomyTypeError."""
        self.ty = ty
        self.value = value
        self.path = path or []
        super().__init__()

    def __str__(self) -> str:
        """Get string representation of AutonomyTypeError."""
        path = _path_to_str(self.path)
        msg = f"Error in field '{path}'. Expected type {self.ty}, got {type(self.value)} (value: {self.value})"
        return msg


Result = Optional[AutonomyTypeError]  # returns error context


def check(  # pylint: disable=too-many-return-statements
    value: Any, ty: Type[Any]
) -> Result:
    """
    Check a value against a type.

    # Examples
    >>> assert is_error(check(1, str))
    >>> assert not is_error(check(1, int))
    >>> assert is_error(check(1, list))
    >>> assert is_error(check(1.3, int))
    >>> assert is_error(check(1.3, Union[str, int]))
    """
    if isinstance(value, MagicMock):
        # testing - any magic value is ignored
        return None
    if not isinstance(value, type) and dataclasses.is_dataclass(ty):
        # dataclass
        return check_dataclass(value, ty)
    if is_typeddict(ty):
        # should use `typing.is_typeddict` in future
        return check_typeddict(value, ty)
    to = get_origin(ty)
    if to is not None:
        # generics
        err = check(value, to)
        if is_error(err):
            return err

        if to is list or to is set or to is frozenset:
            err = check_mono_container(value, ty)
        elif to is dict:
            err = check_dict(value, ty)  # type: ignore
        elif to is tuple:
            err = check_tuple(value, ty)
        elif to is Literal:
            err = check_literal(value, ty)
        elif to is Union or is_pep604_union(to):
            err = check_union(value, ty)
        elif to is type:
            err = check_class(value, ty)
        return err
    if isinstance(ty, type):
        # concrete type
        if is_pep604_union(ty):
            pass  # pragma: no cover
        elif issubclass(ty, bool):
            if not isinstance(value, ty):
                return AutonomyTypeError(ty=ty, value=value)
        elif issubclass(ty, int):  # For boolean
            return check_int(value, ty)
        elif ty is typing.Any:
            # `isinstance(value, typing.Any) fails on python 3.11`
            # https://stackoverflow.com/questions/68031358/typeerror-typing-any-cannot-be-used-with-isinstance
            pass
        elif not isinstance(value, ty):
            return AutonomyTypeError(ty=ty, value=value)
    return None


def check_class(value: Any, ty: Type[Any]) -> Result:
    """Check class type."""
    if not issubclass(value, get_args(ty)):
        return AutonomyTypeError(ty=ty, value=value)
    return None


def check_int(value: Any, ty: Type[Any]) -> Result:
    """Check int type."""
    if isinstance(value, bool) or not isinstance(value, ty):
        return AutonomyTypeError(ty=ty, value=value)
    return None


def check_literal(value: Any, ty: Type[Any]) -> Result:
    """Check literal type."""
    if all(value != t for t in get_args(ty)):
        return AutonomyTypeError(ty=ty, value=value)
    return None


def check_tuple(value: Any, ty: Type[Tuple[Any, ...]]) -> Result:
    """Check tuple type."""
    types_ = get_args(ty)
    if len(types_) == 2 and types_[1] == ...:
        # arbitrary length tuple (e.g. Tuple[int, ...])
        for v in value:
            err = check(v, types_[0])
            if is_error(err):
                return err
        return None

    if len(value) != len(types_):
        return AutonomyTypeError(ty=ty, value=value)
    for v, t in zip(value, types_):
        err = check(v, t)
        if is_error(err):
            return err
    return None


def check_union(value: Any, ty: Type[Any]) -> Result:
    """Check union type."""
    if any(not is_error(check(value, t)) for t in get_args(ty)):
        return None
    return AutonomyTypeError(ty=ty, value=value)


def check_mono_container(
    value: Any, ty: Union[Type[List[Any]], Type[Set[Any]], Type[FrozenSet[Any]]]
) -> Result:
    """Check mono container type."""
    ty_item = get_args(ty)[0]
    for v in value:
        err = check(v, ty_item)
        if is_error(err):
            return err
    return None


def check_dict(value: Dict[Any, Any], ty: Type[Dict[Any, Any]]) -> Result:
    """Check dict type."""
    args = get_args(ty)
    ty_key = args[0]
    ty_item = args[1]
    for k, v in value.items():
        err = check(k, ty_key)
        if is_error(err):
            return err
        err = check(v, ty_item)
        if err is not None:
            err.path.append(k)
            return err
    return None


def check_dataclass(value: Any, ty: Type[Any]) -> Result:
    """Check dataclass type."""
    if not dataclasses.is_dataclass(value):
        return AutonomyTypeError(ty, value)
    for k, ty_ in typing.get_type_hints(ty).items():
        v = getattr(value, k)
        err = check(v, ty_)
        if err is not None:
            err.path.append(k)
            return err
    return None


def check_typeddict(value: Any, ty: Type[Any]) -> Result:
    """Check typeddict type."""
    if not isinstance(value, dict):
        return AutonomyTypeError(ty, value)  # pragma: no cover
    is_total: bool = ty.__total__  # type: ignore
    for k, ty_ in typing.get_type_hints(ty).items():
        if k not in value:
            if is_total:
                return AutonomyTypeError(ty_, value, [k])
            continue
        v = value[k]
        err = check(v, ty_)
        if err is not None:
            err.path.append(k)
            return err
    return None


# TODO: incorporate
def is_typevar(ty: Type[Any]) -> TypeGuard[TypeVar]:
    """Check typevar."""
    return isinstance(ty, TypeVar)  # pragma: no cover


def is_error(ret: Result) -> TypeGuard[AutonomyTypeError]:
    """Check error."""
    return ret is not None


def is_typeddict(ty: Type[Any]) -> TypeGuard[Type[TypedDict]]:  # type: ignore
    """Check typeddict."""
    # TODO: Should use `typing.is_typeddict` in future
    #       or, use publich API
    T = "_TypedDictMeta"
    for mod in [typing, typing_extensions]:
        if hasattr(mod, T) and isinstance(ty, getattr(mod, T)):
            return True
    return False


def check_type(name: str, value: Any, type_hint: Any) -> None:
    """Check value against type hint recursively"""
    err = check(value, type_hint)
    if err is not None:
        err.path.append(name)
        raise err


def is_primitive_or_none(obj: Any) -> bool:
    """Checks if the given object is a primitive type or `None`."""
    primitives = (bool, int, float, str)
    return isinstance(obj, primitives) or obj is None


def is_json_serializable(obj: Any) -> bool:
    """Checks if the given object is json serializable."""
    if isinstance(obj, (tuple, list)):
        return all(is_json_serializable(x) for x in obj)
    if isinstance(obj, dict):
        return all(
            is_primitive_or_none(k) and is_json_serializable(v) for k, v in obj.items()
        )

    return is_primitive_or_none(obj)


def filter_negative(mapping: Dict[str, int]) -> Iterator[str]:
    """Return the keys of a dictionary for which the values are negative integers."""
    return (key for key, number in mapping.items() if number < 0)


def consensus_threshold(nb: int) -> int:
    """
    Get consensus threshold.

    :param nb: the number of participants
    :return: the consensus threshold
    """
    return ceil((2 * nb + 1) / 3)


KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")


def inverse(dict_: Dict[KeyType, ValueType]) -> Dict[ValueType, List[KeyType]]:
    """Get the inverse of a dictionary."""
    inverse_: Dict[ValueType, List[KeyType]] = {val: [] for val in dict_.values()}
    for key, value in dict_.items():
        inverse_[value].append(key)
    return inverse_
