<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours"></a>

# packages.valory.skills.abstract`_`round`_`abci.tests.data.dummy`_`abci.behaviours

This package contains round behaviours of DummyAbciApp.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyBaseBehaviour"></a>

## DummyBaseBehaviour Objects

```python
class DummyBaseBehaviour(BaseBehaviour, ABC)
```

Base behaviour for the common apps' skill.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyBaseBehaviour.synchronized_data"></a>

#### synchronized`_`data

```python
@property
def synchronized_data() -> SynchronizedData
```

Return the synchronized data.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyBaseBehaviour.params"></a>

#### params

```python
@property
def params() -> Params
```

Return the params.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyStartingBehaviour"></a>

## DummyStartingBehaviour Objects

```python
class DummyStartingBehaviour(DummyBaseBehaviour)
```

DummyStartingBehaviour

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyStartingBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the act, supporting asynchronous execution.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyRandomnessBehaviour"></a>

## DummyRandomnessBehaviour Objects

```python
class DummyRandomnessBehaviour(RandomnessBehaviour)
```

DummyRandomnessBehaviour

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyKeeperSelectionBehaviour"></a>

## DummyKeeperSelectionBehaviour Objects

```python
class DummyKeeperSelectionBehaviour(SelectKeeperBehaviour)
```

DummyKeeperSelectionBehaviour

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyKeeperSelectionBehaviour.serialized_keepers"></a>

#### serialized`_`keepers

```python
@staticmethod
def serialized_keepers(keepers: Deque[str], keeper_retries: int = 1) -> str
```

Get the keepers serialized.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyKeeperSelectionBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the act, supporting asynchronous execution.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyFinalBehaviour"></a>

## DummyFinalBehaviour Objects

```python
class DummyFinalBehaviour(DummyBaseBehaviour)
```

DummyFinalBehaviour

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyFinalBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the act, supporting asynchronous execution.

<a id="packages.valory.skills.abstract_round_abci.tests.data.dummy_abci.behaviours.DummyRoundBehaviour"></a>

## DummyRoundBehaviour Objects

```python
class DummyRoundBehaviour(AbstractRoundBehaviour)
```

DummyRoundBehaviour

