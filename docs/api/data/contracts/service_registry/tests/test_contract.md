<a id="autonomy.data.contracts.service_registry.tests.test_contract"></a>

# autonomy.data.contracts.service`_`registry.tests.test`_`contract

Tests for valory/service_registry contract.

<a id="autonomy.data.contracts.service_registry.tests.test_contract.event_filter_patch"></a>

#### event`_`filter`_`patch

```python
def event_filter_patch(event: str, return_value: Any) -> mock._patch
```

Returns an event filter patch for the given event name.

<a id="autonomy.data.contracts.service_registry.tests.test_contract.BaseServiceRegistryContractTest"></a>

## BaseServiceRegistryContractTest Objects

```python
class BaseServiceRegistryContractTest(BaseRegistriesContractsTest)
```

Base class for Service Registry contract tests

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract"></a>

## TestServiceRegistryContract Objects

```python
@skip_docker_tests
class TestServiceRegistryContract(BaseServiceRegistryContractTest)
```

Test Service Registry Contract

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_verify_contract"></a>

#### test`_`verify`_`contract

```python
@pytest.mark.parametrize("valid_address", (True, False))
def test_verify_contract(valid_address: bool) -> None
```

Run verify test. If abi file is updated tests + addresses need updating

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_exists"></a>

#### test`_`exists

```python
@pytest.mark.parametrize("service_id, expected", [(INVALID_SERVICE_ID, False),
                                                  (VALID_SERVICE_ID, True)])
def test_exists(service_id: int, expected: int) -> None
```

Test whether service id exists

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_get_agent_instances"></a>

#### test`_`get`_`agent`_`instances

```python
def test_get_agent_instances() -> None
```

Test agent instances retrieval

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_get_service_owner"></a>

#### test`_`get`_`service`_`owner

```python
def test_get_service_owner() -> None
```

Test service owner retrieval.

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_get_token_uri"></a>

#### test`_`get`_`token`_`uri

```python
def test_get_token_uri() -> None
```

Test `get_token_uri` method.

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_get_service_information"></a>

#### test`_`get`_`service`_`information

```python
def test_get_service_information() -> None
```

Test `test_get_service_information` method.

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_get_slash_data"></a>

#### test`_`get`_`slash`_`data

```python
def test_get_slash_data() -> None
```

Test the `get_slash_data`.

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_get_operator"></a>

#### test`_`get`_`operator

```python
def test_get_operator() -> None
```

Test `get_operator` method.

<a id="autonomy.data.contracts.service_registry.tests.test_contract.TestServiceRegistryContract.test_get_operators_mapping"></a>

#### test`_`get`_`operators`_`mapping

```python
def test_get_operators_mapping() -> None
```

Test `get_operator` method.

