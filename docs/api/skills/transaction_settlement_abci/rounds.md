<a id="packages.valory.skills.transaction_settlement_abci.rounds"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.rounds

This module contains the data classes for the `transaction settlement` ABCI application.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

Event enumeration for the price estimation demo.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.rotate_list"></a>

#### rotate`_`list

```python
def rotate_list(my_list: list, positions: int) -> List[str]
```

Rotate a list n positions.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState"></a>

## PeriodState Objects

```python
class PeriodState(BasePeriodState)
```

Class to represent a period state.

This state is replicated by the tendermint application.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.safe_contract_address"></a>

#### safe`_`contract`_`address

```python
@property
def safe_contract_address() -> str
```

Get the safe contract address.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.oracle_contract_address"></a>

#### oracle`_`contract`_`address

```python
@property
def oracle_contract_address() -> str
```

Get the oracle contract address.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.participant_to_signature"></a>

#### participant`_`to`_`signature

```python
@property
def participant_to_signature() -> Mapping[str, SignaturePayload]
```

Get the participant_to_signature.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.tx_hashes_history"></a>

#### tx`_`hashes`_`history

```python
@property
def tx_hashes_history() -> Optional[List[str]]
```

Get the tx hashes history.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.final_tx_hash"></a>

#### final`_`tx`_`hash

```python
@property
def final_tx_hash() -> str
```

Get the final_tx_hash.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.final_verification_status"></a>

#### final`_`verification`_`status

```python
@property
def final_verification_status() -> VerificationStatus
```

Get the final verification status.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.most_voted_tx_hash"></a>

#### most`_`voted`_`tx`_`hash

```python
@property
def most_voted_tx_hash() -> str
```

Get the most_voted_tx_hash.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.is_final_tx_hash_set"></a>

#### is`_`final`_`tx`_`hash`_`set

```python
@property
def is_final_tx_hash_set() -> bool
```

Check if most_voted_estimate is set.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.most_voted_estimate"></a>

#### most`_`voted`_`estimate

```python
@property
def most_voted_estimate() -> float
```

Get the most_voted_estimate.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.is_most_voted_estimate_set"></a>

#### is`_`most`_`voted`_`estimate`_`set

```python
@property
def is_most_voted_estimate_set() -> bool
```

Check if most_voted_estimate is set.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.nonce"></a>

#### nonce

```python
@property
def nonce() -> Optional[Nonce]
```

Get the nonce.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.max_priority_fee_per_gas"></a>

#### max`_`priority`_`fee`_`per`_`gas

```python
@property
def max_priority_fee_per_gas() -> Optional[int]
```

Get the gas data.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FinishedRegistrationRound"></a>

## FinishedRegistrationRound Objects

```python
class FinishedRegistrationRound(DegenerateRound)
```

A round representing that agent registration has finished

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FinishedRegistrationFFWRound"></a>

## FinishedRegistrationFFWRound Objects

```python
class FinishedRegistrationFFWRound(DegenerateRound)
```

A fast-forward round representing that agent registration has finished

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FinishedTransactionSubmissionRound"></a>

## FinishedTransactionSubmissionRound Objects

```python
class FinishedTransactionSubmissionRound(DegenerateRound)
```

A round that represents that transaction submission has finished

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FailedRound"></a>

## FailedRound Objects

```python
class FailedRound(DegenerateRound)
```

A round that represents that the period failed

<a id="packages.valory.skills.transaction_settlement_abci.rounds.CollectSignatureRound"></a>

## CollectSignatureRound Objects

```python
class CollectSignatureRound(CollectDifferentUntilThresholdRound)
```

A round in which agents sign the transaction

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FinalizationRound"></a>

## FinalizationRound Objects

```python
class FinalizationRound(OnlyKeeperSendsRound)
```

A round that represents transaction signing has finished

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FinalizationRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.RandomnessTransactionSubmissionRound"></a>

## RandomnessTransactionSubmissionRound Objects

```python
class RandomnessTransactionSubmissionRound(CollectSameUntilThresholdRound)
```

A round for generating randomness

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionRoundA"></a>

## SelectKeeperTransactionSubmissionRoundA Objects

```python
class SelectKeeperTransactionSubmissionRoundA(CollectSameUntilThresholdRound)
```

A round in which a keeper is selected for transaction submission

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionRoundB"></a>

## SelectKeeperTransactionSubmissionRoundB Objects

```python
class SelectKeeperTransactionSubmissionRoundB(CollectSameUntilThresholdRound)
```

A round in which a keeper is selected for transaction submission

<a id="packages.valory.skills.transaction_settlement_abci.rounds.ResetRound"></a>

## ResetRound Objects

```python
class ResetRound(CollectSameUntilThresholdRound)
```

A round that represents the reset of a period

<a id="packages.valory.skills.transaction_settlement_abci.rounds.ResetRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.ResetAndPauseRound"></a>

## ResetAndPauseRound Objects

```python
class ResetAndPauseRound(CollectSameUntilThresholdRound)
```

A round that represents that consensus is reached (the final round)

<a id="packages.valory.skills.transaction_settlement_abci.rounds.ResetAndPauseRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.ValidateTransactionRound"></a>

## ValidateTransactionRound Objects

```python
class ValidateTransactionRound(VotingRound)
```

A round in which agents validate the transaction

<a id="packages.valory.skills.transaction_settlement_abci.rounds.ValidateTransactionRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.CheckTransactionHistoryRound"></a>

## CheckTransactionHistoryRound Objects

```python
class CheckTransactionHistoryRound(CollectSameUntilThresholdRound)
```

A round in which agents check the transaction history to see if any previous tx has been validated

<a id="packages.valory.skills.transaction_settlement_abci.rounds.CheckTransactionHistoryRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.TransactionSubmissionAbciApp"></a>

## TransactionSubmissionAbciApp Objects

```python
class TransactionSubmissionAbciApp(AbciApp[Event])
```

TransactionSubmissionAbciApp

Initial round: RandomnessTransactionSubmissionRound

Initial states: {RandomnessTransactionSubmissionRound}

Transition states:
0. RandomnessTransactionSubmissionRound
    - done: 1.
    - round timeout: 6.
    - no majority: 0.
1. SelectKeeperTransactionSubmissionRoundA
    - done: 2.
    - round timeout: 6.
    - no majority: 6.
2. CollectSignatureRound
    - done: 3.
    - round timeout: 6.
    - no majority: 6.
3. FinalizationRound
    - done: 4.
    - round timeout: 5.
    - failed: 5.
4. ValidateTransactionRound
    - done: 7.
    - negative: 6.
    - none: 6.
    - validate timeout: 3.
    - no majority: 4.
5. SelectKeeperTransactionSubmissionRoundB
    - done: 3.
    - round timeout: 6.
    - no majority: 6.
6. ResetRound
    - done: 0.
    - reset timeout: 9.
    - no majority: 9.
7. ResetAndPauseRound
    - done: 8.
    - reset and pause timeout: 9.
    - no majority: 9.
8. FinishedTransactionSubmissionRound
9. FailedRound

Final states: {FinishedTransactionSubmissionRound, FailedRound}

Timeouts:
    round timeout: 30.0
    validate timeout: 30.0
    reset timeout: 30.0
    reset and pause timeout: 30.0

