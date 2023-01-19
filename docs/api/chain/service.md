<a id="autonomy.chain.service"></a>

# autonomy.chain.service

Helper functions to manage on-chain services

<a id="autonomy.chain.service.get_agent_instances"></a>

#### get`_`agent`_`instances

```python
def get_agent_instances(ledger_api: LedgerApi, chain_type: ChainType, token_id: int) -> Dict
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
def get_service_info(ledger_api: LedgerApi, chain_type: ChainType, token_id: int) -> ServiceInfo
```

Returns service info.

**Arguments**:

- `ledger_api`: `aea.crypto.LedgerApi` object for interacting with the chain
- `chain_type`: Chain type
- `token_id`: Token ID pointing to the on-chain service

**Returns**:

security deposit, multisig address, IPFS hash for config,

<a id="autonomy.chain.service.activate_service"></a>

#### activate`_`service

```python
def activate_service(ledger_api: LedgerApi, crypto: Crypto, chain_type: ChainType, service_id: int) -> None
```

Activate service.

Once you have minted the service on-chain, you'll have to activate the service
before you can proceed further.

**Arguments**:

- `ledger_api`: `aea.crypto.LedgerApi` object for interacting with the chain
- `crypto`: `aea.crypto.Crypto` object which has a funded key
- `chain_type`: Chain type
- `service_id`: Service ID retrieved after minting a service

<a id="autonomy.chain.service.register_instance"></a>

#### register`_`instance

```python
def register_instance(ledger_api: LedgerApi, crypto: Crypto, chain_type: ChainType, service_id: int, instance: str, agent_id: int) -> None
```

Register instance.

Once you have a service with an active registration, you can register agent
which will be a part of the service deployment. Using this method you can
register maximum N amounts per agents, N being the number of slots for an agent
with agent id being `agent_id`.

Make sure the instance address you provide is not already a part of any service
and not as same as the service owner.

**Arguments**:

                of when deployed
- `ledger_api`: `aea.crypto.LedgerApi` object for interacting with the chain
- `crypto`: `aea.crypto.Crypto` object which has a funded key
- `chain_type`: Chain type
- `service_id`: Service ID retrieved after minting a service
- `instance`: Address of the agent instance
- `agent_id`: Agent ID of the agent that you want this instance to be a part

<a id="autonomy.chain.service.deploy_service"></a>

#### deploy`_`service

```python
def deploy_service(ledger_api: LedgerApi, crypto: Crypto, chain_type: ChainType, service_id: int, deployment_payload: Optional[str] = None) -> None
```

Deploy service.

Using this method you can deploy a service on-chain once you have activated
the service and registered the required agent instances.

**Arguments**:

                        deployment transaction
- `ledger_api`: `aea.crypto.LedgerApi` object for interacting with the chain
- `crypto`: `aea.crypto.Crypto` object which has a funded key
- `chain_type`: Chain type
- `service_id`: Service ID retrieved after minting a service
- `deployment_payload`: Deployment payload to include when making the

