<a id="packages.valory.skills.abstract_round_abci.tests.test_models"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`models

Test the models.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel"></a>

## TestApiSpecsModel Objects

```python
class TestApiSpecsModel()
```

Test ApiSpecsModel.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.setup"></a>

#### setup

```python
def setup() -> None
```

Setup test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_init"></a>

#### test`_`init

```python
def test_init() -> None
```

Test initialization.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_retries"></a>

#### test`_`retries

```python
def test_retries() -> None
```

Tests for retries.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_get_spec"></a>

#### test`_`get`_`spec

```python
def test_get_spec() -> None
```

Test get_spec method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_process_response_with_depth_0"></a>

#### test`_`process`_`response`_`with`_`depth`_`0

```python
def test_process_response_with_depth_0() -> None
```

Test process_response method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_process_response_with_depth_1"></a>

#### test`_`process`_`response`_`with`_`depth`_`1

```python
def test_process_response_with_depth_1() -> None
```

Test process_response method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_process_response_with_key_none"></a>

#### test`_`process`_`response`_`with`_`key`_`none

```python
def test_process_response_with_key_none() -> None
```

Test process_response method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.ConcreteRound"></a>

## ConcreteRound Objects

```python
class ConcreteRound(AbstractRound)
```

A ConcreteRoundA for testing purposes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.ConcreteRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Handle the end of the block.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState"></a>

## TestSharedState Objects

```python
class TestSharedState()
```

Test SharedState(Model) class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_initialization"></a>

#### test`_`initialization

```python
@mock.patch.object(SharedState, "_process_abci_app_cls")
def test_initialization(*_: Any) -> None
```

Test the initialization of the shared state.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_setup"></a>

#### test`_`setup

```python
@mock.patch.object(SharedState, "_process_abci_app_cls")
def test_setup(*_: Any) -> None
```

Test setup method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_synchronized_data_negative_not_available"></a>

#### test`_`synchronized`_`data`_`negative`_`not`_`available

```python
@mock.patch.object(SharedState, "_process_abci_app_cls")
def test_synchronized_data_negative_not_available(*_: Any) -> None
```

Test 'synchronized_data' property getter, negative case (not available).

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_synchronized_data_positive"></a>

#### test`_`synchronized`_`data`_`positive

```python
@mock.patch.object(SharedState, "_process_abci_app_cls")
def test_synchronized_data_positive(*_: Any) -> None
```

Test 'synchronized_data' property getter, negative case (not available).

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_synchronized_data_db"></a>

#### test`_`synchronized`_`data`_`db

```python
def test_synchronized_data_db(*_: Any) -> None
```

Test 'synchronized_data' AbciAppDB.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_process_abci_app_cls_negative_not_a_class"></a>

#### test`_`process`_`abci`_`app`_`cls`_`negative`_`not`_`a`_`class

```python
def test_process_abci_app_cls_negative_not_a_class() -> None
```

Test '_process_abci_app_cls', negative case (not a class).

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_process_abci_app_cls_negative_not_subclass_of_abstract_round"></a>

#### test`_`process`_`abci`_`app`_`cls`_`negative`_`not`_`subclass`_`of`_`abstract`_`round

```python
def test_process_abci_app_cls_negative_not_subclass_of_abstract_round() -> None
```

Test '_process_abci_app_cls', negative case (not subclass of AbstractRound).

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_process_abci_app_cls_positive"></a>

#### test`_`process`_`abci`_`app`_`cls`_`positive

```python
def test_process_abci_app_cls_positive() -> None
```

Test '_process_abci_app_cls', positive case.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestBenchmarkTool"></a>

## TestBenchmarkTool Objects

```python
class TestBenchmarkTool()
```

Test BenchmarkTool

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestBenchmarkTool.test_end_2_end"></a>

#### test`_`end`_`2`_`end

```python
def test_end_2_end() -> None
```

Test end 2 end of the tool.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_requests_model_initialization"></a>

#### test`_`requests`_`model`_`initialization

```python
def test_requests_model_initialization() -> None
```

Test initialization of the 'Requests(Model)' class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_base_params_model_initialization"></a>

#### test`_`base`_`params`_`model`_`initialization

```python
def test_base_params_model_initialization() -> None
```

Test initialization of the 'BaseParams(Model)' class.

