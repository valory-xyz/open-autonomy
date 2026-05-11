<a id="autonomy.data.contracts.recovery_module.contract"></a>

# autonomy.data.contracts.recovery`_`module.contract

This module contains the class to connect to the `RecoveryModule` contract.

<a id="autonomy.data.contracts.recovery_module.contract.RecoveryModule"></a>

## RecoveryModule Objects

```python
class RecoveryModule(Contract)
```

The RecoveryModule contract

<a id="autonomy.data.contracts.recovery_module.contract.RecoveryModule.get_recover_access_transaction"></a>

#### get`_`recover`_`access`_`transaction

```python
@classmethod
def get_recover_access_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        raise_on_try: bool = False) -> Dict[str, Any]
```

Get the recover access transaction.

