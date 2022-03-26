<a id="packages.valory.skills.abstract_round_abci.io.load"></a>

# packages.valory.skills.abstract`_`round`_`abci.io.load

This module contains all the loading operations of the behaviours.

<a id="packages.valory.skills.abstract_round_abci.io.load.AbstractLoader"></a>

## AbstractLoader Objects

```python
class AbstractLoader(ABC)
```

An abstract `Loader` class.

<a id="packages.valory.skills.abstract_round_abci.io.load.AbstractLoader.load_single_file"></a>

#### load`_`single`_`file

```python
@abstractmethod
def load_single_file(path: str) -> SupportedSingleObjectType
```

Load a single file.

<a id="packages.valory.skills.abstract_round_abci.io.load.AbstractLoader.load"></a>

#### load

```python
def load(path: str, multiple: bool) -> SupportedObjectType
```

Load one or more files.

**Arguments**:

- `path`: the path to the file to load. If multiple, then the path should be a folder with the files.
- `multiple`: whether multiple files are expected to be loaded. The path should be a folder with the files.

**Returns**:

the loaded file.

<a id="packages.valory.skills.abstract_round_abci.io.load.CSVLoader"></a>

## CSVLoader Objects

```python
class CSVLoader(AbstractLoader)
```

A csv files Loader.

<a id="packages.valory.skills.abstract_round_abci.io.load.CSVLoader.load_single_file"></a>

#### load`_`single`_`file

```python
def load_single_file(path: str) -> NativelySupportedSingleObjectType
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

<a id="packages.valory.skills.abstract_round_abci.io.load.ForecasterLoader.load_single_file"></a>

#### load`_`single`_`file

```python
def load_single_file(path: str) -> NativelySupportedSingleObjectType
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

<a id="packages.valory.skills.abstract_round_abci.io.load.JSONLoader.load_single_file"></a>

#### load`_`single`_`file

```python
def load_single_file(path: str) -> NativelySupportedSingleObjectType
```

Read a json file.

**Arguments**:

- `path`: the path to retrieve the json file from.

**Returns**:

the deserialized json file's content.

<a id="packages.valory.skills.abstract_round_abci.io.load.Loader"></a>

## Loader Objects

```python
class Loader(AbstractLoader)
```

Class which loads files.

<a id="packages.valory.skills.abstract_round_abci.io.load.Loader.__init__"></a>

#### `__`init`__`

```python
def __init__(filetype: Optional[SupportedFiletype], custom_loader: CustomLoaderType)
```

Initialize a `Loader`.

<a id="packages.valory.skills.abstract_round_abci.io.load.Loader.load_single_file"></a>

#### load`_`single`_`file

```python
def load_single_file(path: str) -> SupportedSingleObjectType
```

Load a single file.

