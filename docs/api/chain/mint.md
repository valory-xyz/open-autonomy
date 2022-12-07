<a id="autonomy.chain.mint"></a>

# autonomy.chain.mint

Helpers for minting components

<a id="autonomy.chain.mint.serialize_metadata"></a>

#### serialize`_`metadata

```python
def serialize_metadata(package_hash: str, public_id: PublicId, description: str, nft_image_hash: str) -> str
```

Serialize metadata.

<a id="autonomy.chain.mint.publish_metadata"></a>

#### publish`_`metadata

```python
def publish_metadata(public_id: PublicId, package_path: Path, nft_image_hash: str) -> str
```

Publish service metadata.

<a id="autonomy.chain.mint.verify_and_fetch_token_id_from_event"></a>

#### verify`_`and`_`fetch`_`token`_`id`_`from`_`event

```python
def verify_and_fetch_token_id_from_event(event: Dict, unit_type: RegistriesManager.UnitType, metadata_hash: str, ledger_api: LedgerApi) -> Optional[int]
```

Verify and extract token id from a registry event

<a id="autonomy.chain.mint.mint_component"></a>

#### mint`_`component

```python
def mint_component(ledger_api: LedgerApi, crypto: Crypto, metadata_hash: str, component_type: RegistriesManager.UnitType, chain_type: ChainType, dependencies: Optional[List[int]] = None) -> Optional[int]
```

Publish component on-chain.

