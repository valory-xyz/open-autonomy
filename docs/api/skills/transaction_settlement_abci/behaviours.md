<a id="packages.valory.skills.transaction_settlement_abci.behaviours"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.behaviours

This module contains the behaviours for the 'abci' skill.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.TransactionSettlementBaseState"></a>

## TransactionSettlementBaseState Objects

```python
class TransactionSettlementBaseState(BaseState,  ABC)
```

Base state behaviour for the common apps' skill.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.TransactionSettlementBaseState.period_state"></a>

#### period`_`state

```python
@property
def period_state() -> PeriodState
```

Return the period state.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.TransactionSettlementBaseState.params"></a>

#### params

```python
@property
def params() -> TransactionParams
```

Return the params.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.TransactionSettlementBaseState.serialized_keepers"></a>

#### serialized`_`keepers

```python
@staticmethod
def serialized_keepers(keepers: Deque[str], keeper_retries: int) -> str
```

Get the keepers serialized.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.RandomnessTransactionSubmissionBehaviour"></a>

## RandomnessTransactionSubmissionBehaviour Objects

```python
class RandomnessTransactionSubmissionBehaviour(RandomnessBehaviour)
```

Retrieve randomness.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SelectKeeperTransactionSubmissionBehaviourA"></a>

## SelectKeeperTransactionSubmissionBehaviourA Objects

```python
class SelectKeeperTransactionSubmissionBehaviourA(  # pylint: disable=too-many-ancestors
    SelectKeeperBehaviour,  TransactionSettlementBaseState)
```

Select the keeper agent.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SelectKeeperTransactionSubmissionBehaviourA.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SelectKeeperTransactionSubmissionBehaviourB"></a>

## SelectKeeperTransactionSubmissionBehaviourB Objects

```python
class SelectKeeperTransactionSubmissionBehaviourB(  # pylint: disable=too-many-ancestors
    SelectKeeperTransactionSubmissionBehaviourA)
```

Select the keeper b agent.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SelectKeeperTransactionSubmissionBehaviourB.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
    - If we have not selected enough keepers for the period,
        select a keeper randomly and add it to the keepers' queue, with top priority.
    - Otherwise, cycle through the keepers' subset, using the following logic:
        A `PENDING` verification status means that we have not received any errors,
        therefore, all we know is that the tx has not been mined yet due to low pricing.
        Consequently, we are going to retry with the same keeper in order to replace the transaction.
        However, if we receive a status other than `PENDING`, we need to cycle through the keepers' subset.
        Moreover, if the current keeper has reached the allowed number of retries, then we cycle anyway.
    - Send the transaction with the keepers and wait for it to be mined.
    - Wait until ABCI application transitions to the next round.
    - Go to the next behaviour state (set done event).

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SelectKeeperTransactionSubmissionBehaviourBAfterTimeout"></a>

## SelectKeeperTransactionSubmissionBehaviourBAfterTimeout Objects

```python
class SelectKeeperTransactionSubmissionBehaviourBAfterTimeout(  # pylint: disable=too-many-ancestors
    SelectKeeperTransactionSubmissionBehaviourB)
```

Select the keeper b agent after a timeout.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.ValidateTransactionBehaviour"></a>

## ValidateTransactionBehaviour Objects

```python
class ValidateTransactionBehaviour(TransactionSettlementBaseState)
```

Validate a transaction.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.ValidateTransactionBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Validate that the transaction hash provided by the keeper points to a
  valid transaction.
- Send the transaction with the validation result and wait for it to be
  mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.ValidateTransactionBehaviour.has_transaction_been_sent"></a>

#### has`_`transaction`_`been`_`sent

```python
def has_transaction_been_sent() -> Generator[None, None, Optional[bool]]
```

Transaction verification.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.CheckTransactionHistoryBehaviour"></a>

## CheckTransactionHistoryBehaviour Objects

```python
class CheckTransactionHistoryBehaviour(TransactionSettlementBaseState)
```

Check the transaction history.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.CheckTransactionHistoryBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.CheckLateTxHashesBehaviour"></a>

## CheckLateTxHashesBehaviour Objects

```python
class CheckLateTxHashesBehaviour(  # pylint: disable=too-many-ancestors
    CheckTransactionHistoryBehaviour)
```

Check the late-arriving transaction hashes.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SynchronizeLateMessagesBehaviour"></a>

## SynchronizeLateMessagesBehaviour Objects

```python
class SynchronizeLateMessagesBehaviour(TransactionSettlementBaseState)
```

Synchronize late-arriving messages state.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SynchronizeLateMessagesBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any)
```

Initialize a `SynchronizeLateMessagesBehaviour`

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SynchronizeLateMessagesBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SynchronizeLateMessagesBehaviour.clean_up"></a>

#### clean`_`up

```python
def clean_up() -> None
```

Clean up the behaviour.

Clean the local `tx_hash` and `late_messages` parameters if we were able to complete the round,
and have therefore been synced.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SignatureBehaviour"></a>

## SignatureBehaviour Objects

```python
class SignatureBehaviour(TransactionSettlementBaseState)
```

Signature state.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SignatureBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Request the signature of the transaction hash.
- Send the signature as a transaction and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.FinalizeBehaviour"></a>

## FinalizeBehaviour Objects

```python
class FinalizeBehaviour(TransactionSettlementBaseState)
```

Finalize state.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.FinalizeBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator[None, None, None]
```

Do the action.

Steps:
- If the agent is the keeper, then prepare the transaction and send it.
- Otherwise, wait until the next round.
- If a timeout is hit, set exit A event, otherwise set done event.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.FinalizeBehaviour.clean_up"></a>

#### clean`_`up

```python
def clean_up() -> None
```

Clean the local tx hash parameter if we were able to complete the round, and have therefore been synced.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.FinalizeBehaviour.handle_late_messages"></a>

#### handle`_`late`_`messages

```python
def handle_late_messages(message: Message) -> None
```

Store a potentially late-arriving message locally.

**Arguments**:

- `message`: the late arriving message to handle.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.ResetBehaviour"></a>

## ResetBehaviour Objects

```python
class ResetBehaviour(TransactionSettlementBaseState)
```

Reset state.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.ResetBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.TransactionSettlementRoundBehaviour"></a>

## TransactionSettlementRoundBehaviour Objects

```python
class TransactionSettlementRoundBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the basic transaction settlement.

