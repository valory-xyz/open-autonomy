<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`base`_`rounds

Test the base round classes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectionRound"></a>

## TestCollectionRound Objects

```python
class TestCollectionRound(_BaseRoundTestClass)
```

Test class for CollectionRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectionRound.setup_method"></a>

#### setup`_`method

```python
def setup_method() -> None
```

Setup test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectionRound.test_serialized_collection"></a>

#### test`_`serialized`_`collection

```python
def test_serialized_collection() -> None
```

Test `serialized_collection` property.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectionRound.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectDifferentUntilAllRound"></a>

## TestCollectDifferentUntilAllRound Objects

```python
class TestCollectDifferentUntilAllRound(_BaseRoundTestClass)
```

Test class for CollectDifferentUntilAllRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectDifferentUntilAllRound.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run Tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectSameUntilAllRound"></a>

## TestCollectSameUntilAllRound Objects

```python
class TestCollectSameUntilAllRound(_BaseRoundTestClass)
```

Test class for CollectSameUntilAllRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectSameUntilAllRound.test_run"></a>

#### test`_`run

```python
def test_run() -> None
```

Run Tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectSameUntilThresholdRound"></a>

## TestCollectSameUntilThresholdRound Objects

```python
class TestCollectSameUntilThresholdRound(_BaseRoundTestClass)
```

Test CollectSameUntilThresholdRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectSameUntilThresholdRound.test_run"></a>

#### test`_`run

```python
@pytest.mark.parametrize(
    "selection_key",
    ("dummy_selection_key", tuple(f"dummy_selection_key_{i}"
                                  for i in range(2))),
)
def test_run(selection_key: Union[str, Tuple[str, ...]]) -> None
```

Run tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectSameUntilThresholdRound.test_run_with_none"></a>

#### test`_`run`_`with`_`none

```python
def test_run_with_none() -> None
```

Run tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestOnlyKeeperSendsRound"></a>

## TestOnlyKeeperSendsRound Objects

```python
class TestOnlyKeeperSendsRound(_BaseRoundTestClass,
                               BaseOnlyKeeperSendsRoundTest)
```

Test OnlyKeeperSendsRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestOnlyKeeperSendsRound.test_run"></a>

#### test`_`run

```python
@pytest.mark.parametrize("payload_key",
                         ("dummy_key", tuple(f"dummy_key_{i}"
                                             for i in range(2))))
def test_run(payload_key: Union[str, Tuple[str, ...]]) -> None
```

Run tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestOnlyKeeperSendsRound.test_keeper_payload_is_none"></a>

#### test`_`keeper`_`payload`_`is`_`none

```python
def test_keeper_payload_is_none() -> None
```

Test keeper payload valur set to none.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestVotingRound"></a>

## TestVotingRound Objects

```python
class TestVotingRound(_BaseRoundTestClass)
```

Test VotingRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestVotingRound.setup_test_voting_round"></a>

#### setup`_`test`_`voting`_`round

```python
def setup_test_voting_round() -> DummyVotingRound
```

Setup test voting round

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestVotingRound.test_vote_count"></a>

#### test`_`vote`_`count

```python
def test_vote_count() -> None
```

Testing agent vote count

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestVotingRound.test_threshold"></a>

#### test`_`threshold

```python
@pytest.mark.parametrize("vote", [True, False, None])
def test_threshold(vote: Optional[bool]) -> None
```

Runs threshold test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestVotingRound.test_end_round_no_majority"></a>

#### test`_`end`_`round`_`no`_`majority

```python
def test_end_round_no_majority() -> None
```

Test end round

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestVotingRound.test_invalid_vote_payload_count"></a>

#### test`_`invalid`_`vote`_`payload`_`count

```python
def test_invalid_vote_payload_count() -> None
```

Testing agent vote count with invalid payload.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectDifferentUntilThresholdRound"></a>

## TestCollectDifferentUntilThresholdRound Objects

```python
class TestCollectDifferentUntilThresholdRound(_BaseRoundTestClass)
```

Test CollectDifferentUntilThresholdRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectDifferentUntilThresholdRound.test_run"></a>

#### test`_`run

```python
@pytest.mark.parametrize("required_confirmations",
                         (MAX_PARTICIPANTS, MAX_PARTICIPANTS + 1))
def test_run(required_confirmations: int) -> None
```

Run tests.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectDifferentUntilThresholdRound.test_end_round"></a>

#### test`_`end`_`round

```python
def test_end_round() -> None
```

Test end round

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectNonEmptyUntilThresholdRound"></a>

## TestCollectNonEmptyUntilThresholdRound Objects

```python
class TestCollectNonEmptyUntilThresholdRound(_BaseRoundTestClass)
```

Test `CollectNonEmptyUntilThresholdRound`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectNonEmptyUntilThresholdRound.test_get_non_empty_values"></a>

#### test`_`get`_`non`_`empty`_`values

```python
def test_get_non_empty_values() -> None
```

Test `_get_non_empty_values`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectNonEmptyUntilThresholdRound.test_process_payload"></a>

#### test`_`process`_`payload

```python
def test_process_payload() -> None
```

Test `process_payload`.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectNonEmptyUntilThresholdRound.test_end_block"></a>

#### test`_`end`_`block

```python
@pytest.mark.parametrize(
    "selection_key",
    ("dummy_selection_key", tuple(f"dummy_selection_key_{i}"
                                  for i in range(2))),
)
@pytest.mark.parametrize(
    "is_value_none, expected_event",
    ((True, DummyEvent.NONE), (False, DummyEvent.DONE)),
)
def test_end_block(selection_key: Union[str, Tuple[str, ...]],
                   is_value_none: bool, expected_event: str) -> None
```

Test `end_block` when collection threshold is reached.

