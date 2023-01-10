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
def publish_metadata(public_id: PublicId, package_path: Path, nft_image_hash: str, description: str) -> str
```

Publish service metadata.

<a id="autonomy.chain.mint.get_contract"></a>

#### get`_`contract

```python
def get_contract(public_id: PublicId) -> Contract
```

Load contract for given public id.

<a id="autonomy.chain.mint.transact"></a>

#### transact

```python
def transact(ledger_api: LedgerApi, crypto: Crypto, tx: Dict) -> Dict
```

Make a transaction and return a receipt

<a id="autonomy.chain.mint.mint_component"></a>

#### mint`_`component

```python
def mint_component(ledger_api: LedgerApi, crypto: Crypto, metadata_hash: str, component_type: UnitType, chain_type: ChainType, dependencies: Optional[List[int]] = None) -> Optional[int]
```

Publish component on-chain.

