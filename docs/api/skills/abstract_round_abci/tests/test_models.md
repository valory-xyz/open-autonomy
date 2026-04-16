<a id="packages.valory.skills.abstract_round_abci.tests.test_models"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`models

Test the models.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel"></a>

## TestApiSpecsModel Objects

```python
class TestApiSpecsModel()
```

Test ApiSpecsModel.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Setup test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_init"></a>

#### test`_`init

```python
def test_init() -> None
```

Test initialization.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_suggested_sleep_time"></a>

#### test`_`suggested`_`sleep`_`time

```python
@pytest.mark.parametrize("retries", range(10))
def test_suggested_sleep_time(retries: int) -> None
```

Test `suggested_sleep_time`

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_process_response"></a>

#### test`_`process`_`response

```python
@pytest.mark.parametrize(
    "api_specs_config, message, expected_res, expected_error",
    (
        (
            dict(
                **BASE_DUMMY_SPECS_CONFIG,
                response_key="value",
                response_index=None,
                response_type="float",
                error_key=None,
                error_index=None,
                error_data=None,
            ),
            MagicMock(body=b'{"value": "10.232"}'),
            10.232,
            None,
        ),
        (
            dict(
                **BASE_DUMMY_SPECS_CONFIG,
                response_key="test:response:key",
                response_index=2,
                response_type="dict",
                error_key="error:key",
                error_index=3,
                error_type="str",
                error_data=None,
            ),
            MagicMock(
                body=
                b'{"test": {"response": {"key": ["does_not_matter", "does_not_matter", {"this": "matters"}]}}}'
            ),
            {
                "this": "matters"
            },
            None,
        ),
        (
            dict(
                **BASE_DUMMY_SPECS_CONFIG,
                response_key="test:response:key",
                response_index=2,
                error_key="error:key",
                error_index=3,
                error_type="str",
                error_data=None,
            ),
            MagicMock(body=b'{"cannot be parsed'),
            None,
            None,
        ),
        (
            dict(
                **BASE_DUMMY_SPECS_CONFIG,
                response_key="test:response:key",
                response_index=2,
                error_key="error:key",
                error_index=3,
                error_type="str",
                error_data=None,
            ),
            MagicMock(
                # the null will raise `TypeError` and we test that it is handled
                body=
                b'{"test": {"response": {"key": ["does_not_matter", "does_not_matter", null]}}}'
            ),
            "None",
            None,
        ),
        (
            dict(
                **BASE_DUMMY_SPECS_CONFIG,
                response_key="test:response:key",
                response_index=
                2,  # this will raise `IndexError` and we test that it is handled
                error_key="error:key",
                error_index=3,
                error_type="str",
                error_data=None,
            ),
            MagicMock(
                body=
                b'{"test": {"response": {"key": ["does_not_matter", "does_not_matter"]}}}'
            ),
            None,
            None,
        ),
        (
            dict(
                **BASE_DUMMY_SPECS_CONFIG,
                response_key=
                "test:response:key",  # this will raise `KeyError` and we test that it is handled
                response_index=2,
                error_key="error:key",
                error_index=3,
                error_type="str",
                error_data=None,
            ),
            MagicMock(
                body=
                b'{"test": {"response": {"key_does_not_match": ["does_not_matter", "does_not_matter"]}}}'
            ),
            None,
            None,
        ),
        (
            dict(
                **BASE_DUMMY_SPECS_CONFIG,
                response_key="test:response:key",
                response_index=2,
                error_key="error:key",
                error_index=3,
                error_type="str",
                error_data=None,
            ),
            MagicMock(
                body=
                b'{"test": {"response": {"key_does_not_match": ["does_not_matter", "does_not_matter"]}}, '
                b'"error": {"key": [0, 1, 2, "test that the error is being parsed correctly"]}}'
            ),
            None,
            "test that the error is being parsed correctly",
        ),
    ),
)
def test_process_response(api_specs_config: dict, message: MagicMock,
                          expected_res: Any, expected_error: Any) -> None
