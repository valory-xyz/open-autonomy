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

Resolve token URI

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.filter_token_id_from_emitted_events"></a>

#### filter`_`token`_`id`_`from`_`emitted`_`events

```python
@classmethod
def filter_token_id_from_emitted_events(
        cls, ledger_api: LedgerApi, contract_address: str) -> Optional[int]
```

Returns `CreateUnit` event filter.

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.verify_service_has_been_activated"></a>

#### verify`_`service`_`has`_`been`_`activated

```python
@classmethod
def verify_service_has_been_activated(cls, ledger_api: LedgerApi,
                                      contract_address: str,
                                      service_id: int) -> bool
```

Checks for a successful service registration event in the latest block

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.verify_agent_instance_registration"></a>

#### verify`_`agent`_`instance`_`registration

```python
@classmethod
def verify_agent_instance_registration(cls, ledger_api: LedgerApi,
                                       contract_address: str, service_id: int,
                                       instance_check: Set[str]) -> Set[str]
```

Checks for the registered instances and filters out the instances that are registered from the given array

<a id="autonomy.data.contracts.service_registry.contract.ServiceRegistryContract.verify_service_has_been_deployed"></a>

#### verify`_`service`_`has`_`been`_`deployed

```python
@classmethod
def verify_service_has_been_deployed(cls, ledger_api: LedgerApi,
                                     contract_address: str,
                                     service_id: int) -> bool
```

Checks for a successful service registration event in the latest block

