<a id="autonomy.chain.metadata"></a>

# autonomy.chain.metadata

Metadata helpers.

<a id="autonomy.chain.metadata.serialize_metadata"></a>

#### serialize`_`metadata

```python
def serialize_metadata(package_hash: str, public_id: PublicId,
                       description: str, nft_image_hash: str) -> str
```

Serialize metadata.

<a id="autonomy.chain.metadata.publish_metadata"></a>

#### publish`_`metadata

```python
def publish_metadata(public_id: PublicId, package_path: Path,
                     nft_image_hash: str, description: str) -> str
```

Publish service metadata.

