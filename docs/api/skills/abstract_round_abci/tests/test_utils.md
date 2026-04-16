<a id="packages.valory.skills.abstract_round_abci.tests.test_utils"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`utils

Test the utils.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand"></a>

## TestVerifyDrand Objects

```python
class TestVerifyDrand()
```

Test DrandVerify.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Setup test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand.test_verify"></a>

#### test`_`verify

```python
def test_verify() -> None
```

Test verify method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand.test_verify_fails"></a>

#### test`_`verify`_`fails

```python
def test_verify_fails() -> None
```

Test verify method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.TestVerifyDrand.test_negative_and_overflow"></a>

#### test`_`negative`_`and`_`overflow

```python
@pytest.mark.parametrize("value", (-1, MAX_UINT64 + 1))
def test_negative_and_overflow(value: int) -> None
```

Test verify method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_verify_int_to_bytes_big_fuzz"></a>

#### test`_`verify`_`int`_`to`_`bytes`_`big`_`fuzz

```python
@given(st.integers(min_value=0, max_value=MAX_UINT64))
def test_verify_int_to_bytes_big_fuzz(integer: int) -> None
```

Test VerifyDrand.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_verify_int_to_bytes_big_raises"></a>

#### test`_`verify`_`int`_`to`_`bytes`_`big`_`raises

```python
@pytest.mark.parametrize("integer", [-1, MAX_UINT64 + 1])
def test_verify_int_to_bytes_big_raises(integer: int) -> None
```

Test VerifyDrand._int_to_bytes_big

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_verify_randomness_hash_fuzz"></a>

#### test`_`verify`_`randomness`_`hash`_`fuzz

```python
@given(st.binary())
def test_verify_randomness_hash_fuzz(input_bytes: bytes) -> None
```

Test VerifyDrand._verify_randomness_hash

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_get_data_from_nested_dict"></a>

#### test`_`get`_`data`_`from`_`nested`_`dict

```python
@given(
    st.lists(st.text(), min_size=1, max_size=50),
    st.binary(),
    st.characters(),
)
def test_get_data_from_nested_dict(nested_keys: List[str], final_value: bytes,
                                   separator: str) -> None
```

Test `get_data_from_nested_dict`

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_get_value_with_type"></a>

#### test`_`get`_`value`_`with`_`type

```python
@pytest.mark.parametrize(
    "type_name, type_, value",
    (
        ("str", str, "1"),
        ("int", int, 1),
        ("float", float, 1.1),
        ("dict", dict, {
            1: 1
        }),
        ("list", list, [1]),
        ("non_existent", None, 1),
    ),
)
def test_get_value_with_type(type_name: str, type_: Type, value: Any) -> None
```

Test `get_value_with_type`

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_parse_tendermint_p2p_url"></a>

#### test`_`parse`_`tendermint`_`p2p`_`url

```python
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
def test_parse_tendermint_p2p_url(url: str,
                                  expected_output: Tuple[str, int]) -> None
```

Test `parse_tendermint_p2p_url` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_is_primitive_or_none"></a>

#### test`_`is`_`primitive`_`or`_`none

```python
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
def test_is_primitive_or_none(valid_obj: Any, invalid_obj: Any) -> None
```

Test `is_primitive_or_none`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_is_json_serializable"></a>

#### test`_`is`_`json`_`serializable

```python
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
def test_is_json_serializable(valid_obj: Any, invalid_obj: Any) -> None
```

Test `is_json_serializable`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_filter_negative"></a>

#### test`_`filter`_`negative

```python
@given(
    positive=st.dictionaries(st.text(), st.integers(min_value=0)),
    negative=st.dictionaries(st.text(), st.integers(max_value=-1)),
)
def test_filter_negative(positive: Dict[str, int],
                         negative: Dict[str, int]) -> None
```

Test `filter_negative`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_consensus_threshold"></a>

#### test`_`consensus`_`threshold

```python
@pytest.mark.parametrize(
    "nb, threshold",
    ((1, 1), (2, 2), (3, 3), (4, 3), (5, 4), (6, 5), (100, 67), (300, 201)),
)
def test_consensus_threshold(nb: int, threshold: int) -> None
```

Test `consensus_threshold`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_utils.test_inverse"></a>

#### test`_`inverse

```python
@pytest.mark.parametrize(
    "dict_, expected",
    (
        ({}, {}),
        (
            {
                "test": "this",
                "which?": "this"
            },
            {
                "this": ["test", "which?"]
            },
        ),
        (
            {
                "test": "this",
                "which?": "this",
                "hm": "ok"
            },
            {
                "this": ["test", "which?"],
                "ok": ["hm"]
            },
        ),
        (
            {
                "test": "this",
                "hm": "ok"
            },
            {
                "this": ["test"],
                "ok": ["hm"]
            },
        ),
        (
            {
                "test": "this",
                "hm": "ok",
                "ok": "ok"
            },
            {
                "this": ["test"],
                "ok": ["hm", "ok"]
            },
        ),
        (
            {
                "test": "this",
                "which?": "this",
                "hm": "ok",
                "ok": "ok"
            },
            {
                "this": ["test", "which?"],
                "ok": ["hm", "ok"]
            },
        ),
    ),
)
def test_inverse(dict_: Dict[KeyType, ValueType],
                 expected: Dict[ValueType, List[KeyType]]) -> None
```

Test `inverse`.

