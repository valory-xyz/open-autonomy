<a id="packages.valory.skills.abstract_round_abci.behaviours"></a>

# packages.valory.skills.abstract`_`round`_`abci.behaviours

This module contains the behaviours for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.behaviours._MetaRoundBehaviour"></a>

## `_`MetaRoundBehaviour Objects

```python
class _MetaRoundBehaviour(ABCMeta)
```

A metaclass that validates AbstractRoundBehaviour's attributes.

<a id="packages.valory.skills.abstract_round_abci.behaviours._MetaRoundBehaviour.__new__"></a>

#### `__`new`__`

```python
def __new__(mcs, name: str, bases: Tuple, namespace: Dict,
            **kwargs: Any) -> Type
```

Initialize the class.

<a id="packages.valory.skills.abstract_round_abci.behaviours.PendingOffencesBehaviour"></a>

## PendingOffencesBehaviour Objects

```python
class PendingOffencesBehaviour(BaseBehaviour)
```

A behaviour responsible for checking whether there are any pending offences.

<a id="packages.valory.skills.abstract_round_abci.behaviours.PendingOffencesBehaviour.round_sequence"></a>

#### round`_`sequence

```python
@property
def round_sequence() -> RoundSequence
```

Get the round sequence from the shared state.

<a id="packages.valory.skills.abstract_round_abci.behaviours.PendingOffencesBehaviour.pending_offences"></a>

#### pending`_`offences

```python
@property
def pending_offences() -> Set[PendingOffense]
```

Get the pending offences from the round sequence.

<a id="packages.valory.skills.abstract_round_abci.behaviours.PendingOffencesBehaviour.has_pending_offences"></a>

#### has`_`pending`_`offences

```python
def has_pending_offences() -> bool
```

Check if there are any pending offences.

<a id="packages.valory.skills.abstract_round_abci.behaviours.PendingOffencesBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Checks the pending offences.

This behaviour simply checks if the set of pending offences is not empty.
When it’s not empty, it pops the offence from the set, and sends it to the rest of the agents via a payload

**Returns**:

None

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour"></a>

## AbstractRoundBehaviour Objects

```python
class AbstractRoundBehaviour(  # pylint: disable=too-many-instance-attributes
        Behaviour,
        ABC,
        Generic[EventType],
        metaclass=_MetaRoundBehaviour)
```

This behaviour implements an abstract round behaviour.

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour.background_behaviours_cls"></a>

#### background`_`behaviours`_`cls

type: ignore

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize the behaviour.

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour.instantiate_behaviour_cls"></a>

#### instantiate`_`behaviour`_`cls

```python
def instantiate_behaviour_cls(behaviour_cls: BehaviourType) -> BaseBehaviour
```

Instantiate the behaviours class.

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the behaviours.

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the behaviour

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour.act"></a>

#### act

```python
def act() -> None
```

Implement the behaviour.

