<a id="packages.valory.skills.registration_abci.tests.test_behaviours"></a>

# packages.valory.skills.registration`_`abci.tests.test`_`behaviours

Tests for valory/registration_abci skill's behaviours.

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.consume"></a>

#### consume

```python
def consume(iterator: Iterable) -> None
```

Consume the iterator

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.as_context"></a>

#### as`_`context

```python
@contextmanager
def as_context(*contexts: Any) -> Generator[None, None, None]
```

Set contexts

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.RegistrationAbciBaseCase"></a>

## RegistrationAbciBaseCase Objects

```python
class RegistrationAbciBaseCase(FSMBehaviourBaseCase)
```

Base case for testing RegistrationAbci FSMBehaviour.

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.BaseRegistrationTestBehaviour"></a>

## BaseRegistrationTestBehaviour Objects

```python
class BaseRegistrationTestBehaviour(RegistrationAbciBaseCase)
```

Base test case to test RegistrationBehaviour.

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.BaseRegistrationTestBehaviour.test_registration"></a>

#### test`_`registration

```python
@pytest.mark.parametrize(
        "setup_data, expected_initialisation",
        (
            ({}, None),
            ({"test": []}, None),
            ({"test": [], "valid": [1, 2]}, '{"valid": [1, 2]}'),
        ),
    )
def test_registration(setup_data: Dict, expected_initialisation: Optional[str]) -> None
```

Test registration.

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour"></a>

## TestRegistrationStartupBehaviour Objects

```python
class TestRegistrationStartupBehaviour(RegistrationAbciBaseCase)
```

Test case to test RegistrationStartupBehaviour.

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.setup"></a>

#### setup

```python
def setup(**kwargs: Any) -> None
```

Setup

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.agent_instances"></a>

#### agent`_`instances

```python
@property
def agent_instances() -> List[str]
```

Agent instance addresses

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.state"></a>

#### state

```python
@property
def state() -> RegistrationStartupBehaviour
```

Current behavioural state

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.logger"></a>

#### logger

```python
@property
def logger() -> str
```

Logger

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.mocked_service_registry_address"></a>

#### mocked`_`service`_`registry`_`address

```python
@property
def mocked_service_registry_address() -> mock._patch
```

Mocked service registry address

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.mocked_on_chain_service_id"></a>

#### mocked`_`on`_`chain`_`service`_`id

```python
@property
def mocked_on_chain_service_id() -> mock._patch
```

Mocked on chain service id

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.mock_is_correct_contract"></a>

#### mock`_`is`_`correct`_`contract

```python
def mock_is_correct_contract(error_response: bool = False) -> None
```

Mock service registry contract call to for contract verification

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.mock_get_agent_instances"></a>

#### mock`_`get`_`agent`_`instances

```python
def mock_get_agent_instances(*agent_instances: str, *, error_response: bool = False) -> None
```

Mock get agent instances

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.mock_tendermint_request"></a>

#### mock`_`tendermint`_`request

```python
def mock_tendermint_request(request_kwargs: Dict, response_kwargs: Dict) -> None
```

Mock Tendermint request.

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.mock_get_tendermint_info"></a>

#### mock`_`get`_`tendermint`_`info

```python
def mock_get_tendermint_info(*addresses: str) -> None
```

Mock get Tendermint info

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.mock_get_local_tendermint_params"></a>

#### mock`_`get`_`local`_`tendermint`_`params

```python
def mock_get_local_tendermint_params(valid_response: bool = True) -> None
```

Mock Tendermint get local params

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.mock_tendermint_update"></a>

#### mock`_`tendermint`_`update

```python
def mock_tendermint_update(valid_response: bool = True) -> None
```

Mock Tendermint update

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.dummy_reset_tendermint_with_wait_wrapper"></a>

#### dummy`_`reset`_`tendermint`_`with`_`wait`_`wrapper

```python
@staticmethod
def dummy_reset_tendermint_with_wait_wrapper(valid_response: bool) -> Callable[[], Generator[None, None, Optional[bool]]]
```

Wrapper for a Dummy `reset_tendermint_with_wait` method.

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_init"></a>

#### test`_`init

```python
def test_init() -> None
```

Empty init

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_no_contract_address"></a>

#### test`_`no`_`contract`_`address

```python
def test_no_contract_address(caplog: LogCaptureFixture) -> None
```

Test service registry contract address not provided

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_request_personal"></a>

#### test`_`request`_`personal

```python
@pytest.mark.parametrize("valid_response", [True, False])
def test_request_personal(valid_response: bool, caplog: LogCaptureFixture) -> None
```

Test get tendermint configuration

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_failed_verification"></a>

#### test`_`failed`_`verification

```python
def test_failed_verification(caplog: LogCaptureFixture) -> None
```

Test service registry contract not correctly deployed

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_failed_service_info"></a>

#### test`_`failed`_`service`_`info

```python
def test_failed_service_info(caplog: LogCaptureFixture) -> None
```

Test get service info failure

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_no_agents_registered"></a>

#### test`_`no`_`agents`_`registered

```python
def test_no_agents_registered(caplog: LogCaptureFixture) -> None
```

Test no agent instances registered

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_self_not_registered"></a>

#### test`_`self`_`not`_`registered

```python
def test_self_not_registered(caplog: LogCaptureFixture) -> None
```

Test node operator agent not registered

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_response_service_info"></a>

#### test`_`response`_`service`_`info

```python
def test_response_service_info(caplog: LogCaptureFixture) -> None
```

Test registered addresses retrieved

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_collection_complete"></a>

#### test`_`collection`_`complete

```python
def test_collection_complete(caplog: LogCaptureFixture) -> None
```

Test registered addresses retrieved

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_request_update"></a>

#### test`_`request`_`update

```python
@pytest.mark.parametrize("valid_response", [True, False])
@mock.patch.object(BaseBehaviour, "reset_tendermint_with_wait")
def test_request_update(_: mock.Mock, valid_response: bool, caplog: LogCaptureFixture) -> None
```

Test Tendermint config update

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviour.test_request_restart"></a>

#### test`_`request`_`restart

```python
@pytest.mark.parametrize("valid_response", [True, False])
def test_request_restart(valid_response: bool, caplog: LogCaptureFixture) -> None
```

Test Tendermint start

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationStartupBehaviourNoConfigShare"></a>

## TestRegistrationStartupBehaviourNoConfigShare Objects

```python
class TestRegistrationStartupBehaviourNoConfigShare(BaseRegistrationTestBehaviour)
```

Test case to test RegistrationBehaviour.

<a id="packages.valory.skills.registration_abci.tests.test_behaviours.TestRegistrationBehaviour"></a>

## TestRegistrationBehaviour Objects

```python
class TestRegistrationBehaviour(BaseRegistrationTestBehaviour)
```

Test case to test RegistrationBehaviour.

