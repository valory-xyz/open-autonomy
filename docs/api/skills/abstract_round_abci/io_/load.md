<a id="packages.valory.skills.abstract_round_abci.io_.load"></a>

# packages.valory.skills.abstract`_`round`_`abci.io`_`.load

This module contains all the loading operations of the behaviours.

<a id="packages.valory.skills.abstract_round_abci.io_.load.AbstractLoader"></a>

## AbstractLoader Objects

```python
class AbstractLoader(ABC)
```

An abstract `Loader` class.

<a id="packages.valory.skills.abstract_round_abci.io_.load.AbstractLoader.load_single_object"></a>

#### load`_`single`_`object

```python
@abstractmethod
def load_single_object(
        serialized_object: str) -> NativelySupportedSingleObjectType
```

Load a single object.

<a id="packages.valory.skills.abstract_round_abci.io_.load.AbstractLoader.load"></a>

#### load

```python
def load(serialized_objects: Dict[str, str]) -> SupportedObjectType
```

Load one or more serialized objects.

**Arguments**:

- `serialized_objects`: A mapping of filenames to serialized object they contained.

**Returns**:

the loaded file(s).

<a id="packages.valory.skills.abstract_round_abci.io_.load.JSONLoader"></a>

## JSONLoader Objects

```python
class JSONLoader(AbstractLoader)
```

A JSON file loader.

<a id="packages.valory.skills.abstract_round_abci.io_.load.JSONLoader.load_single_object"></a>

#### load`_`single`_`object

```python
def load_single_object(
        serialized_object: str) -> NativelySupportedSingleObjectType
```

Read a json file.

**Arguments**:

- `serialized_object`: the file serialized into a JSON string.

**Returns**:

the deserialized json file's content.

<a id="packages.valory.skills.abstract_round_abci.io_.load.Loader"></a>

## Loader Objects

```python
class Loader(AbstractLoader)
```

Class which loads objects.

<a id="packages.valory.skills.abstract_round_abci.io_.load.Loader.__init__"></a>

#### `__`init`__`

```python
def __init__(filetype: Optional[Any], custom_loader: CustomLoaderType)
```

Initialize a `Loader`.

<a id="packages.valory.skills.abstract_round_abci.io_.load.Loader.load_single_object"></a>

#### load`_`single`_`object

```python
def load_single_object(serialized_object: str) -> SupportedSingleObjectType
```

Load a single file.

