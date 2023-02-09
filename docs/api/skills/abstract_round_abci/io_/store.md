<a id="packages.valory.skills.abstract_round_abci.io_.store"></a>

# packages.valory.skills.abstract`_`round`_`abci.io`_`.store

This module contains all the storing operations of the behaviours.

<a id="packages.valory.skills.abstract_round_abci.io_.store.SupportedFiletype"></a>

## SupportedFiletype Objects

```python
class SupportedFiletype(Enum)
```

Enum for the supported filetypes of the IPFS interacting methods.

<a id="packages.valory.skills.abstract_round_abci.io_.store.AbstractStorer"></a>

## AbstractStorer Objects

```python
class AbstractStorer(ABC)
```

An abstract `Storer` class.

<a id="packages.valory.skills.abstract_round_abci.io_.store.AbstractStorer.__init__"></a>

#### `__`init`__`

```python
def __init__(path: str)
```

Initialize an abstract storer.

<a id="packages.valory.skills.abstract_round_abci.io_.store.AbstractStorer.serialize_object"></a>

#### serialize`_`object

```python
@abstractmethod
def serialize_object(filename: str, obj: SupportedSingleObjectType,
                     **kwargs: Any) -> Dict[str, str]
```

Store a single file.

<a id="packages.valory.skills.abstract_round_abci.io_.store.AbstractStorer.store"></a>

#### store

```python
def store(obj: SupportedObjectType, multiple: bool,
          **kwargs: Any) -> Dict[str, str]
```

Serialize one or multiple objects.

<a id="packages.valory.skills.abstract_round_abci.io_.store.JSONStorer"></a>

## JSONStorer Objects

```python
class JSONStorer(AbstractStorer)
```

A JSON file storer.

<a id="packages.valory.skills.abstract_round_abci.io_.store.JSONStorer.serialize_object"></a>

#### serialize`_`object

```python
def serialize_object(filename: str, obj: NativelySupportedSingleObjectType,
                     **kwargs: Any) -> Dict[str, str]
```

Serialize an object to JSON.

**Arguments**:

- `filename`: under which name the provided object should be serialized. Note that it will appear in IPFS with this name.
- `obj`: the object to store.

**Returns**:

a dict mapping the name to the serialized object.

<a id="packages.valory.skills.abstract_round_abci.io_.store.Storer"></a>

## Storer Objects

```python
class Storer(AbstractStorer)
```

Class which serializes objects.

<a id="packages.valory.skills.abstract_round_abci.io_.store.Storer.__init__"></a>

#### `__`init`__`

```python
def __init__(filetype: Optional[Any],
             custom_storer: Optional[CustomStorerType], path: str)
```

Initialize a `Storer`.

<a id="packages.valory.skills.abstract_round_abci.io_.store.Storer.serialize_object"></a>

#### serialize`_`object

```python
def serialize_object(filename: str, obj: NativelySupportedObjectType,
                     **kwargs: Any) -> Dict[str, str]
```

Store a single object.

