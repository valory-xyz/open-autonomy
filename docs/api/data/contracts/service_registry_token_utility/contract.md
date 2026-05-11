<a id="autonomy.data.contracts.service_registry_token_utility.contract"></a>

# autonomy.data.contracts.service`_`registry`_`token`_`utility.contract

This module contains the scaffold contract definition.

<a id="autonomy.data.contracts.service_registry_token_utility.contract.ServiceRegistryTokenUtilityContract"></a>

## ServiceRegistryTokenUtilityContract Objects

```python
class ServiceRegistryTokenUtilityContract(Contract)
```

The scaffold contract class for a smart contract.

<a id="autonomy.data.contracts.service_registry_token_utility.contract.ServiceRegistryTokenUtilityContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> JSONLike
```

Handler method for the 'GET_RAW_TRANSACTION' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

<a id="autonomy.data.contracts.service_registry_token_utility.contract.ServiceRegistryTokenUtilityContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> bytes
```

Handler method for the 'GET_RAW_MESSAGE' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

<a id="autonomy.data.contracts.service_registry_token_utility.contract.ServiceRegistryTokenUtilityContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> JSONLike
```

Handler method for the 'GET_STATE' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

<a id="autonomy.data.contracts.service_registry_token_utility.contract.ServiceRegistryTokenUtilityContract.is_token_secured_service"></a>

#### is`_`token`_`secured`_`service

```python
@classmethod
def is_token_secured_service(cls, ledger_api: LedgerApi, contract_address: str,
                             service_id: int) -> JSONLike
```

Check if a service is secured service.

<a id="autonomy.data.contracts.service_registry_token_utility.contract.ServiceRegistryTokenUtilityContract.get_agent_bond"></a>

#### get`_`agent`_`bond

```python
@classmethod
def get_agent_bond(cls, ledger_api: LedgerApi, contract_address: str,
                   service_id: int, agent_id: int) -> JSONLike
```

Check if a service is secured service.

