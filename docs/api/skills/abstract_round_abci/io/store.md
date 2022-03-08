<a id="packages.valory.skills.abstract_round_abci.io.store"></a>

# packages.valory.skills.abstract`_`round`_`abci.io.store

This module contains all the storing operations of the behaviours.

<a id="packages.valory.skills.abstract_round_abci.io.store.SupportedFiletype"></a>

## SupportedFiletype Objects

```python
class SupportedFiletype(Enum)
```

Enum for the supported filetypes of the IPFS interacting methods.

<a id="packages.valory.skills.abstract_round_abci.io.store.AbstractStorer"></a>

## AbstractStorer Objects

```python
class AbstractStorer(ABC)
```

An abstract `Storer` class.

<a id="packages.valory.skills.abstract_round_abci.io.store.AbstractStorer.__init__"></a>

#### `__`init`__`

```python
def __init__(path: str)
```

Initialize an abstract storer.

<a id="packages.valory.skills.abstract_round_abci.io.store.AbstractStorer.store"></a>

#### store

```python
@abstractmethod
def store(obj: SupportedObjectType, **kwargs: Any) -> None
```

Store a file.

<a id="packages.valory.skills.abstract_round_abci.io.store.JSONStorer"></a>

## JSONStorer Objects

```python
class JSONStorer(AbstractStorer)
```

A JSON file storer.

<a id="packages.valory.skills.abstract_round_abci.io.store.JSONStorer.store"></a>

#### store

```python
def store(obj: NativelySupportedObjectType, **kwargs: Any) -> None
```

Store a JSON.

<a id="packages.valory.skills.abstract_round_abci.io.store.CSVStorer"></a>

## CSVStorer Objects

```python
class CSVStorer(AbstractStorer)
```

A CSV file storer.

<a id="packages.valory.skills.abstract_round_abci.io.store.CSVStorer.store"></a>

#### store

```python
def store(obj: NativelySupportedObjectType, **kwargs: Any) -> None
```

Store a pandas dataframe.

<a id="packages.valory.skills.abstract_round_abci.io.store.ForecasterStorer"></a>

## ForecasterStorer Objects

```python
class ForecasterStorer(AbstractStorer)
```

A pmdarima Pipeline storer.

<a id="packages.valory.skills.abstract_round_abci.io.store.ForecasterStorer.store"></a>

#### store

```python
def store(obj: NativelySupportedObjectType, **kwargs: Any) -> None
```

Store a pmdarima Pipeline.

<a id="packages.valory.skills.abstract_round_abci.io.store.Storer"></a>

## Storer Objects

```python
class Storer(CSVStorer, ForecasterStorer, JSONStorer)
```

Class which stores files.

<a id="packages.valory.skills.abstract_round_abci.io.store.Storer.__init__"></a>

#### `__`init`__`

```python
def __init__(filetype: Optional[SupportedFiletype], custom_storer: Optional[CustomStorerType], path: str)
```

Initialize a `Storer`.

<a id="packages.valory.skills.abstract_round_abci.io.store.Storer.store"></a>

#### store

```python
def store(obj: SupportedObjectType, **kwargs: Any) -> None
```

Load a file from a given path.

