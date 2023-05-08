<a id="packages.valory.skills.abstract_round_abci.io_.ipfs"></a>

# packages.valory.skills.abstract`_`round`_`abci.io`_`.ipfs

This module contains all the interaction operations of the behaviours with IPFS.

<a id="packages.valory.skills.abstract_round_abci.io_.ipfs.IPFSInteractionError"></a>

## IPFSInteractionError Objects

```python
class IPFSInteractionError(Exception)
```

A custom exception for IPFS interaction errors.

<a id="packages.valory.skills.abstract_round_abci.io_.ipfs.IPFSInteract"></a>

## IPFSInteract Objects

```python
class IPFSInteract()
```

Class for interacting with IPFS.

<a id="packages.valory.skills.abstract_round_abci.io_.ipfs.IPFSInteract.__init__"></a>

#### `__`init`__`

```python
def __init__(loader_cls: Type = Loader, storer_cls: Type = Storer)
```

Initialize an `IPFSInteract` object.

<a id="packages.valory.skills.abstract_round_abci.io_.ipfs.IPFSInteract.store"></a>

#### store

```python
def store(filepath: str,
          obj: SupportedObjectType,
          multiple: bool,
          filetype: Optional[SupportedFiletype] = None,
          custom_storer: Optional[CustomStorerType] = None,
          **kwargs: Any) -> Dict[str, str]
```

Temporarily store a file locally, in order to send it to IPFS and retrieve a hash, and then delete it.

<a id="packages.valory.skills.abstract_round_abci.io_.ipfs.IPFSInteract.load"></a>

#### load

```python
def load(serialized_objects: Dict[str, str],
         filetype: Optional[SupportedFiletype] = None,
         custom_loader: CustomLoaderType = None) -> SupportedObjectType
```

Deserialize objects received via IPFS.

