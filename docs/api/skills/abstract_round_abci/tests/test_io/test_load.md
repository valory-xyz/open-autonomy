<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_load"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`io.test`_`load

Tests for the loading functionality of abstract round abci.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_load.TestLoader"></a>

## TestLoader Objects

```python
class TestLoader()
```

Tests for the `Loader`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_load.TestLoader.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Setup the tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_load.TestLoader.test__get_loader_from_filetype"></a>

#### test`__`get`_`loader`_`from`_`filetype

```python
@staticmethod
@pytest.mark.parametrize(
    "filetype, custom_loader, expected_loader",
    (
        (None, None, None),
        (SupportedFiletype.JSON, None, JSONLoader.load_single_object),
        (
            SupportedFiletype.JSON,
            __dummy_custom_loader,
            JSONLoader.load_single_object,
        ),
        (None, __dummy_custom_loader, __dummy_custom_loader),
    ),
)
def test__get_loader_from_filetype(
        filetype: Optional[SupportedFiletype], custom_loader: CustomLoaderType,
        expected_loader: Optional[SupportedLoaderType]) -> None
```

Test `_get_loader_from_filetype`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_load.TestLoader.test_load"></a>

#### test`_`load

```python
def test_load() -> None
```

Test `load`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_load.TestLoader.test_no_object"></a>

#### test`_`no`_`object

```python
def test_no_object() -> None
```

Test `load` throws error when no object is provided.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.test_load.TestLoader.test_load_multiple_objects"></a>

#### test`_`load`_`multiple`_`objects

```python
def test_load_multiple_objects() -> None
```

Test `load` when multiple objects are to be deserialized.

