<a id="autonomy.data.packages.valory.contracts.registries_manager.contract"></a>

# autonomy.data.packages.valory.contracts.registries`_`manager.contract

This module contains the class to connect to the Service Registry contract.

<a id="autonomy.data.packages.valory.contracts.registries_manager.contract.RegistriesManagerContract"></a>

## RegistriesManagerContract Objects

```python
class RegistriesManagerContract(Contract)
```

The Service Registry contract.

<a id="autonomy.data.packages.valory.contracts.registries_manager.contract.RegistriesManagerContract.UnitType"></a>

## UnitType Objects

```python
class UnitType(Enum)
```

Unit type.

<a id="autonomy.data.packages.valory.contracts.registries_manager.contract.RegistriesManagerContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any) -> Optional[JSONLike]
```

Get the Safe transaction.

<a id="autonomy.data.packages.valory.contracts.registries_manager.contract.RegistriesManagerContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any) -> Optional[bytes]
```

Get raw message.

<a id="autonomy.data.packages.valory.contracts.registries_manager.contract.RegistriesManagerContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any) -> Optional[JSONLike]
```

Get state.

<a id="autonomy.data.packages.valory.contracts.registries_manager.contract.RegistriesManagerContract.create"></a>

#### create

```python
@classmethod
def create(cls, ledger_api: LedgerApi, contract_address: str, component_type: UnitType, metadata_hash: str, owner: str, dependencies: Optional[List[int]] = None) -> None
```

Create a component.

