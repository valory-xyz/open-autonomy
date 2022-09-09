<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours"></a>

# packages.valory.skills.oracle`_`deployment`_`abci.tests.test`_`behaviours

Tests for valory/registration_abci skill's behaviours.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.OracleDeploymentAbciBaseCase"></a>

## OracleDeploymentAbciBaseCase Objects

```python
class OracleDeploymentAbciBaseCase(FSMBehaviourBaseCase)
```

Base case for testing PriceEstimation FSMBehaviour.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.TestRandomnessOracle"></a>

## TestRandomnessOracle Objects

```python
class TestRandomnessOracle(BaseRandomnessBehaviourTest)
```

Test randomness safe.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.TestSelectKeeperOracleBehaviour"></a>

## TestSelectKeeperOracleBehaviour Objects

```python
class TestSelectKeeperOracleBehaviour(BaseSelectKeeperBehaviourTest)
```

Test SelectKeeperBehaviour.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.BaseDeployBehaviourTest"></a>

## BaseDeployBehaviourTest Objects

```python
class BaseDeployBehaviourTest(FSMBehaviourBaseCase)
```

Base DeployBehaviourTest.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.BaseDeployBehaviourTest.test_deployer_act"></a>

#### test`_`deployer`_`act

```python
def test_deployer_act() -> None
```

Run tests.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.BaseDeployBehaviourTest.test_not_deployer_act"></a>

#### test`_`not`_`deployer`_`act

```python
def test_not_deployer_act() -> None
```

Run tests.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.TestDeployOracleBehaviour"></a>

## TestDeployOracleBehaviour Objects

```python
class TestDeployOracleBehaviour(BaseDeployBehaviourTest,  OracleDeploymentAbciBaseCase)
```

Test DeployOracleBehaviour.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.BaseValidateBehaviourTest"></a>

## BaseValidateBehaviourTest Objects

```python
class BaseValidateBehaviourTest(FSMBehaviourBaseCase)
```

Test ValidateSafeBehaviour.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.BaseValidateBehaviourTest.test_validate_behaviour"></a>

#### test`_`validate`_`behaviour

```python
def test_validate_behaviour() -> None
```

Run test.

<a id="packages.valory.skills.oracle_deployment_abci.tests.test_behaviours.TestValidateOracleBehaviour"></a>

## TestValidateOracleBehaviour Objects

```python
class TestValidateOracleBehaviour(
    BaseValidateBehaviourTest,  OracleDeploymentAbciBaseCase)
```

Test ValidateOracleBehaviour.

