<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.test`_`base`_`rounds

Test the base round classes.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectionRound"></a>

## TestCollectionRound Objects

```python
class TestCollectionRound(_BaseRoundTestClass)
```

Test class for CollectionRound.

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
def test_run() -> None
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
class TestOnlyKeeperSendsRound(_BaseRoundTestClass,  BaseOnlyKeeperSendsRoundTest)
```

Test OnlyKeeperSendsRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestOnlyKeeperSendsRound.test_run"></a>

#### test`_`run

```python
def test_run() -> None
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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestVotingRound.test_negative_threshold"></a>

#### test`_`negative`_`threshold

```python
def test_negative_threshold() -> None
```

Runs test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestVotingRound.test_positive_threshold"></a>

#### test`_`positive`_`threshold

```python
def test_positive_threshold() -> None
```

Runs test.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectDifferentUntilThresholdRound"></a>

## TestCollectDifferentUntilThresholdRound Objects

```python
class TestCollectDifferentUntilThresholdRound(_BaseRoundTestClass)
```

Test CollectDifferentUntilThresholdRound.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectDifferentUntilThresholdRound.test_run"></a>

#### test`_`run

```python
@pytest.mark.parametrize(
        "required_confirmations", (MAX_PARTICIPANTS, MAX_PARTICIPANTS + 1)
    )
def test_run(required_confirmations: int) -> None
```

Run tests.

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

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectNonEmptyUntilThresholdRound.test_end_block_no_threshold_reached"></a>

#### test`_`end`_`block`_`no`_`threshold`_`reached

```python
@pytest.mark.parametrize("is_majority_possible", (True, False))
@pytest.mark.parametrize("reach_block_confirmations", (True, False))
def test_end_block_no_threshold_reached(is_majority_possible: bool, reach_block_confirmations: bool) -> None
```

Test `end_block` when no collection threshold is reached.

<a id="packages.valory.skills.abstract_round_abci.tests.test_base_rounds.TestCollectNonEmptyUntilThresholdRound.test_end_block"></a>

#### test`_`end`_`block

```python
@pytest.mark.parametrize(
        "is_value_none, expected_event", ((True, "none"), (False, "done"))
    )
def test_end_block(is_value_none: bool, expected_event: str) -> None
```

Test `end_block` when collection threshold is reached.

