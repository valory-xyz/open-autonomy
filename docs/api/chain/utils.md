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

<a id="autonomy.chain.utils.verify_component_dependencies"></a>

#### verify`_`component`_`dependencies

```python
def verify_component_dependencies(ledger_api: LedgerApi,
                                  contract_address: str,
                                  dependencies: List[int],
                                  package_configuration: PackageConfiguration,
                                  skip_hash_check: bool = False) -> None
```

Verify package dependencies using on-chain metadata.

<a id="autonomy.chain.utils.verify_service_dependencies"></a>

#### verify`_`service`_`dependencies

```python
def verify_service_dependencies(ledger_api: LedgerApi,
                                contract_address: str,
                                agent_id: int,
                                service_configuration: Service,
                                skip_hash_check: bool = False) -> None
```

Verify package dependencies using on-chain metadata.

