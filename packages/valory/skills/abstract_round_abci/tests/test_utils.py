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

"""Test the utils.py module of the skill."""

from collections import defaultdict
from string import printable
from typing import Any, Dict, List, Tuple, Type
from unittest import mock

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from packages.valory.skills.abstract_round_abci.tests.conftest import profile_name
from packages.valory.skills.abstract_round_abci.utils import (
    DEFAULT_TENDERMINT_P2P_PORT,
    KeyType,
    MAX_UINT64,
    ValueType,
    VerifyDrand,
    consensus_threshold,
    filter_negative,
    get_data_from_nested_dict,
    get_value_with_type,
    inverse,
    is_json_serializable,
    is_primitive_or_none,
    parse_tendermint_p2p_url,
)


settings.load_profile(profile_name)


# pylint: skip-file


DRAND_PUBLIC_KEY: str = "868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784a9402801af31"

DRAND_VALUE = {
    "round": 1416669,
    "randomness": "f6be4bf1fa229f22340c1a5b258f809ac4af558200775a67dacb05f0cb258a11",
    "signature": (
        "b44d00516f46da3a503f9559a634869b6dc2e5d839e46ec61a090e3032172954929a5"
        "d9bd7197d7739fe55db770543c71182562bd0ad20922eb4fe6b8a1062ed21df3b68de"
        "44694eb4f20b35262fa9d63aa80ad3f6172dd4d33a663f21179604"
    ),
    "previous_signature": (
        "903c60a4b937a804001032499a855025573040cb86017c38e2b1c3725286756ce8f33"
        "61188789c17336beaf3f9dbf84b0ad3c86add187987a9a0685bc5a303e37b008fba8c"
        "44f02a416480dd117a3ff8b8075b1b7362c58af195573623187463"
    ),
}


class TestVerifyDrand:
    """Test DrandVerify."""

    drand_check: VerifyDrand

    def setup(
        self,
    ) -> None:
        """Setup test."""
        self.drand_check = VerifyDrand()

    def test_verify(
        self,
    ) -> None:
        """Test verify method."""

        result, error = self.drand_check.verify(DRAND_VALUE, DRAND_PUBLIC_KEY)
        assert result
        assert error is None

    def test_verify_fails(
        self,
    ) -> None:
        """Test verify method."""

        drand_value = DRAND_VALUE.copy()
        del drand_value["randomness"]
        result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)
        assert not result
        assert error == "DRAND dict is missing value for 'randomness'"

        drand_value = DRAND_VALUE.copy()
        drand_value["randomness"] = "".join(
            list(drand_value["randomness"])[:-1] + ["0"]  # type: ignore
        )
        result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)
        assert not result
        assert error == "Failed randomness hash check."

        drand_value = DRAND_VALUE.copy()
        with mock.patch.object(
            self.drand_check, "_verify_signature", return_value=False
        ):
            result, error = self.drand_check.verify(drand_value, DRAND_PUBLIC_KEY)

        assert not result
        assert error == "Failed bls.Verify check."

    @pytest.mark.parametrize("value", (-1, MAX_UINT64 + 1))
    def test_negative_and_overflow(self, value: int) -> None:
        """Test verify method."""
        with pytest.raises(ValueError):
            self.drand_check._int_to_bytes_big(value)


@given(st.integers(min_value=0, max_value=MAX_UINT64))
def test_verify_int_to_bytes_big_fuzz(integer: int) -> None:
    """Test VerifyDrand."""

    VerifyDrand._int_to_bytes_big(integer)


@pytest.mark.parametrize("integer", [-1, MAX_UINT64 + 1])
def test_verify_int_to_bytes_big_raises(integer: int) -> None:
    """Test VerifyDrand._int_to_bytes_big"""

    expected = "VerifyDrand can only handle positive numbers representable with 8 bytes"
    with pytest.raises(ValueError, match=expected):
        VerifyDrand._int_to_bytes_big(integer)


@given(st.binary())
def test_verify_randomness_hash_fuzz(input_bytes: bytes) -> None:
    """Test VerifyDrand._verify_randomness_hash"""

    VerifyDrand._verify_randomness_hash(input_bytes, input_bytes)


@given(
    st.lists(st.text(), min_size=1, max_size=50),
    st.binary(),
    st.characters(),
)
def test_get_data_from_nested_dict(
    nested_keys: List[str], final_value: bytes, separator: str
) -> None:
    """Test `get_data_from_nested_dict`"""
    assume(not any(separator in key for key in nested_keys))

    def create_nested_dict() -> defaultdict:
        """Recursively create a nested dict of arbitrary size."""
        return defaultdict(create_nested_dict)

    nested_dict = create_nested_dict()
    key_access = (f"[nested_keys[{i}]]" for i in range(len(nested_keys)))
    expression = "nested_dict" + "".join(key_access)
    expression += " = final_value"
    exec(expression)  # nosec

    serialized_keys = separator.join(nested_keys)
    actual = get_data_from_nested_dict(nested_dict, serialized_keys, separator)
    assert actual == final_value