```

Test `process_response` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestApiSpecsModel.test_attribute_manipulation"></a>

#### test`_`attribute`_`manipulation

```python
def test_attribute_manipulation() -> None
```

Test manipulating the attributes.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.SharedState"></a>

## SharedState Objects

```python
class SharedState(BaseSharedState)
```

Shared State for testing purposes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState"></a>

## TestSharedState Objects

```python
class TestSharedState()
```

Test SharedState(Model) class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_initialization"></a>

#### test`_`initialization

```python
def test_initialization(*_: Any) -> None
```

Test the initialization of the shared state.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.dummy_state_setup"></a>

#### dummy`_`state`_`setup

```python
@staticmethod
def dummy_state_setup(shared_state: SharedState) -> None
```

Setup a shared state instance with dummy params.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_setup_slashing"></a>

#### test`_`setup`_`slashing

```python
@pytest.mark.parametrize(
    "acn_configured_agents, validator_to_agent, raises",
    (
        (
            {i
             for i in range(4)},
            {
                f"validator_address_{i}": i
                for i in range(4)
            },
            False,
        ),
        (
            {i
             for i in range(5)},
            {
                f"validator_address_{i}": i
                for i in range(4)
            },
            True,
        ),
        (
            {i
             for i in range(4)},
            {
                f"validator_address_{i}": i
                for i in range(5)
            },
            True,
        ),
    ),
)
def test_setup_slashing(acn_configured_agents: Set[str],
                        validator_to_agent: Dict[str,
                                                 str], raises: bool) -> None
```

Test the `validator_to_agent` properties.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_setup"></a>

#### test`_`setup

```python
def test_setup(*_: Any) -> None
```

Test setup method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_get_validator_address"></a>

#### test`_`get`_`validator`_`address

```python
@pytest.mark.parametrize(
    "initial_tm_configs, address_input, exception, expected",
    (
        (
            {},
            "0x1",
            "The validator address of non-participating agent `0x1` was requested.",
            None,
        ),
        ({}, "0x0", "SharedState's setup was not performed successfully.",
         None),
        (
            {
                "0x0": None
            },
            "0x0",
            "ACN registration has not been successfully performed for agent `0x0`. "
            "Have you set the `share_tm_config_on_startup` flag to `true` in the configuration?",
            None,
        ),
        (
            {
                "0x0": {}
            },
            "0x0",
            "The tendermint configuration for agent `0x0` is invalid: `{}`.",
            None,
        ),
        (
            {
                "0x0": {
                    "address": None
                }
            },
            "0x0",
            "The tendermint configuration for agent `0x0` is invalid: `{'address': None}`.",
            None,
        ),
        (
            {
                "0x0": {
                    "address": "test_validator_address"
                }
            },
            "0x0",
            None,
            "test_validator_address",
        ),
    ),
)
def test_get_validator_address(initial_tm_configs: Dict[str,
                                                        Optional[Dict[str,
                                                                      Any]]],
                               address_input: str, exception: Optional[str],
                               expected: Optional[str]) -> None
```

Test `get_validator_address` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_acn_container"></a>

#### test`_`acn`_`container

```python
@pytest.mark.parametrize("self_idx", (range(4)))
def test_acn_container(self_idx: int) -> None
```

Test the `acn_container` method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_synchronized_data_negative_not_available"></a>

#### test`_`synchronized`_`data`_`negative`_`not`_`available

```python
def test_synchronized_data_negative_not_available(*_: Any) -> None
```

Test 'synchronized_data' property getter, negative case (not available).

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_synchronized_data_positive"></a>

#### test`_`synchronized`_`data`_`positive

```python
def test_synchronized_data_positive(*_: Any) -> None
```

Test 'synchronized_data' property getter, negative case (not available).

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_synchronized_data_db"></a>

#### test`_`synchronized`_`data`_`db

```python
def test_synchronized_data_db(*_: Any) -> None
```

Test 'synchronized_data' AbciAppDB.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_get_acn_result"></a>

#### test`_`get`_`acn`_`result

```python
@pytest.mark.parametrize(
    "address_to_acn_deliverable, n_participants, expected",
    (
        ({}, 4, None),
        ({
            i: "test"
            for i in range(4)
        }, 4, "test"),
        (
            {
                i: TendermintRecoveryParams("test")
                for i in range(4)
            },
            4,
            TendermintRecoveryParams("test"),
        ),
        ({
            1: "test",
            2: "non-matching",
            3: "test",
            4: "test"
        }, 4, "test"),
        ({
            i: "test"
            for i in range(4)
        }, 4, "test"),
        ({
            1: "no",
            2: "result",
            3: "matches",
            4: ""
        }, 4, None),
    ),
)
def test_get_acn_result(address_to_acn_deliverable: Dict[str, Any],
                        n_participants: int, expected: Optional[str]) -> None
