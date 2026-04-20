<a id="packages.valory.contracts.gnosis_safe_proxy_factory.tests.test_contract"></a>

# packages.valory.contracts.gnosis`_`safe`_`proxy`_`factory.tests.test`_`contract

Tests for valory/gnosis contract.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.tests.test_contract.TestGnosisSafeProxyFactory"></a>

## TestGnosisSafeProxyFactory Objects

```python
@skip_docker_tests
class TestGnosisSafeProxyFactory(BaseGanacheContractTest)
```

Test deployment of the proxy to Ganache.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.tests.test_contract.TestGnosisSafeProxyFactory.deployment_kwargs"></a>

#### deployment`_`kwargs

```python
@classmethod
def deployment_kwargs(cls) -> Dict[str, Any]
```

Get deployment kwargs.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.tests.test_contract.TestGnosisSafeProxyFactory.test_deploy"></a>

#### test`_`deploy

```python
def test_deploy() -> None
```

Test deployment results.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.tests.test_contract.TestGnosisSafeProxyFactory.test_build_tx_deploy_proxy_contract_with_nonce"></a>

#### test`_`build`_`tx`_`deploy`_`proxy`_`contract`_`with`_`nonce

```python
def test_build_tx_deploy_proxy_contract_with_nonce() -> None
```

Test build_tx_deploy_proxy_contract_with_nonce method.

<a id="packages.valory.contracts.gnosis_safe_proxy_factory.tests.test_contract.TestGnosisSafeProxyFactory.test_verify"></a>

#### test`_`verify

```python
def test_verify() -> None
```

Test verification of deployed contract results.

