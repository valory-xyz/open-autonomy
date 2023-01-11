<a id="autonomy.chain.base"></a>

# autonomy.chain.base

Chain interaction base classes.

<a id="autonomy.chain.base.UnitType"></a>

## UnitType Objects

```python
class UnitType(Enum)
```

Unit type.

<a id="autonomy.chain.base.RegistryContracts"></a>

## RegistryContracts Objects

```python
class RegistryContracts()
```

On chain registry contracts helper

<a id="autonomy.chain.base.RegistryContracts.get_contract"></a>

#### get`_`contract

```python
@staticmethod
def get_contract(public_id: PublicId) -> Contract
```

Load contract for given public id.

<a id="autonomy.chain.base.RegistryContracts.registries_manager"></a>

#### registries`_`manager

```python
@property
def registries_manager() -> Contract
```

Returns an instance of the registries manager contract.

<a id="autonomy.chain.base.RegistryContracts.component_registry"></a>

#### component`_`registry

```python
@property
def component_registry() -> Contract
```

Returns an instance of the registries manager contract.

<a id="autonomy.chain.base.RegistryContracts.agent_registry"></a>

#### agent`_`registry

```python
@property
def agent_registry() -> Contract
```

Returns an instance of the registries manager contract.

