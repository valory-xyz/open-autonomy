<a id="packages.valory.skills.transaction_settlement_abci.rounds"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.rounds

This module contains the data classes for the `transaction settlement` ABCI application.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.Event"></a>

## Event Objects

```python
class Event(Enum)
```

Event enumeration for the price estimation demo.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData"></a>

## SynchronizedData Objects

```python
class SynchronizedData(BaseSynchronizedData)
```

Class to represent the synchronized data.

This data is replicated by the tendermint application.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.participant_to_signature"></a>

#### participant`_`to`_`signature

```python
@property
def participant_to_signature() -> Mapping[str, SignaturePayload]
```

Get the participant_to_signature.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.tx_hashes_history"></a>

#### tx`_`hashes`_`history

```python
@property
def tx_hashes_history() -> List[str]
```

Get the current cycle's tx hashes history, which has not yet been verified.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.keepers"></a>

#### keepers

```python
@property
def keepers() -> Deque[str]
```

Get the current cycle's keepers who have tried to submit a transaction.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.keepers_threshold_exceeded"></a>

#### keepers`_`threshold`_`exceeded

```python
@property
def keepers_threshold_exceeded() -> bool
```

Check if the number of selected keepers has exceeded the allowed limit.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.most_voted_randomness_round"></a>

#### most`_`voted`_`randomness`_`round

```python
@property
def most_voted_randomness_round() -> int
```

Get the first in priority keeper to try to re-submit a transaction.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.most_voted_keeper_address"></a>

#### most`_`voted`_`keeper`_`address

```python
@property
def most_voted_keeper_address() -> str
```

Get the first in priority keeper to try to re-submit a transaction.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.is_keeper_set"></a>

#### is`_`keeper`_`set

```python
@property
def is_keeper_set() -> bool
```

Check whether keeper is set.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.keeper_retries"></a>

#### keeper`_`retries

```python
@property
def keeper_retries() -> int
```

Get the number of times the current keeper has retried.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.to_be_validated_tx_hash"></a>

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
then it is incorrectly used and raises an error.

**Returns**:

the tx hash which is ready for validation.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.final_tx_hash"></a>

#### final`_`tx`_`hash

```python
@property
def final_tx_hash() -> str
```

Get the verified tx hash.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.final_verification_status"></a>

#### final`_`verification`_`status

```python
@property
def final_verification_status() -> VerificationStatus
```

Get the final verification status.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.most_voted_tx_hash"></a>

#### most`_`voted`_`tx`_`hash

```python
@property
def most_voted_tx_hash() -> str
```

Get the most_voted_tx_hash.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.missed_messages"></a>

#### missed`_`messages

```python
@property
def missed_messages() -> Dict[str, int]
```

The number of missed messages per agent address.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.n_missed_messages"></a>

#### n`_`missed`_`messages

```python
@property
def n_missed_messages() -> int
```

The number of missed messages in total.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.should_check_late_messages"></a>

#### should`_`check`_`late`_`messages

```python
@property
def should_check_late_messages() -> bool
```

Check if we should check for late-arriving messages.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.late_arriving_tx_hashes"></a>

#### late`_`arriving`_`tx`_`hashes

```python
@property
def late_arriving_tx_hashes() -> Dict[str, List[str]]
```

Get the late_arriving_tx_hashes.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.suspects"></a>

#### suspects

```python
@property
def suspects() -> Tuple[str]
```

Get the suspect agents.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.most_voted_check_result"></a>

#### most`_`voted`_`check`_`result

```python
@property
def most_voted_check_result() -> str
```

Get the most voted checked result.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.participant_to_check"></a>

#### participant`_`to`_`check

```python
@property
def participant_to_check() -> Mapping[str, CheckTransactionHistoryPayload]
```

Get the mapping from participants to checks.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.participant_to_late_messages"></a>

#### participant`_`to`_`late`_`messages

```python
@property
def participant_to_late_messages(
) -> Mapping[str, SynchronizeLateMessagesPayload]
```

Get the mapping from participants to checks.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizedData.get_chain_id"></a>

#### get`_`chain`_`id

```python
def get_chain_id(default_chain_id: str) -> str
```

Get the chain id.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FailedRound"></a>

## FailedRound Objects

