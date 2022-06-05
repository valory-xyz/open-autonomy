<a id="packages.valory.skills.safe_deployment_abci.rounds"></a>

# packages.valory.skills.safe`_`deployment`_`abci.rounds

This module contains the data classes for the safe deployment ABCI application.

<a id="packages.valory.skills.safe_deployment_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

Event enumeration for the price estimation demo.

<a id="packages.valory.skills.safe_deployment_abci.rounds.SynchronizedData"></a>

## SynchronizedData Objects

```python
class SynchronizedData(BaseSynchronizedData)
```

Class to represent the synchronized data.

This data is replicated by the tendermint application.

<a id="packages.valory.skills.safe_deployment_abci.rounds.SynchronizedData.safe_contract_address"></a>

#### safe`_`contract`_`address

```python
@property
def safe_contract_address() -> str
```

Get the safe contract address.

<a id="packages.valory.skills.safe_deployment_abci.rounds.RandomnessSafeRound"></a>

## RandomnessSafeRound Objects

```python
class RandomnessSafeRound(CollectSameUntilThresholdRound)
```

A round for generating randomness

<a id="packages.valory.skills.safe_deployment_abci.rounds.SelectKeeperSafeRound"></a>

## SelectKeeperSafeRound Objects

```python
class SelectKeeperSafeRound(CollectSameUntilThresholdRound)
```

A round in a which keeper is selected

<a id="packages.valory.skills.safe_deployment_abci.rounds.DeploySafeRound"></a>

## DeploySafeRound Objects

```python
class DeploySafeRound(OnlyKeeperSendsRound)
```

A round in a which the safe is deployed

<a id="packages.valory.skills.safe_deployment_abci.rounds.ValidateSafeRound"></a>

## ValidateSafeRound Objects

```python
class ValidateSafeRound(VotingRound)
```

A round in a which the safe address is validated

<a id="packages.valory.skills.safe_deployment_abci.rounds.FinishedSafeRound"></a>

## FinishedSafeRound Objects

```python
class FinishedSafeRound(DegenerateRound)
```

A round that represents that the safe has been deployed

<a id="packages.valory.skills.safe_deployment_abci.rounds.SafeDeploymentAbciApp"></a>

## SafeDeploymentAbciApp Objects

```python
class SafeDeploymentAbciApp(AbciApp[Event])
```

SafeDeploymentAbciApp

Initial round: RandomnessSafeRound

Initial states: {RandomnessSafeRound}

Transition states:
    0. RandomnessSafeRound
        - done: 1.
        - round timeout: 0.
        - no majority: 0.
    1. SelectKeeperSafeRound
        - done: 2.
        - round timeout: 0.
        - no majority: 0.
    2. DeploySafeRound
        - done: 3.
        - deploy timeout: 1.
        - failed: 1.
    3. ValidateSafeRound
        - done: 4.
        - negative: 0.
        - none: 0.
        - validate timeout: 0.
        - no majority: 0.
    4. FinishedSafeRound

Final states: {FinishedSafeRound}

Timeouts:
    round timeout: 30.0
    validate timeout: 30.0
    deploy timeout: 30.0

