<a id="autonomy.cli.helpers.chain"></a>

# autonomy.cli.helpers.chain

On-chain interaction helpers.

<a id="autonomy.cli.helpers.chain.serialize_metadata"></a>

#### serialize`_`metadata

```python
def serialize_metadata(package_hash: str, public_id: PublicId, description: str, nft_image_hash: str = DEFAULT_NFT_IMAGE_HASH) -> str
```

Serialize metadata.

<a id="autonomy.cli.helpers.chain.publish_metadata"></a>

#### publish`_`metadata

```python
def publish_metadata(public_id: PublicId, package_path: Path, ipfs_tool: IPFSTool, nft_image_hash: str = DEFAULT_NFT_IMAGE_HASH) -> str
```

Publish service metadata.

<a id="autonomy.cli.helpers.chain.verify_and_fetch_token_id_from_event"></a>

#### verify`_`and`_`fetch`_`token`_`id`_`from`_`event

```python
def verify_and_fetch_token_id_from_event(event: Dict, unit_type: RegistryManager.UnitType, metadata_hash: str, ledger_api: LedgerApi) -> Optional[int]
```

Verify and extract token id from a registry event

<a id="autonomy.cli.helpers.chain.publish_component"></a>

#### publish`_`component

```python
def publish_component(package_path: Path, package_type: PackageType, crypto: Crypto, dependencies: Optional[List[int]] = None) -> None
```

Publish component to on-chain contract.