```python
class FailedRound(DegenerateRound, ABC)
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
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.RandomnessTransactionSubmissionRound"></a>

## RandomnessTransactionSubmissionRound Objects

```python
class RandomnessTransactionSubmissionRound(CollectSameUntilThresholdRound)
```

A round for generating randomness

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionARound"></a>

## SelectKeeperTransactionSubmissionARound Objects

```python
class SelectKeeperTransactionSubmissionARound(CollectSameUntilThresholdRound)
```

A round in which a keeper is selected for transaction submission

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionARound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionBRound"></a>

## SelectKeeperTransactionSubmissionBRound Objects

```python
class SelectKeeperTransactionSubmissionBRound(
        SelectKeeperTransactionSubmissionARound)
```

A round in which a new keeper is selected for transaction submission

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionBAfterTimeoutRound"></a>

## SelectKeeperTransactionSubmissionBAfterTimeoutRound Objects

```python
class SelectKeeperTransactionSubmissionBAfterTimeoutRound(
        SelectKeeperTransactionSubmissionBRound)
```

A round in which a new keeper is selected for tx submission after a round timeout of the previous keeper

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SelectKeeperTransactionSubmissionBAfterTimeoutRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
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
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
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
def end_block() -> Optional[Tuple[BaseSynchronizedData, Enum]]
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
def end_block() -> Optional[Tuple[BaseSynchronizedData, Event]]
```

Process the end of the block.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizeLateMessagesRound.process_payload"></a>

#### process`_`payload

```python
def process_payload(payload: BaseTxPayload) -> None
```

Process payload.

<a id="packages.valory.skills.transaction_settlement_abci.rounds.SynchronizeLateMessagesRound.check_payload"></a>

#### check`_`payload

```python
def check_payload(payload: BaseTxPayload) -> None
```

Check Payload

<a id="packages.valory.skills.transaction_settlement_abci.rounds.FinishedTransactionSubmissionRound"></a>

## FinishedTransactionSubmissionRound Objects

```python
class FinishedTransactionSubmissionRound(DegenerateRound, ABC)
```

A round that represents the transition to the ResetAndPauseRound

<a id="packages.valory.skills.transaction_settlement_abci.rounds.ResetRound"></a>

## ResetRound Objects

```python
class ResetRound(CollectSameUntilThresholdRound)
```

A round that represents the reset of a period

<a id="packages.valory.skills.transaction_settlement_abci.rounds.ResetRound.end_block"></a>

#### end`_`block

```python
def end_block() -> Optional[Tuple[BaseSynchronizedData, Event]]
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
        - round timeout: 0.
        - no majority: 0.
    1. SelectKeeperTransactionSubmissionARound
        - done: 2.
        - round timeout: 1.
        - no majority: 10.
        - incorrect serialization: 12.
    2. CollectSignatureRound
        - done: 3.
        - round timeout: 2.
        - no majority: 10.
    3. FinalizationRound
        - done: 4.
        - check history: 5.
        - finalize timeout: 7.
        - finalization failed: 6.
        - check late arriving message: 8.
        - insufficient funds: 6.
    4. ValidateTransactionRound
        - done: 11.
        - negative: 5.
        - none: 6.
        - validate timeout: 5.
        - no majority: 4.
    5. CheckTransactionHistoryRound
        - done: 11.
        - negative: 6.
        - none: 12.
        - check timeout: 5.
        - no majority: 5.
        - check late arriving message: 8.
    6. SelectKeeperTransactionSubmissionBRound
        - done: 3.
        - round timeout: 6.
        - no majority: 10.
        - incorrect serialization: 12.
    7. SelectKeeperTransactionSubmissionBAfterTimeoutRound
        - done: 3.
        - check history: 5.
        - check late arriving message: 8.
        - round timeout: 7.
        - no majority: 10.
        - incorrect serialization: 12.
    8. SynchronizeLateMessagesRound
        - done: 9.
        - round timeout: 8.
        - none: 6.
        - suspicious activity: 12.
    9. CheckLateTxHashesRound
        - done: 11.
        - negative: 12.
        - none: 12.
        - check timeout: 9.
        - no majority: 12.
        - check late arriving message: 8.
    10. ResetRound
        - done: 0.
        - reset timeout: 12.
        - no majority: 12.
    11. FinishedTransactionSubmissionRound
    12. FailedRound

Final states: {FailedRound, FinishedTransactionSubmissionRound}

Timeouts:
    round timeout: 30.0
    finalize timeout: 30.0
    validate timeout: 30.0
    check timeout: 30.0
    reset timeout: 30.0

