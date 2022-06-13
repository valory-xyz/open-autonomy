<a id="autonomy.configurations.base"></a>

# autonomy.configurations.base

Base configurations.

<a id="autonomy.configurations.base.recurse"></a>

#### recurse

```python
def recurse(obj: Dict[str, Any]) -> Dict[str, Any]
```

Recursively explore a json object until no dictionaries remain.

<a id="autonomy.configurations.base.Service"></a>

## Service Objects

```python
class Service(PackageConfiguration)
```

Service package configuration.

<a id="autonomy.configurations.base.Service.__init__"></a>

#### `__`init`__`

```python
def __init__(name: SimpleIdOrStr, author: SimpleIdOrStr, agent: PublicId, version: str = "", license_: str = "", aea_version: str = "", fingerprint: Optional[Dict[str, str]] = None, fingerprint_ignore_patterns: Optional[Sequence[str]] = None, description: str = "", number_of_agents: int = 4, network: Optional[str] = None, build_entrypoint: Optional[str] = None, overrides: Optional[List] = None) -> None
```

Initialise object.

<a id="autonomy.configurations.base.Service.overrides"></a>

#### overrides

```python
@property
def overrides() -> List
```

Returns component overrides.

<a id="autonomy.configurations.base.Service.overrides"></a>

#### overrides

```python
@overrides.setter
def overrides(obj: List) -> None
```

Set overrides.

<a id="autonomy.configurations.base.Service.json"></a>

#### json

```python
@property
def json() -> Dict
```

Returns an ordered Dict for service config.

<a id="autonomy.configurations.base.Service.validate_config_data"></a>

#### validate`_`config`_`data

```python
@classmethod
def validate_config_data(cls, json_data: Dict, env_vars_friendly: bool = False) -> None
```

Validate config data.

<a id="autonomy.configurations.base.Service.check_overrides_match_spec"></a>

#### check`_`overrides`_`match`_`spec

```python
def check_overrides_match_spec(overrides: List) -> bool
```

Check that overrides are valid.

- number of overrides is 1
- number of overrides == number of agents in spec
- number of overrides is 0

**Arguments**:

- `overrides`: List of overrides

**Returns**:

True if overrides are valid

<a id="autonomy.configurations.base.Service.check_overrides_valid"></a>

#### check`_`overrides`_`valid

```python
def check_overrides_valid(overrides: List, env_vars_friendly: bool = False) -> Dict[ComponentId, Dict[Any, Any]]
```

Uses the aea helper libraries to check individual overrides.

<a id="autonomy.configurations.base.Service.process_component_section"></a>

#### process`_`component`_`section

```python
def process_component_section(component_index: int, component_configuration_json: Dict) -> Tuple[ComponentId, Dict]
```

Process a component configuration in an agent configuration file.

It breaks down in:
- extract the component id
- validate the component configuration
- check that there are only configurable fields

**Arguments**:

- `component_index`: the index of the component in the file.
- `component_configuration_json`: the JSON object.

**Returns**:

the processed component configuration.

<a id="autonomy.configurations.base.Service.try_to_process_singular_override"></a>

#### try`_`to`_`process`_`singular`_`override

```python
@staticmethod
def try_to_process_singular_override(component_id: ComponentId, config_class: ComponentConfiguration, component_configuration_json: Dict) -> Dict
```

Try to process component with a singular component overrides.

<a id="autonomy.configurations.base.Service.try_to_process_nested_fields"></a>

#### try`_`to`_`process`_`nested`_`fields

```python
def try_to_process_nested_fields(component_id: ComponentId, component_index: int, config_class: ComponentConfiguration, component_configuration_json: Dict) -> Dict
```

Try to process component with nested overrides.

