<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds"></a>

# packages.valory.skills.abstract`_`round`_`abci.test`_`tools.rounds

Test tools for testing rounds.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.get_participants"></a>

#### get`_`participants

```python
def get_participants() -> FrozenSet[str]
```

Participants

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyEvent"></a>

## DummyEvent Objects

```python
class DummyEvent(Enum)
```

Dummy Event

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyTxPayload"></a>

## DummyTxPayload Objects

```python
@dataclass(frozen=True)
class DummyTxPayload(BaseTxPayload)
```

Dummy Transaction Payload.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummySynchronizedData"></a>

## DummySynchronizedData Objects

```python
class DummySynchronizedData(BaseSynchronizedData)
```

Dummy synchronized data for tests.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.get_dummy_tx_payloads"></a>

#### get`_`dummy`_`tx`_`payloads

```python
def get_dummy_tx_payloads(participants: FrozenSet[str],
                          value: Any = None,
                          vote: Optional[bool] = False,
                          is_value_none: bool = False,
                          is_vote_none: bool = False) -> List[DummyTxPayload]
```

Returns a list of DummyTxPayload objects.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyRound"></a>

## DummyRound Objects

```python
class DummyRound(AbstractRound)
```

Dummy round.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

end_block method.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyCollectionRound"></a>

## DummyCollectionRound Objects

```python
class DummyCollectionRound(CollectionRound, DummyRound)
```

Dummy Class for CollectionRound

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyCollectDifferentUntilAllRound"></a>

## DummyCollectDifferentUntilAllRound Objects

```python
class DummyCollectDifferentUntilAllRound(CollectDifferentUntilAllRound,
                                         DummyRound)
```

Dummy Class for CollectDifferentUntilAllRound

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyCollectSameUntilAllRound"></a>

## DummyCollectSameUntilAllRound Objects

```python
class DummyCollectSameUntilAllRound(CollectSameUntilAllRound, DummyRound)
```

Dummy Class for CollectSameUntilThresholdRound

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyCollectDifferentUntilThresholdRound"></a>

## DummyCollectDifferentUntilThresholdRound Objects

```python
class DummyCollectDifferentUntilThresholdRound(
        CollectDifferentUntilThresholdRound, DummyRound)
```

Dummy Class for CollectDifferentUntilThresholdRound

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyCollectSameUntilThresholdRound"></a>

## DummyCollectSameUntilThresholdRound Objects

```python
class DummyCollectSameUntilThresholdRound(CollectSameUntilThresholdRound,
                                          DummyRound)
```

Dummy Class for CollectSameUntilThresholdRound

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyOnlyKeeperSendsRound"></a>

## DummyOnlyKeeperSendsRound Objects

```python
class DummyOnlyKeeperSendsRound(OnlyKeeperSendsRound, DummyRound)
```

Dummy Class for OnlyKeeperSendsRound

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyVotingRound"></a>

## DummyVotingRound Objects

```python
class DummyVotingRound(VotingRound, DummyRound)
```

Dummy Class for VotingRound

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.DummyCollectNonEmptyUntilThresholdRound"></a>

## DummyCollectNonEmptyUntilThresholdRound Objects

```python
class DummyCollectNonEmptyUntilThresholdRound(
        CollectNonEmptyUntilThresholdRound, DummyRound)
```

Dummy Class for `CollectNonEmptyUntilThresholdRound`

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseRoundTestClass"></a>

## BaseRoundTestClass Objects

```python
class BaseRoundTestClass()
```

Base test class.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseRoundTestClass.setup"></a>

#### setup

```python
def setup() -> None
```

Setup test class.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseCollectDifferentUntilAllRoundTest"></a>

## BaseCollectDifferentUntilAllRoundTest Objects

```python
class BaseCollectDifferentUntilAllRoundTest(  # pylint: disable=too-few-public-methods
        BaseRoundTestClass)
```

Tests for rounds derived from CollectDifferentUntilAllRound.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseCollectSameUntilAllRoundTest"></a>

## BaseCollectSameUntilAllRoundTest Objects

```python
class BaseCollectSameUntilAllRoundTest(BaseRoundTestClass)
```

Tests for rounds derived from CollectSameUntilAllRound.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseCollectSameUntilThresholdRoundTest"></a>

## BaseCollectSameUntilThresholdRoundTest Objects

```python
class BaseCollectSameUntilThresholdRoundTest(  # pylint: disable=too-few-public-methods
        BaseRoundTestClass)
```

Tests for rounds derived from CollectSameUntilThresholdRound.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseOnlyKeeperSendsRoundTest"></a>

## BaseOnlyKeeperSendsRoundTest Objects

```python
class BaseOnlyKeeperSendsRoundTest(  # pylint: disable=too-few-public-methods
        BaseRoundTestClass)
```

Tests for rounds derived from OnlyKeeperSendsRound.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseVotingRoundTest"></a>

## BaseVotingRoundTest Objects

```python
class BaseVotingRoundTest(BaseRoundTestClass)
```

Tests for rounds derived from VotingRound.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseCollectDifferentUntilThresholdRoundTest"></a>

## BaseCollectDifferentUntilThresholdRoundTest Objects

```python
class BaseCollectDifferentUntilThresholdRoundTest(  # pylint: disable=too-few-public-methods
        BaseRoundTestClass)
```

Tests for rounds derived from CollectDifferentUntilThresholdRound.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds.BaseCollectNonEmptyUntilThresholdRound"></a>

## BaseCollectNonEmptyUntilThresholdRound Objects

```python
class BaseCollectNonEmptyUntilThresholdRound(  # pylint: disable=too-few-public-methods
        BaseCollectDifferentUntilThresholdRoundTest)
```

Tests for rounds derived from `CollectNonEmptyUntilThresholdRound`.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds._BaseRoundTestClass"></a>

## `_`BaseRoundTestClass Objects

```python
class _BaseRoundTestClass(BaseRoundTestClass)
```

Base test class.

<a id="packages.valory.skills.abstract_round_abci.test_tools.rounds._BaseRoundTestClass.setup"></a>

#### setup

```python
def setup() -> None
```

Setup test class.

