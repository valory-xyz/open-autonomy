<a id="autonomy.data.contracts.agent_registry.contract"></a>

# autonomy.data.contracts.agent`_`registry.contract

This module contains the class to connect to the Service Registry contract.

<a id="autonomy.data.contracts.agent_registry.contract.AgentRegistryContract"></a>

## AgentRegistryContract Objects

```python
class AgentRegistryContract(Contract)
```

The Agent Registry contract.

<a id="autonomy.data.contracts.agent_registry.contract.AgentRegistryContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> Optional[JSONLike]
```

Get the Safe transaction.

<a id="autonomy.data.contracts.agent_registry.contract.AgentRegistryContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> Optional[bytes]
```

Get raw message.

<a id="autonomy.data.contracts.agent_registry.contract.AgentRegistryContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> Optional[JSONLike]
```

Get state.

<a id="autonomy.data.contracts.agent_registry.contract.AgentRegistryContract.get_create_events"></a>

#### get`_`create`_`events

```python
@classmethod
def get_create_events(cls, ledger_api: LedgerApi, contract_address: str,
                      receipt: JSONLike) -> Optional[int]
```

Returns `CreateUnit` event filter.

<a id="autonomy.data.contracts.agent_registry.contract.AgentRegistryContract.get_update_hash_events"></a>

#### get`_`update`_`hash`_`events

```python
@classmethod
def get_update_hash_events(cls, ledger_api: LedgerApi, contract_address: str,
                           receipt: JSONLike) -> Optional[int]
```

Returns `CreateUnit` event filter.

<a id="autonomy.data.contracts.agent_registry.contract.AgentRegistryContract.get_token_uri"></a>

#### get`_`token`_`uri

```python
@classmethod
def get_token_uri(cls, ledger_api: LedgerApi, contract_address: str,
                  token_id: int) -> str
```

Returns the latest metadata URI for a component.

