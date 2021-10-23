<a id="packages.valory.skills.price_estimation_abci.behaviours"></a>

# packages.valory.skills.price`_`estimation`_`abci.behaviours

This module contains the behaviours for the 'abci' skill.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseState"></a>

## PriceEstimationBaseState Objects

```python
class PriceEstimationBaseState(BaseState,  ABC)
```

Base state behaviour for the price estimation skill.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseState.period_state"></a>

#### period`_`state

```python
@property
def period_state() -> PeriodState
```

Return the period state.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseState.params"></a>

#### params

```python
@property
def params() -> Params
```

Return the params.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationBaseState.shared_state"></a>

#### shared`_`state

```python
@property
def shared_state() -> SharedState
```

Return the shared state.

<a id="packages.valory.skills.price_estimation_abci.behaviours.TendermintHealthcheckBehaviour"></a>

## TendermintHealthcheckBehaviour Objects

```python
class TendermintHealthcheckBehaviour(PriceEstimationBaseState)
```

Check whether Tendermint nodes are running.

<a id="packages.valory.skills.price_estimation_abci.behaviours.TendermintHealthcheckBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Check whether tendermint is running or not.

Steps:
- Do a http request to the tendermint health check endpoint
- Retry until healthcheck passes or timeout is hit. Raise if timed out.
- If healthcheck passes set done event.

<a id="packages.valory.skills.price_estimation_abci.behaviours.RegistrationBehaviour"></a>

## RegistrationBehaviour Objects

```python
class RegistrationBehaviour(PriceEstimationBaseState)
```

Register to the next round.

<a id="packages.valory.skills.price_estimation_abci.behaviours.RegistrationBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Build a registration transaction.
- Send the transaction and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.RandomnessBehaviour"></a>

## RandomnessBehaviour Objects

```python
class RandomnessBehaviour(PriceEstimationBaseState)
```

Check whether Tendermint nodes are running.

<a id="packages.valory.skills.price_estimation_abci.behaviours.RandomnessBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Check whether tendermint is running or not.

Steps:
- Do a http request to the tendermint health check endpoint
- Retry until healthcheck passes or timeout is hit. Raise if timed out.
- If healthcheck passes set done event.

<a id="packages.valory.skills.price_estimation_abci.behaviours.SelectKeeperBehaviour"></a>

## SelectKeeperBehaviour Objects

```python
class SelectKeeperBehaviour(PriceEstimationBaseState,  ABC)
```

Select the keeper agent.

<a id="packages.valory.skills.price_estimation_abci.behaviours.SelectKeeperBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Select a keeper randomly.
- Send the transaction with the keeper and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.SelectKeeperABehaviour"></a>

## SelectKeeperABehaviour Objects

```python
class SelectKeeperABehaviour(SelectKeeperBehaviour)
```

Select the keeper agent.

<a id="packages.valory.skills.price_estimation_abci.behaviours.SelectKeeperBBehaviour"></a>

## SelectKeeperBBehaviour Objects

```python
class SelectKeeperBBehaviour(SelectKeeperBehaviour)
```

Select the keeper agent.

<a id="packages.valory.skills.price_estimation_abci.behaviours.DeploySafeBehaviour"></a>

## DeploySafeBehaviour Objects

```python
class DeploySafeBehaviour(PriceEstimationBaseState)
```

Deploy Safe.

<a id="packages.valory.skills.price_estimation_abci.behaviours.DeploySafeBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- If the agent is the designated deployer, then prepare the deployment transaction and send it.
- Otherwise, wait until the next round.
- If a timeout is hit, set exit A event, otherwise set done event.

<a id="packages.valory.skills.price_estimation_abci.behaviours.ValidateSafeBehaviour"></a>

## ValidateSafeBehaviour Objects

```python
class ValidateSafeBehaviour(PriceEstimationBaseState)
```

ValidateSafe.

<a id="packages.valory.skills.price_estimation_abci.behaviours.ValidateSafeBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Validate that the contract address provided by the keeper points to a valid contract.
- Send the transaction with the validation result and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.ValidateSafeBehaviour.has_correct_contract_been_deployed"></a>

#### has`_`correct`_`contract`_`been`_`deployed

```python
def has_correct_contract_been_deployed() -> Generator[None, None, bool]
```

Contract deployment verification.

<a id="packages.valory.skills.price_estimation_abci.behaviours.ObserveBehaviour"></a>

## ObserveBehaviour Objects

```python
class ObserveBehaviour(PriceEstimationBaseState)
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
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.WaitBehaviour"></a>

## WaitBehaviour Objects

```python
class WaitBehaviour(PriceEstimationBaseState)
```

Wait behaviour.

This behaviour is used to regroup the agents after a failure.

<a id="packages.valory.skills.price_estimation_abci.behaviours.WaitBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

<a id="packages.valory.skills.price_estimation_abci.behaviours.EstimateBehaviour"></a>

## EstimateBehaviour Objects

```python
class EstimateBehaviour(PriceEstimationBaseState)
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
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.TransactionHashBehaviour"></a>

## TransactionHashBehaviour Objects

```python
class TransactionHashBehaviour(PriceEstimationBaseState)
```

Share the transaction hash for the signature round.

<a id="packages.valory.skills.price_estimation_abci.behaviours.TransactionHashBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Request the transaction hash for the safe transaction. This is the hash that needs to be signed by a threshold of agents.
- Send the transaction hash as a transaction and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.SignatureBehaviour"></a>

## SignatureBehaviour Objects

```python
class SignatureBehaviour(PriceEstimationBaseState)
```

Signature state.

<a id="packages.valory.skills.price_estimation_abci.behaviours.SignatureBehaviour.async_act"></a>

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

<a id="packages.valory.skills.price_estimation_abci.behaviours.FinalizeBehaviour"></a>

## FinalizeBehaviour Objects

```python
class FinalizeBehaviour(PriceEstimationBaseState)
```

Finalize state.

<a id="packages.valory.skills.price_estimation_abci.behaviours.FinalizeBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator[None, None, None]
```

Do the action.

Steps:
- If the agent is the keeper, then prepare the transaction and send it.
- Otherwise, wait until the next round.
- If a timeout is hit, set exit A event, otherwise set done event.

<a id="packages.valory.skills.price_estimation_abci.behaviours.ValidateTransactionBehaviour"></a>

## ValidateTransactionBehaviour Objects

```python
class ValidateTransactionBehaviour(PriceEstimationBaseState)
```

ValidateTransaction.

<a id="packages.valory.skills.price_estimation_abci.behaviours.ValidateTransactionBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Validate that the transaction hash provided by the keeper points to a valid transaction.
- Send the transaction with the validation result and wait for it to be mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.price_estimation_abci.behaviours.ValidateTransactionBehaviour.has_transaction_been_sent"></a>

#### has`_`transaction`_`been`_`sent

```python
def has_transaction_been_sent() -> Generator[None, None, bool]
```

Contract deployment verification.

<a id="packages.valory.skills.price_estimation_abci.behaviours.EndBehaviour"></a>

## EndBehaviour Objects

```python
class EndBehaviour(PriceEstimationBaseState)
```

Final state.

<a id="packages.valory.skills.price_estimation_abci.behaviours.EndBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Trivially log the state.

<a id="packages.valory.skills.price_estimation_abci.behaviours.PriceEstimationConsensusBehaviour"></a>

## PriceEstimationConsensusBehaviour Objects

```python
class PriceEstimationConsensusBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the price estimation.

