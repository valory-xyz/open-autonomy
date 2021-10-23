<a id="packages.valory.skills.abstract_round_abci.behaviours"></a>

# packages.valory.skills.abstract`_`round`_`abci.behaviours

This module contains the behaviours for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour"></a>

## AbstractRoundBehaviour Objects

```python
class AbstractRoundBehaviour(FSMBehaviour)
```

This behaviour implements an abstract round.

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize the behaviour.

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

<a id="packages.valory.skills.abstract_round_abci.behaviours.AbstractRoundBehaviour.current_state"></a>

#### current`_`state

```python
@property
def current_state() -> Optional[BaseState]
```

Get the current state.

