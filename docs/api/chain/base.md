<a id="autonomy.chain.base"></a>

# autonomy.chain.base

Chain interaction base classes.

<a id="autonomy.chain.base.get_abi"></a>

#### get`_`abi

```python
def get_abi(filename: str) -> Dict
```

Service contract ABI.

<a id="autonomy.chain.base.BaseContract"></a>

## BaseContract Objects

```python
class BaseContract()
```

Base contract interface.

<a id="autonomy.chain.base.BaseContract.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_api: LedgerApi, contract_config: ContractConfig, crypto: Crypto) -> None
```

Initialize contract interface.

<a id="autonomy.chain.base.BaseContract.contract"></a>

#### contract

```python
@property
def contract() -> ContractInterfaceType
```

Contract interface.

<a id="autonomy.chain.base.RegistryManager"></a>

## RegistryManager Objects

```python
class RegistryManager(BaseContract)
```

Registry manager contract interface.

<a id="autonomy.chain.base.RegistryManager.UnitType"></a>

## UnitType Objects

```python
class UnitType(Enum)
```

Unit type.

<a id="autonomy.chain.base.RegistryManager.create"></a>

#### create

```python
def create(component_type: UnitType, metadata_hash: str, owner: Optional[str] = None, dependencies: Optional[List[int]] = None) -> None
```

Create component.

<a id="autonomy.chain.base.ComponentRegistry"></a>

## ComponentRegistry Objects

```python
class ComponentRegistry(BaseContract)
```

Component registry contract interface.

<a id="autonomy.chain.base.ComponentRegistry.get_create_unit_event_filter"></a>

#### get`_`create`_`unit`_`event`_`filter

```python
def get_create_unit_event_filter() -> Iterable[Dict]
```

Returns `CreateUnit` event filter.

