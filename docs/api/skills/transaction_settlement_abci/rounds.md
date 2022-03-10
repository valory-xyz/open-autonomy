<a id="packages.valory.skills.transaction_settlement_abci.rounds"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.rounds

This module contains the data classes for the `transaction settlement` ABCI application.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

Event enumeration for the price estimation demo.

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
def tx_hashes_history() -> List[str]
```

Get the current cycle's tx hashes history, which has not yet been verified.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.to_be_validated_tx_hash"></a>

#### to`_`be`_`validated`_`tx`_`hash

```python
@property
def to_be_validated_tx_hash() -> str
```

Get the tx hash which is ready for validation.

This will always be the last hash in the `tx_hashes_history`,
due to the way we are inserting the hashes in the array.
We keep the hashes sorted by the time of their finalization.
If this property is accessed before the finalization succeeds,
then it is incorrectly used and raises an internal error.

**Returns**:

the tx hash which is ready for validation.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.final_tx_hash"></a>

#### final`_`tx`_`hash

```python
@property
def final_tx_hash() -> str
```

Get the verified tx hash.

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

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.missed_messages"></a>

#### missed`_`messages

```python
@property
def missed_messages() -> int
```

Check the number of missed messages.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.should_check_late_messages"></a>

#### should`_`check`_`late`_`messages

```python
@property
def should_check_late_messages() -> bool
```

Check if we should check for late-arriving messages.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.late_arriving_tx_hashes"></a>

#### late`_`arriving`_`tx`_`hashes

```python
@property
def late_arriving_tx_hashes() -> List[str]
```

Get the late_arriving_tx_hashes.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.PeriodState.is_reset_params_set"></a>

#### is`_`reset`_`params`_`set

```python
@property
def is_reset_params_set() -> bool
```

Get the reset params flag.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FailedRound"></a>

## FailedRound Objects

```python
class FailedRound(DegenerateRound,  ABC)
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

A round in which a new keeper is selected for transaction submission

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionRoundBAfterTimeout"></a>

## SelectKeeperTransactionSubmissionRoundBAfterTimeout Objects

```python
class SelectKeeperTransactionSubmissionRoundBAfterTimeout(
    SelectKeeperTransactionSubmissionRoundB)
```

A round in which a new keeper is selected for transaction submission after a round timeout of the first keeper

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionRoundBAfterTimeout.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Enum]]
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

<a id="packages.valory.skills.transaction_settlement_abci.rounds.CheckLateTxHashesRound"></a>

## CheckLateTxHashesRound Objects

```python
class CheckLateTxHashesRound(CheckTransactionHistoryRound)
```

A round in which agents check the late-arriving transaction hashes to see if any of them has been validated

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizeLateMessagesRound"></a>

## SynchronizeLateMessagesRound Objects

```python
class SynchronizeLateMessagesRound(CollectNonEmptyUntilThresholdRound)
```

A round in which agents synchronize potentially late arriving messages

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizeLateMessagesRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BasePeriodState, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FinishedTransactionSubmissionRound"></a>

## FinishedTransactionSubmissionRound Objects

```python
class FinishedTransactionSubmissionRound(DegenerateRound,  ABC)
```

A round that represents that transaction submission has finished

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
        - round timeout: 10.
        - no majority: 0.
    1. SelectKeeperTransactionSubmissionRoundA
        - done: 2.
        - round timeout: 10.
        - no majority: 10.
    2. CollectSignatureRound
        - done: 3.
        - round timeout: 10.
        - no majority: 10.
    3. FinalizationRound
        - done: 4.
        - check history: 5.
        - round timeout: 7.
        - finalization failed: 6.
        - check late arriving message: 8.
    4. ValidateTransactionRound
        - done: 11.
        - negative: 5.
        - none: 3.
        - validate timeout: 3.
        - no majority: 4.
    5. CheckTransactionHistoryRound
        - done: 11.
        - negative: 12.
        - none: 12.
        - round timeout: 5.
        - no majority: 12.
        - check late arriving message: 8.
    6. SelectKeeperTransactionSubmissionRoundB
        - done: 3.
        - round timeout: 10.
        - no majority: 10.
    7. SelectKeeperTransactionSubmissionRoundBAfterTimeout
        - done: 3.
        - round timeout: 10.
        - no majority: 10.
    8. SynchronizeLateMessagesRound
        - done: 9.
        - round timeout: 8.
        - no majority: 8.
        - none: 12.
        - missed and late messages mismatch: 12.
    9. CheckLateTxHashesRound
        - done: 11.
        - negative: 12.
        - none: 12.
        - round timeout: 9.
        - no majority: 12.
    10. ResetRound
        - done: 0.
        - reset timeout: 12.
        - no majority: 12.
    11. FinishedTransactionSubmissionRound
    12. FailedRound

Final states: {FailedRound, FinishedTransactionSubmissionRound}

Timeouts:
    round timeout: 30.0
    validate timeout: 30.0
    reset timeout: 30.0
    reset and pause timeout: 30.0

