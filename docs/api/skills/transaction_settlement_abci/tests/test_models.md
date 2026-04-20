<a id="packages.valory.skills.transaction_settlement_abci.tests.test_models"></a>

# packages.valory.skills.transaction`_`settlement`_`abci.tests.test`_`models

Test the models.py module of the skill.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_models.TestTransactionParams"></a>

## TestTransactionParams Objects

```python
class TestTransactionParams()
```

Test TransactionParams class.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_models.TestTransactionParams.setup_class"></a>

#### setup`_`class

```python
def setup_class() -> None
```

Read the default config only once.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_models.TestTransactionParams.test_ensure_validate_timeout"></a>

#### test`_`ensure`_`validate`_`timeout

```python
def test_ensure_validate_timeout() -> None
```

Test that `_ensure_validate_timeout` raises when `validate_timeout` is lower than the allowed minimum.

<a id="packages.valory.skills.transaction_settlement_abci.tests.test_models.TestTransactionParams.test_gas_params"></a>

#### test`_`gas`_`params

```python
@pytest.mark.parametrize(
    "gas_params",
    [
        {},
        {
            "gas_price": 1
        },
        {
            "max_fee_per_gas": 1
        },
        {
            "max_priority_fee_per_gas": 1
        },
        {
            "gas_price": 1,
            "max_fee_per_gas": 1,
            "max_priority_fee_per_gas": 1,
        },
    ],
)
def test_gas_params(gas_params: Dict[str, Any]) -> None
```

Test that gas params are being handled properly.

