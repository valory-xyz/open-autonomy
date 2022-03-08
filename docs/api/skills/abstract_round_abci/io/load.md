<a id="packages.valory.skills.abstract_round_abci.io.load"></a>

# packages.valory.skills.abstract`_`round`_`abci.io.load

This module contains all the loading operations of the behaviours.

<a id="packages.valory.skills.abstract_round_abci.io.load.AbstractLoader"></a>

## AbstractLoader Objects

```python
class AbstractLoader(ABC)
```

An abstract `Loader` class.

<a id="packages.valory.skills.abstract_round_abci.io.load.AbstractLoader.load"></a>

#### load

```python
@abstractmethod
def load(path: str) -> SupportedObjectType
```

Load a file.

<a id="packages.valory.skills.abstract_round_abci.io.load.CSVLoader"></a>

## CSVLoader Objects

```python
class CSVLoader(AbstractLoader)
```

A csv files Loader.

<a id="packages.valory.skills.abstract_round_abci.io.load.CSVLoader.load"></a>

#### load

```python
def load(path: str) -> NativelySupportedObjectType
```

Read a pandas dataframe from a csv file.

**Arguments**:

- `path`: the path of the csv.

**Returns**:

the pandas dataframe.

<a id="packages.valory.skills.abstract_round_abci.io.load.ForecasterLoader"></a>

## ForecasterLoader Objects

```python
class ForecasterLoader(AbstractLoader)
```

A `pmdarima` forecaster loader.

<a id="packages.valory.skills.abstract_round_abci.io.load.ForecasterLoader.load"></a>

#### load

```python
def load(path: str) -> NativelySupportedObjectType
```

Load a `pmdarima` forecaster.

**Arguments**:

- `path`: path to store the forecaster.

**Returns**:

a `pmdarima.pipeline.Pipeline`.

<a id="packages.valory.skills.abstract_round_abci.io.load.JSONLoader"></a>

## JSONLoader Objects

```python
class JSONLoader(AbstractLoader)
```

A JSON file loader.

<a id="packages.valory.skills.abstract_round_abci.io.load.JSONLoader.load"></a>

#### load

```python
def load(path: str) -> NativelySupportedObjectType
```

Read a json file.

**Arguments**:

- `path`: the path to retrieve the json file from.

**Returns**:

the deserialized json file's content.

<a id="packages.valory.skills.abstract_round_abci.io.load.Loader"></a>

## Loader Objects

```python
class Loader(
    CSVLoader,  ForecasterLoader,  JSONLoader)
```

Class which loads files.

<a id="packages.valory.skills.abstract_round_abci.io.load.Loader.__init__"></a>

#### `__`init`__`

```python
def __init__(filetype: Optional[SupportedFiletype], custom_loader: CustomLoaderType)
```

Initialize a `Loader`.

<a id="packages.valory.skills.abstract_round_abci.io.load.Loader.load"></a>

#### load

```python
def load(path: str) -> SupportedObjectType
```

Load a file from a given path.

