<a id="packages.valory.skills.price_estimation_abci.behaviours"></a>

# packages.valory.skills.price`_`estimation`_`abci.behaviours

This module contains the behaviours for the 'abci' skill.

<a id="packages.valory.skills.price_estimation_abci.behaviours.to_int"></a>

#### to`_`int

```python
def to_int(most_voted_estimate: float, decimals: int) -> int
```

Convert to int.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseBehaviour"></a>

## PriceEstimationBaseBehaviour Objects

```python
class PriceEstimationBaseBehaviour(BaseBehaviour,  ABC)
```

Base behaviour for the common apps' skill.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseBehaviour.synchronized_data"></a>

#### synchronized`_`data

```python
@property
def synchronized_data() -> SynchronizedData
```

Return the synchronized data.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseBehaviour.params"></a>

#### params

```python
@property
def params() -> Params
```

Return the params.

<a id="packages.valory.skills.price_estimation_abci.behaviours.ObserveBehaviour"></a>

## ObserveBehaviour Objects

```python
class ObserveBehaviour(PriceEstimationBaseBehaviour)
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
- Go to the next behaviour (set done event).

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
class EstimateBehaviour(PriceEstimationBaseBehaviour)
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
- Go to the next behaviour (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.pack_for_server"></a>

#### pack`_`for`_`server

```python
def pack_for_server(participants: Sequence[str], decimals: int, period_count: int, estimate: float, observations: Dict[str, float], data_source: str, unit: str, **_: Dict[str, str], ,) -> bytes
```

Package server data for signing

<a id="packages.valory.skills.price_estimation_abci.behaviours.TransactionHashBehaviour"></a>

## TransactionHashBehaviour Objects

```python
class TransactionHashBehaviour(PriceEstimationBaseBehaviour)
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
- Go to the next behaviour (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.TransactionHashBehaviour.send_to_server"></a>

#### send`_`to`_`server

```python
def send_to_server() -> Generator
```

Send data to server.

We send current period data of the agents and the previous
cycle's on-chain settlement tx hash. The current cycle's tx hash
is not available at this stage yet, and the first iteration will
contain no tx hash since there has not been on-chain transaction
settlement yet.

:yield: the http response

<a id="packages.valory.skills.price_estimation_abci.behaviours.ObserverRoundBehaviour"></a>

## ObserverRoundBehaviour Objects

```python
class ObserverRoundBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the observer behaviour.

