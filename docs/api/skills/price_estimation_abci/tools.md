<a id="packages.valory.skills.price_estimation_abci.tools"></a>

# packages.valory.skills.price`_`estimation`_`abci.tools

This module contains the model to aggregate the price observations deterministically.

<a id="packages.valory.skills.price_estimation_abci.tools.aggregate"></a>

#### aggregate

```python
def aggregate(*observations: float) -> float
```

Aggregate a list of observations.

<a id="packages.valory.skills.price_estimation_abci.tools.random_selection"></a>

#### random`_`selection

```python
def random_selection(elements: List[str], randomness: float) -> str
```

Select a random element from a list.

:param: elements: a list of elements to choose among
:param: randomness: a random number in the [0,1) interval

**Returns**:

a randomly chosen element

