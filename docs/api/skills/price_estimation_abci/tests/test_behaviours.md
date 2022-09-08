<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours"></a>

# packages.valory.skills.price`_`estimation`_`abci.tests.test`_`behaviours

Tests for valory/price_estimation_abci skill's behaviours.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.DummyRoundId"></a>

## DummyRoundId Objects

```python
class DummyRoundId()
```

Dummy class for setting round_id for exit condition.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.DummyRoundId.__init__"></a>

#### `__`init`__`

```python
def __init__(round_id: str) -> None
```

Dummy class for setting round_id for exit condition.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.PriceEstimationFSMBehaviourBaseCase"></a>

## PriceEstimationFSMBehaviourBaseCase Objects

```python
class PriceEstimationFSMBehaviourBaseCase(FSMBehaviourBaseCase)
```

Base case for testing PriceEstimation FSMBehaviour.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestObserveBehaviour"></a>

## TestObserveBehaviour Objects

```python
class TestObserveBehaviour(PriceEstimationFSMBehaviourBaseCase)
```

Test ObserveBehaviour.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestObserveBehaviour.test_observer_behaviour"></a>

#### test`_`observer`_`behaviour

```python
def test_observer_behaviour() -> None
```

Run tests.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestObserveBehaviour.test_observer_behaviour_retries_exceeded"></a>

#### test`_`observer`_`behaviour`_`retries`_`exceeded

```python
def test_observer_behaviour_retries_exceeded() -> None
```

Run tests.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestObserveBehaviour.test_observed_value_none"></a>

#### test`_`observed`_`value`_`none

```python
def test_observed_value_none() -> None
```

Test when `observed` value is none.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestObserveBehaviour.test_clean_up"></a>

#### test`_`clean`_`up

```python
def test_clean_up() -> None
```

Test when `observed` value is none.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestEstimateBehaviour"></a>

## TestEstimateBehaviour Objects

```python
class TestEstimateBehaviour(PriceEstimationFSMBehaviourBaseCase)
```

Test EstimateBehaviour.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestEstimateBehaviour.test_estimate"></a>

#### test`_`estimate

```python
def test_estimate() -> None
```

Test estimate behaviour.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.mock_to_server_message_flow"></a>

#### mock`_`to`_`server`_`message`_`flow

```python
def mock_to_server_message_flow(self: "TestTransactionHashBehaviour", this_period_count: int, prev_tx_hash: str) -> None
```

Mock to server message flow

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.get_valid_server_data"></a>

#### get`_`valid`_`server`_`data

```python
def get_valid_server_data() -> Dict[str, Any]
```

Get valid server data

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestTransactionHashBehaviour"></a>

## TestTransactionHashBehaviour Objects

```python
@pytest.mark.parametrize(
    "broadcast_to_server, this_period_count", ((True, 0), (False, 0), (True, 1))
)
class TestTransactionHashBehaviour(PriceEstimationFSMBehaviourBaseCase)
```

Test TransactionHashBehaviour.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestTransactionHashBehaviour.test_estimate"></a>

#### test`_`estimate

```python
def test_estimate(broadcast_to_server: bool, this_period_count: int) -> None
```

Test estimate behaviour.

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestPackForServer"></a>

## TestPackForServer Objects

```python
class TestPackForServer(PriceEstimationFSMBehaviourBaseCase)
```

Test packaging of data for signing by agents

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.TestPackForServer.test_pack_for_server"></a>

#### test`_`pack`_`for`_`server

```python
@pytest.mark.parametrize(
        "mutation, remains_valid",
        (
            ({}, True),  # do nothing
            ({"participants": ("",) * 4}, True),
            ({"period_count": (1 << 256) - 1}, True),
            ({"period_count": 1 << 256}, False),
            ({"estimate": f"{'9'*30}.{'9'*1}"}, True),
            ({"estimate": f"{'9'*30}.{'9'*2}"}, False),
            ({"data_source": "a" * 32}, True),
            ({"data_source": "a" * 33}, False),
            ({"unit": "a" * 32}, True),
            ({"unit": "a" * 33}, False),
        ),
    )
def test_pack_for_server(mutation: Dict[str, Any], remains_valid: bool) -> None
```

Test packaging valid and invalid data

<a id="packages.valory.skills.price_estimation_abci.tests.test_behaviours.test_fuzz_pack_for_server"></a>

#### test`_`fuzz`_`pack`_`for`_`server

```python
@pytest.mark.skip
def test_fuzz_pack_for_server() -> None
```

Test fuzz pack_for_server.

