<a id="autonomy.chain.base"></a>

# autonomy.chain.base

Chain interaction base classes.

<a id="autonomy.chain.base.UnitType"></a>

## UnitType Objects

```python
class UnitType(Enum)
```

Unit type

Same as https://github.com/valory-xyz/autonolas-registries/blob/v1.0.1/contracts/interfaces/IRegistry.sol#L6-L9

<a id="autonomy.chain.base.ServiceState"></a>

## ServiceState Objects

```python
class ServiceState(Enum)
```

Service state

Same as https://github.com/valory-xyz/autonolas-registries/blob/v1.0.1/contracts/ServiceRegistry.sol#L41-L48

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
def get_contract(public_id: PublicId, cache: bool = True) -> Contract
```

Load contract for given public id.

<a id="autonomy.chain.base.RegistryContracts.registries_manager"></a>

#### registries`_`manager

```python
@property
def registries_manager() -> Contract
```

Returns an instance of the registries manager contract.

<a id="autonomy.chain.base.RegistryContracts.service_manager"></a>

#### service`_`manager

```python
@property
def service_manager() -> Contract
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

<a id="autonomy.chain.base.RegistryContracts.service_registry"></a>

#### service`_`registry

```python
@property
def service_registry() -> Contract
```

Returns an instance of the registries manager contract.

<a id="autonomy.chain.base.RegistryContracts.service_registry_token_utility"></a>

#### service`_`registry`_`token`_`utility

```python
@property
def service_registry_token_utility() -> Contract
```

Returns an instance of the service registry token utility contract.

<a id="autonomy.chain.base.RegistryContracts.erc20"></a>

#### erc20

```python
@property
def erc20() -> Contract
```

Returns an instance of the service registry token utility contract.

<a id="autonomy.chain.base.RegistryContracts.gnosis_safe"></a>

#### gnosis`_`safe

```python
@property
def gnosis_safe() -> Contract
```

Returns an instance of the service registry token utility contract.

<a id="autonomy.chain.base.RegistryContracts.gnosis_safe_proxy_factory"></a>

#### gnosis`_`safe`_`proxy`_`factory

```python
@property
def gnosis_safe_proxy_factory() -> Contract
```

Returns an instance of the service registry token utility contract.

<a id="autonomy.chain.base.RegistryContracts.multisend"></a>

#### multisend

```python
@property
def multisend() -> Contract
```

Returns an instance of the service registry token utility contract.

