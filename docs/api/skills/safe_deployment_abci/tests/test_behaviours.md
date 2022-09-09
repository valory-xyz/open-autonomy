<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours"></a>

# packages.valory.skills.safe`_`deployment`_`abci.tests.test`_`behaviours

Tests for valory/registration_abci skill's behaviours.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.BaseValidateBehaviourTest"></a>

## BaseValidateBehaviourTest Objects

```python
class BaseValidateBehaviourTest(FSMBehaviourBaseCase)
```

Test ValidateSafeBehaviour.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.BaseValidateBehaviourTest.test_validate_behaviour"></a>

#### test`_`validate`_`behaviour

```python
def test_validate_behaviour() -> None
```

Run test.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.BaseDeployBehaviourTest"></a>

## BaseDeployBehaviourTest Objects

```python
class BaseDeployBehaviourTest(FSMBehaviourBaseCase)
```

Base DeployBehaviourTest.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.BaseDeployBehaviourTest.test_deployer_act"></a>

#### test`_`deployer`_`act

```python
def test_deployer_act() -> None
```

Run tests.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.BaseDeployBehaviourTest.test_not_deployer_act"></a>

#### test`_`not`_`deployer`_`act

```python
def test_not_deployer_act() -> None
```

Run tests.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.SafeDeploymentAbciBaseCase"></a>

## SafeDeploymentAbciBaseCase Objects

```python
class SafeDeploymentAbciBaseCase(FSMBehaviourBaseCase)
```

Base case for testing PriceEstimation FSMBehaviour.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.TestRandomnessSafe"></a>

## TestRandomnessSafe Objects

```python
class TestRandomnessSafe(BaseRandomnessBehaviourTest)
```

Test randomness safe.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.TestSelectKeeperSafeBehaviour"></a>

## TestSelectKeeperSafeBehaviour Objects

```python
class TestSelectKeeperSafeBehaviour(BaseSelectKeeperBehaviourTest)
```

Test SelectKeeperBehaviour.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.TestDeploySafeBehaviour"></a>

## TestDeploySafeBehaviour Objects

```python
class TestDeploySafeBehaviour(BaseDeployBehaviourTest,  SafeDeploymentAbciBaseCase)
```

Test DeploySafeBehaviour.

<a id="packages.valory.skills.safe_deployment_abci.tests.test_behaviours.TestValidateSafeBehaviour"></a>

## TestValidateSafeBehaviour Objects

```python
class TestValidateSafeBehaviour(BaseValidateBehaviourTest,  SafeDeploymentAbciBaseCase)
```

Test ValidateSafeBehaviour.