```

Test `get_acn_result`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_recovery_params_on_init"></a>

#### test`_`recovery`_`params`_`on`_`init

```python
def test_recovery_params_on_init() -> None
```

Test that `tm_recovery_params` get initialized correctly.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.TestSharedState.test_set_last_reset_params"></a>

#### test`_`set`_`last`_`reset`_`params

```python
def test_set_last_reset_params() -> None
```

Test that `last_reset_params` get set correctly.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_incorrect_setup"></a>

#### test`_`incorrect`_`setup

```python
@pytest.mark.parametrize(
    "setup, error_text",
    (
        ({}, "`setup` params contain no values!"),
        (
            {
                "a": "b"
            },
            "Value for `safe_contract_address` missing from the `setup` params.",
        ),
    ),
)
def test_incorrect_setup(setup: Dict[str, Any], error_text: str) -> None
```

Test BaseParams model initialization with incorrect setup data.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_genesis_block"></a>

#### test`_`genesis`_`block

```python
def test_genesis_block() -> None
```

Test genesis block methods.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_genesis_evidence"></a>

#### test`_`genesis`_`evidence

```python
def test_genesis_evidence() -> None
```

Test genesis evidence methods.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_genesis_validator"></a>

#### test`_`genesis`_`validator

```python
def test_genesis_validator() -> None
```

Test genesis validator methods.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_genesis_consensus_params"></a>

#### test`_`genesis`_`consensus`_`params

```python
def test_genesis_consensus_params() -> None
```

Test genesis consensus params methods.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_genesis_config"></a>

#### test`_`genesis`_`config

```python
def test_genesis_config() -> None
```

Test genesis config methods.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_meta_shared_state_when_instance_not_subclass_of_shared_state"></a>

#### test`_`meta`_`shared`_`state`_`when`_`instance`_`not`_`subclass`_`of`_`shared`_`state

```python
def test_meta_shared_state_when_instance_not_subclass_of_shared_state(
) -> None
```

Test instantiation of meta class when instance not a subclass of shared state.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_shared_state_instantiation_without_attributes_raises_error"></a>

#### test`_`shared`_`state`_`instantiation`_`without`_`attributes`_`raises`_`error

```python
def test_shared_state_instantiation_without_attributes_raises_error() -> None
```

Test that definition of concrete subclass of SharedState without attributes raises error.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.A"></a>

## A Objects

```python
@dataclass
class A()
```

Class for testing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.B"></a>

## B Objects

```python
@dataclass
class B()
```

Class for testing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.C"></a>

## C Objects

```python
class C(TypedDict)
```

Class for testing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.D"></a>

## D Objects

```python
class D(TypedDict)
```

Class for testing.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_type_check_positive"></a>

#### test`_`type`_`check`_`positive

```python
@pytest.mark.parametrize("name,value,type_hint", testdata_positive)
def test_type_check_positive(name: str, value: Any, type_hint: Any) -> None
```

Test the type check mixin.

<a id="packages.valory.skills.abstract_round_abci.tests.test_models.test_type_check_negative"></a>

#### test`_`type`_`check`_`negative

```python
@pytest.mark.parametrize("name,value,type_hint", testdata_negative)
def test_type_check_negative(name: str, value: Any, type_hint: Any) -> None
```

Test the type check mixin.

