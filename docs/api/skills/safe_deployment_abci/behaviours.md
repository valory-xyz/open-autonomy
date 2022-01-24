<a id="packages.valory.skills.safe_deployment_abci.behaviours"></a>

# packages.valory.skills.safe`_`deployment`_`abci.behaviours

This module contains the data classes for the safe deployment ABCI application.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.SafeDeploymentBaseState"></a>

## SafeDeploymentBaseState Objects

```python
class SafeDeploymentBaseState(BaseState)
```

Base state behaviour for the common apps' skill.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.SafeDeploymentBaseState.period_state"></a>

#### period`_`state

```python
@property
def period_state() -> PeriodState
```

Return the period state.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.RandomnessSafeBehaviour"></a>

## RandomnessSafeBehaviour Objects

```python
class RandomnessSafeBehaviour(RandomnessBehaviour)
```

Retrieve randomness for oracle deployment.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.SelectKeeperSafeBehaviour"></a>

## SelectKeeperSafeBehaviour Objects

```python
class SelectKeeperSafeBehaviour(SelectKeeperBehaviour)
```

Select the keeper agent.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.DeploySafeBehaviour"></a>

## DeploySafeBehaviour Objects

```python
class DeploySafeBehaviour(SafeDeploymentBaseState)
```

Deploy Safe.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.DeploySafeBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- If the agent is the designated deployer, then prepare the deployment
  transaction and send it.
- Otherwise, wait until the next round.
- If a timeout is hit, set exit A event, otherwise set done event.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.ValidateSafeBehaviour"></a>

## ValidateSafeBehaviour Objects

```python
class ValidateSafeBehaviour(SafeDeploymentBaseState)
```

Validate Safe.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.ValidateSafeBehaviour.async_act"></a>

#### async`_`act

```python
def async_act() -> Generator
```

Do the action.

Steps:
- Validate that the contract address provided by the keeper points to a
  valid contract.
- Send the transaction with the validation result and wait for it to be
  mined.
- Wait until ABCI application transitions to the next round.
- Go to the next behaviour state (set done event).

<a id="packages.valory.skills.safe_deployment_abci.behaviours.ValidateSafeBehaviour.has_correct_contract_been_deployed"></a>

#### has`_`correct`_`contract`_`been`_`deployed

```python
def has_correct_contract_been_deployed() -> Generator[None, None, bool]
```

Contract deployment verification.

<a id="packages.valory.skills.safe_deployment_abci.behaviours.SafeDeploymentRoundBehaviour"></a>

## SafeDeploymentRoundBehaviour Objects

```python
class SafeDeploymentRoundBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the safe deployment.

