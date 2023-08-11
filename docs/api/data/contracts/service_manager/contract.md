<a id="autonomy.data.contracts.service_manager.contract"></a>

# autonomy.data.contracts.service`_`manager.contract

This module contains the class to connect to the Service Registry contract.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract"></a>

## ServiceManagerContract Objects

```python
class ServiceManagerContract(Contract)
```

The Service manager contract.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> Optional[JSONLike]
```

Get the Safe transaction.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> Optional[bytes]
```

Get raw message.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> Optional[JSONLike]
```

Get state.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_create_transaction"></a>

#### get`_`create`_`transaction

```python
@classmethod
def get_create_transaction(cls,
                           ledger_api: LedgerApi,
                           contract_address: str,
                           owner: str,
                           sender: str,
                           metadata_hash: str,
                           agent_ids: List[int],
                           agent_params: List[List[int]],
                           threshold: int,
                           raise_on_try: bool = False) -> Dict[str, Any]
```

Retrieve the service owner.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_activate_registration_transaction"></a>

#### get`_`activate`_`registration`_`transaction

```python
@classmethod
def get_activate_registration_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        security_deposit: int,
        raise_on_try: bool = False) -> Dict[str, Any]
```

Retrieve the service owner.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_register_instance_transaction"></a>

#### get`_`register`_`instance`_`transaction

```python
@classmethod
def get_register_instance_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        instances: List[str],
        agent_ids: List[int],
        security_deposit: int,
        raise_on_try: bool = False) -> Dict[str, Any]
```

Retrieve the service owner.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_service_deploy_transaction"></a>

#### get`_`service`_`deploy`_`transaction

```python
@classmethod
def get_service_deploy_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        gnosis_safe_multisig: str,
        deployment_payload: str,
        raise_on_try: bool = False) -> Dict[str, Any]
```

Retrieve the service owner.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_terminate_service_transaction"></a>

#### get`_`terminate`_`service`_`transaction

```python
@classmethod
def get_terminate_service_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        raise_on_try: bool = False) -> Dict[str, Any]
```

Retrieve the service owner.

<a id="autonomy.data.contracts.service_manager.contract.ServiceManagerContract.get_unbond_service_transaction"></a>

#### get`_`unbond`_`service`_`transaction

```python
@classmethod
def get_unbond_service_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: str,
        owner: str,
        service_id: int,
        raise_on_try: bool = False) -> Dict[str, Any]
```

Retrieve the service owner.

