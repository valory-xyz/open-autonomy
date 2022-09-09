<a id="packages.valory.skills.abstract_round_abci.tests.test_io.conftest"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`io.conftest

Conftest module for io tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.conftest.dummy_obj"></a>

#### dummy`_`obj

```python
@pytest.fixture
def dummy_obj() -> StoredJSONType
```

A dummy custom object to test the storing with.

<a id="packages.valory.skills.abstract_round_abci.tests.test_io.conftest.dummy_multiple_obj"></a>

#### dummy`_`multiple`_`obj

```python
@pytest.fixture
def dummy_multiple_obj(dummy_obj: StoredJSONType) -> Dict[str, StoredJSONType]
```

Many dummy custom objects to test the storing with.

