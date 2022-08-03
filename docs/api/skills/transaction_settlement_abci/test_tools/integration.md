<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.test`_`tools.integration

Integration tests for various transaction settlement skill's failure modes.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._SafeConfiguredHelperIntegration"></a>

## `_`SafeConfiguredHelperIntegration Objects

```python
class _SafeConfiguredHelperIntegration(IntegrationBaseCase)
```

Base test class for integration tests with Gnosis, but no contract, deployed.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._SafeConfiguredHelperIntegration.setup"></a>

#### setup

```python
@classmethod
def setup(cls, **kwargs: Any) -> None
```

Setup.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._GnosisHelperIntegration"></a>

## `_`GnosisHelperIntegration Objects

```python
class _GnosisHelperIntegration(_SafeConfiguredHelperIntegration)
```

Class that assists Gnosis instantiation.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._GnosisHelperIntegration.setup"></a>

#### setup

```python
@classmethod
def setup(cls, **kwargs: Any) -> None
```

Setup.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._TxHelperIntegration"></a>

## `_`TxHelperIntegration Objects

```python
class _TxHelperIntegration(_GnosisHelperIntegration)
```

Class that assists tx settlement related operations.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._TxHelperIntegration.sign_tx"></a>

#### sign`_`tx

```python
def sign_tx() -> None
```

Sign a transaction

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._TxHelperIntegration.send_tx"></a>

#### send`_`tx

```python
def send_tx(simulate_timeout: bool = False) -> None
```

Send a transaction

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._TxHelperIntegration.validate_tx"></a>

#### validate`_`tx

```python
def validate_tx(simulate_timeout: bool = False, mining_interval_secs: float = 0) -> None
```

Validate the sent transaction.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration.GnosisIntegrationBaseCase"></a>

## GnosisIntegrationBaseCase Objects

```python
class GnosisIntegrationBaseCase(
    _TxHelperIntegration,  _HarHatHelperIntegration,  HardHatAMMBaseTest)
```

Base test class for integration tests in a Hardhat environment, with Gnosis deployed.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration.GnosisIntegrationBaseCase.setup"></a>

#### setup

```python
@classmethod
def setup(cls, **kwargs: Any) -> None
```

Setup.

