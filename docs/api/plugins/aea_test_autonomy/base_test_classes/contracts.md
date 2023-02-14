<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts"></a>

# plugins.aea-test-autonomy.aea`_`test`_`autonomy.base`_`test`_`classes.contracts

Base test classes.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseContractTest"></a>

## BaseContractTest Objects

```python
class BaseContractTest(ABC)
```

Base test class for contract tests.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseContractTest.deploy"></a>

#### deploy

```python
@classmethod
def deploy(cls, **kwargs: Any) -> None
```

Deploy the contract.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseContractTest.deployment_kwargs"></a>

#### deployment`_`kwargs

```python
@classmethod
def deployment_kwargs(cls) -> Dict[str, Any]
```

Get deployment kwargs.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseGanacheContractTest"></a>

## BaseGanacheContractTest Objects

```python
class BaseGanacheContractTest(BaseContractTest, GanacheBaseTest)
```

Base test case for testing contracts on Ganache.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseHardhatGnosisContractTest"></a>

## BaseHardhatGnosisContractTest Objects

```python
class BaseHardhatGnosisContractTest(BaseContractTest, HardHatGnosisBaseTest)
```

Base test case for testing contracts on Hardhat with Gnosis.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseHardhatAMMContractTest"></a>

## BaseHardhatAMMContractTest Objects

```python
class BaseHardhatAMMContractTest(BaseContractTest, HardHatAMMBaseTest)
```

Base test case for testing AMM contracts on Hardhat.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseRegistriesContractsTest"></a>

## BaseRegistriesContractsTest Objects

```python
class BaseRegistriesContractsTest(BaseContractTest, RegistriesBaseTest)
```

Base test case for the registries contract.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseContractWithDependencyTest"></a>

## BaseContractWithDependencyTest Objects

```python
class BaseContractWithDependencyTest(BaseContractTest)
```

Base test contract with contract dependencies

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseGanacheContractWithDependencyTest"></a>

## BaseGanacheContractWithDependencyTest Objects

```python
class BaseGanacheContractWithDependencyTest(BaseContractWithDependencyTest,
                                            GanacheBaseTest)
```

Base test case for testing contracts with dependencies on Ganache.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseHardhatGnosisContractWithDependencyTest"></a>

## BaseHardhatGnosisContractWithDependencyTest Objects

```python
class BaseHardhatGnosisContractWithDependencyTest(
        BaseContractWithDependencyTest, HardHatGnosisBaseTest)
```

Base test case for testing contracts with dependencies on Hardhat with Gnosis.

<a id="plugins.aea-test-autonomy.aea_test_autonomy.base_test_classes.contracts.BaseHardhatAMMContractWithDependencyTest"></a>

## BaseHardhatAMMContractWithDependencyTest Objects

```python
class BaseHardhatAMMContractWithDependencyTest(BaseContractWithDependencyTest,
                                               HardHatAMMBaseTest)
```

Base test case for testing AMM contracts with dependencies on Hardhat.

