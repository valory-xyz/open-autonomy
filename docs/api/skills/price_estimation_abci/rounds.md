<a id="packages.valory.skills.price_estimation_abci.rounds"></a>

# packages.valory.skills.price`_`estimation`_`abci.rounds

This module contains the data classes for the price estimation ABCI application.

<a id="packages.valory.skills.price_estimation_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

Event enumeration for the price estimation demo.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData"></a>

## SynchronizedData Objects

```python
class SynchronizedData(BaseSynchronizedData)
```

Class to represent the synchronized data.

This data is replicated by the tendermint application.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData.set_aggregator_method"></a>

#### set`_`aggregator`_`method

```python
def set_aggregator_method(aggregator_method: str) -> None
```

Set aggregator method.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData.safe_contract_address"></a>

#### safe`_`contract`_`address

```python
@property
def safe_contract_address() -> str
```

Get the safe contract address.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData.oracle_contract_address"></a>

#### oracle`_`contract`_`address

```python
@property
def oracle_contract_address() -> str
```

Get the oracle contract address.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData.estimate"></a>

#### estimate

```python
@property
def estimate() -> float
```

Get the estimate.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData.most_voted_estimate"></a>

#### most`_`voted`_`estimate

```python
@property
def most_voted_estimate() -> float
```

Get the most_voted_estimate.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData.most_voted_tx_hash"></a>

#### most`_`voted`_`tx`_`hash

```python
@property
def most_voted_tx_hash() -> float
```

Get the most_voted_tx_hash.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData.participant_to_observations"></a>

#### participant`_`to`_`observations

```python
@property
def participant_to_observations() -> Dict
```

Get the participant_to_observations.

<a id="packages.valory.skills.price_estimation_abci.rounds.SynchronizedData.participant_to_estimate"></a>

#### participant`_`to`_`estimate

```python
@property
def participant_to_estimate() -> Dict
```

Get the participant_to_estimate.

<a id="packages.valory.skills.price_estimation_abci.rounds.CollectObservationRound"></a>

## CollectObservationRound Objects

```python
class CollectObservationRound(CollectDifferentUntilThresholdRound)
```

A round in which agents collect observations

<a id="packages.valory.skills.price_estimation_abci.rounds.EstimateConsensusRound"></a>

## EstimateConsensusRound Objects

```python
class EstimateConsensusRound(CollectSameUntilThresholdRound)
```

A round in which agents reach consensus on an estimate

<a id="packages.valory.skills.price_estimation_abci.rounds.TxHashRound"></a>

## TxHashRound Objects

```python
class TxHashRound(CollectSameUntilThresholdRound)
```

A round in which agents compute the transaction hash

<a id="packages.valory.skills.price_estimation_abci.rounds.FinishedPriceAggregationRound"></a>

## FinishedPriceAggregationRound Objects

```python
class FinishedPriceAggregationRound(DegenerateRound)
```

A round that represents price aggregation has finished

<a id="packages.valory.skills.price_estimation_abci.rounds.PriceAggregationAbciApp"></a>

## PriceAggregationAbciApp Objects

```python
class PriceAggregationAbciApp(AbciApp[Event])
```

PriceAggregationAbciApp

Initial round: CollectObservationRound

Initial states: {CollectObservationRound}

Transition states:
    0. CollectObservationRound
        - done: 1.
        - round timeout: 0.
        - no majority: 0.
    1. EstimateConsensusRound
        - done: 2.
        - round timeout: 0.
        - no majority: 0.
    2. TxHashRound
        - done: 3.
        - none: 0.
        - round timeout: 0.
        - no majority: 0.
    3. FinishedPriceAggregationRound

Final states: {FinishedPriceAggregationRound}

Timeouts:
    round timeout: 30.0

