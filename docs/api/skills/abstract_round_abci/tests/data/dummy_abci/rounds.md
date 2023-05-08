<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.data.dummy`_`abci.rounds

This package contains the rounds of DummyAbciApp.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

DummyAbciApp Events

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.SynchronizedData"></a>

## SynchronizedData Objects

```python
class SynchronizedData(BaseSynchronizedData)
```

Class to represent the synchronized data.

This data is replicated by the tendermint application.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.DummyMixinRound"></a>

## DummyMixinRound Objects

```python
class DummyMixinRound(AbstractRound, ABC)
```

DummyMixinRound

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.DummyMixinRound.synchronized_data"></a>

#### synchronized`_`data

```python
@property
def synchronized_data() -> SynchronizedData
```

Return the synchronized data.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.DummyStartingRound"></a>

## DummyStartingRound Objects

```python
class DummyStartingRound(CollectSameUntilAllRound, DummyMixinRound)
```

DummyStartingRound

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.DummyStartingRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.DummyRandomnessRound"></a>

## DummyRandomnessRound Objects

```python
class DummyRandomnessRound(CollectSameUntilThresholdRound, DummyMixinRound)
```

DummyRandomnessRound

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.DummyKeeperSelectionRound"></a>

## DummyKeeperSelectionRound Objects

```python
class DummyKeeperSelectionRound(CollectSameUntilThresholdRound,
                                DummyMixinRound)
```

DummyKeeperSelectionRound

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.DummyFinalRound"></a>

## DummyFinalRound Objects

```python
class DummyFinalRound(OnlyKeeperSendsRound, DummyMixinRound)
```

DummyFinalRound

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.rounds.DummyAbciApp"></a>

## DummyAbciApp Objects

```python
class DummyAbciApp(AbciApp[Event])
```

DummyAbciApp

