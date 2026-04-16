<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`tools.test`_`rounds

Test the `rounds` test tool module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.test_get_participants"></a>

#### test`_`get`_`participants

```python
def test_get_participants() -> None
```

Test `get_participants`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyTxPayloadMatcher"></a>

## DummyTxPayloadMatcher Objects

```python
class DummyTxPayloadMatcher()
```

A `DummyTxPayload` matcher for assertion comparisons.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyTxPayloadMatcher.__init__"></a>

#### `__`init`__`

```python
def __init__(expected: DummyTxPayload) -> None
```

Initialize the matcher.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyTxPayloadMatcher.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Needs to be implemented for better assertion messages.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyTxPayloadMatcher.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

The method that will be used for the assertion comparisons.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.test_get_dummy_tx_payloads"></a>

#### test`_`get`_`dummy`_`tx`_`payloads

```python
@given(
    st.frozensets(st.text(max_size=200), max_size=100),
    st.text(max_size=500),
    st.one_of(st.none(), st.booleans()),
    st.booleans(),
)
def test_get_dummy_tx_payloads(participants: FrozenSet[str], value: str,
                               vote: Optional[bool],
                               is_value_none: bool) -> None
```

Test `get_dummy_tx_payloads`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestDummyTxPayload"></a>

## TestDummyTxPayload Objects

```python
class TestDummyTxPayload()
```

Test class for `DummyTxPayload`

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestDummyTxPayload.test_properties"></a>

#### test`_`properties

```python
@staticmethod
@given(st.text(max_size=200), st.text(max_size=500), st.booleans())
def test_properties(sender: str, value: str, vote: bool) -> None
```

Test all the properties.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestDummySynchronizedData"></a>

## TestDummySynchronizedData Objects

```python
class TestDummySynchronizedData()
```

Test class for `DummySynchronizedData`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestDummySynchronizedData.test_most_voted_keeper_address"></a>

#### test`_`most`_`voted`_`keeper`_`address

```python
@staticmethod
@given(st.lists(st.text(max_size=200), max_size=100))
def test_most_voted_keeper_address(
        most_voted_keeper_address_data: List[str]) -> None
```

Test `most_voted_keeper_address`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseRoundTestClass"></a>

## TestBaseRoundTestClass Objects

```python
class TestBaseRoundTestClass()
```

Test `BaseRoundTestClass`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseRoundTestClass.test_test_no_majority_event"></a>

#### test`_`test`_`no`_`majority`_`event

```python
@staticmethod
def test_test_no_majority_event() -> None
```

Test `_test_no_majority_event`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseRoundTestClass.test_complete_run"></a>

#### test`_`complete`_`run

```python
@staticmethod
@given(st.integers(min_value=0, max_value=100), st.integers(min_value=1))
def test_complete_run(iter_count: int, shift: int) -> None
```

Test `_complete_run`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.BaseTestBase"></a>

## BaseTestBase Objects

```python
class BaseTestBase()
```

Base class for the Base tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.BaseTestBase.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Setup that is run before each test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.BaseTestBase.create_test_gen"></a>

#### create`_`test`_`gen

```python
def create_test_gen(**kwargs: Any) -> None
```

Create the base test generator.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.BaseTestBase.exhaust_base_test_gen"></a>

#### exhaust`_`base`_`test`_`gen

```python
def exhaust_base_test_gen() -> None
```

Exhaust the base test generator.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.BaseTestBase.run_test"></a>

#### run`_`test

```python
def run_test(**kwargs: Any) -> None
```

Run a test for a base test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectDifferentUntilAllRoundWithEndBlock"></a>

## DummyCollectDifferentUntilAllRoundWithEndBlock Objects

```python
class DummyCollectDifferentUntilAllRoundWithEndBlock(
        DummyCollectDifferentUntilAllRound)
```

A `DummyCollectDifferentUntilAllRound` with `end_block` implemented.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectDifferentUntilAllRoundWithEndBlock.__init__"></a>

#### `__`init`__`

```python
def __init__(dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any)
```

Initialize the dummy class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectDifferentUntilAllRoundWithEndBlock.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

A dummy `end_block` implementation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseCollectDifferentUntilAllRoundTest"></a>

## TestBaseCollectDifferentUntilAllRoundTest Objects

```python
class TestBaseCollectDifferentUntilAllRoundTest(BaseTestBase)
```

Test `BaseCollectDifferentUntilAllRoundTest`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseCollectDifferentUntilAllRoundTest.test_test_round"></a>

#### test`_`test`_`round

```python
@given(st.one_of(st.none(), st.sampled_from(DummyEvent)), )
def test_test_round(exit_event: DummyEvent) -> None
```

Test `_test_round`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectSameUntilAllRoundWithEndBlock"></a>

## DummyCollectSameUntilAllRoundWithEndBlock Objects

```python
class DummyCollectSameUntilAllRoundWithEndBlock(DummyCollectSameUntilAllRound)
```

A `DummyCollectSameUntilAllRound` with `end_block` implemented.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectSameUntilAllRoundWithEndBlock.__init__"></a>

#### `__`init`__`

```python
def __init__(dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any)
```

Initialize the dummy class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectSameUntilAllRoundWithEndBlock.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

A dummy `end_block` implementation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseCollectSameUntilAllRoundTest"></a>

## TestBaseCollectSameUntilAllRoundTest Objects

```python
class TestBaseCollectSameUntilAllRoundTest(BaseTestBase)
```

Test `BaseCollectSameUntilAllRoundTest`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseCollectSameUntilAllRoundTest.test_test_round"></a>

#### test`_`test`_`round

```python
@given(
    st.sampled_from(DummyEvent),
    st.text(max_size=500),
    st.booleans(),
)
def test_test_round(exit_event: DummyEvent, common_value: str,
                    finished: bool) -> None
