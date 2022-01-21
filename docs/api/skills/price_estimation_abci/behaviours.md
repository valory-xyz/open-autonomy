<a id="packages.valory.skills.price_estimation_abci.behaviours"></a>

# packages.valory.skills.price`_`estimation`_`abci.behaviours

This module contains the behaviours for the 'abci' skill.

<a id="packages.valory.skills.price_estimation_abci.behaviours.to_int"></a>

#### to`_`int

```python
def to_int(most_voted_estimate: float, decimals: int) -> int
```

Convert to int.

<a id="packages.valory.skills.price_estimation_abci.behaviours.payload_to_hex"></a>

#### payload`_`to`_`hex

```python
def payload_to_hex(tx_hash: str, ether_value: int, safe_tx_gas: int, to_address: str, data: bytes) -> str
```

Serialise to a hex string.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseState"></a>

## PriceEstimationBaseState Objects

```python
class PriceEstimationBaseState(BaseState,  ABC)
```

Base state behaviour for the common apps' skill.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseState.period_state"></a>

#### period`_`state

```python
@property
def period_state() -> PeriodState
```

Return the period state.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseState.params"></a>

#### params

```python
@property
def params() -> Params
```

Return the params.

<a id="packages.valory.skills.price_estimation_abci.behaviours.ObserveBehaviour"></a>

## ObserveBehaviour Objects

```python
class ObserveBehaviour(PriceEstimationBaseState)
```

Observe price estimate.

<a id="packages.valory.skills.price_estimation_abci.behaviours.ObserveBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Ask the configured API the price of a currency.
- If the request fails, retry until max retries are exceeded.
- Send an observation transaction and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.ObserveBehaviour.clean_up"></a>

#### clean`_`up

```python
def clean_up() -> None
```

Clean up the resources due to a 'stop' event.

It can be optionally implemented by the concrete classes.

<a id="packages.valory.skills.price_estimation_abci.behaviours.EstimateBehaviour"></a>

## EstimateBehaviour Objects

```python
class EstimateBehaviour(PriceEstimationBaseState)
```

Estimate price.

<a id="packages.valory.skills.price_estimation_abci.behaviours.EstimateBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Run the script to compute the estimate starting from the shared observations.
- Build an estimate transaction and send the transaction and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.TransactionHashBehaviour"></a>

## TransactionHashBehaviour Objects

```python
class TransactionHashBehaviour(PriceEstimationBaseState)
```

Share the transaction hash for the signature round.

<a id="packages.valory.skills.price_estimation_abci.behaviours.TransactionHashBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Request the transaction hash for the safe transaction. This is the
  hash that needs to be signed by a threshold of agents.
- Send the transaction hash as a transaction and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.ObserverRoundBehaviour"></a>

## ObserverRoundBehaviour Objects

```python
class ObserverRoundBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the observer behaviour.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationConsensusBehaviour"></a>

## PriceEstimationConsensusBehaviour Objects

```python
class PriceEstimationConsensusBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the price estimation.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationConsensusBehaviour.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the behaviour.