@pytest.mark.parametrize(
    "type_name, type_, value",
    (
        ("str", str, "1"),
        ("int", int, 1),
        ("float", float, 1.1),
        ("dict", dict, {1: 1}),
        ("list", list, [1]),
        ("non_existent", None, 1),
    ),
)
def test_get_value_with_type(type_name: str, type_: Type, value: Any) -> None:
    """Test `get_value_with_type`"""
    if type_ is None:
        with pytest.raises(
            AttributeError, match=f"module 'builtins' has no attribute '{type_name}'"
        ):
            get_value_with_type(value, type_name)
        return

    actual = get_value_with_type(value, type_name)
    assert type(actual) == type_
    assert actual == value


@pytest.mark.parametrize(
    ("url", "expected_output"),
    (
        ("localhost", ("localhost", DEFAULT_TENDERMINT_P2P_PORT)),
        ("localhost:80", ("localhost", 80)),
        ("some.random.host:80", ("some.random.host", 80)),
        ("1.1.1.1", ("1.1.1.1", DEFAULT_TENDERMINT_P2P_PORT)),
        ("1.1.1.1:80", ("1.1.1.1", 80)),
    ),
)
def test_parse_tendermint_p2p_url(url: str, expected_output: Tuple[str, int]) -> None:
    """Test `parse_tendermint_p2p_url` method."""

    assert parse_tendermint_p2p_url(url=url) == expected_output


@given(
    st.one_of(st.none(), st.integers(), st.floats(), st.text(), st.booleans()),
    st.one_of(
        st.nothing(),
        st.frozensets(st.integers()),
        st.sets(st.integers()),
        st.lists(st.integers()),
        st.dictionaries(st.integers(), st.integers()),
        st.dates(),
        st.complex_numbers(),
        st.just(object()),
    ),
)
def test_is_primitive_or_none(valid_obj: Any, invalid_obj: Any) -> None:
    """Test `is_primitive_or_none`."""
    assert is_primitive_or_none(valid_obj)
    assert not is_primitive_or_none(invalid_obj)


@given(
    st.recursive(
        st.none() | st.booleans() | st.floats() | st.text(printable),
        lambda children: st.lists(children)
        | st.dictionaries(st.text(printable), children),
    ),
    st.one_of(
        st.nothing(),
        st.frozensets(st.integers()),
        st.sets(st.integers()),
        st.dates(),
        st.complex_numbers(),
        st.just(object()),
    ),
)
def test_is_json_serializable(valid_obj: Any, invalid_obj: Any) -> None:
    """Test `is_json_serializable`."""
    assert is_json_serializable(valid_obj)
    assert not is_json_serializable(invalid_obj)


@given(
    positive=st.dictionaries(st.text(), st.integers(min_value=0)),
    negative=st.dictionaries(st.text(), st.integers(max_value=-1)),
)
def test_filter_negative(positive: Dict[str, int], negative: Dict[str, int]) -> None:
    """Test `filter_negative`."""
    assert len(tuple(filter_negative(positive))) == 0
    assert set(filter_negative(negative)) == set(negative.keys())


@pytest.mark.parametrize(
    "nb, threshold",
    ((1, 1), (2, 2), (3, 3), (4, 3), (5, 4), (6, 5), (100, 67), (300, 201)),
)
def test_consensus_threshold(nb: int, threshold: int) -> None:
    """Test `consensus_threshold`."""
    assert consensus_threshold(nb) == threshold


@pytest.mark.parametrize(
    "dict_, expected",
    (
        ({}, {}),
        (
            {"test": "this", "which?": "this"},
            {"this": ["test", "which?"]},
        ),
        (
            {"test": "this", "which?": "this", "hm": "ok"},
            {"this": ["test", "which?"], "ok": ["hm"]},
        ),
        (
            {"test": "this", "hm": "ok"},
            {"this": ["test"], "ok": ["hm"]},
        ),
        (
            {"test": "this", "hm": "ok", "ok": "ok"},
            {"this": ["test"], "ok": ["hm", "ok"]},
        ),
        (
            {"test": "this", "which?": "this", "hm": "ok", "ok": "ok"},
            {"this": ["test", "which?"], "ok": ["hm", "ok"]},
        ),
    ),
)
def test_inverse(
    dict_: Dict[KeyType, ValueType], expected: Dict[ValueType, List[KeyType]]
) -> None:
    """Test `inverse`."""
    assert inverse(dict_) == expected
