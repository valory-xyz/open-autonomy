<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.test`_`tools.integration

Integration tests for various transaction settlement skill's failure modes.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._SafeConfiguredHelperIntegration"></a>

## `_`SafeConfiguredHelperIntegration Objects

```python
class _SafeConfiguredHelperIntegration(IntegrationBaseCase, ABC)
```

Base test class for integration tests with Gnosis, but no contract, deployed.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._SafeConfiguredHelperIntegration.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls, **kwargs: Any) -> None
```

Setup.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._GnosisHelperIntegration"></a>

## `_`GnosisHelperIntegration Objects

```python
class _GnosisHelperIntegration(_SafeConfiguredHelperIntegration, ABC)
```

Class that assists Gnosis instantiation.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._GnosisHelperIntegration.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls, **kwargs: Any) -> None
```

Setup.

<a id="packages.valory.skills.transaction_settlement_abci.test_tools.integration._TxHelperIntegration"></a>

## `_`TxHelperIntegration Objects

```python
class _TxHelperIntegration(_GnosisHelperIntegration, ABC)
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
def validate_tx(simulate_timeout: bool = False,
                mining_interval_secs: float = 0) -> None
```

Validate the sent transaction.

