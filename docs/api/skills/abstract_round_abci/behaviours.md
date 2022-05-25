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
def __new__(mcs, name: str, bases: Tuple, namespace: Dict, **kwargs: Any) -> Type
```

Initialize the class.

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour"></a>

## AbstractRoundBehaviour Objects

```python
class AbstractRoundBehaviour(
    Behaviour,  ABC,  Generic[EventType], metaclass=_MetaRoundBehaviour)
```

This behaviour implements an abstract round behaviour.

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

Set up the behaviour.

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

