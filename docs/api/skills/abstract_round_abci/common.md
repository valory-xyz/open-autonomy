<a id="packages.valory.skills.abstract_round_abci.common"></a>

# packages.valory.skills.abstract`_`round`_`abci.common

This module contains the behaviours, round and payloads for the 'abstract_round_abci' skill.

<a id="packages.valory.skills.abstract_round_abci.common.random_selection"></a>

#### random`_`selection

```python
def random_selection(elements: List[Any], randomness: float) -> str
```

Select a random element from a list.

:param: elements: a list of elements to choose among
:param: randomness: a random number in the [0,1) interval
:return: a randomly chosen element


<a id="packages.valory.skills.abstract_round_abci.common.RandomnessBehaviour"></a>

## RandomnessBehaviour Objects

```python
class RandomnessBehaviour(BaseBehaviour, ABC)
```

Behaviour to collect randomness values from DRAND service for keeper agent selection.

<a id="packages.valory.skills.abstract_round_abci.common.RandomnessBehaviour.failsafe_randomness"></a>

#### failsafe`_`randomness

```python
def failsafe_randomness() -> Generator[None, None, RandomnessObservation]
```

This methods provides a failsafe for randomness retrieval.

**Returns**:

derived randomness

<a id="packages.valory.skills.abstract_round_abci.common.RandomnessBehaviour.get_randomness_from_api"></a>

#### get`_`randomness`_`from`_`api

```python
def get_randomness_from_api() -> Generator[None, None, RandomnessObservation]
```

Retrieve randomness from given api specs.

<a id="packages.valory.skills.abstract_round_abci.common.RandomnessBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Retrieve randomness from API.

Steps:
- Do a http request to the API.
- Retry until receiving valid values for randomness or retries exceed.
- If retrieved values are valid continue else generate randomness from chain.

<a id="packages.valory.skills.abstract_round_abci.common.RandomnessBehaviour.clean_up"></a>

#### clean`_`up

```python
def clean_up() -> None
```

Clean up the resources due to a 'stop' event.

It can be optionally implemented by the concrete classes.

<a id="packages.valory.skills.abstract_round_abci.common.SelectKeeperBehaviour"></a>

## SelectKeeperBehaviour Objects

```python
class SelectKeeperBehaviour(BaseBehaviour, ABC)
```

Select the keeper agent.

<a id="packages.valory.skills.abstract_round_abci.common.SelectKeeperBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Select a keeper randomly.
- Send the transaction with the keeper and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

