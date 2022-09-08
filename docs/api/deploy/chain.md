<a id="autonomy.deploy.chain"></a>

# autonomy.deploy.chain

Utils to support on-chain contract interactions.

<a id="autonomy.deploy.chain.get_abi"></a>

#### get`_`abi

```python
def get_abi(path: Path) -> Dict
```

Read the ABI from the provided path.

<a id="autonomy.deploy.chain.ServiceRegistry"></a>

## ServiceRegistry Objects

```python
class ServiceRegistry()
```

Class to represent on-chain service registry.

<a id="autonomy.deploy.chain.ServiceRegistry.__init__"></a>

#### `__`init`__`

```python
def __init__(chain_type: str = "staging", rpc_url: Optional[str] = None, service_contract_address: Optional[str] = None) -> None
```

Initialize object.

<a id="autonomy.deploy.chain.ServiceRegistry.resolve_token_id"></a>

#### resolve`_`token`_`id

```python
def resolve_token_id(token_id: int) -> Dict
```

Resolve token id using on-chain contracts.

<a id="autonomy.deploy.chain.ServiceRegistry.get_agent_instances"></a>

#### get`_`agent`_`instances

```python
def get_agent_instances(token_id: int) -> Tuple[int, List[str]]
```

Get the list of agent instances.

**Arguments**:

- `token_id`: Token ID pointing to the on-chain service

**Returns**:

number of agent instances and the list of registered addressed

<a id="autonomy.deploy.chain.ServiceRegistry.get_service_info"></a>

#### get`_`service`_`info

```python
def get_service_info(token_id: int) -> ServiceInfo
```

Returns service info.

**Arguments**:

- `token_id`: Token ID pointing to the on-chain service

**Returns**:

security deposit, multisig address, IPFS hash for config,

