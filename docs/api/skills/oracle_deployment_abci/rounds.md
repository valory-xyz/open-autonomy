<a id="packages.valory.skills.oracle_deployment_abci.rounds"></a>

# packages.valory.skills.oracle`_`deployment`_`abci.rounds

This module contains the data classes for the oracle deployment ABCI application.

<a id="packages.valory.skills.oracle_deployment_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

Event enumeration for the price estimation demo.

<a id="packages.valory.skills.oracle_deployment_abci.rounds.SynchronizedData"></a>

## SynchronizedData Objects

```python
class SynchronizedData(BaseSynchronizedData)
```

Class to represent the synchronized data.

This data is replicated by the tendermint application.

<a id="packages.valory.skills.oracle_deployment_abci.rounds.SynchronizedData.safe_contract_address"></a>

#### safe`_`contract`_`address

```python
@property
def safe_contract_address() -> str
```

Get the safe contract address.

<a id="packages.valory.skills.oracle_deployment_abci.rounds.SynchronizedData.oracle_contract_address"></a>

#### oracle`_`contract`_`address

```python
@property
def oracle_contract_address() -> str
```

Get the oracle contract address.

<a id="packages.valory.skills.oracle_deployment_abci.rounds.RandomnessOracleRound"></a>

## RandomnessOracleRound Objects

```python
class RandomnessOracleRound(CollectSameUntilThresholdRound)
```

A round for generating randomness

<a id="packages.valory.skills.oracle_deployment_abci.rounds.SelectKeeperOracleRound"></a>

## SelectKeeperOracleRound Objects

```python
class SelectKeeperOracleRound(CollectSameUntilThresholdRound)
```

A round in a which keeper is selected

<a id="packages.valory.skills.oracle_deployment_abci.rounds.DeployOracleRound"></a>

## DeployOracleRound Objects

```python
class DeployOracleRound(OnlyKeeperSendsRound)
```

A round in a which the oracle is deployed

<a id="packages.valory.skills.oracle_deployment_abci.rounds.ValidateOracleRound"></a>

## ValidateOracleRound Objects

```python
class ValidateOracleRound(VotingRound)
```

A round in a which the oracle address is validated

<a id="packages.valory.skills.oracle_deployment_abci.rounds.FinishedOracleRound"></a>

## FinishedOracleRound Objects

```python
class FinishedOracleRound(DegenerateRound)
```

A round that represents that the oracle has been deployed

<a id="packages.valory.skills.oracle_deployment_abci.rounds.OracleDeploymentAbciApp"></a>

## OracleDeploymentAbciApp Objects

```python
class OracleDeploymentAbciApp(AbciApp[Event])
```

OracleDeploymentAbciApp

Initial round: RandomnessOracleRound

Initial states: {RandomnessOracleRound}

Transition states:
    0. RandomnessOracleRound
        - done: 1.
        - round timeout: 0.
        - no majority: 0.
    1. SelectKeeperOracleRound
        - done: 2.
        - round timeout: 0.
        - no majority: 0.
    2. DeployOracleRound
        - done: 3.
        - deploy timeout: 1.
        - failed: 1.
    3. ValidateOracleRound
        - done: 4.
        - negative: 0.
        - none: 0.
        - validate timeout: 0.
        - no majority: 0.
    4. FinishedOracleRound

Final states: {FinishedOracleRound}

Timeouts:
    round timeout: 30.0
    validate timeout: 30.0
    deploy timeout: 30.0

