<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_store"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`io.test`_`store

Tests for the storing functionality of abstract round abci.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_store.TestStorer"></a>

## TestStorer Objects

```python
class TestStorer()
```

Tests for the `Storer`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_store.TestStorer.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Setup the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_store.TestStorer.test__get_single_storer_from_filetype"></a>

#### test`__`get`_`single`_`storer`_`from`_`filetype

```python
@staticmethod
@pytest.mark.parametrize(
    "filetype, custom_storer, expected_storer",
    (
        (None, None, None),
        (SupportedFiletype.JSON, None, JSONStorer.serialize_object),
        (
            SupportedFiletype.JSON,
            __dummy_custom_storer,
            JSONStorer.serialize_object,
        ),
        (None, __dummy_custom_storer, __dummy_custom_storer),
    ),
)
def test__get_single_storer_from_filetype(
        filetype: Optional[SupportedFiletype],
        custom_storer: Optional[CustomStorerType],
        expected_storer: Optional[SupportedStorerType],
        tmp_path: PosixPath) -> None
```

Test `_get_single_storer_from_filetype`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_store.TestStorer.test_store"></a>

#### test`_`store

```python
def test_store() -> None
```

Test `store`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_store.TestStorer.test_store_multiple"></a>

#### test`_`store`_`multiple

```python
def test_store_multiple() -> None
```

Test `store` when multiple files are present.

