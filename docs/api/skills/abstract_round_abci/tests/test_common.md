<a id="packages.valory.skills.abstract_round_abci.tests.test_common"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`common

Test the common.py module of the skill.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.test_random_selection"></a>

#### test`_`random`_`selection

```python
def test_random_selection() -> None
```

Test 'random_selection'

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.DummyRandomnessBehaviour"></a>

## DummyRandomnessBehaviour Objects

```python
class DummyRandomnessBehaviour(RandomnessBehaviour)
```

Dummy randomness behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.DummySelectKeeperBehaviour"></a>

## DummySelectKeeperBehaviour Objects

```python
class DummySelectKeeperBehaviour(SelectKeeperBehaviour)
```

Dummy select keeper behaviour.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.BaseDummyBehaviour"></a>

## BaseDummyBehaviour Objects

```python
class BaseDummyBehaviour()
```

A Base dummy behaviour class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.BaseDummyBehaviour.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Setup the test class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.dummy_generator"></a>

#### dummy`_`generator

```python
def dummy_generator(
    return_value: ReturnValueType
) -> Callable[[Any, Any], Generator[None, None, ReturnValueType]]
```

A method that returns a dummy generator which yields nothing once and then returns the given `return_value`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.last_iteration"></a>

#### last`_`iteration

```python
def last_iteration(gen: Generator) -> None
```

Perform a generator iteration and ensure that it is the last one.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestRandomnessBehaviour"></a>

## TestRandomnessBehaviour Objects

```python
class TestRandomnessBehaviour(BaseDummyBehaviour)
```

Test `RandomnessBehaviour`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestRandomnessBehaviour.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Setup the test class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestRandomnessBehaviour.test_failsafe_randomness"></a>

#### test`_`failsafe`_`randomness

```python
@pytest.mark.parametrize(
    "return_value, expected_hash",
    (
        (MagicMock(performative=LedgerApiMessage.Performative.ERROR), None),
        (MagicMock(state=MagicMock(body={"hash_key_is_not_in_body": ""})),
         None),
        (
            MagicMock(state=MagicMock(body={"hash": "test_randomness"})),
            {
                "randomness":
                "d067b86fa5235e7e5225e8328e8faac5c279cbf57131d647e4da0a70df6d3d7b",
                "round": 0,
            },
        ),
    ),
)
def test_failsafe_randomness(return_value: MagicMock,
                             expected_hash: Optional[str]) -> None
```

Test `failsafe_randomness`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestRandomnessBehaviour.test_get_randomness_from_api"></a>

#### test`_`get`_`randomness`_`from`_`api

```python
@pytest.mark.parametrize("randomness_response", ("test", None))
@pytest.mark.parametrize("verified", (True, False))
def test_get_randomness_from_api(randomness_response: Optional[str],
                                 verified: bool) -> None
```

Test `get_randomness_from_api`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestRandomnessBehaviour.test_async_act"></a>

#### test`_`async`_`act

```python
@pytest.mark.parametrize(
    "retries_exceeded, failsafe_succeeds",
    # (False, False) is not tested, because it does not make sense
    ((True, False), (True, True), (False, True)),
)
@pytest.mark.parametrize(
    "observation",
    (
        None,
        {},
        {
            "randomness":
            "d067b86fa5235e7e5225e8328e8faac5c279cbf57131d647e4da0a70df6d3d7b",
            "round": 0,
        },
    ),
)
def test_async_act(retries_exceeded: bool, failsafe_succeeds: bool,
                   observation: Optional[Dict[str, Union[str, int]]]) -> None
```

Test `async_act`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestRandomnessBehaviour.test_clean_up"></a>

#### test`_`clean`_`up

```python
def test_clean_up() -> None
```

Test `clean_up`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestRandomnessBehaviour.teardown_method"></a>

#### teardown`_`method

```python
def teardown_method() -> None
```

Teardown run after each test method.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestSelectKeeperBehaviour"></a>

## TestSelectKeeperBehaviour Objects

```python
class TestSelectKeeperBehaviour(BaseDummyBehaviour)
```

Tests for `SelectKeeperBehaviour`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestSelectKeeperBehaviour.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls) -> None
```

Setup the test class.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestSelectKeeperBehaviour.test_select_keeper"></a>

#### test`_`select`_`keeper

```python
@mock.patch.object(random, "shuffle", lambda do_not_shuffle: do_not_shuffle)
@pytest.mark.parametrize(
    "participants, blacklisted_keepers, most_voted_keeper_address, expected_keeper",
    (
        (
            frozenset((f"test_p{i}" for i in range(4))),
            set(),
            "test_p0",
            "test_p1",
        ),
        (
            frozenset((f"test_p{i}" for i in range(4))),
            set(),
            "test_p1",
            "test_p2",
        ),
        (
            frozenset((f"test_p{i}" for i in range(4))),
            set(),
            "test_p2",
            "test_p3",
        ),
        (
            frozenset((f"test_p{i}" for i in range(4))),
            set(),
            "test_p3",
            "test_p0",
        ),
        (
            frozenset((f"test_p{i}" for i in range(4))),
            {f"test_p{i}"
             for i in range(1)},
            "test_p1",
            "test_p2",
        ),
        (
            frozenset((f"test_p{i}" for i in range(4))),
            {f"test_p{i}"
             for i in range(4)},
            "",
            "",
        ),
    ),
)
def test_select_keeper(participants: FrozenSet[str],
                       blacklisted_keepers: Set[str],
                       most_voted_keeper_address: str,
                       expected_keeper: str) -> None
```

Test `_select_keeper`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_common.TestSelectKeeperBehaviour.test_async_act"></a>

#### test`_`async`_`act

```python
def test_async_act() -> None
```

Test `async_act`.

