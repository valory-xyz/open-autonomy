<a id="autonomy.chain.service"></a>

# autonomy.chain.service

Helper functions to manage on-chain services

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

<a id="autonomy.chain.service.register_instance"></a>

#### register`_`instance

```python
def register_instance(ledger_api: LedgerApi, crypto: Crypto, chain_type: ChainType, service_id: int, instance: str, agent_id: int) -> None
```

Activate service.

<a id="autonomy.chain.service.deploy_service"></a>

#### deploy`_`service

```python
def deploy_service(ledger_api: LedgerApi, crypto: Crypto, chain_type: ChainType, service_id: int, deployment_payload: Optional[str] = None) -> None
```

Activate service.

