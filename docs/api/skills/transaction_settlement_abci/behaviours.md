<a id="packages.valory.skills.transaction_settlement_abci.behaviours"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.behaviours

This module contains the behaviours for the 'abci' skill.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.hex_to_payload"></a>

#### hex`_`to`_`payload

```python
def hex_to_payload(payload: str) -> Tuple[str, int, int, str, bytes]
```

Decode payload.

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

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.RandomnessTransactionSubmissionBehaviour"></a>

## RandomnessTransactionSubmissionBehaviour Objects

```python
class RandomnessTransactionSubmissionBehaviour(RandomnessBehaviour)
```

Retrieve randomness.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SelectKeeperTransactionSubmissionBehaviourA"></a>

## SelectKeeperTransactionSubmissionBehaviourA Objects

```python
class SelectKeeperTransactionSubmissionBehaviourA(SelectKeeperBehaviour)
```

Select the keeper agent.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.SelectKeeperTransactionSubmissionBehaviourB"></a>

## SelectKeeperTransactionSubmissionBehaviourB Objects

```python
class SelectKeeperTransactionSubmissionBehaviourB(SelectKeeperBehaviour)
```

Select the keeper agent.

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

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.BaseResetBehaviour"></a>

## BaseResetBehaviour Objects

```python
class BaseResetBehaviour(TransactionSettlementBaseState)
```

Reset state.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.BaseResetBehaviour.start_reset"></a>

#### start`_`reset

```python
def start_reset() -> Generator
```

Start tendermint reset.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.BaseResetBehaviour.end_reset"></a>

#### end`_`reset

```python
def end_reset() -> None
```

End tendermint reset.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.BaseResetBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Trivially log the state.
- Sleep for configured interval.
- Build a registration transaction.
- Send the transaction and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.ResetBehaviour"></a>

## ResetBehaviour Objects

```python
class ResetBehaviour(BaseResetBehaviour)
```

Reset state.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.ResetAndPauseBehaviour"></a>

## ResetAndPauseBehaviour Objects

```python
class ResetAndPauseBehaviour(BaseResetBehaviour)
```

Reset and pause state.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.TransactionSettlementConsensusBehaviour"></a>

## TransactionSettlementConsensusBehaviour Objects

```python
class TransactionSettlementConsensusBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the transaction settlement.

<a id="packages.valory.skills.transaction_settlement_abci.behaviours.TransactionSettlementConsensusBehaviour.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the behaviour.

