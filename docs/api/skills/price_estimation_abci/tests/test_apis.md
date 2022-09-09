<a id="packages.valory.skills.price_estimation_abci.tests.test_apis"></a>

# packages.valory.skills.price`_`estimation`_`abci.tests.test`_`apis

Test various price apis.

<a id="packages.valory.skills.price_estimation_abci.tests.test_apis.DummyMessage"></a>

## DummyMessage Objects

```python
class DummyMessage()
```

Dummy api specs class.

<a id="packages.valory.skills.price_estimation_abci.tests.test_apis.DummyMessage.__init__"></a>

#### `__`init`__`

```python
def __init__(body: bytes) -> None
```

Initializes DummyMessage

<a id="packages.valory.skills.price_estimation_abci.tests.test_apis.make_request"></a>

#### make`_`request

```python
def make_request(api_specs: Dict) -> requests.Response
```

Make request using api specs.

<a id="packages.valory.skills.price_estimation_abci.tests.test_apis.test_price_api"></a>

#### test`_`price`_`api

```python
@price_apis
def test_price_api(api_specs: List[Tuple[str, Union[str, List]]]) -> None
```

Test various price api specs.

<a id="packages.valory.skills.price_estimation_abci.tests.test_apis.test_randomness_api"></a>

#### test`_`randomness`_`api

```python
@randomness_apis
def test_randomness_api(api_specs: List[Tuple[str, Union[str, List]]]) -> None
```

Test various price api specs.

