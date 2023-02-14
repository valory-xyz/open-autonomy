<a id="packages.valory.skills.abstract_round_abci.test_tools.common"></a>

# packages.valory.skills.abstract`_`round`_`abci.test`_`tools.common

Test common classes.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.CommonBaseCase"></a>

## CommonBaseCase Objects

```python
class CommonBaseCase(FSMBehaviourBaseCase)
```

Base case for testing PriceEstimation FSMBehaviour.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseRandomnessBehaviourTest"></a>

## BaseRandomnessBehaviourTest Objects

```python
class BaseRandomnessBehaviourTest(CommonBaseCase)
```

Test RandomnessBehaviour.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseRandomnessBehaviourTest.test_randomness_behaviour"></a>

#### test`_`randomness`_`behaviour

```python
def test_randomness_behaviour() -> None
```

Test RandomnessBehaviour.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseRandomnessBehaviourTest.test_invalid_drand_value"></a>

#### test`_`invalid`_`drand`_`value

```python
def test_invalid_drand_value() -> None
```

Test invalid drand values.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseRandomnessBehaviourTest.test_invalid_response"></a>

#### test`_`invalid`_`response

```python
def test_invalid_response() -> None
```

Test invalid json response.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseRandomnessBehaviourTest.test_max_retries_reached_fallback"></a>

#### test`_`max`_`retries`_`reached`_`fallback

```python
def test_max_retries_reached_fallback() -> None
```

Test with max retries reached.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseRandomnessBehaviourTest.test_max_retries_reached_fallback_fail"></a>

#### test`_`max`_`retries`_`reached`_`fallback`_`fail

```python
def test_max_retries_reached_fallback_fail() -> None
```

Test with max retries reached.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseRandomnessBehaviourTest.test_max_retries_reached_fallback_fail_case_2"></a>

#### test`_`max`_`retries`_`reached`_`fallback`_`fail`_`case`_`2

```python
def test_max_retries_reached_fallback_fail_case_2() -> None
```

Test with max retries reached.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseRandomnessBehaviourTest.test_clean_up"></a>

#### test`_`clean`_`up

```python
def test_clean_up() -> None
```

Test when `observed` value is none.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseSelectKeeperBehaviourTest"></a>

## BaseSelectKeeperBehaviourTest Objects

```python
class BaseSelectKeeperBehaviourTest(CommonBaseCase)
```

Test SelectKeeperBehaviour.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseSelectKeeperBehaviourTest.test_select_keeper"></a>

#### test`_`select`_`keeper

```python
@mock.patch.object(SkillContext,
                   "agent_address",
                   new_callable=mock.PropertyMock)
@pytest.mark.parametrize(
    "blacklisted_keepers",
    (
        set(),
        {"a_1"},
        {"test_agent_address" + "t" * 24},
        {"a_1" + "t" * 39, "a_2" + "t" * 39, "test_agent_address" + "t" * 24},
    ),
)
def test_select_keeper(agent_address_mock: mock.Mock,
                       blacklisted_keepers: Set[str]) -> None
```

Test select keeper agent.

<a id="packages.valory.skills.abstract_round_abci.test_tools.common.BaseSelectKeeperBehaviourTest.test_select_keeper_preexisting_keeper"></a>

#### test`_`select`_`keeper`_`preexisting`_`keeper

```python
def test_select_keeper_preexisting_keeper() -> None
```

Test select keeper agent.

