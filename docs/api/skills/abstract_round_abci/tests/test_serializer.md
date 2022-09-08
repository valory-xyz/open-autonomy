<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`serializer

Test the serializer.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.hypothesis_cleanup"></a>

#### hypothesis`_`cleanup

```python
@pytest.fixture(scope="session", autouse=True)
def hypothesis_cleanup() -> Generator
```

Fixture to remove hypothesis directory after tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_encode_decode_i"></a>

#### test`_`encode`_`decode`_`i

```python
def test_encode_decode_i() -> None
```

Test encode decode logic.

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_encode_decode_ii"></a>

#### test`_`encode`_`decode`_`ii

```python
def test_encode_decode_ii() -> None
```

Test encode decode logic.

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.node"></a>

#### node

```python
def node() -> defaultdict
```

Recursive defaultdict

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.to_dict"></a>

#### to`_`dict

```python
def to_dict(dd: Dict[str, Any]) -> Dict[str, Any]
```

Recursive defaultdict to dict

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.types_of"></a>

#### types`_`of

```python
def types_of(d: Dict[str, Any]) -> Dict[str, Any]
```

Get `key: type(value)` mapping, recursively.

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.is_decodable"></a>

#### is`_`decodable

```python
def is_decodable(b: bytes) -> bool
```

Check if bytes can be decoded

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.is_serializer_compatible"></a>

#### is`_`serializer`_`compatible

```python
def is_serializer_compatible(data: Dict) -> bool
```

Check whether the serializer can reconstitute the data

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_unsupported_key_types"></a>

#### test`_`unsupported`_`key`_`types

```python
@pytest.mark.parametrize(
    "unsupported_type",
    [bool, int, float, tuple, frozenset],
)
def test_unsupported_key_types(unsupported_type: Any) -> None
```

Python accepted key-types not compatible with protobuf

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_unsupported_value_type"></a>

#### test`_`unsupported`_`value`_`type

```python
@pytest.mark.parametrize(
    "unsupported_type",
    [tuple, list, set, frozenset],
)
def test_unsupported_value_type(unsupported_type: Any) -> None
```

Not implemented.

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_single_values"></a>

#### test`_`single`_`values

```python
@pytest.mark.parametrize(
    "value",
    [True, 1 << 256, 3.14, "string", b"bytes", {}],
)
def test_single_values(value: Any) -> None
```

Single value type test

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_nested_mapping"></a>

#### test`_`nested`_`mapping

```python
def test_nested_mapping() -> None
```

Nested mapping test

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_randomized_mapping"></a>

#### test`_`randomized`_`mapping

```python
@given(st.builds(zip, st.lists(st.text(), unique=True), st.lists(value_strategy)))
def test_randomized_mapping(zipper: Any) -> None
```

Test randomized mappings

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_randomized_nested_mapping"></a>

#### test`_`randomized`_`nested`_`mapping

```python
@given(st.recursive(value_strategy, lambda trees: st.dictionaries(st.text(), trees)))
def test_randomized_nested_mapping(data: Any) -> None
```

Test randomized nested mappings

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_encode_nan"></a>

#### test`_`encode`_`nan

```python
def test_encode_nan() -> None
```

Test encode Nan.

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_fuzz_encode"></a>

#### test`_`fuzz`_`encode

```python
@pytest.mark.skip
def test_fuzz_encode() -> None
```

Fuzz test for serializer. Run directly as a function, not through pytest

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_encode_non_unicode_raises"></a>

#### test`_`encode`_`non`_`unicode`_`raises

```python
def test_encode_non_unicode_raises() -> None
```

Test encode non unicode.

<a id="packages.valory.skills.abstract_round_abci.tests.test_serializer.test_sentinel_raises"></a>

#### test`_`sentinel`_`raises

```python
def test_sentinel_raises() -> None
```

Test SENTINEL.

