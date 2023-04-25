<a id="autonomy.chain.utils"></a>

# autonomy.chain.utils

Utility functions.

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

