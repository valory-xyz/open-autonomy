<a id="autonomy.chain.service"></a>

# autonomy.chain.service

Helper functions to manage on-chain services

<a id="autonomy.chain.service.MultiSendOperation"></a>

## MultiSendOperation Objects

```python
class MultiSendOperation(Enum)
```

Operation types.

<a id="autonomy.chain.service.get_delployment_payload"></a>

#### get`_`delployment`_`payload

```python
def get_delployment_payload(fallback_handler: Optional[str] = None) -> str
```

Calculates deployment payload.

<a id="autonomy.chain.service.get_agent_instances"></a>

#### get`_`agent`_`instances

```python
def get_agent_instances(ledger_api: LedgerApi, chain_type: ChainType,
                        token_id: int) -> Dict
```

Get the list of agent instances.

**Arguments**:

- `ledger_api`: `aea.crypto.LedgerApi` object for interacting with the chain
- `chain_type`: Chain type
- `token_id`: Token ID pointing to the on-chain service

**Returns**:

number of agent instances and the list of registered addressed

<a id="autonomy.chain.service.get_service_info"></a>

#### get`_`service`_`info

```python
def get_service_info(ledger_api: LedgerApi, chain_type: ChainType,
                     token_id: int) -> ServiceInfo
```

Returns service info.

**Arguments**:

- `ledger_api`: `aea.crypto.LedgerApi` object for interacting with the chain
- `chain_type`: Chain type
- `token_id`: Token ID pointing to the on-chain service

**Returns**:

security deposit, multisig address, IPFS hash for config,
threshold, max number of agent instances, number of agent instances,
service state, list of cannonical agents

<a id="autonomy.chain.service.get_token_deposit_amount"></a>

#### get`_`token`_`deposit`_`amount

```python
def get_token_deposit_amount(ledger_api: LedgerApi,
                             chain_type: ChainType,
                             service_id: int,
                             agent_id: Optional[int] = None) -> int
```

Returns service info.

<a id="autonomy.chain.service.get_activate_registration_amount"></a>

#### get`_`activate`_`registration`_`amount

```python
def get_activate_registration_amount(ledger_api: LedgerApi,
                                     chain_type: ChainType, service_id: int,
                                     agents: List[int]) -> int
```

Get activate registration amount.

<a id="autonomy.chain.service.is_service_token_secured"></a>

#### is`_`service`_`token`_`secured

```python
def is_service_token_secured(ledger_api: LedgerApi, chain_type: ChainType,
                             service_id: int) -> bool
```

Check if the service is token secured.

<a id="autonomy.chain.service.approve_erc20_usage"></a>

#### approve`_`erc20`_`usage

```python
def approve_erc20_usage(ledger_api: LedgerApi,
                        crypto: Crypto,
                        chain_type: ChainType,
                        spender: str,
                        amount: int,
                        sender: str,
                        dry_run: bool = False,
                        timeout: Optional[float] = None,
                        retries: Optional[int] = None,
                        sleep: Optional[float] = None) -> None
```

Approve ERC20 token usage.

<a id="autonomy.chain.service.ServiceManager"></a>

## ServiceManager Objects

```python
class ServiceManager()
```

Service manager.

<a id="autonomy.chain.service.ServiceManager.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_api: LedgerApi,
             crypto: Crypto,
             chain_type: ChainType,
             dry_run: bool = False,
             timeout: Optional[float] = None,
             retries: Optional[int] = None,
             sleep: Optional[float] = None) -> None
```

Initialize object.

<a id="autonomy.chain.service.ServiceManager.get_service_info"></a>

#### get`_`service`_`info

```python
def get_service_info(token_id: int) -> ServiceInfo
```

Returns service info.

**Arguments**:

- `token_id`: Token ID pointing to the on-chain service

**Returns**:

security deposit, multisig address, IPFS hash for config,
threshold, max number of agent instances, number of agent instances,
service state, list of cannonical agents

<a id="autonomy.chain.service.ServiceManager.activate"></a>

#### activate

```python
def activate(service_id: int) -> None
```

Activate service.

Once you have minted the service on-chain, you'll have to activate the service
before you can proceed further.

**Arguments**:

- `service_id`: Service ID retrieved after minting a service

<a id="autonomy.chain.service.ServiceManager.register_instance"></a>

#### register`_`instance

```python
def register_instance(service_id: int, instances: List[str],
                      agent_ids: List[int]) -> None
```

Register instance.

Once you have a service with an active registration, you can register agent
which will be a part of the service deployment. Using this method you can
register maximum N amounts per agents, N being the number of slots for an agent
with agent id being `agent_id`.

Make sure the instance address you provide is not already a part of any service
and not as same as the service owner.

**Arguments**:

- `service_id`: Service ID retrieved after minting a service
- `instances`: Address of the agent instance
- `agent_ids`: Agent ID of the agent that you want this instance to be a part
of when deployed

<a id="autonomy.chain.service.ServiceManager.deploy"></a>

#### deploy

```python
def deploy(service_id: int,
           fallback_handler: Optional[str] = None,
           reuse_multisig: bool = False) -> None
```

Deploy service.

Using this method you can deploy a service on-chain once you have activated
the service and registered the required agent instances.

**Arguments**:

- `service_id`: Service ID retrieved after minting a service
- `fallback_handler`: Fallback handler address for gnosis safe multisig
- `reuse_multisig`: Use multisig from the previous deployment

<a id="autonomy.chain.service.ServiceManager.terminate"></a>

#### terminate

```python
def terminate(service_id: int) -> None
```

Terminate service.

Using this method you can terminate a service on-chain once you have activated
the service and registered the required agent instances.

**Arguments**:

- `service_id`: Service ID retrieved after minting a service

<a id="autonomy.chain.service.ServiceManager.unbond"></a>

#### unbond

```python
def unbond(service_id: int) -> None
```

Unbond service.

Using this method you can unbond a service on-chain once you have terminated
the service.

**Arguments**:

- `service_id`: Service ID retrieved after minting a service

<a id="autonomy.chain.service.get_reuse_multisig_payload"></a>

#### get`_`reuse`_`multisig`_`payload

```python
def get_reuse_multisig_payload(
        ledger_api: LedgerApi, crypto: Crypto, chain_type: ChainType,
        service_id: int) -> Tuple[Optional[str], Optional[str]]
```

Reuse multisig.

