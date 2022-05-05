<a id="packages.valory.skills.abstract_round_abci.io.ipfs"></a>

# packages.valory.skills.abstract`_`round`_`abci.io.ipfs

This module contains all the interaction operations of the behaviours with IPFS.

<a id="packages.valory.skills.abstract_round_abci.io.ipfs.IPFSInteractionError"></a>

## IPFSInteractionError Objects

```python
class IPFSInteractionError(Exception)
```

A custom exception for IPFS interaction errors.

<a id="packages.valory.skills.abstract_round_abci.io.ipfs.IPFSInteract"></a>

## IPFSInteract Objects

```python
class IPFSInteract()
```

Class for interacting with IPFS.

<a id="packages.valory.skills.abstract_round_abci.io.ipfs.IPFSInteract.__init__"></a>

#### `__`init`__`

```python
def __init__(domain: str)
```

Initialize an `IPFSInteract`.

**Arguments**:

- `domain`: the IPFS domain name.

<a id="packages.valory.skills.abstract_round_abci.io.ipfs.IPFSInteract.store_and_send"></a>

#### store`_`and`_`send

```python
def store_and_send(filepath: str, obj: SupportedObjectType, multiple: bool, filetype: Optional[SupportedFiletype] = None, custom_storer: Optional[CustomStorerType] = None, **kwargs: Any, ,) -> str
```

Temporarily store a file locally, in order to send it to IPFS and retrieve a hash, and then delete it.

<a id="packages.valory.skills.abstract_round_abci.io.ipfs.IPFSInteract.get_and_read"></a>

#### get`_`and`_`read

```python
def get_and_read(hash_: str, target_dir: str, multiple: bool = False, filename: Optional[str] = None, filetype: Optional[SupportedFiletype] = None, custom_loader: CustomLoaderType = None) -> SupportedObjectType
```

Get, store and read a file from IPFS.