```

Test `_test_round`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectSameUntilThresholdRoundWithEndBlock"></a>

## DummyCollectSameUntilThresholdRoundWithEndBlock Objects

```python
class DummyCollectSameUntilThresholdRoundWithEndBlock(
        DummyCollectSameUntilThresholdRound)
```

A `DummyCollectSameUntilThresholdRound` with `end_block` overriden.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectSameUntilThresholdRoundWithEndBlock.__init__"></a>

#### `__`init`__`

```python
def __init__(dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any)
```

Initialize the dummy class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectSameUntilThresholdRoundWithEndBlock.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

A dummy `end_block` override.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseCollectSameUntilThresholdRoundTest"></a>

## TestBaseCollectSameUntilThresholdRoundTest Objects

```python
class TestBaseCollectSameUntilThresholdRoundTest(BaseTestBase)
```

Test `BaseCollectSameUntilThresholdRoundTest`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseCollectSameUntilThresholdRoundTest.test_test_round"></a>

#### test`_`test`_`round

```python
@given(
    st.sampled_from(DummyEvent),
    st.text(max_size=500),
)
def test_test_round(exit_event: DummyEvent, most_voted_payload: str) -> None
```

Test `_test_round`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyOnlyKeeperSendsRoundTest"></a>

## DummyOnlyKeeperSendsRoundTest Objects

```python
class DummyOnlyKeeperSendsRoundTest(DummyOnlyKeeperSendsRound)
```

A `DummyOnlyKeeperSendsRound` with `end_block` implemented.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyOnlyKeeperSendsRoundTest.__init__"></a>

#### `__`init`__`

```python
def __init__(dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any)
```

Initialize the dummy class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyOnlyKeeperSendsRoundTest.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

A dummy `end_block` implementation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseOnlyKeeperSendsRoundTest"></a>

## TestBaseOnlyKeeperSendsRoundTest Objects

```python
class TestBaseOnlyKeeperSendsRoundTest(BaseTestBase)
```

Test `BaseOnlyKeeperSendsRoundTest`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseOnlyKeeperSendsRoundTest.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Setup that is run before each test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseOnlyKeeperSendsRoundTest.test_test_round"></a>

#### test`_`test`_`round

```python
@given(
    st.sampled_from(DummyEvent),
    st.text(),
)
def test_test_round(exit_event: DummyEvent, keeper_value: str) -> None
```

Test `_test_round`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyBaseVotingRoundTestWithEndBlock"></a>

## DummyBaseVotingRoundTestWithEndBlock Objects

```python
class DummyBaseVotingRoundTestWithEndBlock(DummyVotingRound)
```

A `DummyVotingRound` with `end_block` overriden.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyBaseVotingRoundTestWithEndBlock.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

A dummy `end_block` override.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseVotingRoundTest"></a>

## TestBaseVotingRoundTest Objects

```python
class TestBaseVotingRoundTest(BaseTestBase)
```

Test `BaseVotingRoundTest`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseVotingRoundTest.test_test_round"></a>

#### test`_`test`_`round

```python
@given(st.one_of(st.none(), st.booleans()), )
def test_test_round(is_keeper_set: Optional[bool]) -> None
```

Test `_test_round`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectDifferentUntilThresholdRoundWithEndBlock"></a>

## DummyCollectDifferentUntilThresholdRoundWithEndBlock Objects

```python
class DummyCollectDifferentUntilThresholdRoundWithEndBlock(
        DummyCollectDifferentUntilThresholdRound)
```

A `DummyCollectDifferentUntilThresholdRound` with `end_block` implemented.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectDifferentUntilThresholdRoundWithEndBlock.__init__"></a>

#### `__`init`__`

```python
def __init__(dummy_exit_event: DummyEvent, *args: Any, **kwargs: Any)
```

Initialize the dummy class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.DummyCollectDifferentUntilThresholdRoundWithEndBlock.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

A dummy `end_block` implementation.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseCollectDifferentUntilThresholdRoundTest"></a>

## TestBaseCollectDifferentUntilThresholdRoundTest Objects

```python
class TestBaseCollectDifferentUntilThresholdRoundTest(BaseTestBase)
```

Test `BaseCollectDifferentUntilThresholdRoundTest`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_tools.test_rounds.TestBaseCollectDifferentUntilThresholdRoundTest.test_test_round"></a>

#### test`_`test`_`round

```python
@given(st.sampled_from(DummyEvent))
def test_test_round(exit_event: DummyEvent) -> None
```

Test `_test_round`.

