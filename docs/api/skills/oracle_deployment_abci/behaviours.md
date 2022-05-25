<a id="packages.valory.skills.oracle_deployment_abci.behaviours"></a>

# packages.valory.skills.oracle`_`deployment`_`abci.behaviours

This module contains the data classes for the oracle deployment ABCI application.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.OracleDeploymentBaseBehaviour"></a>

## OracleDeploymentBaseBehaviour Objects

```python
class OracleDeploymentBaseBehaviour(BaseBehaviour)
```

Base behaviour for the common apps' skill.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.OracleDeploymentBaseBehaviour.synchronized_data"></a>

#### synchronized`_`data

```python
@property
def synchronized_data() -> SynchronizedData
```

Return the synchronized data.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.OracleDeploymentBaseBehaviour.params"></a>

#### params

```python
@property
def params() -> Params
```

Return the synchronized data.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.RandomnessOracleBehaviour"></a>

## RandomnessOracleBehaviour Objects

```python
class RandomnessOracleBehaviour(RandomnessBehaviour)
```

Retrieve randomness for oracle deployment.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.SelectKeeperOracleBehaviour"></a>

## SelectKeeperOracleBehaviour Objects

```python
class SelectKeeperOracleBehaviour(SelectKeeperBehaviour)
```

Select the keeper agent.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.DeployOracleBehaviour"></a>

## DeployOracleBehaviour Objects

```python
class DeployOracleBehaviour(OracleDeploymentBaseBehaviour)
```

Deploy oracle.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.DeployOracleBehaviour.async_act"></a>

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

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.ValidateOracleBehaviour"></a>

## ValidateOracleBehaviour Objects

```python
class ValidateOracleBehaviour(OracleDeploymentBaseBehaviour)
```

Validate oracle.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.ValidateOracleBehaviour.async_act"></a>

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
- Go to the next behaviour (set done event).

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.ValidateOracleBehaviour.has_correct_contract_been_deployed"></a>

#### has`_`correct`_`contract`_`been`_`deployed

```python
def has_correct_contract_been_deployed() -> Generator[None, None, bool]
```

Contract deployment verification.

<a id="packages.valory.skills.oracle_deployment_abci.behaviours.OracleDeploymentRoundBehaviour"></a>

## OracleDeploymentRoundBehaviour Objects

```python
class OracleDeploymentRoundBehaviour(AbstractRoundBehaviour)
```

This behaviour manages the consensus stages for the oracle deployment.

