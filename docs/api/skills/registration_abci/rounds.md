<a id="packages.valory.skills.registration_abci.rounds"></a>

# packages.valory.skills.registration`_`abci.rounds

This module contains the data classes for common apps ABCI application.

<a id="packages.valory.skills.registration_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

Event enumeration for the price estimation demo.

<a id="packages.valory.skills.registration_abci.rounds.SynchronizedData"></a>

## SynchronizedData Objects

```python
class SynchronizedData(BaseSynchronizedData)
```

Class to represent the synchronized data.

This data is replicated by the tendermint application.

<a id="packages.valory.skills.registration_abci.rounds.SynchronizedData.safe_contract_address"></a>

#### safe`_`contract`_`address

```python
@property
def safe_contract_address() -> str
```

Get the safe contract address.

<a id="packages.valory.skills.registration_abci.rounds.FinishedRegistrationRound"></a>

## FinishedRegistrationRound Objects

```python
class FinishedRegistrationRound(DegenerateRound)
```

A round representing that agent registration has finished

<a id="packages.valory.skills.registration_abci.rounds.FinishedRegistrationFFWRound"></a>

## FinishedRegistrationFFWRound Objects

```python
class FinishedRegistrationFFWRound(DegenerateRound)
```

A fast-forward round representing that agent registration has finished

<a id="packages.valory.skills.registration_abci.rounds.RegistrationStartupRound"></a>

## RegistrationStartupRound Objects

```python
class RegistrationStartupRound(CollectSameUntilAllRound)
```

A round in which the agents get registered.

This round waits until all agents have registered.

<a id="packages.valory.skills.registration_abci.rounds.RegistrationStartupRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.registration_abci.rounds.RegistrationRound"></a>

## RegistrationRound Objects

```python
class RegistrationRound(CollectSameUntilThresholdRound)
```

A round in which the agents get registered.

This rounds waits until the threshold of agents has been reached
and then a further x block confirmations.

<a id="packages.valory.skills.registration_abci.rounds.RegistrationRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.registration_abci.rounds.AgentRegistrationAbciApp"></a>

## AgentRegistrationAbciApp Objects

```python
class AgentRegistrationAbciApp(AbciApp[Event])
```

AgentRegistrationAbciApp

Initial round: RegistrationStartupRound

Initial states: {RegistrationRound, RegistrationStartupRound}

Transition states:
    0. RegistrationStartupRound
        - done: 2.
        - fast forward: 3.
    1. RegistrationRound
        - done: 3.
        - no majority: 1.
    2. FinishedRegistrationRound
    3. FinishedRegistrationFFWRound

Final states: {FinishedRegistrationFFWRound, FinishedRegistrationRound}

Timeouts:
    round timeout: 30.0

