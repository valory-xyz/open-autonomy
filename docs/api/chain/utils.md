<a id="autonomy.chain.utils"></a>

# autonomy.chain.utils

Utility functions.

<a id="autonomy.chain.utils.get_ipfs_hash_from_uri"></a>

#### get`_`ipfs`_`hash`_`from`_`uri

```python
def get_ipfs_hash_from_uri(uri: str) -> str
```

Split IPFS hash from the ipfs uri

<a id="autonomy.chain.utils.resolve_component_id"></a>

#### resolve`_`component`_`id

```python
def resolve_component_id(ledger_api: LedgerApi,
                         contract_address: str,
                         token_id: int,
                         is_agent: bool = False,
                         is_service: bool = False) -> Dict
```

Resolve component ID to metadata json

<a id="autonomy.chain.utils.parse_public_id_from_metadata"></a>

#### parse`_`public`_`id`_`from`_`metadata

```python
def parse_public_id_from_metadata(id_string: str) -> PublicId
```

Parse public ID from on-chain metadata.

<a id="autonomy.chain.utils.is_service_manager_token_compatible_chain"></a>

#### is`_`service`_`manager`_`token`_`compatible`_`chain

```python
def is_service_manager_token_compatible_chain(ledger_api: LedgerApi) -> bool
```

Verify package dependencies using on-chain metadata.

