<a id="autonomy.data.contracts.service_registry.contract"></a>

# autonomy.data.contracts.service`_`registry.contract

This module contains the class to connect to the Service Registry contract.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract"></a>

## ServiceRegistryContract Objects

```python
class ServiceRegistryContract(Contract)
```

The Service Registry contract.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> Optional[JSONLike]
```

Get the Safe transaction.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> Optional[bytes]
```

Get raw message.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> Optional[JSONLike]
```

Get state.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.is_l1_chain"></a>

#### is`_`l1`_`chain

```python
@staticmethod
def is_l1_chain(ledger_api: LedgerApi) -> bool
```

Check if we're interecting with an L1 chain

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.load_l2_build"></a>

#### load`_`l2`_`build

```python
@staticmethod
def load_l2_build() -> JSONLike
```

Load L2 ABI

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_instance"></a>

#### get`_`instance

```python
@classmethod
def get_instance(cls,
                 ledger_api: LedgerApi,
                 contract_address: Optional[str] = None) -> Any
```

Get contract instance.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.verify_contract"></a>

#### verify`_`contract

```python
@classmethod
def verify_contract(cls, ledger_api: LedgerApi,
                    contract_address: str) -> Dict[str, Union[bool, str]]
```

Verify the contract's bytecode

**Arguments**:

- `ledger_api`: the ledger API object
- `contract_address`: the contract address

**Returns**:

the verified status

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.exists"></a>

#### exists

```python
@classmethod
def exists(cls, ledger_api: LedgerApi, contract_address: str,
           service_id: int) -> bool
```

Check if the service id exists

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_agent_instances"></a>

#### get`_`agent`_`instances

```python
@classmethod
def get_agent_instances(cls, ledger_api: LedgerApi, contract_address: str,
                        service_id: int) -> Dict[str, Any]
```

Retrieve on-chain agent instances.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_service_owner"></a>

#### get`_`service`_`owner

```python
@classmethod
def get_service_owner(cls, ledger_api: LedgerApi, contract_address: str,
                      service_id: int) -> Dict[str, Any]
```

Retrieve the service owner.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_service_information"></a>

#### get`_`service`_`information

```python
@classmethod
def get_service_information(cls, ledger_api: LedgerApi, contract_address: str,
                            token_id: int) -> ServiceInfo
```

Retrieve service information

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_token_uri"></a>

#### get`_`token`_`uri

```python
@classmethod
def get_token_uri(cls, ledger_api: LedgerApi, contract_address: str,
                  token_id: int) -> str
```

Returns the latest metadata URI for a component.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_create_events"></a>

#### get`_`create`_`events

```python
@classmethod
def get_create_events(cls, ledger_api: LedgerApi, contract_address: str,
                      receipt: JSONLike) -> Optional[int]
```

Returns `CreateUnit` event filter.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_update_events"></a>

#### get`_`update`_`events

```python
@classmethod
def get_update_events(cls, ledger_api: LedgerApi, contract_address: str,
                      receipt: JSONLike) -> Optional[int]
```

Returns `CreateUnit` event filter.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_update_hash_events"></a>

#### get`_`update`_`hash`_`events

```python
@classmethod
def get_update_hash_events(cls, ledger_api: LedgerApi, contract_address: str,
                           receipt: JSONLike) -> Optional[int]
```

Returns `CreateUnit` event filter.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.process_receipt"></a>

#### process`_`receipt

```python
@classmethod
def process_receipt(cls, ledger_api: LedgerApi, contract_address: str,
                    event: str, receipt: JSONLike) -> JSONLike
```

Checks for a successful service registration event in the latest block

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_slash_data"></a>

#### get`_`slash`_`data

```python
@classmethod
def get_slash_data(cls, ledger_api: LedgerApi, contract_address: str,
                   agent_instances: List[str], amounts: List[int],
                   service_id: int) -> Dict[str, bytes]
```

Gets the encoded arguments for a slashing tx, which should only be called via the multisig.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.process_slash_receipt"></a>

#### process`_`slash`_`receipt

```python
@classmethod
def process_slash_receipt(cls, ledger_api: LedgerApi, contract_address: str,
                          tx_hash: str) -> Optional[JSONLike]
```

Process the slash receipt.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `tx_hash`: the hash of a slash tx to be processed.

**Returns**:

a dictionary with the timestamp of the slashing and the `OperatorSlashed` events.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.get_operators_mapping"></a>

#### get`_`operators`_`mapping

```python
@classmethod
def get_operators_mapping(cls, ledger_api: LedgerApi, contract_address: str,
                          agent_instances: FrozenSet[str]) -> Dict[str, str]
```

Retrieve a mapping of the given agent instances to their operators.

Please keep in mind that this method performs a call for each agent instance.

**Arguments**:

- `ledger_api`: the ledger api.
- `contract_address`: the contract address.
- `agent_instances`: the agent instances to be mapped.

**Returns**:

a mapping of the given agent instances to their operators.

