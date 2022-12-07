<a id="autonomy.chain.base"></a>

# autonomy.chain.base

Chain interaction base classes.

<a id="autonomy.chain.base.BaseContract"></a>

## BaseContract Objects

```python
class BaseContract()
```

Base contract interface.

<a id="autonomy.chain.base.BaseContract.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_api: LedgerApi, crypto: Crypto, chain_type: ChainType) -> None
```

Initialize contract interface.

<a id="autonomy.chain.base.BaseContract.contract"></a>

#### contract

```python
@property
def contract() -> ContractInterfaceType
```

Contract interface.

<a id="autonomy.chain.base.RegistriesManager"></a>

## RegistriesManager Objects

```python
class RegistriesManager(BaseContract)
```

Registry manager contract interface.

<a id="autonomy.chain.base.RegistriesManager.UnitType"></a>

## UnitType Objects

```python
class UnitType(Enum)
```

Unit type.

<a id="autonomy.chain.base.RegistriesManager.create"></a>

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

